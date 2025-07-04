from fastapi import FastAPI, Depends, UploadFile, HTTPException, Query, File, Form, Body

from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import OAuth2AuthorizationCodeBearer
# from azure.identity import DefaultAzureCredential, get_bearer_token_provider
# from azure.storage.blob import BlobServiceClient
# import schemas, utils.crud as crud
# from database import CosmosDB
import os
import uuid
from contextlib import asynccontextmanager
from fastapi.responses import StreamingResponse, Response
import json, asyncio
import logging

from datetime import datetime 
from typing import List
import time

# Import TranscriptionFactory
from utils.audio import inspect_wav, inspect_audio, convert_mp3_to_wav, inspect_mp3
from utils.transcription import TranscriptionFactory
from utils.transcription_batch import TranscriptionBatchFactory
from utils.analyze import AnalysisFactory
from utils.storage import StorageFactory
from utils.states import History, Transcription, Transcript_chunk
# from api_key_auth import ensure_valid_api_key

# API to upload files from blob storage by blob names
from pydantic import BaseModel
from fastapi import Body

class BlobNamesRequest(BaseModel):
    files: list[str]

session_data = {}


# Lifespan handler for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code: initialize database and configure logging
    # app.state.db = None
    # app.state.db = CosmosDB()
    
    # Initialize history state
    app.state.history = []  # List to store History objects
    
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)s: %(asctime)s - %(message)s')
    print("Database initialized.")
    print("History state initialized.")
    yield
    # Shutdown code (optional)
    # Cleanup database connection
    app.state.db = None
    # Clear history state
    app.state.history = None

app = FastAPI(lifespan=lifespan)
# app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, dependencies=[Depends(ensure_valid_api_key)])
# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper functions for history management
def add_history_record(user_id: str, session_id: str, history_type: str = "transcription") -> History:
    """Create a new history record and add it to the application state."""
    history_id = str(uuid.uuid4())
    history_record = History(
        id=history_id,
        user_id=user_id,
        session_id=session_id,
        type=history_type
    )
    app.state.history.append(history_record)
    return history_record

def add_transcription_to_history(history_id: str, transcription: Transcription) -> bool:
    """Add a transcription to an existing history record."""
    for history_record in app.state.history:
        if history_record.id == history_id:
            history_record.transcriptions.append(transcription)
            return True
    return False

def get_history_by_id(history_id: str) -> History:
    """Get a history record by its ID."""
    for history_record in app.state.history:
        if history_record.id == history_id:
            return history_record
    return None

def get_user_history(user_id: str, visible_only: bool = True) -> List[History]:
    """Get all history records for a specific user."""
    user_histories = []
    for history_record in app.state.history:
        if history_record.user_id == user_id:
            if not visible_only or history_record.visible:
                user_histories.append(history_record)
    return user_histories

def get_session_history(session_id: str, visible_only: bool = True) -> List[History]:
    """Get all history records for a specific session."""
    session_histories = []
    for history_record in app.state.history:
        if history_record.session_id == session_id:
            if not visible_only or history_record.visible:
                session_histories.append(history_record)
    return session_histories


def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@app.get("/health")
async def health_check():
    logger = logging.getLogger("health_check")
    logger.setLevel(logging.INFO)
    logger.info("Health check endpoint called")
    # print("Health check endpoint called")
    return {"status": "healthy"}

# API to list blobs in storage for frontend selection
@app.get("/loadfiles")
async def load_files():
    logger = logging.getLogger("load_files")
    logger.setLevel(logging.INFO)
    try:
        storage = StorageFactory()
        blobs = storage.list_blobs()
        logger.info(f"Found {len(blobs)} blobs in storage.")
        return {"files": blobs}
    except Exception as e:
        logger.error(f"Error listing blobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list blobs from storage")
    


