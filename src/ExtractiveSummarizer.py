import re


class ExtractiveSummarizer:
    """
    Simple extractive summarizer.
    Selects important sentences from the input text.
    """

    def __init__(self, config=None):
        pass

    def summarize(self, text, summary_length="medium"):
        if not text or not text.strip():
            return "⚠️ Please provide valid text."

        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        if len(sentences) <= 2:
            return text.strip()

        if summary_length == "short":
            count = max(1, len(sentences) // 3)

        elif summary_length == "long":
            count = max(1, (len(sentences) * 2) // 3)

        else:
            count = max(1, len(sentences) // 2)

        # Simple sentence scoring
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())

        stop_words = {
            "the", "is", "a", "an", "and", "or", "of",
            "to", "in", "on", "for", "with", "this",
            "that", "it", "from", "are", "was", "were"
        }

        frequency = {}

        for word in words:
            if word not in stop_words:
                frequency[word] = frequency.get(word, 0) + 1

        scored_sentences = []

        for index, sentence in enumerate(sentences):
            sentence_words = re.findall(
                r'\b[a-zA-Z]+\b',
                sentence.lower()
            )

            score = sum(
                frequency.get(word, 0)
                for word in sentence_words
            )

            scored_sentences.append(
                (score, index, sentence)
            )

        top_sentences = sorted(
            scored_sentences,
            reverse=True
        )[:count]

        # Restore original order
        top_sentences = sorted(
            top_sentences,
            key=lambda x: x[1]
        )

        return " ".join(
            sentence[2] for sentence in top_sentences
        )