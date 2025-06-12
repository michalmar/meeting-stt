import requests
import json
import time
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def submit_transcription(display_name, description, locale, content_urls, model_url, properties):
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_endpoint = os.getenv("AZURE_SPEECH_ENDPOINT")
    url = f"{speech_endpoint}/speechtotext/v3.2/transcriptions"
    headers = {
        "Ocp-Apim-Subscription-Key": speech_key,
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
    response = requests.post(url, headers=headers, json=payload)
    return response

def get_transcription_status(transcription_id):
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_endpoint = os.getenv("AZURE_SPEECH_ENDPOINT")
    url = f"{speech_endpoint}/speechtotext/v3.2/transcriptions/{transcription_id}"
    headers = {
        "Ocp-Apim-Subscription-Key": speech_key,
    }
    response = requests.get(url, headers=headers)
    return response

def extract_transcription_id(response):
    # Extract and return the last part of the "self" URL from JSON response
    data = response.json()
    transcription_id = data.get("self", "").split("/")[-1]
    return transcription_id

def retrieve_transcription_files(transcription_id):
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_endpoint = os.getenv("AZURE_SPEECH_ENDPOINT")
    url = f"{speech_endpoint}/speechtotext/v3.2/transcriptions/{transcription_id}/files"
    headers = {
        "Ocp-Apim-Subscription-Key": speech_key,
    }
    response = requests.get(url, headers=headers)
    return response

def download_transcription_file(response):
    # Extract transcription file with kind 'Transcription' and download content.
    data = response.json()
    transcription_file_url = None
    for item in data.get("values", []):
        if item.get("kind") == "Transcription":
            transcription_file_url = item.get("links", {}).get("contentUrl")
            break
    if transcription_file_url:
        file_response = requests.get(transcription_file_url)
        print("Downloaded file. Status Code:", file_response.status_code)
        # Optionally, save file (uncomment to save):
        # with open("transcription_file.json", "wb") as f:
        #     f.write(file_response.content)
        return file_response.content
    else:
        print("No transcription file found.")
        return None

def main(content_url, which_model="whisper"):
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_endpoint = os.getenv("AZURE_SPEECH_ENDPOINT")
    import time  # if not already imported at the top
    start_time = time.time()  # start time measurement
    # # Parse filename from content_url query parameter 'speechstudiofilename'
    # qs = parse_qs(urlparse(content_url).query)
    # file_name = qs.get("speechstudiofilename", ["transcription.json"])[0]

    file_name = extract_filename(content_url)
    
    display_name = f"Transcription for {file_name}"
    print("Display Name:", display_name)
    description = "Speech Studio Batch speech to text"
    whisper_model = "e418c4a9-9937-4db7-b2c9-8afbff72d950"
    speech_model = "7805eb1a-52b8-4c99-a5d1-155bbcb499f7"
    if which_model == "whisper":
        model_url = f"{speech_endpoint}/speechtotext/v3.2/models/base/{whisper_model}"
    elif which_model == "speech":
        model_url = f"{speech_endpoint}/speechtotext/v3.2/models/base/{speech_model}"
    else:
        print("Invalid model specified. Use 'whisper' or 'speech'.")
        return
    # Choose model URL (change if needed)
    # model_url = f"https://eastus.api.cognitive.microsoft.com/speechtotext/v3.2/models/base/{whisper_model}"
    locale = "ua-UA"  # Ukrainian locale
    content_urls = [content_url]
    properties = {
        "wordLevelTimestampsEnabled": False,
        "displayFormWordLevelTimestampsEnabled": True,
        "diarizationEnabled": False,
        "punctuationMode": "DictatedAndAutomatic",
        "profanityFilterMode": "Masked",
    }

    # Submit transcription
    res = submit_transcription(display_name, description, locale, content_urls, model_url, properties)
    print("Submission Status Code:", res.status_code)
    # print("Submission Response:", res.text)
    
    transcription_id = extract_transcription_id(res)
    print("Extracted Transcription ID:", transcription_id)
    
    # Poll until transcription status is 'Succeeded'
    while True:
        status_res = get_transcription_status(transcription_id)
        try:
            status_data = status_res.json()
        except Exception as e:
            print("Failed to parse status response:", e)
            break
        status = status_data.get("status", "").lower()
        print("Current Status:", status)
        if status == "succeeded":
            break
        if status == "failed":
            print("Transcription failed.")
            return
        time.sleep(5)  # wait 5 seconds before re-checking

    # Retrieve and download transcription file
    ret = retrieve_transcription_files(transcription_id)
    print("Files Retrieval Status Code:", ret.status_code)
    # print("Files Retrieval Response:", ret.text)
    
    file_content = download_transcription_file(ret)
    if file_content is None:
        print("No transcription file downloaded.")
        return

    recognized_object = json.loads(file_content)
    
    # Save the recognized object to the file derived from content_url 
    # Append current timestamp (YYYYMMDDHHMMSS) to the filename
    timestamp = time.strftime("%Y%m%d%H%M%S")
    file_path = f"{file_name}_{which_model}_{timestamp}.json"
   
    with open(file_path, "w", encoding='utf-8') as f:
        json.dump(recognized_object, f, indent=4, ensure_ascii=False)
    print(f"Recognized object saved to {file_path}")

    total_time = time.time() - start_time
    print(f"Total time elapsed: {total_time:.2f} seconds")

def extract_model_from_filename(filename):
    # Assuming filename format: <something>_<model>_<timestamp>.json
    parts = filename.rsplit('_', 2)
    if len(parts) >= 2:
        model_candidate = parts[-2].lower()
        if "whisper" in model_candidate:
            return "whisper"
        elif "speech" in model_candidate:
            return "speech"
    return "unknown"

def analyze_results():
    folder = os.getcwd()
    results = []
    for file in os.listdir(folder):
        if file.endswith(".json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    text = f.read()
                youtube_found = "youtube" in text.lower()
                model = extract_model_from_filename(file)
                results.append((file, model, youtube_found))
            except Exception as e:
                print(f"Failed to process {file}: {e}")

    # Print table header and separator line
    header = f"{'Filename':40} | {'Model':10} | {'YouTube Found':15}"
    print(header)
    print("-" * len(header))
    for filename, model, youtube_found in results:
        print(f"{filename:40} | {model:10} | {str(youtube_found):15}")



def extract_filename(url):
    parsed_url = urlparse(url)
    return os.path.basename(parsed_url.path)

if __name__ == "__main__":

    ANALYZE_RESULTS_ONLY = False # Set to True to analyze results only, False to run the main function
    if ANALYZE_RESULTS_ONLY:
        analyze_results()
        sys.exit(0)

    import sys
    # Use the first command-line argument as content_url or default to the current value
    if len(sys.argv) > 1:
        content_url = sys.argv[1]
    else:
        content_url = "***"
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_ENDPOINT")
    url_prefix = f"{storage_account}/CONTAINER"
    sas_token = '***'
    
    # NOTE: needs to be in root project folder (names as used for locating the files in storage)
    files = [
        "a.wav",
    ]

    # loop for ten time
    for i in range(10):
        print("Iteration:", i + 1)
        
        for file in files:
            content_url = f"{url_prefix}/{file}?{sas_token}"
            print("Using content URL:", content_url)

            model = "whisper"  # or "speech"
            print("Using model:", model)
            main(content_url, model)

            # model = "speech"  # or "whisper"
            # print("Using model:", model)
            # main(content_url, model)

    # Call the analyze_results function to analyze the results
    print("Analyzing results...")
    analyze_results()
    print("All done!")