@app.post("/uploadfromblob")
async def upload_from_blob(request: BlobNamesRequest = Body(...)):
    logger = logging.getLogger("upload_from_blob")
    logger.setLevel(logging.INFO)
    file_infos = []
    storage = StorageFactory()
    for blob_name in request.files:
        logger.info(f"Downloading and processing blob: {blob_name}")
        try:
            temp_path = f"./data/upload_{os.path.basename(blob_name)}"
            storage.download_file(blob_name, temp_path)
            # Inspect the audio file type first
            try:
                audio_info = inspect_audio(temp_path)
            except Exception as e:
                audio_info = {"filetype": "unknown", "success": False, "message": str(e)}

            # If it's mp3, convert to wav and update temp_path
            if audio_info.get("filetype") == "mp3":
                try:
                    inspection_info = inspect_mp3(temp_path)
                except Exception as e:
                    audio_info["conversion_error"] = str(e)
            elif audio_info.get("filetype") == "wav":
                inspection_info = inspect_wav(temp_path)

            # Determine the filename to report (converted or original), only keep the filename, not the whole path
            converted_path = audio_info.get("converted_wav_path")
            if converted_path:
                result_filename = os.path.basename(converted_path)
            else:
                result_filename = os.path.basename(temp_path)
            file_infos.append({
                "filename": result_filename,
                "filename_original": os.path.basename(blob_name),
                "inspect": inspection_info,
                "filetype": audio_info.get("filetype"),
                "audio_type": audio_info
            })
        except Exception as err:
            logger.error(f"Error processing blob {blob_name}: {str(err)}")
            file_infos.append({
                "filename": os.path.basename(blob_name),
                "error": str(err)
            })
    return {"status": "success", "files": file_infos}


@app.post("/upload")
async def upload_files(indexName: str = Form(...), files: List[UploadFile] = File(...)):
    logger = logging.getLogger("upload_files")
    logger.setLevel(logging.INFO)
    logger.info(f"Received indexName: {indexName}")
    file_infos = []
    for file in files:
        logger.info(f"Uploading file: {file.filename}")
        try:
            # Save uploaded file to a temporary location
            temp_path = f"./data/upload_{file.filename}"
            contents = await file.read()
            with open(temp_path, "wb") as f_out:
                f_out.write(contents)
            # Inspect the audio file type first
            try:
                audio_info = inspect_audio(temp_path)
            except Exception as e:
                audio_info = {"filetype": "unknown", "success": False, "message": str(e)}

            # If it's mp3, convert to wav and update temp_path
            if audio_info.get("filetype") == "mp3":
                try:
                    # conv_result = convert_mp3_to_wav(temp_path)
                    # Update temp_path to point to the new wav file
                    # temp_path = conv_result["output"]
                    # audio_info["converted_to_wav"] = True
                    # audio_info["converted_wav_path"] = temp_path
                    inspection_info = inspect_mp3(temp_path)
                    
                except Exception as e:
                    audio_info["conversion_error"] = str(e)
            elif audio_info.get("filetype") == "wav":
                # audio_info["converted_to_wav"] = False
                # audio_info["converted_wav_path"] = None
                inspection_info = inspect_wav(temp_path)

            # Determine the filename to report (converted or original), only keep the filename, not the whole path
            converted_path = audio_info.get("converted_wav_path")
            if converted_path:
                result_filename = os.path.basename(converted_path)
            else:
                result_filename = os.path.basename(temp_path)
            file_infos.append({
                "filename": result_filename,
                "filename_original": os.path.basename(file.filename),
                "inspect": inspection_info,
                "filetype": audio_info.get("filetype"),
                "audio_type": audio_info
            })
        except Exception as err:
            logger.error(f"Error processing file {file.filename}: {str(err)}")
            file_infos.append({
                "filename": file.filename,
                "error": str(err)
            })
    return {"status": "success", "files": file_infos}


