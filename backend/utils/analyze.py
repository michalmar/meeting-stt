
import os
import json
from collections import Counter, defaultdict
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load environment variables from .env file
load_dotenv(override=True)

# Get Azure OpenAI endpoint and model name from environment variables
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
MODEL_NAME = os.getenv("MODEL_NAME")
MODEL_NAME_REASONING = os.getenv("MODEL_NAME_REASONING")  # Fallback to MODEL_NAME if not set



class AnalysisFactory:
    def __init__(self, transcript_path="transcription_results.txt", language="cs-CZ"):
        self.transcript_path = transcript_path
        self.language = language

        # Set up Azure AD token provider for authentication
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        )

        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint = AZURE_OPENAI_ENDPOINT, 
            azure_ad_token_provider=token_provider,
            api_version="2025-04-01-preview"
        )


    def analyze_transcript(self, transcript, callback=None, custom_prompt=None):
        """
        Analyze a transcript string for basic statistics: word count, speaker count, duration, per-speaker stats.
        Expects a transcript string with one JSON or text line per utterance.
        Calls the callback with each parsed utterance (optional).
        Returns a dictionary with analytics results.
        Accepts an optional custom_prompt to override the default system prompt.
        """
        text = self._run_query(transcript, callback=callback, custom_prompt=custom_prompt)
    
        analysis = {
            "transcript_text": transcript,
            "main_summary": text,
            "main_topics": "topics ",
            "most_active_speakers": "speaker1, speaker2",
        }
        ret = {
            "message": "Query executed successfully",
            "data": {
                "analysis": analysis,
            }
        }
    
        if callback:
            callback(ret)
        return ret


    def _run_query(self, prompt, callback=None, custom_prompt=None):
        """
        Run a query against the analyzed transcript data.
        """

        if custom_prompt and custom_prompt.strip():
            system_prompt = custom_prompt.strip()
        else:
            # Load system prompt from JINJA2 file
            prompt_path = Path(__file__).parent.parent / "prompts" / "transcript_analysis.jinja2"
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    system_prompt = f.read()
            except Exception as e:
                logger.error(f"Could not read system prompt file: {e}")
                system_prompt = "You are a professional call transcript analyst assistant. (Prompt file missing)"

        messages = [
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
                        "type": "text",
                        "text": prompt
                    },
                ]
            }
        ]

        logger.info('Sending data to LLM')
        logger.info(f'LLM messages: {json.dumps(messages, indent=2)}')
        # Call the Azure OpenAI model
        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=2000,
            temperature=0.2,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=False
        )

        # response = self.client.responses.create(
        #     # model=MODEL_NAME_REASONING,
        #     # reasoning={
        #     #     "effort":  "low",         # optional: low | medium | high
        #     #     "summary": "detailed",      # auto | concise | detailed
        #     # },
        #     model=MODEL_NAME,
        #     # model=MODEL_NAME_REASONING,
        #     input=messages,
        # )
        logger.info('Received response from LLM')
        logger.info(f'LLM full response: {response}')


        content_text = None
        try:
            # for item in response.output:
            #     if getattr(item, 'type', None) == 'message' and hasattr(item, 'content'):
            #         content_text = item.content[0].text
            #         break
            content_text = response.choices[0].message.content
        except Exception as e:
            logger.error(f'Could not extract content text from LLM response: {e}')
            # return 'Error: Could not extract content from LLM response.'
        if not content_text:
            logger.error('No message output found in LLM response')
            # return 'Error: No message output found in LLM response.'


        if callback:
            callback({
                "message": "Query executed successfully",
                "data": {
                    "text": content_text,
                }
            })
        
        return content_text
    

if __name__ == "__main__":
    # Example usage
    factory = AnalysisFactory()
    transcript = """
    Guest-1: Dobrý den, vítejte.
    Guest-2: Ahoj basto co si přeješ?
    Guest-1: Díky a čau.
    """
    
    def print_callback(result):
        print("Callback result:", result)

    analysis_result = factory.analyze_transcript(transcript, callback=print_callback)
    print("Analysis Result:", analysis_result)