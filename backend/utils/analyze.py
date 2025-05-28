import os
import json
from collections import Counter, defaultdict
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
import logging

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


    def analyze_transcript(self, transcript, callback=None):
        """
        Analyze a transcript string for basic statistics: word count, speaker count, duration, per-speaker stats.
        Expects a transcript string with one JSON or text line per utterance.
        Calls the callback with each parsed utterance (optional).
        Returns a dictionary with analytics results.
        """
        
        text = self._run_query(transcript, callback=callback)


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

    def _run_query(self, prompt, callback=None):
        """
        Run a query against the analyzed transcript data.
        """
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": """
                        You are a professional analyst and reporter. Your task is to analyze the following meeting transcript and provide:
                        1. A detailed summary of the main topics discussed
                        2. The most active speakers in the meeting
                        3. Any notable quotes or statements made by the speakers
                        4. Tasks or action items that were assigned during the meeting with their respective owners and deadlines 

                        """
                        # "text": """
                        # You are a /proffesional call transcript analystassistant. 
                        
                        # Analyze the following customer service call transcript between a banking agent and a customer. Identify and summarize the following:
                        # 1.	Customer’s main issue or request
                        # 2.	Agent’s response approach (e.g., helpful, formal, empathetic, etc.)
                        # 3.	Tone and sentiment of both the customer and the agent
                        # 4.	Was the issue resolved? Explain how.
                        # 5.	Suggestions for improving the interaction, if any

                        # ouptut should be in a JSON format with the following keys:
                        # {
                        #     "customer_issue": "Customer's main issue or request",
                        #     "agent_response_approach": "Agent's response approach (e.g., helpful, formal, empathetic, etc.)",
                        #     "tone_and_sentiment": { 
                        #         "customer": "Tone and sentiment of the customer",
                        #         "agent": "Tone and sentiment of the agent"
                        #     },  
                        #     "issue_resolution": "Was the issue resolved? Explain how.",
                        #     "improvement_suggestions": "Suggestions for improving the interaction, if any"
                        # }
                        # Make sure to provide a detailed and comprehensive analysis.
                        # If you are not sure about something, just say "I don't know".
                        # Do not make up any information.
                        # Do not include any additional text or explanations outside of the JSON format.
                        # """
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