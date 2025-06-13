#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE.md file in the project root for full license information.
"""
Batch transcription factory for Azure Speech Services
Provides functionality to submit, monitor and retrieve batch transcription jobs using Azure Speech-to-Text API.
"""

import requests
import json
import time
import logging
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import os
import re

# Load environment variables from .env file
load_dotenv(override=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class TranscriptionBatchFactory:
    """
    Factory class for handling Azure Speech Services batch transcription operations.
    
    This class provides methods to:
    - Submit batch transcription jobs
    - Monitor transcription status
    - Retrieve transcription results
    - Manage different speech models (Whisper, standard speech models)
    """
    
    def __init__(self, 
                 speech_key=None, 
                 speech_endpoint=None,
                 speech_region=None,
                 language="en-US"):
        """
        Initialize the TranscriptionBatchFactory with Azure Speech service credentials.
        
        Args:
            speech_key (str, optional): Azure Speech service subscription key
            speech_endpoint (str, optional): Azure Speech service endpoint
            speech_region (str, optional): Azure Speech service region
            language (str): Default language for transcriptions
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing TranscriptionBatchFactory with provided parameters or environment variables.")
        
        self.speech_key = speech_key or os.getenv("AZURE_SPEECH_KEY")
        self.speech_endpoint = speech_endpoint or os.getenv("AZURE_SPEECH_ENDPOINT")
        self.speech_region = speech_region or os.getenv("AZURE_SPEECH_REGION")
        self.language = language
        
        if not all([self.speech_key, self.speech_endpoint, self.speech_region]):
            raise ValueError("Missing required Azure Speech service credentials. Please check environment variables or parameters.")

    def submit_transcription(self, display_name, description, locale, content_urls, model_url, properties):
        """
        Submit a batch transcription job to Azure Speech Services.
        
        Args:
            display_name (str): Display name for the transcription job
            description (str): Description of the transcription job
            locale (str): Language locale for transcription
            content_urls (list): List of audio file URLs to transcribe
            model_url (str): URL of the speech model to use
            properties (dict): Additional properties for the transcription job
            
        Returns:
            requests.Response: HTTP response from the API
        """
        self.logger.info(f"Submitting transcription job: {display_name}")
        
        url = f"https://{self.speech_region}.api.cognitive.microsoft.com/speechtotext/v3.2/transcriptions"
        headers = {
            "Ocp-Apim-Subscription-Key": self.speech_key,
            "Content-Type": "application/json",
        }
        payload = {
            "displayName": display_name,
            "description": description,
            "locale": locale,
            "contentUrls": content_urls,
            "model": {"self": model_url},
            "properties": properties,
            "customProperties": {},
            "temperature": 0.0,
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            self.logger.info(f"Successfully submitted transcription job. Status: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to submit transcription job: {e}")
            raise

    def get_transcription_status(self, transcription_id):
        """
        Get the current status of a batch transcription job.
        
        Args:
            transcription_id (str): ID of the transcription job
            
        Returns:
            requests.Response: HTTP response containing status information
        """
        url = f"https://{self.speech_region}.api.cognitive.microsoft.com/speechtotext/v3.2/transcriptions/{transcription_id}"
        headers = {
            "Ocp-Apim-Subscription-Key": self.speech_key,
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to get transcription status: {e}")
            raise

    def extract_transcription_id(self, response):
        """
        Extract transcription ID from the API response.
        
        Args:
            response (requests.Response): Response from transcription submission
            
        Returns:
            str: Transcription ID
        """
        try:
            data = response.json()
            transcription_id = data.get("self", "").split("/")[-1]
            self.logger.info(f"Extracted transcription ID: {transcription_id}")
            return transcription_id
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to extract transcription ID: {e}")
            raise

    def retrieve_transcription_files(self, transcription_id):
        """
        Retrieve the list of files for a completed transcription job.
        
        Args:
            transcription_id (str): ID of the transcription job
            
        Returns:
            requests.Response: HTTP response containing file information
        """
        url = f"https://{self.speech_region}.api.cognitive.microsoft.com/speechtotext/v3.2/transcriptions/{transcription_id}/files"
        headers = {
            "Ocp-Apim-Subscription-Key": self.speech_key,
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to retrieve transcription files: {e}")
            raise

    def download_transcription_file(self, response):
        """
        Download the transcription content from the API response.
        
        Args:
            response (requests.Response): Response from retrieve_transcription_files
            
        Returns:
            bytes or None: Transcription file content, or None if not found
        """
        try:
            data = response.json()
            transcription_file_url = None
            
            # Find the transcription file
            for item in data.get("values", []):
                if item.get("kind") == "Transcription":
                    transcription_file_url = item.get("links", {}).get("contentUrl")
                    break
            
            if transcription_file_url:
                file_response = requests.get(transcription_file_url)
                file_response.raise_for_status()
                self.logger.info("Successfully downloaded transcription file")
                return file_response.content
            else:
                self.logger.warning("No transcription file found in response")
                return None
                
        except (json.JSONDecodeError, requests.exceptions.RequestException) as e:
            self.logger.error(f"Failed to download transcription file: {e}")
            return None

    def get_model_ids(self, skip=100, top=200):
        """
        Get model IDs from Azure Speech-to-Text API.
        
        Args:
            skip (int): Number of items to skip (default: 100)
            top (int): Number of items to return (default: 200)
        
        Returns:
            list: List of model information dictionaries
        """
        self.logger.info(f"Fetching model IDs with skip={skip}, top={top}")
        
        url = f"https://{self.speech_region}.api.cognitive.microsoft.com/speechtotext/models/base"
        params = {
            "api-version": "2024-11-15",
            "skip": skip,
            "top": top
        }
        headers = {
            "Ocp-Apim-Subscription-Key": self.speech_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            model_ids = []
            
            # Handle different response formats
            if isinstance(data, list):
                # Direct list of models
                for model in data:
                    if "self" in model:
                        model_id = self._extract_model_id_from_self_url(model["self"])
                        if model_id:
                            model_ids.append({
                                "id": model_id,
                                "displayName": model.get("displayName", ""),
                                "description": model.get("description", ""),
                                "locale": model.get("locale", "")
                            })
            elif isinstance(data, dict):
                if "values" in data:
                    # Paginated response
                    for model in data["values"]:
                        if "self" in model:
                            model_id = self._extract_model_id_from_self_url(model["self"])
                            if model_id:
                                model_ids.append({
                                    "id": model_id,
                                    "displayName": model.get("displayName", ""),
                                    "description": model.get("description", ""),
                                    "locale": model.get("locale", "")
                                })
                elif "self" in data:
                    # Single model response
                    model_id = self._extract_model_id_from_self_url(data["self"])
                    if model_id:
                        model_ids.append({
                            "id": model_id,
                            "displayName": data.get("displayName", ""),
                            "description": data.get("description", ""),
                            "locale": data.get("locale", "")
                        })
            
            self.logger.info(f"Found {len(model_ids)} models")
            return model_ids
            
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            self.logger.error(f"Error getting model IDs: {e}")
            return []

    def _extract_model_id_from_self_url(self, self_url):
        """
        Extract model ID from the self URL.
        
        Args:
            self_url (str): The self URL from the API response
            
        Returns:
            str or None: The extracted model ID or None if not found
        """
        # URL format: https://eastus.api.cognitive.microsoft.com/speechtotext/models/base/69adf293-9664-4040-932b-02ed16332e00?api-version=2024-11-15
        match = re.search(r'/models/base/([a-f0-9-]+)', self_url)
        return match.group(1) if match else None

    def find_model_by_name(self, model_name_pattern, locale=None):
        """
        Find models by name pattern and optionally by locale.
        Retries up to 10 times with different skip values to search through paginated results.
        
        Args:
            model_name_pattern (str): Pattern to search for in model names (case-insensitive)
            locale (str, optional): Locale to filter by
            
        Returns:
            list: List of matching models
        """
        self.logger.info(f"Searching for models matching pattern: '{model_name_pattern}'")
        
        matching_models = []
        max_retries = 10
        model_found = False
        
        for attempt in range(max_retries):
            skip_value = 900 + (attempt * 100)  # Skip 900, 1000, 1100, etc.
            self.logger.debug(f"Search attempt {attempt + 1}/{max_retries} (skip={skip_value})")
            
            models = self.get_model_ids(skip=skip_value, top=100)
            
            # If no models returned, we've reached the end
            if not models:
                self.logger.debug(f"No more models found at skip={skip_value}")
                break
            
            # Search through current batch of models
            batch_matches = []
            for model in models:
                name_match = model_name_pattern.lower() in model['displayName'].lower()
                locale_match = locale is None or model['locale'].lower() == locale.lower()
                
                if name_match and locale_match:
                    batch_matches.append(model)
                    model_found = True
                    self.logger.info(f"Found matching model: {model['displayName']} ({model['id']}) - {model['locale']}")
                    break
            
            matching_models.extend(batch_matches)
            if model_found:
                self.logger.info(f"Found {len(matching_models)} total matching models")
                break
        
        return matching_models
 
    def transcribe_batch(self, content_url, model="whisper", callback=None):
        """
        Main method to perform batch transcription of an audio file.
        
        Args:
            content_url (str): URL of the audio file to transcribe
            which_model (str): Model type to use ("whisper" or "speech")
            callback (function, optional): Callback function for progress updates
            
        Returns:
            dict: Transcription results
        """
        self.logger.info(f"Starting batch transcription for: {content_url}")
        start_time = time.time()

        file_name = self._extract_filename(content_url)
        
        display_name = f"Transcription for {file_name}"
        description = "Speech Studio Batch speech to text"
        
        # Dynamically get model IDs
        model_id = self._get_model_id(model)
        model_url = f"https://{self.speech_region}.api.cognitive.microsoft.com/speechtotext/models/base/{model_id}"

        # Configure transcription properties
        locale = "cs-cz"  # Czech locale - could be parameterized
        content_urls = [content_url]
        properties = {
            "wordLevelTimestampsEnabled": False,
            "displayFormWordLevelTimestampsEnabled": True,
            "diarizationEnabled": False,
            "punctuationMode": "DictatedAndAutomatic",
            "profanityFilterMode": "Masked",
            "languageIdentification": {
                "candidateLocales": [
                    "uk-ua",
                    "ru-ru",
                    "cs-cz"
                ]
            },
        }

        # Submit transcription
        response = self.submit_transcription(display_name, description, locale, content_urls, model_url, properties)
        transcription_id = self.extract_transcription_id(response)
        
        # Poll until transcription status is 'Succeeded'
        self._wait_for_completion(transcription_id, callback)
        
        # Retrieve and download transcription file
        files_response = self.retrieve_transcription_files(transcription_id)
        file_content = self.download_transcription_file(files_response)
        
        if file_content is None:
            self.logger.error("No transcription file downloaded.")
            return None

        # Parse and save results
        recognized_object = json.loads(file_content)

        # Convert recognizedPhrases to a more usable format
        recognizedPhrases = recognized_object["recognizedPhrases"]
        for phrase in recognizedPhrases:
            del phrase["offset"]
            del phrase["duration"]
            phrase["text"] = phrase["nBest"][0]["display"]
            del phrase["nBest"]
            phrase["person"] = "customer" if phrase["channel"] == 1 else "agent"
            # phrase["offsetInTicks"] = phrase["offsetInTicks"] / 10000

        # Assuming recognizedPhrases is your list of dictionaries
        recognizedPhrases = sorted(recognizedPhrases, key=lambda x: x['offsetInTicks'])


        for phrase in recognizedPhrases:
            transcription_object = {
                "event_type": "transcribed",
                "session": transcription_id,
                "offset": phrase["offsetMilliseconds"],
                "duration": phrase.get("durationMilliseconds", 0),
                "text": phrase.get("text"),
                "speaker_id": phrase.get("person"),
                "result_id": None,
                "filename": file_name,
                "language": phrase.get("language"),
            }
            if callback:
                callback(transcription_object)
            # print("\n")
        if callback:
            callback({"event_type": "session_stopped", "session": transcription_id, "filename": file_name, "language": locale})
        
        # # Save the recognized object to file with timestamp
        # timestamp = time.strftime("%Y%m%d%H%M%S")
        # file_path = f"{file_name}_{which_model}_{timestamp}.json"
       
        # with open(file_path, "w", encoding='utf-8') as f:
        #     json.dump(recognized_object, f, indent=4, ensure_ascii=False)
        
        total_time = time.time() - start_time
        # self.logger.info(f"Transcription completed. Results saved to {file_path}")
        self.logger.info(f"Total time elapsed: {total_time:.2f} seconds")
        
        return recognized_object

    def _get_model_id(self, which_model):
        """
        Get the appropriate model ID based on the model type.
        
        Args:
            which_model (str): Model type ("whisper" or "speech")
            
        Returns:
            str: Model ID
        """
        model_id = None
        
        if which_model == "whisper":
            # Look for Whisper models
            whisper_models = self.find_model_by_name("Whisper Large V2")
            if whisper_models:
                model_id = whisper_models[0]['id']
                self.logger.info(f"Using Whisper model: {whisper_models[0]['displayName']} ({model_id})")
            else:
                # Fallback to hardcoded ID
                model_id = "e418c4a9-9937-4db7-b2c9-8afbff72d950"
                self.logger.warning(f"Using fallback Whisper model ID: {model_id}")
                
        elif which_model == "speech":
            # Look for other speech models (not Whisper)
            all_models = self.get_model_ids()
            speech_models = [m for m in all_models if "whisper" not in m['displayName'].lower()]
            if speech_models:
                model_id = speech_models[0]['id']
                self.logger.info(f"Using Speech model: {speech_models[0]['displayName']} ({model_id})")
            else:
                # Fallback to hardcoded ID
                model_id = "7805eb1a-52b8-4c99-a5d1-155bbcb499f7"
                self.logger.warning(f"Using fallback Speech model ID: {model_id}")
        else:
            raise ValueError("Invalid model specified. Use 'whisper' or 'speech'.")
            
        return model_id

    def _wait_for_completion(self, transcription_id, callback=None):
        """
        Wait for transcription job to complete by polling the status.
        
        Args:
            transcription_id (str): ID of the transcription job
            callback (function, optional): Callback function for status updates
        """
        self.logger.info(f"Polling transcription status for ID: {transcription_id}")
        
        while True:
            status_response = self.get_transcription_status(transcription_id)
            try:
                status_data = status_response.json()
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse status response: {e}")
                break
                
            status = status_data.get("status", "").lower()
            self.logger.info(f"Current status: {status}")
            
            if callback:
                # callback({"event_type": "status", "status": status, "details": status_data})
                callback({"event_type": "status", "status": status})
            
            if status == "succeeded":
                self.logger.info("Transcription completed successfully")
                break
            elif status == "failed":
                self.logger.error("Transcription failed")
                raise RuntimeError("Transcription job failed")
            elif status == "canceled":
                self.logger.error("Transcription was canceled")
                raise RuntimeError("Transcription job was canceled")
                
            time.sleep(5)  # Wait 5 seconds before re-checking

    def _extract_filename(self, url):
        """
        Extract filename from URL.
        
        Args:
            url (str): URL to extract filename from
            
        Returns:
            str: Extracted filename
        """
        parsed_url = urlparse(url)
        return os.path.basename(parsed_url.path)


    def get_transcription_files_paginated(self, transcription_id, skip=0, top=100):
        """
        Get transcription files from Azure Speech-to-Text API with pagination.
        
        Args:
            transcription_id (str): The transcription ID
            skip (int): Number of items to skip (default: 0)
            top (int): Number of items to return (default: 100)
        
        Returns:
            dict: Response containing values array and nextLink
        """
        url = f"https://{self.speech_region}.api.cognitive.microsoft.com/speechtotext/v3.2-preview.2/transcriptions/{transcription_id}/files"
        params = {
            "skip": skip,
            "top": top
        }
        headers = {
            "Ocp-Apim-Subscription-Key": self.speech_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract files information
            files = []
            if isinstance(data, dict):
                if "values" in data:
                    # Paginated response
                    for file_item in data["values"]:
                        files.append({
                            "name": file_item.get("name", ""),
                            "kind": file_item.get("kind", ""),
                            "properties": file_item.get("properties", {}),
                            "createdDateTime": file_item.get("createdDateTime", ""),
                            "links": file_item.get("links", {}),
                            "self": file_item.get("self", "")
                        })
            
            result = {
                "values": files,
                "nextLink": data.get("@nextLink") if isinstance(data, dict) else None,
                "total_count": len(files)
            }
            
            self.logger.info(f"Found {len(files)} files for transcription {transcription_id}")
            return result
            
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            self.logger.error(f"Error getting transcription files: {e}")
            return {"values": [], "nextLink": None, "total_count": 0}

    def get_all_transcription_files(self, transcription_id):
        """
        Get all transcription files by iterating through all pages.
        
        Args:
            transcription_id (str): The transcription ID
        
        Returns:
            list: List of all files across all pages
        """
        all_files = []
        skip = 0
        top = 100
        
        while True:
            self.logger.debug(f"Fetching transcription files - skip={skip}, top={top}")
            
            result = self.get_transcription_files_paginated(transcription_id, skip=skip, top=top)
            
            # Add files from current page
            current_files = result.get("values", [])
            all_files.extend(current_files)
            
            # Check if there are more pages
            next_link = result.get("nextLink")
            if not next_link or len(current_files) == 0:
                self.logger.debug("No more files to fetch")
                break
            
            # Increment skip for next page
            skip += top
        
        self.logger.info(f"Total transcription files found: {len(all_files)}")
        return all_files

    def find_transcription_file_by_kind(self, transcription_id, kind_filter="Transcription"):
        """
        Find transcription files by kind (e.g., 'Transcription', 'Report', etc.).
        
        Args:
            transcription_id (str): The transcription ID
            kind_filter (str): The kind of file to find (default: 'Transcription')
        
        Returns:
            list: List of matching files
        """
        all_files = self.get_all_transcription_files(transcription_id)
        
        matching_files = []
        for file_item in all_files:
            if file_item.get("kind", "").lower() == kind_filter.lower():
                matching_files.append(file_item)
        
        self.logger.info(f"Found {len(matching_files)} files with kind '{kind_filter}'")
        return matching_files


def callback_example(event_dict):
    """
    Example callback function to handle transcription events.
    
    Args:
        event_dict (dict): Event information dictionary
    """
    print(f"Event received: {event_dict}")


if __name__ == "__main__":
    # Example usage of the TranscriptionBatchFactory
    
    # Uncomment to test file retrieval for existing transcription
    # factory = TranscriptionBatchFactory()
    # files = factory.get_all_transcription_files("8c8eb58e-52af-485f-a0f6-1ef525680a31")  # Example transcription ID
    # for file in files:
    #     print(f"File: {file['name']}, Kind: {file['kind']}, Created: {file['createdDateTime']}")
    # exit(0)
    
    # Initialize the factory
    factory = TranscriptionBatchFactory(language="cs-CZ")
    
    # Configure storage and files
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_ENDPOINT")
    url_prefix = f"{storage_account}/data"
    
    # List of files to transcribe (should be available in your Azure Storage)
    files = [
        "test-transcription-cz.wav",  # Remove 'x' from filename
    ]

    for file in files:
        # Construct the full URL to the audio file
        content_url = f"{url_prefix}/{file}"
        # For files with SAS tokens, uncomment the following line:
        content_url = 'https://stw43tl4s4i6hmg.blob.core.windows.net/data/test-transcription-cz.wav?sp=r&st=2025-06-13T10:28:42Z&se=2025-06-13T18:28:42Z&spr=https&sv=2024-11-04&sr=b&sig=zy1a%2BESMMUhin97Ew4D%2FmgH8aUdKcOlHyGrDbcPEg7s%3D'
        
        print(f"Processing file: {file}")
        print(f"Content URL: {content_url}")

        # Transcribe with Whisper model
        model = "whisper"
        print(f"Using model: {model}")
        
        try:
            result = factory.transcribe_batch(content_url, model, callback=callback_example)
            if result:
                print(f"Transcription completed successfully for {file}")
            else:
                print(f"Transcription failed for {file}")
        except Exception as e:
            print(f"Error processing {file}: {e}")

        # Optionally, also try with speech model
        # model = "speech"
        # print(f"Using model: {model}")
        # try:
        #     result = factory.transcribe_batch(content_url, model, callback=callback_example)
        #     if result:
        #         print(f"Transcription completed successfully for {file} with {model}")
        # except Exception as e:
        #     print(f"Error processing {file} with {model}: {e}")

