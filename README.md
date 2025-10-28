<h1 align="center"> 🧠 AI Text Morph Summarizer & Paraphraser </h1>

<p align="center">
<b>AI Text Morph</b> is an advanced NLP-based application that <b>summarizes</b> and <b>paraphrases</b> long or complex text using state-of-the-art transformer models.  
It seamlessly integrates <b>Hugging Face Inference API</b> and <b>Groq API</b> within a <b>Streamlit</b> interface for real-time intelligent text generation.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Made%20With-Python_3.10+-blueviolet?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/Framework-Streamlit-ff4b4b?style=flat-square&logo=streamlit" />
  <img src="https://img.shields.io/badge/NLP-HuggingFace-FCC624?style=flat-square&logo=huggingface" />
  <img src="https://img.shields.io/badge/AI-Groq_API-8A2BE2?style=flat-square&logo=ai" />
  <img src="https://img.shields.io/badge/License-MIT-success?style=flat-square" />
</p>

<h6 align="center">
  <b>Smart AI Tool for Text Summarization & Paraphrasing in Real-Time</b><br>
  <i>Built with Streamlit • Hugging Face • Groq API</i>
</h6>

---

## 🚀 Features

- 🧩 **Dual Summarization** – Abstractive & Extractive methods for flexibility  
- ✨ **Intelligent Paraphrasing** – Rewrites sentences naturally using LLaMA 3.1  
- ⚡ **Real-Time Processing** – Fast inference via Groq Cloud  
- 🧠 **LLM-Driven Architecture** – Uses state-of-the-art transformer models  
- 🔐 **Environment Variables** – Secure credential management using `.env`  
- 🧾 **Modular Codebase** – Easy to extend and maintain  
- 🖥️ **Streamlit UI** – Simple, interactive, and responsive web interface  

---

## 🧩 Tech Stack

| Layer | Technology |
|-------|-------------|
| **Frontend** | Streamlit |
| **Backend** | Python 3.10+ |
| **AI/NLP** | Hugging Face Transformers, Groq API |
| **Configuration** | dotenv + YAML |
| **Logging** | Python logging |
| **Environment** | Virtualenv |

---

## 🤖 AI Models

| Model | Developer | Purpose |
|--------|------------|----------|
| **BART (`facebook/bart-large-cnn`)** | Meta AI | Text Summarization |
| **LLaMA 3.1 (`llama-3.1-8b-instant`)** | Meta AI | Text Paraphrasing |

---

## 📁 Project Structure

```
AI-TEXT-MORPH-PROJECT/
├── mvp/
│   ├── __init__.py
│   ├── abstractive.py       # Abstractive summarization
│   ├── extractive.py        # Extractive summarization
│   ├── parapharsing.py      # Text paraphrasing
│   ├── mvp_pipeline.py      # Main pipeline
│   └── test_run.py          # Test scripts
│
├── simple_app.py            # CLI version
├── ui_app.py                # Streamlit web app
├── config.yaml              # Configuration file
├── requirements.txt         # Dependencies
├── .env.example             # API key template
└── README.md
```


---


## ⚙️ Installation

Follow these steps to set up and run **AI Text Morph** locally:

```bash
# 1️⃣ Clone this repository
git clone https://github.com/JeetMourya/AI-TEXT-MORPH-PROJECT.git
cd AI-TEXT-MORPH-SUMMARIZER-PROJECT-

# 2️⃣ Create a virtual environment
python -m venv venv
venv\Scripts\activate       # On Windows
# or
source venv/bin/activate    # On macOS/Linux

# 3️⃣ Install dependencies
pip install -r requirements.txt

# 4️⃣ Setup environment variables
cp .env.example .env
# Then edit .env and add your API keys:
HF_API_KEY="your_huggingface_api_key"
GROQ_API_KEY="your_groq_api_key"

# 5️⃣ Run the Streamlit app
streamlit run ui_app.py
💡 Usage Examples
🔹 Abstractive Summarization
from mvp.abstractive import AbstractiveSummarizer
summarizer = AbstractiveSummarizer(api_key="your_hf_key")
summary = summarizer.summarize(text, length='medium')

🔹 Extractive Summarization
from mvp.extractive import ExtractiveSummarizer
summarizer = ExtractiveSummarizer(api_key="your_hf_key")
summary = summarizer.summarize(text, length='short')

🔹 Paraphrasing
from mvp.parapharsing import Paraphraser
paraphraser = Paraphraser()
variations = paraphraser.paraphrase("Your sentence here", num_return_sequences=3)

🔹 Full Pipeline
from mvp.mvp_pipeline import SummarizationPipeline
pipeline = SummarizationPipeline(hf_api_key="your_hf_key")
abstractive = pipeline.summarize(text, method="abstractive")
paraphrased = pipeline.paraphrase("Sample text", 2)

⚙️ Configuration Example (config.yaml)
  summarization:
  max_length: 200
  min_length: 30
  temperature: 0.7

paraphrasing:
  model: "llama-3.1-8b-instant"
  max_tokens: 400

📊 Highlights
✅ Dual Summarization (Abstractive + Extractive)
✅ AI-Based Paraphrasing via LLaMA 3.1
✅ Hugging Face + Groq API Integration
✅ Modular, Configurable Architecture
✅ Secure Environment Variable Management
✅ Streamlit Interface for Easy Interaction

👨‍💻 Developer
Developed by: Jeet Mourya
💡 AI Enthusiast & Full-Stack Developer
📧 jeetmourya7898@gmail.com
🔗 GitHub Profile

Contribution
Feel free to contribute to this project by:

Reporting bugs

Suggesting new features

Submitting pull requests

Improving documentation

📄 License
This project is open source and available under the MIT License.

🤝 Support
For support, email or create an issue in the repository.

⭐ If you find this project useful, please give it a star on GitHub!

text

ये README.md आपके project को professionally present करेगा! इसे add करने के लिए:

```bash
git add README.md
git commit -m "Add professional README with project details and developer information"
git push origin main# AI Text Summarizer & Paraphraser

A powerful web application for text summarization and paraphrasing using Hugging Face Inference API.

## Features

- **Text Summarization**: Both extractive and abstractive methods
- **Text Paraphrasing**: Rewrite text while preserving meaning
- **Multiple Length Options**: Short, medium, and long summaries
- **Download Results**: Save summaries and paraphrased text as files
- **No Local Models**: Uses Hugging Face Inference API

## Installation

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate# AI Text Summarizer & Paraphraser

A powerful web application for text summarization and paraphrasing using Hugging Face Inference API.

## Features

- **Text Summarization**: Both extractive and abstractive methods
- **Text Paraphrasing**: Rewrite text while preserving meaning
- **Multiple Length Options**: Short, medium, and long summaries
- **Download Results**: Save summaries and paraphrased text as files
- **No Local Models**: Uses Hugging Face Inference API

## Installation

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
