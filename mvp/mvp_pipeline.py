from .extractive import ExtractiveSummarizer
from .abstractive import AbstractiveSummarizer

class SummarizationPipeline:
    def __init__(self, api_key):
        self.extractive = ExtractiveSummarizer(api_key)
        self.abstractive = AbstractiveSummarizer(api_key)

    def summarize(self, text, method='abstractive', length='medium'):
        """
        Summarize text using specified method

        Args:
            text (str): Input text to summarize
            method (str): 'extractive' or 'abstractive'
            length (str): 'short', 'medium', or 'long'

        Returns:
            str: Summarized text
        """
        if not text or not text.strip():
            return "Please provide some text to summarize."
            
        if method == 'extractive':
            return self.extractive.summarize(text, length)
        else:
            return self.abstractive.summarize(text, length)

    def paraphrase(self, text):
        """Paraphrase the given text"""
        if not text or not text.strip():
            return "Please provide some text to paraphrase."
        return self.abstractive.paraphrase(text)