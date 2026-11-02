
from ExtractiveSummarizer import ExtractiveSummarizer
from AbstractiveSummarizer import AbstractiveSummarizer
from paraphraser import Paraphraser


class SummarizationPipeline:
    """Combined pipeline for Summarization (HF) + Paraphrasing (GROQ LLM)."""

    def __init__(self, hf_api_key):
        print("Initializing SummarizationPipeline...")

        # Extractive Summarizer
        try:
            self.extractive = ExtractiveSummarizer(hf_api_key)
            print("Extractive Summarizer loaded")
        except Exception as e:
            print(f"Warning: Extractive Summarizer failed: {e}")
            self.extractive = None

        # Abstractive Summarizer
        try:
            self.abstractive = AbstractiveSummarizer(hf_api_key)
            print("Abstractive Summarizer loaded")
        except Exception as e:
            print(f"Warning: Abstractive Summarizer failed: {e}")
            self.abstractive = None

        # GROQ Paraphraser
        try:
            self.paraphraser = Paraphraser()
            print("GROQ Paraphraser loaded")
        except Exception as e:
            print(f"Warning: GROQ Paraphraser failed: {e}")
            self.paraphraser = None

        print("SummarizationPipeline initialized successfully!\n")

    # -------- Summarization --------
    def summarize(self, text, method="abstractive", length="medium"):
        if not text or not text.strip():
            return "No text provided."

        try:
            if method == "extractive":
                if self.extractive is None:
                    return "Extractive Summarizer unavailable."
                return self.extractive.summarize(text, length)

            if self.abstractive is None:
                return "Abstractive Summarizer unavailable."

            return self.abstractive.summarize(text, length)

        except Exception as e:
            return f"Error: {e}"

    # -------- Paraphrasing: list of versions --------
    def paraphrase_versions(self, text, num_return_sequences=3):
        if self.paraphraser is None:
            return ["Paraphraser unavailable."]

        try:
            results = self.paraphraser.paraphrase(
                text,
                num_return_sequences
            )

            if not results:
                return ["No paraphrases returned."]

            if any(
                item.startswith((
                    "API Error",
                    "Groq connection error",
                    "Groq returned",
                    "Could not read",
                    "Could not identify",
                    "Paraphraser unavailable"
                ))
                for item in results
            ):
                return results

            return results[:num_return_sequences]

        except Exception as e:
            return [f"Error in paraphrasing: {e}"]

    # -------- Paraphrasing: formatted string --------
    def paraphrase(self, text, num_return_sequences=3):
        results = self.paraphrase_versions(
            text,
            num_return_sequences
        )

        if not results:
            return "No paraphrases returned."

        if len(results) == 1 and results[0].startswith((
            "API Error",
            "Groq connection error",
            "Groq returned",
            "Could not read",
            "Could not identify",
            "Paraphraser unavailable",
            "Error in paraphrasing"
        )):
            return results[0]

        return "\n\n".join(
            f"Version {index + 1}:\n{variation}"
            for index, variation in enumerate(results)
        )

    # -------- Utilities --------
    def get_status(self):
        return {
            "extractive": self.extractive is not None,
            "abstractive": self.abstractive is not None,
            "groq_paraphraser": self.paraphraser is not None,
        }
