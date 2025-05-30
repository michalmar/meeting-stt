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
        """
        logger = logging.getLogger(__name__)
        logger.info("Starting LLM-based conversation transcription.")
        import base64
        from openai import AzureOpenAI
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
        encoded_image = base64.b64encode(open(self.conversationfilename, 'rb').read()).decode('ascii')
        chat_prompt = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are an AI assistant that helps people find information."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                     {
                        "type": "text",
                        "text": f"""Transcribe the following conversation in {self.language} in attached file. Output format:
                        #Speaker-1:# text
                        #Speaker-2:# text
                        #Speaker-3:# text
                        etc.
                        """
                    },
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

        logger.info("Sending for transcription.")
        completion = client.chat.completions.create(
            model="gpt-4o-audio-preview",
            messages=messages,
            max_tokens=5000,
            temperature=0.2,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=False
        )
        logger.info("Transcribed.")

        logger.info(f"Transcription result: {completion.choices[0].message.content}")

        transcription_text = completion.choices[0].message.content
        
        # Parse speaker lines and emit as individual transcription_object events
        import re
        speaker_line_pattern = re.compile(r"^#(Speaker-\d+):#\s*(.*)$", re.MULTILINE)
        matches = speaker_line_pattern.findall(transcription_text)
        for speaker_id, text in matches:
            transcription_object = {
                "event_type": "transcribed",
                "session": None,
                "offset": None,
                "duration": None,
                "text": text,
                "speaker_id": speaker_id,
                "result_id": None,
                "filename": self.conversationfilename,
            }
            if callback:
                callback(transcription_object)

        logger.info("Finished.")
        if callback:
            callback({"event_type":"session_stopped", "filename":self.conversationfilename})


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
    factory.conversationfilename = "../data/test-transcription-cz.wav"
    factory.conversation_transcription_llm(cback)