# Refactored: file is a string (filename), not UploadFile
@app.post("/submit")
async def submit_transcription(
    file_name: str = Form(...),
    file_name_original: str = Form(...),
    temperature: float = Form(...),
    diarization: str = Form(...),
    language: str = Form(...),
    combine: str = Form(...),
    user_id: str = Form(None),
    session_id: str = Form(None),
    model: str = Form(None),
):
    logger = logging.getLogger("submit_transcription")
    logger.setLevel(logging.INFO)
    logger.info(f"Received file: {file_name}")
    logger.info(f"Temperature: {temperature}, Diarization: {diarization}, Language: {language}, Combine: {combine}, User ID: {user_id}, Session ID: {session_id}, Model: {model}")

    try:
        # Use the provided file name as the path (assume it's in ./data or is a full path)
        if os.path.isabs(file_name):
            temp_path = file_name
        else:
            temp_path = f"./data/{file_name}"
        if not os.path.exists(temp_path):
            raise HTTPException(status_code=404, detail=f"File not found: {temp_path}")
        logger.info(f"Using file at path: {temp_path}")

        # Inspect the audio file type first
        try:
            audio_info = inspect_audio(temp_path)
            logger.info(f"Audio inspection result: {audio_info}")
        except Exception as e:
            audio_info = {"filetype": "unknown", "success": False, "message": str(e)}
            logger.error(f"Error inspecting audio file: {str(e)}")


        # If it's mp3, convert to wav and update temp_path
        if audio_info.get("filetype") == "mp3":
            try:
                conv_result = convert_mp3_to_wav(temp_path)
                temp_path = conv_result["output"]
                logger.info(f"Converted MP3 to WAV: {temp_path}")
            except Exception as e:
                audio_info["conversion_error"] = str(e)
                logger.error(f"Error converting MP3 to WAV: {str(e)}")
        elif audio_info.get("filetype") == "wav":
            logger.info("File is already in WAV format, no conversion needed.")
        else:
            raise HTTPException(status_code=400, detail="Unsupported audio format")
        
        if model == "msft":
            
            # After conversion to wav, check if stereo and convert to mono if needed
            from utils.audio import convert_stereo_wav_to_mono
            inspection_info = inspect_wav(temp_path)
            logger.info(f"Audio inspection info before mono check: {inspection_info}")
            if inspection_info.get("channels") == 2:
                logger.info(f"Converting stereo WAV to mono: {temp_path}")
                mono_result = convert_stereo_wav_to_mono(temp_path)
                logger.info(mono_result["message"])
                # Re-inspect after conversion
                inspection_info = inspect_wav(temp_path)
                logger.info(f"Audio inspection info after mono conversion: {inspection_info}")


            # Prepare the transcription factory with the saved file path
            factory = TranscriptionFactory(
                conversationfilename=temp_path,
                language=language,
                channels=int(inspection_info["channels"]),
                bits_per_sample=int(inspection_info["bits_per_sample"]),
                samples_per_second=int(inspection_info["samples_per_second"]),
            )
            logger.info("TranscriptionFactory initialized successfully.")
        elif model == "llm":
            
            inspection_info = inspect_wav(temp_path)
            logger.info(f"Audio inspection info for LLM: {inspection_info}")
        

            # Prepare the transcription factory with the saved file path
            factory = TranscriptionFactory(
                conversationfilename=temp_path,
                language=language,
                channels=int(inspection_info["channels"]),
                bits_per_sample=int(inspection_info["bits_per_sample"]),
                samples_per_second=int(inspection_info["samples_per_second"]),
            )
            logger.info("TranscriptionFactory initialized successfully.")

        
        elif model == "whisper":
            # Upload processed file to blob storage for batch transcription
            blob_url = None
            try:
                storage = StorageFactory()
                blob_name = f"{os.path.basename(temp_path)}"
                # Generate SAS token for read access (valid for 24 hours)
                blob_url = storage.upload_file(temp_path, blob_name, generate_sas=True, sas_expiry_hours=24)
                logger.info(f"Successfully uploaded file to blob storage with SAS token: {blob_url}")
            except Exception as e:
                logger.error(f"Failed to upload file to blob storage: {str(e)}")
                # Continue with local file processing for non-batch models

            factory = TranscriptionBatchFactory()


        # Create history record if user_id and session_id are provided
        history_record = None
        transcription_record = None
        if user_id and session_id:
            # Check if there's already a history record for this session
            existing_histories = get_session_history(session_id, visible_only=False)
            if existing_histories:
                # Use the most recent history record for this session
                history_record = existing_histories[-1]
                logger.info(f"Using existing history record: {history_record.id}")
            else:
                # Create a new history record
                history_record = add_history_record(user_id, session_id)
                logger.info(f"Created new history record: {history_record.id}")
            
            # Create transcription record
            transcription_record = Transcription(
                file_name=file_name,
                file_name_original=file_name_original,
                language=language,
                model=model,
                temperature=temperature,
                diarization=diarization,
                combine=combine,
                status="pending"
            )
            
            # Add transcription to history
            add_transcription_to_history(history_record.id, transcription_record)
            logger.info(f"Added transcription to history record: {history_record.id}")

        def event_stream():
            import queue
            q = queue.Queue()

            def callback(event_dict):
                # Update transcription record status and content if available
                if transcription_record:
                    if event_dict.get("event_type") == "transcribed":
                        # Create a transcript chunk from the event data
                        chunk = Transcript_chunk(
                            event_type=event_dict.get("event_type", "transcribed"),
                            session=event_dict.get("session"),
                            offset=event_dict.get("offset"),
                            duration=event_dict.get("duration"),
                            text=event_dict.get("text", ""),
                            speaker_id=event_dict.get("speaker_id"),
                            result_id=event_dict.get("result_id"),
                            filename=event_dict.get("filename", transcription_record.file_name),
                            language=transcription_record.language
                        )
                        transcription_record.transcript_chunks.append(chunk)
                        logger.info(f"Added transcript chunk with {len(event_dict.get('text', ''))} characters")
                    elif event_dict.get("event_type") == "transcript":
                        # Handle legacy transcript events that might contain full text
                        # Create a single chunk for backward compatibility
                        chunk = Transcript_chunk(
                            event_type="transcribed",
                            text=event_dict.get("text", ""),
                            filename=transcription_record.file_name,
                            language=transcription_record.language
                        )
                        transcription_record.transcript_chunks.append(chunk)
                        transcription_record.status = "completed"
                        logger.info("Updated transcription record with legacy transcript text")
                    elif event_dict.get("event_type") in ("closing", "session_stopped"):
                        if transcription_record.status == "pending":
                            transcription_record.status = "completed"
                        logger.info(f"Final transcription status: {transcription_record.status}")
                    elif event_dict.get("event_type") == "error":
                        transcription_record.status = "failed"
                        logger.error("Transcription failed, updated status")
                
                # logger.info(f"callback: Received event: {event_dict}")
                q.put(event_dict)

            import threading
            if model == "llm":
                if inspection_info.get("channels") == 2:
                    logger.info("Starting LLM transcription with stereo audio.")
                    t = threading.Thread(target=factory.conversation_transcription_llm_advanced, kwargs={"callback": callback})
                else:
                    logger.info("Starting LLM transcription with mono audio.")
                    t = threading.Thread(target=factory.conversation_transcription_llm, kwargs={"callback": callback})
            elif model == "whisper":
                logger.info("Starting Whisper transcription with batch factory.")
                if blob_url:
                    content_url = blob_url
                    logger.info(f"Using uploaded blob URL for Whisper transcription: {content_url}")
                else:
                    logger.warning("No blob URL available, falling back to local file processing")
                    # Fallback to a default URL or raise an error
                    raise HTTPException(status_code=500, detail="Failed to upload file to blob storage for batch transcription")
                t = threading.Thread(target=factory.transcribe_batch, kwargs={"content_url": content_url, "model": "whisper", "callback": callback})
            elif model == "msft":
                logger.info("Starting MSFT transcription.")
                t = threading.Thread(target=factory.conversation_transcription, kwargs={"callback": callback})
            else:
                logger.error(f"Invalid model specified: {model}")
                raise HTTPException(status_code=400, detail="Invalid model specified. Use 'llm', 'whisper', or 'msft'.")
            t.start()

            while True:
                logger.info("event_stream: Waiting for events...")
                event = q.get()
                # logger.info(f"event_stream: Received event: {event}")
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("event_type") in ("closing","session_stopped"):
                    logger.info("event_stream: Ending stream on session_stopped or closing event.")
                    break
            t.join()

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error processing transcription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process transcription")

