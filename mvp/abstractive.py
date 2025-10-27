import requests
import json

class AbstractiveSummarizer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.summarize_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        self.paraphrase_url = "https://api-inference.huggingface.co/models/ramsrigouthamg/t5_paraphraser"
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def summarize(self, text, length='medium'):
        """
        Abstractive summarization using BART via Hugging Face API
        """
        length_map = {
            'short': {"max_length": 80, "min_length": 30},
            'medium': {"max_length": 130, "min_length": 60},
            'long': {"max_length": 200, "min_length": 100}
        }

        params = length_map.get(length, length_map['medium'])

        payload = {
            "inputs": text,
            "parameters": {
                "max_length": params["max_length"],
                "min_length": params["min_length"],
                "do_sample": False,
                "early_stopping": True
            }
        }

        try:
            response = requests.post(
                self.summarize_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('summary_text', 'No summary generated')
                return str(result)
            else:
                return f"API Error: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Error: {str(e)}"

    def paraphrase(self, text):
        """
        Paraphrase text using T5 via Hugging Face API
        """
        payload = {
            "inputs": text,
            "parameters": {
                "max_length": 256,
                "num_beams": 5,
                "num_return_sequences": 1,
                "temperature": 0.7,
                "repetition_penalty": 1.5
            }
        }

        try:
            response = requests.post(
                self.paraphrase_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', text)
                return str(result)
            else:
                return f"API Error: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Error: {str(e)}"