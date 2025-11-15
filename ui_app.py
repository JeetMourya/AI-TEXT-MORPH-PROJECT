# -*- coding: utf-8 -*-
import streamlit as st
import requests
import json

# Page configuration
st.set_page_config(
    page_title="AI Text Summarizer & Paraphraser - PROFESSIONAL",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# YOUR PERMANENT GROQ API KEY
GROQ_API_KEY = "gsk_cB3ScHxopvjprVTUbRLdWGdyb3FYxvNtrg0AZS4nTS4Xe01RBdwAA"

def clean_duplicate_text(text):
    """Remove duplicate sentences from text"""
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    
    # Remove duplicates while preserving order
    unique_sentences = []
    for sentence in sentences:
        normalized = ' '.join(sentence.lower().split())
        if normalized not in [' '.join(s.lower().split()) for s in unique_sentences]:
            unique_sentences.append(sentence)
    
    # Take reasonable number of sentences
    cleaned_text = '. '.join(unique_sentences[:8]) + '.'
    return cleaned_text

def groq_summarize(text, length='medium'):
    """High-quality summarization using GROQ"""
    try:
        # Clean duplicate text first
        clean_text = clean_duplicate_text(text)
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        length_map = {
            'short': "2-3 sentences",
            'medium': "4-5 sentences", 
            'long': "6-7 sentences"
        }
        
        prompt = f"""Create a concise summary of the following text in {length_map[length]}. Extract the main ideas and key points:

{clean_text}

Summary:"""
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "llama-3.1-8b-instant",
            "temperature": 0.3,
            "max_tokens": 300,
            "top_p": 0.9,
            "stream": False
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            return "API busy. Please try again in few seconds."
    except Exception as e:
        return f"Error: {str(e)}"

def groq_paraphrase(text):
    """High-quality paraphrasing using GROQ"""
    try:
        # Clean duplicate text first
        clean_text = clean_duplicate_text(text)
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Paraphrase the following text completely. Use different words, change sentence structures, and make it sound natural while preserving the original meaning:

{clean_text}

Paraphrased version:"""
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": "llama-3.1-8b-instant",
            "temperature": 0.7,
            "max_tokens": 400,
            "top_p": 0.9,
            "stream": False
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            return "API busy. Please try again in few seconds."
    except Exception as e:
        return f"Error: {str(e)}"

# PROFESSIONAL UI (permanent_app.py style)
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .professional-badge {
        background-color: #00DC82;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .success-box {
        background-color: #d4edda;
        border: 2px solid #c3e6cb;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .api-status {
        background-color: #e8f5e8;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #28a745;
    }
    .feature-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📝 AI Text Summarizer & Paraphraser</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header"><span class="professional-badge">🚀 PROFESSIONAL EDITION</span> - Smart Text Cleaning + Permanent API</div>', unsafe_allow_html=True)

st.markdown("---")

# SIDEBAR (Professional layout)
with st.sidebar:
    st.header("⚙️ Settings")
    
    method = st.radio(
        "Summarization Method",
        ["Extractive", "Abstractive"],
        index=1
    )
    
    length = st.select_slider(
        "Summary Length",
        options=["Short", "Medium", "Long"],
        value="Medium"
    )
    
    st.markdown("---")
    st.markdown("### 🔐 API Status")
    
    st.markdown('<div class="api-status">', unsafe_allow_html=True)
    st.success("✅ **ACTIVE & PERMANENT**")
    st.caption(f"Key: {GROQ_API_KEY[:10]}...{GROQ_API_KEY[-6:]}")
    st.info("🚀  free requests/month")
    st.info("✅ GROQ API KEY LOADED")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🛠️ Smart Features")
    
    st.markdown('<div class="feature-box">', unsafe_allow_html=True)
    st.success("✅ **Auto Duplicate Removal**")
    st.caption("Removes repeated text automatically")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="feature-box">', unsafe_allow_html=True)
    st.success("✅ **GROQ AI Powered**")
    st.caption("High-quality summarization & paraphrasing")
    st.markdown('</div>', unsafe_allow_html=True)

# MAIN CONTENT (Professional layout)
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📄 Input Text")
    input_text = st.text_area(
        "Paste your text below:",
        height=300,
        placeholder="Enter your text here...\n\n💡 Tip: App automatically removes duplicate sentences",
        key="input_text"
    )
    
    # Smart text analysis
    if input_text:
        word_count = len(input_text.split())
        sentences = [s.strip() for s in input_text.split('.') if s.strip()]
        unique_sentences = []
        for s in sentences:
            normalized = ' '.join(s.lower().split())
            if normalized not in [' '.join(us.lower().split()) for us in unique_sentences]:
                unique_sentences.append(s)
        
        st.caption(f"📊 Analysis: {word_count} words | {len(sentences)} sentences | {len(unique_sentences)} unique")
        
        if len(sentences) > len(unique_sentences):
            st.info(f"🔍 Smart cleaning: Removed {len(sentences) - len(unique_sentences)} duplicate sentences")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        summarize_btn = st.button("✨ Summarize", use_container_width=True, type="primary")
    with col_btn2:
        paraphrase_btn = st.button("🔄 Paraphrase", use_container_width=True)

with col2:
    st.subheader("📊 Output")
    
    if summarize_btn and input_text.strip():
        with st.spinner("🚀 GROQ AI is summarizing..."):
            result = groq_summarize(input_text, length.lower())
            if "Error" in result or "busy" in result.lower():
                st.error(f"❌ {result}")
                st.info("💡 Try again in 10 seconds")
            else:
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.success("✅ **Professional Summary Generated Successful!**")
                st.markdown('</div>', unsafe_allow_html=True)
                st.text_area("Summary", result, height=250, key="summary_output")
                
                # Show smart metrics
                original_len = len(input_text)
                summary_len = len(result)
                if original_len > 0:
                    compression = int((1 - summary_len/original_len) * 100)
                    st.caption(f"📈 Smart Compression: {compression}% shorter")
                
                st.download_button(
                    label="📥 Download Summary",
                    data=result,
                    file_name="professional_summary.txt",
                    mime="text/plain"
                )
    
    elif paraphrase_btn and input_text.strip():
        with st.spinner("🚀 GROQ AI is paraphrasing..."):
            result = groq_paraphrase(input_text)
            
            if "Error" in result or "busy" in result.lower():
                st.error(f"❌ {result}")
                st.info("💡 Try again in 10 seconds")
            else:
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.success("✅ **Professional Paraphrase Generated Successful!**")
                st.markdown('</div>', unsafe_allow_html=True)
                st.text_area("Paraphrased Text", result, height=250, key="paraphrase_output")
                
                st.download_button(
                    label="📥 Download Paraphrase",
                    data=result,
                    file_name="professional_paraphrase.txt",
                    mime="text/plain"
                )
    
    else:
        st.info("👈 Enter text and click a button to get started!")
        st.markdown("---")
        st.markdown("### 🎯 Key Features:")
        st.success("• **Smart Duplicate Removal** - Auto-cleans repeated text")
        st.success("• **Permanent API** - Never expires")
        st.success("• **Professional Quality** - GROQ AI powered")
        st.success("• **Download Ready** - Save results instantly")

st.markdown("---")
st.caption("🚀 PROFESSIONAL EDITION • Smart Text Cleaning • Permanent API • Never Expires")
