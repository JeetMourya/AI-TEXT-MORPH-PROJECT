---

# 🔮 Text Morph - Advanced Text Summarization & Paraphrasing

<div align="center">

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-FF4B4B.svg?style=flat\&logo=streamlit\&logoColor=white)
![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-API-yellow.svg)
![NLP](https://img.shields.io/badge/NLP-BART%20%7C%20LLaMA-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

*A sleek, AI-driven web app for intelligent text summarization and paraphrasing using state-of-the-art language models.*

</div>

## 📸 Screenshots

Preview of the Text Morph interface:

![Interface](assets/screenshot1.png)
![Interface](assets/screenshot2.png)

## 📋 Table of Contents

* [🎯 Overview](#-overview)
* [✨ Features](#-features)
* [🛠️ Technologies Used](#️-technologies-used)
* [🤖 AI Models](#-ai-models)
* [🚀 Quick Start](#-quick-start)
* [🔄 Usage](#-usage)
* [📈 Project Structure](#-project-structure)
* [🎨 UI Features](#-ui-features)
* [🤝 Contributing](#-contributing)
* [📄 License](#-license)

## 🎯 Overview

**Text Morph** is an AI-powered platform that simplifies long texts into concise summaries and rephrased versions. It integrates **BART** and **LLaMA 3.1** models to deliver accurate and fluent text transformation.

### Core Functions

1. **Summarization** – Condenses long documents using both extractive and abstractive techniques.
2. **Paraphrasing** – Rewrites content while preserving original meaning.

The application features a modern UI with smooth animations and responsive design—ideal for students, researchers, writers, and professionals.

## ✨ Features

### 🎨 Modern Interface

* Elegant gradient design with purple tones and smooth transitions
* Tab-based navigation: *Process Text*, *Examples*, and *How It Works*
* Fully responsive layout for all screen sizes
* Real-time metrics: word/character count and reduction rate
* Smooth hover and animation effects

### 🤖 AI Intelligence

* **Dual Summarization Modes:**

  * *Extractive* – Selects key sentences.
  * *Abstractive* – Generates natural summaries using AI.
* **Smart Paraphrasing:** Produces fluent alternatives while maintaining meaning.
* **Adjustable Summary Lengths:** Short, Medium, and Long options.

### ⚡ Performance & Convenience

* Quick responses (2–5 seconds)
* No local model setup required
* Download outputs as `.txt` files
* Real-time API connectivity status

## 🛠️ Technologies Used

| Technology                                                                                              | Purpose                   |
| ------------------------------------------------------------------------------------------------------- | ------------------------- |
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat\&logo=python\&logoColor=white)          | Core programming language |
| ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat\&logo=streamlit\&logoColor=white) | Web app framework         |
| ![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-FFD21E?style=flat)                     | API for BART model        |
| ![GROQ](https://img.shields.io/badge/GROQ-000000?style=flat\&logo=groq\&logoColor=white)                | LLaMA model inference API |
| ![Requests](https://img.shields.io/badge/Requests-2CA5E0?style=flat)                                    | API calls                 |
| ![Python-dotenv](https://img.shields.io/badge/python--dotenv-ECD53F?style=flat)                         | Environment management    |
| ![CSS](https://img.shields.io/badge/CSS3-1572B6?style=flat\&logo=css3\&logoColor=white)                 | Styling and animations    |

## 🤖 AI Models

### BART (Bidirectional and Auto-Regressive Transformers)

* **By:** Facebook AI Research
* **Model:** `facebook/bart-large-cnn`
* **Parameters:** 406M
* **Use:** Summarization
* **Highlights:** Context-aware, accurate, and versatile

### LLaMA 3.1 (Large Language Model Meta AI)

* **By:** Meta AI
* **Model:** `llama-3.1-8b-instant`
* **Parameters:** 8B
* **Use:** Paraphrasing
* **Highlights:** Fluent text generation, fast inference, semantic preservation

## 🚀 Quick Start

### Requirements

* Python 3.8+
* Hugging Face API Key
* GROQ API Key

### Setup

```bash
# Clone the repository
git clone https://github.com/kiruthikkumar05/Textmorph-AI.git
cd Textmorph-AI

# Create a virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# or
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Configure API Keys

Create a `.env` file in the project root:

```env
HF_API_KEY=your_huggingface_api_key
GROQ_API_KEY=your_groq_api_key
```

Get your keys from:

* [Hugging Face](https://huggingface.co/settings/tokens)
* [GROQ](https://console.groq.com/keys)

### Launch

```bash
streamlit run app.py
```

## 🔄 Usage

1. **Run the App**

   ```bash
   streamlit run app.py
   ```
2. **Access in Browser** – Visit `http://localhost:8501`
3. **Select Settings** – Choose summarization mode and summary length
4. **Process Text** – Paste text and click **Summarize** or **Paraphrase**
5. **Download Output** – Save results as `.txt`
6. **Explore Tabs** – Examples and explanations available for guidance

## 📈 Project Structure

```
TEXT_MORPH/
├── assets/              # UI assets and screenshots
├── configure/           # Configuration files
├── docs/                # Documentation
├── src/                 # Core application code
├── app.py               # Main Streamlit app
├── requirements.txt     # Dependencies
├── .gitignore
└── README.md
```

## 🎨 UI Features

* Gradient background header with elegant branding
* Sidebar with configuration panel, API status, and quick stats
* Responsive two-column layout for input and output
* Animated feature cards and smooth transitions
* Download and export integration
* Professional color scheme with rounded design elements

## 🤝 Contributing

Contributions are welcome!

1. 🍴 Fork the repository
2. 🌿 Create a branch (`git checkout -b feature/YourFeature`)
3. 💾 Commit your changes (`git commit -m "Add YourFeature"`)
4. 📤 Push to the branch (`git push origin feature/YourFeature`)
5. 🔄 Submit a Pull Request

### Ideas for Improvement

* 🌙 Dark mode
* 🌍 Multi-language support
* 📄 File upload (PDF/DOCX)
* 📊 Batch text processing
* 📝 History tracking
* 🎨 Theme customization
* 🤖 Additional AI models
* 📱 PWA support

## 📄 License

Licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### 🌟 If you found this project helpful, please star the repo! ⭐

**Built with ❤️ | Powered by AI**

[Report Bug](https://github.com/kiruthikkumar05/Textmorph-AI/issues) · [Request Feature](https://github.com/kiruthikkumar05/Textmorph-AI/issues)

</div>

---