# Batch transcription endpoint
@app.post("/submit_batch")
async def submit_batch_transcription(
    contentUrls: List[str] = Form(...),
    language: str = Form(None),
    display_name: str = Form("My Transcription"),
    candidate_locales: List[str] = Form(None),
    channels: int = Form(None),
    bits_per_sample: int = Form(None),
    samples_per_second: int = Form(None),
    user_id: str = Form(None),
    session_id: str = Form(None),
):
    logger = logging.getLogger("submit_batch_transcription")
    logger.setLevel(logging.INFO)
    logger.info(f"Received batch contentUrls: {contentUrls}")
    logger.info(f"Language: {language}, Display Name: {display_name}, Candidate Locales: {candidate_locales}, Channels: {channels}, Bits/Sample: {bits_per_sample}, Sample Rate: {samples_per_second}")

    try:
        # Prepare the transcription factory
        factory = TranscriptionFactory(
            language=language,
            channels=channels,
            bits_per_sample=bits_per_sample,
            samples_per_second=samples_per_second,
        )

        def event_stream():
            import queue
            import threading
            q = queue.Queue()
            results_holder = {"results": None}

            def callback(event_dict):
                # Only put status events, not final results, until the end
                if event_dict.get("event_type") == "transcribed_batch":
                    results_holder["results"] = event_dict
                else:
                    q.put(event_dict)

            def run_batch():
                # Call the batch transcription
                _ = factory.conversation_transcription_batch(
                    contentUrls=contentUrls,
                    callback=callback,
                    locale=language,
                    display_name=display_name,
                    candidate_locales=candidate_locales,
                )
                # After completion, put the final event
                if results_holder["results"]:
                    q.put(results_holder["results"])
                else:
                    # If no results, send a failed event
                    q.put({"event_type": "transcribed_batch", "results": []})

            t = threading.Thread(target=run_batch)
            t.start()

            while True:
                event = q.get()
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("event_type") == "transcribed_batch":
                    break
            t.join()

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error processing batch transcription: {str(e)}")
        # raise HTTPException(status_code=500, detail="Failed to process batch transcription")



