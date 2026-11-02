
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


class AbstractiveSummarizer:
    """
    Abstractive text summarization using Groq API.
    Replaces the previous Hugging Face BART implementation.
    """

    def __init__(self, config=None):
        # Load the root project .env file
        project_root = Path(__file__).resolve().parent.parent
        env_path = project_root / ".env"
        load_dotenv(dotenv_path=env_path, override=False)

        # Use GROQ_API_KEY, not the old Hugging Face token
        self.api_key = os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Add it to the root .env file."
            )

        self.client = Groq(api_key=self.api_key)

        # Current Groq model ID
        self.model = "openai/gpt-oss-20b"

    def summarize(self, text, length="medium"):
        if not text or not text.strip():
            return "Please provide valid text."

               # Map the existing TextMorph length options
        length_settings = {
            "short": {
                "instruction": "Write a very concise but complete summary.",
                "max_tokens": 300
            },
            "medium": {
                "instruction": "Write a balanced, complete summary covering all key points.",
                "max_tokens": 600
            },
            "long": {
                "instruction": "Write a detailed and complete summary covering all important points.",
                "max_tokens": 1000
            }
        }

        # Support numeric values from older code as well
        if isinstance(length, str):
            settings = length_settings.get(
                length.lower(),
                length_settings["medium"]
            )
        else:
            settings = length_settings["medium"]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional text summarization assistant. "
                            "Summarize only the information provided by the user. "
                            "Preserve important facts and meaning. "
                            "Do not invent information. "
                            "Do not add unnecessary introductions."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"{settings['instruction']}\n\n"
                            f"Text to summarize:\n{text}"
                        )
                    }
                ],
                temperature=0.2,
                max_completion_tokens=settings["max_tokens"]
            )

            summary = response.choices[0].message.content

            if not summary:
                return "No summary was returned by Groq."

            return summary.strip()

        except Exception as e:
            return f"Groq API Error: {str(e)}"
