

import base64
from openai import AzureOpenAI
import json
from azure.identity import DefaultAzureCredential
from azure.identity import get_bearer_token_provider
import os

from dotenv import load_dotenv
load_dotenv(override=True)

PROMPT = """
Transcribe the given audio recording into clear, accurate text.

# Steps
1. Carefully listen to the audio recording, ensuring every word is understood.
2. Transcribe the spoken words, maintaining proper grammar, punctuation, and capitalization.
3. Use brackets [like this] to indicate unclear words, background sounds, or any inaudible sections.
    - Example: "[inaudible]" or "[dog barking in the background]".
4. You must every transcribed chunk denote with speaker (e.g., "#Speaker1#", "#Speaker 2#").
5. Omit filler words like "um" or "uh," unless they provide meaningful context.
6. For overlapping speech, transcribe as accurately as possible, using brackets for contextual notes if needed.
7. There can be multiple languages used, so you must denote that at least for every chunk, e.g. [00:21] #Speaker1# (language) ...

# Output Format
- Plain text transcription using standard grammar and formatting.
- Include timestamps for every transcribed chunk (e.g., "[00:21] #Speaker1#: ...").
- Do not include any additional commentary or notes in the output unless explicitly indicated in the recording.
- format the output as JSON list with timestamp, text, speaker, language:

[
{"timestamp": "00:21","text": "...","speaker": "#Speaker1#","language": "detected language"},
{"timestamp": "00:41","text": "...","speaker": "#Speaker2#","language": "detected language"},
...
]

# Notes
- Clarify whether to include background sounds, speech markers, or emotional cues.
- Ensure names and technical terms are spelled correctly, using placeholders (e.g., [name]) if unsure.

"""

# PROMPT = """
# Transcribe the given audio recording into clear, accurate text.

# # Steps
# 1. Carefully listen to the audio recording, ensuring every word is understood.
# 2. You must every transcribed chunk denote with speaker (e.g., "#Speaker1#: text", "#Speaker 2#: text").
# """

api_key = os.getenv("AZURE_OPENAI_KEY_TRANSCRIBE")
api_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_TRANSCRIBE")

audio_file = open("./data/STT - test - EN - banking - long (2).wav", "rb")
# audio_file = open("./data/STT - test - EN - banking - long (1).wav", "rb")

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

# ####
# #### GPT-4o-transcribe model
# ####
# transcription = client.audio.transcriptions.create(
#   model="gpt-4o-transcribe", # prompt OK, diarozation OK, but transcript cut off for long audio
# #   model="gpt-4o-mini-transcribe", # ignores prompt, cannot do diarization
#   file=audio_file, 
#   response_format="text",
# #   prompt="The following conversation is between agent and customer."
#     prompt=PROMPT,
#     temperature=0.0,
#     # language="en",
#     # response_format="json"
#     # stream=True,  # Set to True for streaming response
# )

# print (transcription)
# # for event in transcription:
# #   print(event)


#####
##### GPT-4o-audio-preview model
#####

encoded_image = base64.b64encode(audio_file.read()).decode('ascii')
chat_prompt = [
    {
        "role": "system",
        "content": [
            {
                "type": "text",
                "text": PROMPT
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

completion = client.chat.completions.create(
    model="gpt-4o-audio-preview",
    messages=messages,
    max_tokens=15000,
    temperature=0.0,
    # top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    stop=None,
    stream=False
)

transcription_text = completion.choices[0].message.content

print("Transcription:")
print(transcription_text)