@app.post("/analyze")
async def analyze_transcript(
    transcript: str = Form(..., example="This is a sample transcript."),
    customPrompt: str = Form(None),
):
    """
    Analyze a transcript sent via POST. Expects transcript and optional customPrompt.
    Returns a simple analysis (e.g., word count, sentence count, keywords).
    """
    logger = logging.getLogger("analyze_transcript")
    logger.setLevel(logging.INFO)

    text = transcript
    if not text:
        raise HTTPException(status_code=400, detail="No transcript text provided.")
    
    try:
        af = AnalysisFactory()

        import queue
        import threading
        q = queue.Queue()

        def callback(event_dict):
            q.put(event_dict)

        def run_analysis():
            if customPrompt and customPrompt.strip():
                af.analyze_transcript(text, callback=callback, custom_prompt=customPrompt)
            else:
                af.analyze_transcript(text, callback=callback)

        t = threading.Thread(target=run_analysis)
        t.start()

        def event_stream():
            while True:
                event = q.get()
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("message") == "Query executed successfully":
                    break
            t.join()

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error initializing AnalysisFactory: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initialize analysis factory")


# History Management Endpoints

@app.post("/history/create")
async def create_history_record(
    user_id: str = Form(...),
    session_id: str = Form(...),
    history_type: str = Form("transcription")
):
    """Create a new history record."""
    logger = logging.getLogger("create_history_record")
    logger.setLevel(logging.INFO)
    
    try:
        history_record = add_history_record(user_id, session_id, history_type)
        logger.info(f"Created history record with ID: {history_record.id}")
        return {
            "status": "success",
            "history_id": history_record.id,
            "message": "History record created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating history record: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create history record")

@app.get("/history/user/{user_id}")
async def get_user_history_endpoint(
    user_id: str,
    visible_only: bool = Query(True, description="Show only visible records")
):
    """Get all history records for a specific user."""
    logger = logging.getLogger("get_user_history")
    logger.setLevel(logging.INFO)
    
    try:
        histories = get_user_history(user_id, visible_only)
        logger.info(f"Found {len(histories)} history records for user {user_id}")
        return {
            "status": "success",
            "user_id": user_id,
            "count": len(histories),
            "histories": histories
        }
    except Exception as e:
        logger.error(f"Error retrieving user history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user history")

