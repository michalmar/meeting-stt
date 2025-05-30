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
from utils.analyze import AnalysisFactory
# from api_key_auth import ensure_valid_api_key

session_data = {}


# Lifespan handler for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code: initialize database and configure logging
    # app.state.db = None
    # app.state.db = CosmosDB()
    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)s: %(asctime)s - %(message)s')
    print("Database initialized.")
    yield
    # Shutdown code (optional)
    # Cleanup database connection
    app.state.db = None

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


def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@app.get("/health")
async def health_check():
    logger = logging.getLogger("health_check")
    logger.setLevel(logging.INFO)
    logger.info("Health check endpoint called")
    # print("Health check endpoint called")
    return {"status": "healthy"}

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
                result_filename = file.filename
            file_infos.append({
                "filename": result_filename,
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

@app.post("/submit")
async def submit_transcription(
    file: UploadFile = File(...),
    temperature: float = Form(...),
    diarization: str = Form(...),
    language: str = Form(...),
    combine: str = Form(...),
    user_id: str = Form(None),
    session_id: str = Form(None),
    model: str = Form(None),  # <-- added model parameter
):
    logger = logging.getLogger("submit_transcription")
    logger.setLevel(logging.INFO)
    logger.info(f"Received file: {file.filename}")
    logger.info(f"Temperature: {temperature}, Diarization: {diarization}, Language: {language}, Combine: {combine}, User ID: {user_id}, Session ID: {session_id}, Model: {model}")
    # logger.info(f"Channels: {channels}, Bits/Sample: {bits_per_sample}, Sample Rate: {samples_per_second}")

    try:
        # Read and save the uploaded file to a temporary location
        contents = await file.read()
        logger.info(f"File size: {len(contents)} bytes")
        temp_path = f"./data/upload_{file.filename}"
        with open(temp_path, "wb") as f_out:
            f_out.write(contents)
        logger.info(f"File saved to temporary path: {temp_path}")
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
                # Update temp_path to point to the new wav file
                temp_path = conv_result["output"]          
                logger.info(f"Converted MP3 to WAV: {temp_path}")      
            except Exception as e:
                audio_info["conversion_error"] = str(e)
                logger.error(f"Error converting MP3 to WAV: {str(e)}")
        elif audio_info.get("filetype") == "wav":
            logger.info("File is already in WAV format, no conversion needed.")
            pass
        else:
            raise HTTPException(status_code=400, detail="Unsupported audio format")
        
        inspection_info = inspect_wav(temp_path)
        logger.info(f"Audio inspection info: {inspection_info}")


        # Prepare the transcription factory with the saved file path
        factory = TranscriptionFactory(
            conversationfilename=temp_path,
            language=language,
            channels=int(inspection_info["channels"]),
            bits_per_sample=int(inspection_info["bits_per_sample"]),
            samples_per_second=int(inspection_info["samples_per_second"]),
        )
        logger.info("TranscriptionFactory initialized successfully.")

        def event_stream():
            # Use a queue to communicate between callback and generator
            import queue
            q = queue.Queue()

            def callback(event_dict):
                logger.info(f"callback: Received event: {event_dict}")
                q.put(event_dict)

            # Run transcription in a thread to avoid blocking
            import threading
            if model == "llm":
                logger.info("Starting LLM transcription.")
                t = threading.Thread(target=factory.conversation_transcription_llm, kwargs={"callback": callback})
            elif model == "msft":
                logger.info("Starting MSFT transcription.")
                t = threading.Thread(target=factory.conversation_transcription, kwargs={"callback": callback})
            else:
                logger.error(f"Invalid model specified: {model}")
                raise HTTPException(status_code=400, detail="Invalid model specified. Use 'llm' or 'asr'.")
            # t = threading.Thread(target=factory.conversation_transcription, kwargs={"callback": callback})
            # t = threading.Thread(target=factory.conversation_transcription_llm, kwargs={"callback": callback})
            t.start()

            while True:
                logger.info("event_stream: Waiting for events...")
                event = q.get()
                logger.info(f"event_stream: Received event: {event}")
                yield f"data: {json.dumps(event)}\n\n"
                # Optionally break on a certain event type
                # if event.get("event_type") in ("closing", "session_stopped", "canceled"):
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
    # transcript: dict = Body(..., example={"text": "This is a sample transcript."}),
    transcript: str = Form(..., example="This is a sample transcript."),
    # user_id: str = None,
    # session_id: str = None
):
    """
    Analyze a transcript sent via POST. Expects JSON: {"text": "..."}
    Returns a simple analysis (e.g., word count, sentence count, keywords).
    """
    logger = logging.getLogger("analyze_transcript")
    logger.setLevel(logging.INFO)
    # logger.info(f"Received transcript for analysis. User: {user_id}, Session: {session_id}")

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
            af.analyze_transcript(text, callback=callback)

        t = threading.Thread(target=run_analysis)
        t.start()

        def event_stream():
            while True:
                event = q.get()
                # event_json = json.loads(event["data"]["text"])

                yield f"data: {json.dumps(event)}\n\n"
                # End on a final message (could be improved to check for a specific key)
                if event.get("message") == "Query executed successfully":
                    break
            t.join()

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error initializing AnalysisFactory: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initialize analysis factory")