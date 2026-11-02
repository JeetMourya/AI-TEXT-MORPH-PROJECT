# 📚 API Documentation - Text Morph

## Overview

Text Morph integrates with two primary APIs to provide AI-powered text processing capabilities:

1. **Hugging Face Inference API** - For text summarization (BART model)
2. **GROQ API** - For text paraphrasing (LLaMA 3.1 model)

---

## 🔐 Authentication

Both APIs require authentication via API keys stored in environment variables.

### Setting Up API Keys

Create a `.env` file in the `src/` directory:

```env
HF_API_KEY=your_huggingface_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

### Obtaining API Keys

#### Hugging Face API Key
1. Visit: https://huggingface.co/settings/tokens
2. Sign up or log in
3. Click "New token"
4. Name: "Text Morph"
5. Type: Read
6. Copy the generated token (starts with `hf_`)

#### GROQ API Key
1. Visit: https://console.groq.com/keys
2. Sign up or log in
3. Click "Create API Key"
4. Name: "Text Morph Paraphraser"
5. Copy the generated key (starts with `gsk_`)

---

## 🤖 Hugging Face API

### Base Information

- **Base URL**: `https://api-inference.huggingface.co/models/`
- **Model**: `facebook/bart-large-cnn`
- **Authentication**: Bearer token in headers
- **Timeout**: 60 seconds
- **Rate Limit**: ~1000 requests/hour (free tier)

### Endpoints

#### POST /models/facebook/bart-large-cnn

Generates text summaries using the BART model.

**Request Headers:**
```http
Authorization: Bearer {HF_API_KEY}
Content-Type: application/json
```

**Request Body:**
```json
{
  "inputs": "Your text to summarize goes here...",
  "parameters": {
    "max_length": 130,
    "min_length": 60,
    "do_sample": true,
    "temperature": 0.7,
    "top_p": 0.9
  }
}
```

**Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `inputs` | string | Text to summarize (required) | - |
| `max_length` | integer | Maximum summary length | 130 |
| `min_length` | integer | Minimum summary length | 60 |
| `do_sample` | boolean | Enable sampling for abstractive | false |
| `temperature` | float | Controls randomness (0.0-1.0) | 0.7 |
| `top_p` | float | Nucleus sampling threshold | 0.9 |

**Response (Success - 200):**
```json
[
  {
    "summary_text": "This is the generated summary of your input text."
  }
]
```

**Response (Model Loading - 503):**
```json
{
  "error": "Model facebook/bart-large-cnn is currently loading"
}
```

**Response (Error - 4xx/5xx):**
```json
{
  "error": "Error message describing the issue"
}
```

### Python Implementation Example

```python
import requests

class AbstractiveSummarizer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def summarize(self, text, length='medium'):
        length_map = {
            'short': {"max_length": 60, "min_length": 30},
            'medium': {"max_length": 130, "min_length": 60},
            'long': {"max_length": 200, "min_length": 130}
        }
        
        params = length_map.get(length, length_map['medium'])
        payload = {
            "inputs": text,
            "parameters": {
                **params,
                "do_sample": True,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        response = requests.post(
            self.api_url, 
            headers=self.headers, 
            json=payload, 
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result[0].get("summary_text", "")
        else:
            raise Exception(f"API Error: {response.status_code}")
```

### Error Handling

| Status Code | Meaning | Action |
|-------------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Check input format |
| 401 | Unauthorized | Verify API key |
| 429 | Rate Limit | Wait and retry |
| 503 | Model Loading | Retry after 30-60s |
| 500 | Server Error | Retry with backoff |

---

## 🚀 GROQ API

### Base Information

- **Base URL**: `https://api.groq.com/openai/v1/`
- **Model**: `llama-3.1-8b-instant`
- **Authentication**: Bearer token in headers
- **Timeout**: 60 seconds
- **Rate Limit**: Generous free tier

### Endpoints

#### POST /chat/completions

Generates paraphrased text using LLaMA 3.1 model.

**Request Headers:**
```http
Authorization: Bearer {GROQ_API_KEY}
Content-Type: application/json
```

**Request Body:**
```json
{
  "model": "llama-3.1-8b-instant",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful AI that paraphrases text naturally and clearly."
    },
    {
      "role": "user",
      "content": "Paraphrase the following text: [Your text here]"
    }
  ],
  "temperature": 0.9,
  "max_tokens": 1000
}
```

**Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `model` | string | Model identifier (required) | llama-3.1-8b-instant |
| `messages` | array | Conversation messages | - |
| `temperature` | float | Creativity level (0.0-2.0) | 0.9 |
| `max_tokens` | integer | Maximum response length | 1000 |

**Response (Success - 200):**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "llama-3.1-8b-instant",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "1. First paraphrased version\n2. Second paraphrased version\n3. Third paraphrased version"
      },
      "finish_reason": "stop"
    }
  ]
}
```

**Response (Error):**
```json
{
  "error": {
    "message": "Error description",
    "type": "invalid_request_error",
    "code": "invalid_api_key"
  }
}
```

### Python Implementation Example

```python
import requests
import os

