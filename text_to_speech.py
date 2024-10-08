import requests
import json
import os
from config import *

class TextToSpeech:
    def __init__(self):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/audio/speech"
        self.model = "tts-1"
        self.voice = "alloy"
        self.input_text = None
        self.audio_file_name = "speech.mp3"

    def generate_speech(self,input_text):
        self.input_text = input_text
        payload = {
            "model": self.model,
            "voice": self.voice,
            "input": self.input_text
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(self.base_url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            with open(self.audio_file_name, 'wb') as audio_file:
                audio_file.write(response.content)

            return self.audio_file_name
        else:
            print(f"Failed to generate speech: {response.status_code} - {response.text}")
            return None