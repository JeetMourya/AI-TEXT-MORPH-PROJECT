import os
import re
import time
import requests
from dotenv import load_dotenv


class Paraphraser:
    """Generate paraphrases through separate, rate-limit-aware Groq requests."""

    def __init__(self, model_name="openai/gpt-oss-20b"):
        project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        load_dotenv(os.path.join(project_root, ".env"))

        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in root .env file.")

        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.model_name = model_name
        self.max_retries = 2
        self.max_completion_tokens = 6000
        self.request_pause_seconds = 1.5

    def _retry_delay(self, response, attempt):
        """Read the provider's retry hint; otherwise use bounded backoff."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(1.0, float(retry_after))
            except (TypeError, ValueError):
                pass

        try:
            message = response.json().get("error", {}).get("message", "")
        except (ValueError, AttributeError):
            message = response.text or ""

        match = re.search(
            r"try again in\s*([0-9.]+)\s*s",
            message,
            re.IGNORECASE,
        )
        if match:
            return float(match.group(1)) + 1.0

        return min(5 * (2 ** attempt), 30)

    @staticmethod
    def _clean_paraphrase(content):
        """Remove a simple numbering/label wrapper from a single answer."""
        if not isinstance(content, str):
            return ""

        text = content.strip()
        text = re.sub(
            r"(?is)^\s*(?:paraphrase|rewritten version|version\s*\d*)\s*[:\-]\s*",
            "",
            text,
        )
        text = re.sub(r"^\s*(?:1[.)]|\*\*1[.)]\*\*)\s*", "", text)
        return text.strip().strip('"').strip()

    def _generate_one(self, text, variation_number):
        """Generate exactly one variation, retrying transient failures."""
        prompt = (
            f"Rewrite the text below as paraphrase {variation_number}. "
            "Preserve its complete meaning, facts, technical terms, examples, "
            "and important details. Do not summarize, omit information, or "
            "add facts. Use different wording and natural grammar. "
            "Return only the rewritten text, without a heading or explanation.\n\n"
            f"TEXT:\n{text}"
        )

        last_error = "Groq request failed."

        for attempt in range(self.max_retries + 1):
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a careful academic paraphrasing assistant. "
                            "Preserve all information and meaning. Never summarize."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.5,
                "max_completion_tokens": self.max_completion_tokens,
            }

            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=120,
                )

                if response.status_code == 429:
                    last_error = (
                        "API Error 429: Groq rate limit. "
                        "The request was not completed. "
                        + (response.text or "")[:700]
                    )
                    if attempt < self.max_retries:
                        time.sleep(self._retry_delay(response, attempt))
                        continue
                    return None, last_error

                if response.status_code >= 500:
                    last_error = (
                        f"Groq server error {response.status_code}: "
                        f"{(response.text or '')[:500]}"
                    )
                    if attempt < self.max_retries:
                        time.sleep(3 * (attempt + 1))
                        continue
                    return None, last_error

                if response.status_code != 200:
                    return None, (
                        f"API Error {response.status_code}: "
                        f"{(response.text or '')[:1000]}"
                    )

                data = response.json()
                choices = data.get("choices") or []
                if not choices:
                    last_error = "Groq returned no completion choices."
                    if attempt < self.max_retries:
                        time.sleep(2)
                        continue
                    return None, last_error

                choice = choices[0]
                message = choice.get("message") or {}
                finish_reason = choice.get("finish_reason")
                content = self._clean_paraphrase(message.get("content"))

                if not content:
                    last_error = (
                        "Groq returned empty content for variation "
                        f"{variation_number}. Finish reason: {finish_reason}."
                    )
                    if attempt < self.max_retries:
                        time.sleep(2)
                        continue
                    return None, last_error

                if finish_reason == "length":
                    last_error = (
                        f"Groq truncated variation {variation_number} because "
                        "the completion-token limit was reached. Reduce the "
                        "section size and try again."
                    )
                    return None, last_error

                return content, None

            except requests.exceptions.Timeout:
                last_error = "Groq request timed out."
                if attempt < self.max_retries:
                    time.sleep(2)
                    continue
                return None, last_error

            except requests.exceptions.RequestException as exc:
                return None, f"Groq connection error: {exc}"

            except (ValueError, KeyError, IndexError, TypeError) as exc:
                last_error = f"Could not read Groq response: {exc}"
                if attempt < self.max_retries:
                    time.sleep(2)
                    continue
                return None, last_error

        return None, last_error

    def paraphrase(self, text, num_return_sequences=3):
        """Return the requested number of paraphrases, one API call each."""
        if not isinstance(text, str) or not text.strip():
            return ["Please provide valid text."]

        try:
            count = int(num_return_sequences)
        except (TypeError, ValueError):
            count = 3
        count = max(1, min(count, 3))

        results = []
        for variation_number in range(1, count + 1):
            result, error = self._generate_one(text, variation_number)
            if error:
                # Return a single explicit error marker. The existing pipeline
                # recognises this and will not label a partial set as complete.
                return [f"Groq returned: Variation {variation_number} failed: {error}"]

            results.append(result)
            if variation_number < count:
                time.sleep(self.request_pause_seconds)

        return results