class Paraphraser:
    def __init__(self, model_name="llama-3.1-8b-instant"):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.model_name = model_name
    
    def paraphrase(self, text, num_return_sequences=3):
        prompt = f"Paraphrase the following text. Provide {num_return_sequences} unique variations:\n\n{text}"
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are a helpful AI that paraphrases text."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.9,
            "max_tokens": 1000
        }
        
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            raise Exception(f"API Error: {response.status_code}")
```

### Error Handling

| Status Code | Meaning | Action |
|-------------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Verify API key |
| 429 | Rate Limit | Implement backoff |
| 500 | Server Error | Retry request |

---

## 🔄 Combined Pipeline API

The `SummarizationPipeline` class combines both APIs into a unified interface.

### Class: SummarizationPipeline

**Initialization:**
```python
from combinedPipeline import SummarizationPipeline

pipeline = SummarizationPipeline(hf_api_key="your_hf_key")
```

### Methods

#### summarize(text, method, length)

Generates text summary.

**Parameters:**
- `text` (str): Input text to summarize
- `method` (str): 'extractive' or 'abstractive'
- `length` (str): 'short', 'medium', or 'long'

**Returns:**
- `str`: Generated summary

**Example:**
```python
summary = pipeline.summarize(
    text="Long article text here...",
    method="abstractive",
    length="medium"
)
print(summary)
```

#### paraphrase(text, num_return_sequences)

Generates paraphrased text.

**Parameters:**
- `text` (str): Input text to paraphrase
- `num_return_sequences` (int): Number of variations (default: 3)

**Returns:**
- `str`: Paraphrased variations (newline separated)

**Example:**
```python
paraphrased = pipeline.paraphrase(
    text="The weather is nice today.",
    num_return_sequences=3
)
print(paraphrased)
```

#### get_status()

Returns status of all components.

**Returns:**
- `dict`: Component availability status

**Example:**
```python
status = pipeline.get_status()
# {
#   "extractive": True,
#   "abstractive": True,
#   "groq_paraphraser": True
# }
```

---

## 📊 Rate Limits & Best Practices

### Hugging Face API

**Free Tier Limits:**
- ~1000 requests per hour
- ~30,000 requests per month
- Model warm-up time: 30-60 seconds on first request

**Best Practices:**
1. Implement exponential backoff on 503 errors
2. Cache results when possible
3. Batch requests during off-peak hours
4. Handle model loading gracefully

### GROQ API

**Free Tier Limits:**
- Generous limits for development
- Fast inference speeds
- Minimal cold start time

**Best Practices:**
1. Use appropriate temperature settings
2. Set reasonable max_tokens
3. Implement retry logic
4. Monitor usage dashboard

---

## 🛡️ Security Best Practices

### API Key Management

✅ **DO:**
- Store keys in `.env` files
- Add `.env` to `.gitignore`
- Use environment variables in production
- Rotate keys periodically
- Use separate keys for dev/prod

❌ **DON'T:**
- Hardcode keys in source code
- Commit keys to version control
- Share keys publicly
- Use same key across projects
- Log API keys

### Example Secure Loading

```python
import os
from dotenv import load_dotenv
from pathlib import Path

# Load from specific path
env_path = Path(__file__).parent / "src" / ".env"
load_dotenv(dotenv_path=env_path)

# Access securely
HF_API_KEY = os.getenv('HF_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Validate
if not HF_API_KEY or not GROQ_API_KEY:
    raise ValueError("API keys not found in environment")
```

---

## 🧪 Testing APIs

### Test Hugging Face Connection

```python
import requests

def test_hf_api(api_key):
    url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": "Artificial Intelligence is transforming the world.",
        "parameters": {"max_length": 50, "min_length": 20}
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

test_hf_api("your_api_key_here")
```

### Test GROQ Connection

```python
import requests

def test_groq_api(api_key):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "user", "content": "Say hello!"}
        ],
        "max_tokens": 50
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

test_groq_api("your_api_key_here")
```

---

## 📞 Support & Resources

### Hugging Face
- **Documentation**: https://huggingface.co/docs/api-inference
- **Model Card**: https://huggingface.co/facebook/bart-large-cnn
- **Community Forum**: https://discuss.huggingface.co/
- **Status Page**: https://status.huggingface.co/

### GROQ
- **Documentation**: https://console.groq.com/docs
- **Model Info**: https://groq.com/
- **Support**: https://console.groq.com/support

---

## 🔧 Troubleshooting

### Common Issues

**Issue: "API key not found"**
- Solution: Check `.env` file exists in `src/` folder
- Verify variable names: `HF_API_KEY`, `GROQ_API_KEY`

**Issue: "Model is loading"**
- Solution: Wait 30-60 seconds and retry
- First request after inactivity takes longer

**Issue: "Rate limit exceeded"**
- Solution: Implement exponential backoff
- Wait before retrying (5-10 minutes)

**Issue: "Connection timeout"**
- Solution: Check internet connection
- Increase timeout value
- Retry with exponential backoff

---

## 📝 Changelog

### Version 1.0.0 (Current)
- Initial API integration
- Hugging Face BART summarization
- GROQ LLaMA paraphrasing
- Combined pipeline interface

---

**Last Updated**: October 2025  
**Maintained By**: Jeevan HS 
**License**: MIT