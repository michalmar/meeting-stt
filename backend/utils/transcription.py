#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.
"""
Conversation transcription samples for the Microsoft Cognitive Services Speech SDK
"""

import time
import os
import logging
from scipy.io import wavfile
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech.transcription import ConversationTranscriptionEventArgs,ConversationTranscriptionResult
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(override=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Set up the subscription info for the Speech Service:
# Replace with your own subscription key and endpoint.
# See the limitations in supported regions,
# https://docs.microsoft.com/azure/cognitive-services/speech-service/how-to-use-conversation-transcription
speech_key = os.getenv("AZURE_SPEECH_KEY")
speech_endpoint = os.getenv("AZURE_SPEECH_ENDPOINT")

class TranscriptionFactory:

    def __init__(self, 
                 speech_key=None, 
                 speech_endpoint=None,
                 speech_region=None,
                 conversationfilename="./data/test-transcription-cz.wav",
                 channels=1,
                 bits_per_sample=16,
                 samples_per_second=24000,
                 language="cs-CZ"):
        
       
        logger = logging.getLogger(__name__)
        logger.info("Initializing TranscriptionFactory with provided parameters or environment variables.")
        
        self.speech_key = speech_key or os.getenv("AZURE_SPEECH_KEY")
        self.speech_endpoint = speech_endpoint or os.getenv("AZURE_SPEECH_ENDPOINT")
        self.speech_region = speech_region or os.getenv("AZURE_SPEECH_REGION")
        self.conversationfilename = conversationfilename
        self.channels = channels
        self.bits_per_sample = bits_per_sample
        self.samples_per_second = samples_per_second
        self.language = language

    def conversation_transcription_batch(self, contentUrls, callback=None, locale=None, display_name="My Transcription", candidate_locales=None, poll_interval=5):
        """
        Submits a batch transcription job to Azure Speech-to-Text REST API, polls for completion, and retrieves results.
        Args:
            contentUrls (list): List of URLs to audio files.
            callback (function): Optional callback for status updates.
            locale (str): Locale for transcription (default: self.language).
            display_name (str): Display name for the transcription job.
            candidate_locales (list): Candidate locales for language identification.
            poll_interval (int): Seconds between polling status.
        Returns:
            List of transcription result dicts.
        """
        import requests
        import time
        import logging

        logger = logging.getLogger(__name__)
        logger.info("Starting batch transcription with provided parameters or environment variables.")

        # Use instance or environment variables for key/endpoint
        subscription_key = self.speech_key
        endpoint = self.speech_endpoint
        region = self.speech_region
       

        api_base = endpoint
        transcription_url = f"{api_base}speechtotext/v3.2/transcriptions"
        logger.info(f"Transcription API URL: {transcription_url}")  

        # Prepare request body
        locale = locale or self.language or "en-US"
        logging.info(f"Using locale: {locale}")
        candidate_locales = candidate_locales or [locale]
        logging.info(f"Using candidate locales: {candidate_locales}")
        body = {
            "contentUrls": contentUrls,
            "locale": locale,
            "displayName": display_name,
            # "model": None,
            # "model": { # 20241218
            #     "self": f"{api_base}speechtotext/v3.2/models/base/06fbc28e-1f76-4d3e-8ea1-40b8e873929e"
            # },
            "model": { # Whisper V2
                "self": f"{api_base}speechtotext/v3.2/models/base/69adf293-9664-4040-932b-02ed16332e00"
            },
            # "model": { # Whisper V2
            #     "self": "69adf293-9664-4040-932b-02ed16332e00"
            # },
            
            "properties": {
                "wordLevelTimestampsEnabled": False,
                "displayFormWordLevelTimestampsEnabled": True,
                "diarizationEnabled": True,
                "punctuationMode": "DictatedAndAutomatic",
                "profanityFilterMode": "Masked"
            },
        }

        headers = {
            "Ocp-Apim-Subscription-Key": subscription_key,
            "Content-Type": "application/json"
        }

        # Submit batch transcription job
        try:
            response = requests.post(transcription_url, json=body, headers=headers)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Failed to submit transcription job: {e}")
            raise

        job = response.json()
        # The job location is in the 'Location' header, or get id from job['self']
        transcription_id = None
        if 'Location' in response.headers:
            transcription_id = response.headers['Location'].split('/')[-1]
        elif 'self' in job:
            transcription_id = job['self'].split('/')[-1]
        else:
            raise RuntimeError("Could not determine transcription job ID.")

        status_url = f"{transcription_url}/{transcription_id}"
        files_url = f"{transcription_url}/{transcription_id}/files"

        # Poll for job completion
        status = None
        max_wait = 60 * 30  # 30 minutes max
        waited = 0
        while True:
            try:
                status_resp = requests.get(status_url, headers=headers)
                status_resp.raise_for_status()
                status_json = status_resp.json()
                status = status_json.get('status')
                if callback:
                    callback({"event_type": "status", "status": status, "details": status_json, "duration": waited})
                if status in ("Succeeded", "Failed", "Canceled"):
                    break
            except Exception as e:
                logging.warning(f"Error polling transcription status: {e}")
            time.sleep(poll_interval)
            waited += poll_interval
            if waited > max_wait:
                raise TimeoutError("Transcription job polling timed out.")

        if status != "Succeeded":
            raise RuntimeError(f"Transcription job did not succeed. Status: {status}")

        # Get result files
        try:
            files_resp = requests.get(files_url, headers=headers)
            files_resp.raise_for_status()
            files_json = files_resp.json()
        except Exception as e:
            logging.error(f"Failed to get transcription files: {e}")
            raise

        results = []
        for file_info in files_json.get('values', []):
            if file_info.get('kind') == 'Transcription':
                content_url = file_info['links']['contentUrl']
                try:
                    content_resp = requests.get(content_url)
                    content_resp.raise_for_status()
                    result_json = content_resp.json()
                    results.append(result_json)
                    transcription_object = {
                        "event_type": "transcribed_batch",
                        "filename": file_info,
                        "session": None,
                        "duration": result_json.get('durationMilliseconds'),
                        "combinedRecognizedPhrases": result_json.get('combinedRecognizedPhrases', []),
                        "recognizedPhrases": result_json.get('recognizedPhrases', [])
                        # "properties": evt.result.properties,
                    }
                    {'recognitionStatus': 'Success', 'channel': 0, 'offset': 'PT0.07S', 'duration': 'PT25S', 'offsetInTicks': 700000.0, 'durationInTicks': 250000000.0, 'durationMilliseconds': 25000, 'offsetMilliseconds': 70, 'nBest': [{...}, {...}, {...}, {...}, {...}]}
                    for phrase in transcription_object["recognizedPhrases"]:
                        transcription_object = {
                            "event_type": "transcribed",
                            "recognitionStatus": phrase.get("recognitionStatus"),
                            "channel": phrase.get("channel"),
                            "duration": phrase.get("durationMilliseconds"),
                            "offset": phrase.get("offsetMilliseconds"),
                            "speaker_id": phrase.get("speaker"),
                            
                            "text": phrase.get("nBest")[0].get("display"),
                            "confidence": phrase.get("nBest")[0].get("confidence"),
                            "filename": file_info.get("name"),
                            # "speaker_id": evt.result.speaker_id,
                            
                        }
                     
                        if callback:
                            callback(transcription_object)

                except Exception as e:
                    logging.warning(f"Failed to fetch transcription result from {content_url}: {e}")
        return results
    
    # This sample demonstrates how to use conversation transcription.
    def conversation_transcription(self, callback=None):
        """transcribes a conversation, using an optional external callback(event_dict)"""
        logger = logging.getLogger(__name__)
        logger.info("Starting conversation transcription with provided parameters or environment variables.")
        

        speech_config = speechsdk.SpeechConfig(subscription=self.speech_key, endpoint=self.speech_endpoint)
        
        
        # azure_credential = DefaultAzureCredential()
        # aadToken = azure_credential.get_token("https://cognitiveservices.azure.com/.default")
        # speech_config = speechsdk.SpeechConfig(auth_token=aadToken.token, region=self.speech_region)
        
        wave_format = speechsdk.audio.AudioStreamFormat(self.samples_per_second, self.bits_per_sample, self.channels)
        stream = speechsdk.audio.PushAudioInputStream(stream_format=wave_format)
        audio_config = speechsdk.audio.AudioConfig(stream=stream)

        transcriber = speechsdk.transcription.ConversationTranscriber(speech_config, audio_config, language=self.language)

        done = False
        transcription_results = []


        def stop_cb(evt: speechsdk.SessionEventArgs):
            """callback that signals to stop continuous transcription upon receiving an event `evt`"""
            # logger.info('CLOSING {}'.format(evt))
            # logger.info(f'Stopping async recognition. {evt.reason}')
            transcription_object = {
                "event_type": "closing",
                "session": evt.session_id,
                "text": None,
                "filename": self.conversationfilename,
                # "offset": evt.offset,
                # "properties": evt.properties,
            }
            nonlocal done
            done = True
            if callback:
                callback(transcription_object)

        def on_transcribed(evt: ConversationTranscriptionEventArgs):
            # print('TRANSCRIBED: {}'.format(evt))
            # logger.info(f'TRANSCRIBED: {evt.result.text}')
            transcription_object = {
                "event_type": "transcribed",
                "session": evt.session_id,
                "offset": evt.offset,
                "duration": evt.result.duration,
                "text": evt.result.text,
                "speaker_id": evt.result.speaker_id,
                "result_id": evt.result.result_id,
                "filename": self.conversationfilename,
                # "properties": evt.result.properties,
            }
            # print('TRANSCRIBED: {}'.format(transcription_object["text"]))
            transcription_results.append(transcription_object)
            if callback:
                callback(transcription_object)


        def on_session_started(evt):
            # print('SESSION STARTED: {}'.format(evt))
            # logger.info(f'SESSION STARTED: {evt.session_id}')
            transcription_object = {
                "event_type": "session_started",
                "session": evt.session_id,
                "text": None,
                "filename": self.conversationfilename,
                # "offset": evt.offset,
                # "properties": evt.properties,
            }
            if callback:
                callback(transcription_object)

        def on_session_stopped(evt):
            # logger.info('SESSION STOPPED {}'.format(evt))
            transcription_object = {
                "event_type": "session_stopped",
                "session": evt.session_id,
                "text": None,
                "filename": self.conversationfilename,
                # "offset": evt.offset,
                # "properties": evt.properties,
            }
            nonlocal done
            done = True
            if callback:
                callback(transcription_object)

        def on_canceled(evt):
            # logger.info('CANCELED {}'.format(evt))
            transcription_object = {
                "event_type": "canceled",
                "session": evt.session_id,
                "text": None,
                "filename": self.conversationfilename,
                "evt": evt.reason,
                # "offset": evt.offset,
                # "properties": evt.properties,
            }
            if callback:
                callback(transcription_object)

        # Subscribe to the events fired by the conversation transcriber
        transcriber.transcribed.connect(on_transcribed)
        transcriber.session_started.connect(on_session_started)
        transcriber.session_stopped.connect(on_session_stopped)
        transcriber.canceled.connect(on_canceled)
        # stop continuous transcription on either session stopped or canceled events
        transcriber.session_stopped.connect(stop_cb)
        transcriber.canceled.connect(stop_cb)

        transcriber.start_transcribing_async()
        logger.info("Transcriber started. Now streaming audio...")

        # Read the whole wave files at once and stream it to sdk
        _, wav_data = wavfile.read(self.conversationfilename)
        logger.info(f"Read {wav_data.shape[0]} samples from {self.conversationfilename}.")
        stream.write(wav_data.tobytes())
        stream.close()
        while not done:
            logger.info('Waiting for transcription to complete...')
            time.sleep(.5)
        
        # save the transcription results to a file
        with open("transcription_results.txt", "w") as f:
            for result in transcription_results:
                f.write(f"Session: {result['session']}, Offset: {result['offset']}, Duration: {result['duration']}, Text: {result['text']}, Speaker ID: {result['speaker_id']}, Result ID: {result['result_id']}\n")
        logger.info("Transcription completed. Results saved to transcription_results.txt.")
        transcriber.stop_transcribing_async()
        logger.info("Transcriber stopped.")

    # This sample demonstrates how to use conversation transcription.
    def conversation_transcription_from_microphone(self, callback=None):
        """Transcribes a conversation from the default microphone input. Optionally accepts a callback(event_dict)."""
        speech_config = speechsdk.SpeechConfig(subscription=self.speech_key, endpoint=self.speech_endpoint)
        transcriber = speechsdk.transcription.ConversationTranscriber(speech_config)

        done = False
        transcription_results = []

        def stop_cb(evt: speechsdk.SessionEventArgs):
            print('CLOSING {}'.format(evt))
            transcription_object = {
                "event_type": "closing",
                "session": evt.session_id,
                "text": None,
            }
            nonlocal done
            done = True
            if callback:
                callback(transcription_object)

        def on_transcribed(evt):
            transcription_object = {
                "event_type": "transcribed",
                "session": evt.session_id,
                "offset": evt.offset,
                "duration": evt.result.duration,
                "text": evt.result.text,
                "speaker_id": evt.result.speaker_id,
                "result_id": evt.result.result_id,
            }
            transcription_results.append(transcription_object)
            if callback:
                callback(transcription_object)

        def on_session_started(evt):
            transcription_object = {
                "event_type": "session_started",
                "session": evt.session_id,
                "text": None,
            }
            if callback:
                callback(transcription_object)

        def on_session_stopped(evt):
            print('SESSION STOPPED {}'.format(evt))
            transcription_object = {
                "event_type": "session_stopped",
                "session": evt.session_id,
                "text": None,
            }
            if callback:
                callback(transcription_object)

        def on_canceled(evt):
            print('CANCELED {}'.format(evt))
            transcription_object = {
                "event_type": "canceled",
                "session": evt.session_id,
                "text": None,
            }
            if callback:
                callback(transcription_object)

        # Subscribe to the events fired by the conversation transcriber
        transcriber.transcribed.connect(on_transcribed)
        transcriber.session_started.connect(on_session_started)
        transcriber.session_stopped.connect(on_session_stopped)
        transcriber.canceled.connect(on_canceled)
        # stop continuous transcription on either session stopped or canceled events
        transcriber.session_stopped.connect(stop_cb)
        transcriber.canceled.connect(stop_cb)

        transcriber.start_transcribing_async()

        while not done:
            print('type "stop" then enter when done')
            stop = input()
            if stop.lower() == "stop":
                print('Stopping async recognition.')
                transcriber.stop_transcribing_async()
                break

        # Optionally, save the transcription results to a file
        with open("transcription_results.txt", "w") as f:
            for result in transcription_results:
                f.write(f"Session: {result['session']}, Offset: {result['offset']}, Duration: {result['duration']}, Text: {result['text']}, Speaker ID: {result['speaker_id']}, Result ID: {result['result_id']}\n")



    def conversation_transcription_llm(self, callback=None):
        """
        Transcribes a conversation using an LLM-based API (e.g., OpenAI Whisper/gpt-4o-transcribe),
        outputs results similar to conversation_transcription, and supports an optional callback(event_dict).
        Now expects the LLM to return a JSON array of objects with keys: timestamp, text, speaker, language.
        """
        logger = logging.getLogger(__name__)
        logger.info("Starting LLM-based conversation transcription.")
        import base64
        from openai import AzureOpenAI
        import json
        api_key = os.getenv("AZURE_OPENAI_KEY_TRANSCRIBE")
        api_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_TRANSCRIBE")

        # Initialize Azure OpenAI client with Entra ID authentication
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default"
        )

        client = AzureOpenAI(
            azure_endpoint=api_endpoint,
            azure_ad_token_provider=token_provider,
            api_version="2025-01-01-preview",
        )
        logger.info("Initiated LLM client.")

        prompt_path = Path(__file__).parent.parent / "prompts" / "transcript.jinja2"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except Exception as e:
            logger.error(f"Could not read system prompt file: {e}")
            system_prompt = "You are a professional call transcript analyst assistant. (Prompt file missing)"

        encoded_image = base64.b64encode(open(self.conversationfilename, 'rb').read()).decode('ascii')
        chat_prompt = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": system_prompt
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": encoded_image,
                            "format": "wav"
                        }
                    }
                ]
            }
        ]
        messages = chat_prompt
        transcription_model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME_TRANSCRIBE", "gpt-4o-audio-preview")
        logger.info(f"Sending for transcription with {transcription_model} model.")
        completion = client.chat.completions.create(
            model=transcription_model,
            messages=messages,
            max_tokens=15000,
            temperature=0.0,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=False
        )
        logger.info("Transcribed.")

        transcription_text = completion.choices[0].message.content
        logger.info(f"Transcription result: {transcription_text}")

        #save the transcription result to a file
        with open("transcription_results_TEST.txt", "w") as f:
            f.write(transcription_text)

        # Parse the JSON array returned by the LLM, handling markdown code blocks if present
        import re
        try:
            # Remove markdown code block if present
            match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", transcription_text)
            if match:
                json_str = match.group(1)
            else:
                json_str = transcription_text
            transcription_items = json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to parse LLM transcription as JSON: {e}")
            if callback:
                callback({"event_type": "error", "error": str(e), "raw_content": transcription_text})
            return

        def timestamp_to_ticks(ts):
            """Convert MM:SS or H:MM:SS to milliseconds."""
            try:
                parts = ts.strip().split(":")
                if len(parts) == 2:
                    minutes, seconds = parts
                    total_ms = int(minutes) * 60 * 1000 + int(float(seconds) * 1000)
                elif len(parts) == 3:
                    hours, minutes, seconds = parts
                    total_ms = int(hours) * 3600 * 1000 + int(minutes) * 60 * 1000 + int(float(seconds) * 1000)
                else:
                    total_ms = 0
                return total_ms * 10000  # Convert to ticks (1 tick = 100 nanoseconds)
            except Exception:
                return 0

        for item in transcription_items:
            ts = item.get("timestamp")
            offset_ms = timestamp_to_ticks(ts) if ts else None
            transcription_object = {
                "event_type": "transcribed",
                "session": None,
                "offset": offset_ms,
                "duration": None,
                "text": item.get("text"),
                "speaker_id": item.get("speaker"),
                "result_id": None,
                "filename": self.conversationfilename,
                "language": item.get("language"),
            }
            if callback:
                callback(transcription_object)

        logger.info("Finished.")
        if callback:
            callback({"event_type": "session_stopped", "filename": self.conversationfilename})

    def conversation_transcription_llm_advanced(self, callback=None):
        """
        Advanced transcription that splits audio into left/right channels, transcribes each separately,
        then combines them using LLM with combine prompt for better conversation flow.
        """
        logger = logging.getLogger(__name__)
        logger.info("Starting advanced LLM-based conversation transcription with channel separation.")
        
        import base64
        from openai import AzureOpenAI
        import json
        import os
        import tempfile
        from pathlib import Path
        
        # Import the audio channel extraction function
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from utils.audio import extract_audio_channels
        
        # Initialize Azure OpenAI client
        # api_key = os.getenv("AZURE_OPENAI_KEY_TRANSCRIBE")
        api_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_endpoint_transcribe = os.getenv("AZURE_OPENAI_ENDPOINT_TRANSCRIBE")

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default"
        )

        client = AzureOpenAI(
            azure_endpoint=api_endpoint,
            azure_ad_token_provider=token_provider,
            api_version="2025-01-01-preview",
        )
        client_transcribe = AzureOpenAI(
            azure_endpoint=api_endpoint_transcribe,
            azure_ad_token_provider=token_provider,
            api_version="2025-01-01-preview",
        )
        logger.info("Initiated LLM client.")

        # Step 1: Split audio into left and right channels
        logger.info("Step 1: Splitting audio into left and right channels...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            left_channel_path = os.path.join(temp_dir, "left_channel.wav")
            right_channel_path = os.path.join(temp_dir, "right_channel.wav")
            
            # Extract channels
            channel_result = extract_audio_channels(
                self.conversationfilename,
                left_output_path=left_channel_path,
                right_output_path=right_channel_path
            )
            
            if not channel_result["success"]:
                logger.error(f"Failed to extract audio channels: {channel_result['message']}")
                if callback:
                    callback({"event_type": "error", "error": channel_result['message']})
                return
            else:
                if callback:
                    callback({"event_type": "channels_extracted", "status": "success"})
            
            logger.info("Successfully split audio into channels.")
            
            # Step 2: Transcribe each channel separately
            logger.info("Step 2: Transcribing each channel...")
            
            # Load transcript prompt
            prompt_path = Path(__file__).parent.parent / "prompts" / "transcript_single.jinja2"
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    transcript_system_prompt = f.read()
            except Exception as e:
                logger.error(f"Could not read transcript prompt file: {e}")
                transcript_system_prompt = "You are a professional call transcript analyst assistant. (Prompt file missing)"
            
            transcription_model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME_TRANSCRIBE", "gpt-4o-audio-preview")
            
            # Transcribe left channel
            logger.info("Transcribing left channel...")
            with open(left_channel_path, 'rb') as f:
                left_audio_data = base64.b64encode(f.read()).decode('ascii')
            
            left_messages = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": transcript_system_prompt}]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": left_audio_data,
                                "format": "wav"
                            }
                        }
                    ]
                }
            ]
            
            left_completion = client_transcribe.chat.completions.create(
                model=transcription_model,
                messages=left_messages,
                max_tokens=15000,
                temperature=0.0,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False
            )
            
            left_transcription = left_completion.choices[0].message.content
            logger.info("Left channel transcribed.")
            if callback:
                callback({"event_type": "transcribed_delta", "channel": "left", "text": left_transcription})
            
            # Transcribe right channel
            logger.info("Transcribing right channel...")
            with open(right_channel_path, 'rb') as f:
                right_audio_data = base64.b64encode(f.read()).decode('ascii')
            
            right_messages = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": transcript_system_prompt}]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": right_audio_data,
                                "format": "wav"
                            }
                        }
                    ]
                }
            ]
            
            right_completion = client_transcribe.chat.completions.create(
                model=transcription_model,
                messages=right_messages,
                max_tokens=15000,
                temperature=0.0,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False
            )
            
            right_transcription = right_completion.choices[0].message.content
            logger.info("Right channel transcribed.")
            if callback:
                callback({"event_type": "transcribed_delta", "channel": "right", "text": right_transcription})

            # Step 3: Combine transcriptions using combine prompt
            logger.info("Step 3: Combining transcriptions...")
            
            # Load combine prompt
            combine_prompt_path = Path(__file__).parent.parent / "prompts" / "combine.jinja2"
            try:
                with open(combine_prompt_path, "r", encoding="utf-8") as f:
                    combine_system_prompt = f.read()
            except Exception as e:
                logger.error(f"Could not read combine prompt file: {e}")
                combine_system_prompt = "You are a customer support call center specialist. Combine the agent and customer transcripts into a single conversation."
            
            # Prepare combine prompt with transcriptions
            combine_user_prompt = f"""
agent channel transcript:
{left_transcription}

customer channel transcript:
{right_transcription}
"""
            
            combine_messages = [
                {
                    "role": "system",
                    "content": combine_system_prompt
                },
                {
                    "role": "user",
                    "content": combine_user_prompt
                }
            ]
            
            # Use a different model for text combination if available, otherwise use the same
            combine_model = os.getenv("MODEL_NAME")
            
            combine_completion = client.chat.completions.create(
                model=combine_model,
                messages=combine_messages,
                max_tokens=15000,
                temperature=0.0,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False
            )
            
            combined_transcription = combine_completion.choices[0].message.content
            logger.info("Transcriptions combined successfully.")
            
            # Save the combined transcription result to a file
            with open("transcription_results_ADVANCED.txt", "w", encoding="utf-8") as f:
                f.write("=== LEFT CHANNEL ===\n")
                f.write(left_transcription)
                f.write("\n\n=== RIGHT CHANNEL ===\n")
                f.write(right_transcription)
                f.write("\n\n=== COMBINED RESULT ===\n")
                f.write(combined_transcription)
            
            # Parse the combined transcription and output through callback
            logger.info("Processing combined transcription results...")
            
            def timestamp_to_ticks(ts):
                """Convert MM:SS or H:MM:SS to milliseconds."""
                try:
                    parts = ts.strip().split(":")
                    if len(parts) == 2:
                        minutes, seconds = parts
                        total_ms = int(minutes) * 60 * 1000 + int(float(seconds) * 1000)
                    elif len(parts) == 3:
                        hours, minutes, seconds = parts
                        total_ms = int(hours) * 3600 * 1000 + int(minutes) * 60 * 1000 + int(float(seconds) * 1000)
                    else:
                        total_ms = 0
                    return total_ms * 10000  # Convert to ticks (1 tick = 100 nanoseconds)
                except Exception:
                    return 0
            
            # Try to parse as JSON first, fallback to plain text processing
            try:
                import re
                # Remove markdown code block if present
                match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", combined_transcription)
                if match:
                    json_str = match.group(1)
                else:
                    json_str = combined_transcription
                
                transcription_items = json.loads(json_str)
                
                for item in transcription_items:
                    ts = item.get("timestamp")
                    offset_ms = timestamp_to_ticks(ts) if ts else None
                    transcription_object = {
                        "event_type": "transcribed",
                        "session": None,
                        "offset": offset_ms,
                        "duration": None,
                        "text": item.get("text"),
                        "speaker_id": item.get("speaker"),
                        "result_id": None,
                        "filename": self.conversationfilename,
                        "language": item.get("language"),
                    }
                    if callback:
                        callback(transcription_object)
                        
            except Exception as e:
                logger.warning(f"Could not parse combined transcription as JSON: {e}")
                # Fallback: treat as plain text and create a single transcription object
                transcription_object = {
                    "event_type": "transcribed",
                    "session": None,
                    "offset": 0,
                    "duration": None,
                    "text": combined_transcription,
                    "speaker_id": "combined",
                    "result_id": None,
                    "filename": self.conversationfilename,
                    "language": self.language,
                }
                if callback:
                    callback(transcription_object)
            
            logger.info("Advanced transcription completed.")
            if callback:
                callback({"event_type": "session_stopped", "filename": self.conversationfilename})