@app.get("/history/session/{session_id}")
async def get_session_history_endpoint(
    session_id: str,
    visible_only: bool = Query(True, description="Show only visible records")
):
    """Get all history records for a specific session."""
    logger = logging.getLogger("get_session_history")
    logger.setLevel(logging.INFO)
    
    try:
        histories = get_session_history(session_id, visible_only)
        logger.info(f"Found {len(histories)} history records for session {session_id}")
        return {
            "status": "success",
            "session_id": session_id,
            "count": len(histories),
            "histories": histories
        }
    except Exception as e:
        logger.error(f"Error retrieving session history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session history")

@app.get("/history/{history_id}")
async def get_history_record(history_id: str):
    """Get a specific history record by ID."""
    logger = logging.getLogger("get_history_record")
    logger.setLevel(logging.INFO)
    
    try:
        history_record = get_history_by_id(history_id)
        if not history_record:
            raise HTTPException(status_code=404, detail="History record not found")
        
        logger.info(f"Retrieved history record: {history_id}")
        return {
            "status": "success",
            "history": history_record
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving history record: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history record")

@app.put("/history/{history_id}/visibility")
async def toggle_history_visibility(
    history_id: str,
    visible: bool = Form(...)
):
    """Toggle the visibility of a history record."""
    logger = logging.getLogger("toggle_history_visibility")
    logger.setLevel(logging.INFO)
    
    try:
        history_record = get_history_by_id(history_id)
        if not history_record:
            raise HTTPException(status_code=404, detail="History record not found")
        
        history_record.visible = visible
        logger.info(f"Updated visibility for history record {history_id} to {visible}")
        return {
            "status": "success",
            "history_id": history_id,
            "visible": visible,
            "message": "History visibility updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating history visibility: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update history visibility")

@app.get("/history")
async def get_all_history(
    visible_only: bool = Query(True, description="Show only visible records"),
    limit: int = Query(100, description="Maximum number of records to return")
):
    """Get all history records (with optional filtering)."""
    logger = logging.getLogger("get_all_history")
    logger.setLevel(logging.INFO)
    
    try:
        histories = app.state.history if app.state.history else []
        if visible_only:
            histories = [h for h in histories if h.visible]
        
        # Apply limit
        histories = histories[:limit]
        
        logger.info(f"Retrieved {len(histories)} history records")
        return {
            "status": "success",
            "count": len(histories),
            "histories": histories
        }
    except Exception as e:
        logger.error(f"Error retrieving all history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history records")


@app.post("/history/{history_id}/transcription/{transcription_index}/analysis")
async def add_analysis_to_transcription(
    history_id: str,
    transcription_index: int,
    analysis_text: str = Form(...)
):
    """Add analysis results to a specific transcription in a history record."""
    logger = logging.getLogger("add_analysis_to_transcription")
    logger.setLevel(logging.INFO)
    
    try:
        history_record = get_history_by_id(history_id)
        if not history_record:
            raise HTTPException(status_code=404, detail="History record not found")
        
        if transcription_index >= len(history_record.transcriptions) or transcription_index < 0:
            raise HTTPException(status_code=400, detail="Invalid transcription index")
        
        history_record.transcriptions[transcription_index].analysis = analysis_text
        logger.info(f"Added analysis to transcription {transcription_index} in history {history_id}")
        
        return {
            "status": "success",
            "history_id": history_id,
            "transcription_index": transcription_index,
            "message": "Analysis added successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding analysis to transcription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add analysis to transcription")

@app.get("/history/{history_id}/transcriptions")
async def get_transcriptions_from_history(history_id: str):
    """Get all transcriptions from a specific history record."""
    logger = logging.getLogger("get_transcriptions_from_history")
    logger.setLevel(logging.INFO)
    
    try:
        history_record = get_history_by_id(history_id)
        if not history_record:
            raise HTTPException(status_code=404, detail="History record not found")
        
        logger.info(f"Retrieved {len(history_record.transcriptions)} transcriptions from history {history_id}")
        return {
            "status": "success",
            "history_id": history_id,
            "count": len(history_record.transcriptions),
            "transcriptions": history_record.transcriptions
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transcriptions from history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve transcriptions from history")