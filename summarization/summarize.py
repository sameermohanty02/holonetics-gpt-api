import json
import tiktoken
from openai import AzureOpenAI
import os
import concurrent.futures
from config import *

class Summarize:
    def token_length(self, text):
        encoding = tiktoken.encoding_for_model("gpt-4")
        tokens = encoding.encode(text)
        token_len = len(tokens)
        return tokens, token_len

    def create_chunks(self, chunkSize, overlap, tokens, total_tokens):
        chunks = []
        for i in range(0, total_tokens, chunkSize - overlap):
            chunk = tokens[i:i + chunkSize]
            chunks.append(chunk)
        return chunks

    def summarize_text(self, text, prompt):
        if isinstance(text, dict):
            copied_text = json.dumps(text.copy())
        else:
            copied_text = str(text)

        tokens, total_tokens = self.token_length(copied_text)

        if total_tokens > 7500:
            result = []
            chunks = self.create_chunks(3000, 50, tokens, total_tokens)
            client = AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                api_version=api_version,
            )
            encoding = tiktoken.encoding_for_model("gpt-4")

            def process_chunk(chunk):
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": prompt + f"{encoding.decode(chunk)}"}
                    ],
                    max_tokens=350,
                    temperature=0
                )
                return response.choices[0].message.content

            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
                for future in concurrent.futures.as_completed(futures):
                    result.append(future.result())

            return result
        return False





