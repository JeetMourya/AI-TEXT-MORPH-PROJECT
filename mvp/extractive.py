import requests

class ExtractiveSummarizer:
    def __init__(self, api_key):
        self.api_key = api_key
        # Using a model that works better for extractive-style summarization
        self.api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def summarize(self, text, length='medium'):
        """
        Summarization using Hugging Face API with extractive-style parameters
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
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    summary = result[0].get('summary_text', 'No summary generated')
                    # Ensure we get some output even if short
                    return summary if summary.strip() else "Summary too short, try with longer text."
                return str(result)
            else:
                return f"API Error: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Error: {str(e)}"