def cback(event_dict):
    """callback function to handle events"""
    print("Event received:", event_dict)
    # Here you can process the event_dict as needed
    # For example, you can save it to a database or send it to a message queue
if __name__ == "__main__":
    # Uncomment the function you want to run
    factory = TranscriptionFactory()
    # factory.conversation_transcription(cback)
    # conversation_transcription_from_microphone()
    
    
    # # BATCH
    # factory.conversation_transcription_batch(
    #     contentUrls=["https://storageaimma.blob.core.windows.net/army-stt-input/upload_VO50_20s.wav"],
    #     callback=cback,
    # )
    
    # backend/data/KREDO - Sample conversation - Ukrainian.mp3
    # backend/data/test-transcription-cz.wav
    
    # LLM
    # factory.conversationfilename = "../data/test-transcription-cz.wav"
    # factory.conversationfilename = "./data/STT - test - EN - banking - mid.wav"
    # factory.conversationfilename = "./data/STT - test - UA - banking - mid.wav"
    # factory.conversationfilename = "./data/STT - test - UA - banking - long.wav"
    # factory.conversationfilename = "./data/STT - test - EN - banking - long.wav"
    factory.conversationfilename = "./data/STT - test - EN - banking - long (1).wav"
    factory.conversation_transcription_llm(cback)