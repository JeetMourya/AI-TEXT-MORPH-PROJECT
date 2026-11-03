"""TextMorph - AI-Based Advanced Text Summarization and Paraphrasing System.

Streamlit front end. The AI backend (src/combinedPipeline.py -> SummarizationPipeline)
is used exactly as before: pipeline.summarize(text, method=..., length=...) and
pipeline.paraphrase(text). Nothing here fakes or hardcodes an AI result.
"""
import html
import inspect
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import streamlit as st

# --------------------------------------------------------------------------
# Environment + Hugging Face key resolution.
# This runs BEFORE the backend is imported so that anything the backend reads from
# os.environ at import time already sees the final, consistent key.
# --------------------------------------------------------------------------
# Add src folder to Python path (unchanged from the original app)
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))
env_path = src_path / ".env"

from dotenv import dotenv_values, load_dotenv  # noqa: E402


def _clean_key(value) -> str:
    """Trim whitespace, wrapping quotes and an accidental 'Bearer ' prefix from a pasted token."""
    if value is None:
        return ""
    cleaned = str(value).strip().strip("'\"").strip()
    if cleaned.lower().startswith("bearer "):
        cleaned = cleaned[7:].strip()
    return cleaned


def _secret(name: str):
    """Read one Streamlit secret; returns None when there is no secrets file or the key is absent."""
    try:
        return st.secrets.get(name)
    except Exception:
        return None


# What the operating system provided BEFORE src/.env is read. load_dotenv() never overrides
# an existing variable, so a stale value here would silently win over the value in src/.env.
_PRE_ENV_HF_KEY = _clean_key(os.environ.get("HF_API_KEY"))

try:
    # utf-8-sig drops a Windows BOM; without it the first line would be read as "\ufeffHF_API_KEY".
    load_dotenv(dotenv_path=env_path, encoding="utf-8-sig")
    ENV_FILE_VALUES = dict(dotenv_values(dotenv_path=env_path, encoding="utf-8-sig"))
except TypeError:  # very old python-dotenv without the encoding argument
    load_dotenv(dotenv_path=env_path)
    ENV_FILE_VALUES = dict(dotenv_values(dotenv_path=env_path))


def resolve_hf_key() -> dict:
    """Pick ONE Hugging Face token and make every consumer in this process use it.

    Priority: src/.env HF_API_KEY, OS environment HF_API_KEY, Streamlit secrets HF_API_KEY,
    Streamlit secrets HF_TOKEN (legacy). The returned dict never exposes more than the source,
    notes and the key itself (the key is only ever used internally, never rendered).
    """
    candidates = [
        ("src/.env (HF_API_KEY)", _clean_key(ENV_FILE_VALUES.get("HF_API_KEY"))),
        ("operating-system environment variable HF_API_KEY", _PRE_ENV_HF_KEY),
        ("Streamlit secrets (HF_API_KEY)", _clean_key(_secret("HF_API_KEY"))),
        ("Streamlit secrets (legacy HF_TOKEN)", _clean_key(_secret("HF_TOKEN"))),
    ]
    key, source = "", "not found"
    for label, value in candidates:
        if value:
            key, source = value, label
            break

    notes = []
    if not env_path.exists():
        notes.append("src/.env was not found.")
    elif not _clean_key(ENV_FILE_VALUES.get("HF_API_KEY")):
        notes.append("src/.env exists but has no HF_API_KEY value (check the spelling of the name).")
    if key:
        if _PRE_ENV_HF_KEY and _PRE_ENV_HF_KEY != key:
            notes.append("A different HF_API_KEY was already set in the operating-system environment. "
                         "It was ignored; the source above is used instead.")
        if not key.startswith("hf_"):
            notes.append("The token does not start with 'hf_', which Hugging Face tokens normally do.")
        os.environ["HF_API_KEY"] = key
        other = _clean_key(os.environ.get("HF_TOKEN"))
        if other and other != key:
            # Libraries such as huggingface_hub read HF_TOKEN on their own. Point it at the same token
            # (this process only; no file is changed) so two different tokens can never be in play.
            os.environ["HF_TOKEN"] = key
            notes.append("HF_TOKEN held a different value. For this session it now matches HF_API_KEY.")
    return {"key": key, "source": source, "notes": notes}


HF_KEY_INFO = resolve_hf_key()

# Groq key loading (behaviour unchanged; the three duplicated try-blocks of the original are merged
# into one block that does exactly the same thing).
try:
    if not os.getenv("GROQ_API_KEY"):
        groq_key = st.secrets.get("GROQ_API_KEY")
        if groq_key:
            os.environ["GROQ_API_KEY"] = groq_key
except Exception as e:
    print(f"Cloud secrets loading issue: {e}")

# Existing backend (unchanged) - imported only after the environment above is final
from src.combinedPipeline import SummarizationPipeline  # noqa: E402

from tm_ui import api_status, helpers, theme  # noqa: E402

st.set_page_config(
    page_title="TextMorph - AI Summarization & Paraphrasing",
    page_icon="\u2726",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# Constants and small compatibility helpers
# --------------------------------------------------------------------------
NAV_PAGES = [
    "Dashboard",
    "Text Summarization",
    "Text Paraphrasing",
    "Document Processing",
    "About TextMorph",
    "API / Service Status",
]
NAV_ICONS = {
    "Dashboard": "dashboard",
    "Text Summarization": "summarize",
    "Text Paraphrasing": "edit_note",
    "Document Processing": "description",
    "About TextMorph": "info",
    "API / Service Status": "monitor_heart",
}
EDITOR_MODES = ("summarize", "paraphrase", "document")
MODE_LABEL = {"summarize": "Summarization", "paraphrase": "Paraphrasing", "document": "Document"}

_ver = [int(x) for x in re.findall(r"\d+", st.__version__)[:2]] or [0, 0]
HAS_MATERIAL = tuple(_ver) >= (1, 40)  # :material/icon: labels
# Newer Streamlit versions use width="stretch" instead of use_container_width=True.
STRETCH = {"width": "stretch"} if "width" in inspect.signature(st.button).parameters else {"use_container_width": True}


def card(name: str):
    """A styled container. Uses keyed containers (Streamlit >= 1.39) and falls back to a bordered one."""
    try:
        return st.container(key=f"card_{name}")
    except TypeError:
        return st.container(border=True)


# --------------------------------------------------------------------------
# Design system (presentation only): tokens, one stylesheet, small HTML builders
# --------------------------------------------------------------------------
# NOTE: the input-* tokens drive every text control (text areas, text inputs, file uploader).
# They are always SOLID colours (never transparent) so Streamlit's own theme can't leak through.
_LIGHT = {
    "bg": "#F8FAFC", "surface": "#FFFFFF", "surface-2": "#F1F5F9", "border": "#E2E8F0", "border-strong": "#CBD5E1",
    "text": "#0F172A", "muted": "#64748B", "primary": "#4F46E5", "primary-hover": "#4338CA",
    "primary-soft": "#EEF2FF", "btn": "#4F46E5", "btn-hover": "#4338CA",
    "ok": "#15803D", "ok-soft": "#F0FDF4", "warn": "#B45309", "warn-soft": "#FFFBEB",
    "bad": "#B91C1C", "bad-soft": "#FEF2F2", "shadow": "0 1px 2px rgba(15,23,42,.05), 0 4px 16px rgba(15,23,42,.05)",
    "input-bg": "#FFFFFF", "input-text": "#0F172A", "input-border": "#CBD5E1", "input-placeholder": "#64748B",
    "input-caret": "#4F46E5", "drop-bg": "#F5F7FF", "drop-border": "#818CF8", "drop-text": "#475569",
}
_DARK = {
    "bg": "#0B0D12", "surface": "#12151C", "surface-2": "#1A1E27", "border": "#262B36", "border-strong": "#343A48",
    "text": "#E6E8EE", "muted": "#9AA3B5", "primary": "#818CF8", "primary-hover": "#A5B4FC",
    "primary-soft": "rgba(129,140,248,.14)", "btn": "#6366F1", "btn-hover": "#7C83F5",
    "ok": "#4ADE80", "ok-soft": "rgba(74,222,128,.10)", "warn": "#FBBF24", "warn-soft": "rgba(251,191,36,.10)",
    "bad": "#F87171", "bad-soft": "rgba(248,113,113,.10)", "shadow": "0 1px 2px rgba(0,0,0,.4), 0 6px 20px rgba(0,0,0,.3)",
    "input-bg": "#0E1118", "input-text": "#E6E8EE", "input-border": "#3A4151", "input-placeholder": "#9AA3B5",
    "input-caret": "#A5B4FC", "drop-bg": "#161A24", "drop-border": "#6366F1", "drop-text": "#B4BCCD",
}

_CSS = """
html, body, .stApp, button, input, textarea { font-family: 'Inter', -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif; }
.stApp { background: var(--bg); color: var(--text); }
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1320px; padding-top: 2rem; padding-bottom: 3rem; }

/* ---- text ---- */
.stApp [data-testid="stMarkdownContainer"] p, .stApp [data-testid="stMarkdownContainer"] li,
.stApp [data-testid="stMarkdownContainer"] h1, .stApp [data-testid="stMarkdownContainer"] h2,
.stApp [data-testid="stMarkdownContainer"] h3, .stApp [data-testid="stMarkdownContainer"] h4,
.stApp label, .stApp [data-testid="stWidgetLabel"] p { color: var(--text); }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p { color: var(--muted); }
.stApp a { color: var(--primary); }

/* ---- sidebar ---- */
[data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--border); }
[data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }
[data-testid="stSidebar"] div[role="radiogroup"] { gap: 2px; }
[data-testid="stSidebar"] div[role="radiogroup"] > label { padding: .5rem .75rem; border-radius: 9px; width: 100%; cursor: pointer; transition: background .15s; }
[data-testid="stSidebar"] div[role="radiogroup"] > label:hover { background: var(--surface-2); }
[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child,
[data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-child { display: none; }
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) { background: var(--primary-soft); box-shadow: inset 3px 0 0 var(--primary); }
[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { color: var(--primary) !important; font-weight: 650; }
[data-testid="stSidebar"] div[role="radiogroup"] > label p { font-size: .92rem; }
.tm-brand { display: flex; align-items: center; gap: .7rem; padding: .2rem .35rem .9rem; }
.tm-brand-name { font-weight: 700; font-size: 1.08rem; letter-spacing: -.01em; color: var(--text); line-height: 1.1; }
.tm-brand-sub { font-size: .74rem; color: var(--muted); margin-top: .12rem; }
.tm-nav-label { font-size: .74rem; font-weight: 600; color: var(--muted); margin: 1.2rem .4rem .45rem; letter-spacing: .02em; }
.tm-dotrow { display: flex; align-items: center; gap: .55rem; padding: .28rem .4rem; font-size: .82rem; }
.tm-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--border-strong); flex: 0 0 auto; }
.tm-dot-ok { background: var(--ok); } .tm-dot-warn { background: var(--warn); } .tm-dot-bad { background: var(--bad); }
.tm-dot-name { color: var(--text); font-weight: 600; }
.tm-dot-label { color: var(--muted); margin-left: auto; text-align: right; }
.tm-side-foot { font-size: .74rem; color: var(--muted); line-height: 1.55; margin-top: 1rem; padding: .9rem .4rem 0; border-top: 1px solid var(--border); }
.tm-side-foot b { color: var(--text); font-weight: 600; }

/* ---- cards ---- */
[class*="st-key-card_"], div[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1.1rem 1.25rem 1rem; box-shadow: var(--shadow);
}
[class*="st-key-card_action_"] { transition: border-color .2s, box-shadow .2s; }
[class*="st-key-card_action_"]:hover { border-color: var(--primary); }
[class*="st-key-card_ver_"] { background: var(--bg); box-shadow: none; }
.st-key-card_hero { background: radial-gradient(ellipse at 100% 0%, var(--primary-soft), transparent 55%), var(--surface); padding: 1.7rem 1.8rem 1.4rem; }

/* ---- text inputs & text areas (input + generated output) ----
   Streamlit/BaseWeb nest several elements (wrapper > base-input > textarea) and each one carries its own
   background from Streamlit's theme. Every layer gets a SOLID colour here, otherwise the OS/Streamlit dark
   theme shows through ("black box, dark text"). */
.stTextArea, .stTextInput,
[data-testid="stTextArea"], [data-testid="stTextInput"] { color-scheme: inherit; }
.stTextArea > div, .stTextInput > div,
[data-testid="stTextArea"] > div, [data-testid="stTextInput"] > div,
[data-testid="stTextAreaRootElement"] { background-color: transparent !important; }
[data-baseweb="textarea"], [data-baseweb="input"] {
  background-color: var(--input-bg) !important; border: 1px solid var(--input-border) !important; border-radius: 12px !important;
  box-shadow: none !important; overflow: hidden; }
[data-baseweb="base-input"], [data-baseweb="textarea"] > div, [data-baseweb="input"] > div {
  background-color: var(--input-bg) !important; border: none !important; border-radius: 12px !important; box-shadow: none !important; }
[data-baseweb="textarea"]:focus-within, [data-baseweb="input"]:focus-within {
  border-color: var(--primary) !important; box-shadow: 0 0 0 3px var(--primary-soft) !important; }
.stTextArea textarea, .stTextInput input, [data-baseweb="textarea"] textarea, [data-baseweb="base-input"] textarea, [data-baseweb="base-input"] input {
  background-color: var(--input-bg) !important; color: var(--input-text) !important; -webkit-text-fill-color: var(--input-text) !important;
  caret-color: var(--input-caret) !important; border: none !important; box-shadow: none !important; outline: none !important;
  font-size: .95rem; line-height: 1.65; }
.stTextArea textarea:disabled, .stTextInput input:disabled, [data-baseweb="textarea"] textarea:disabled {
  background-color: var(--input-bg) !important; color: var(--input-text) !important; -webkit-text-fill-color: var(--input-text) !important; opacity: .75; cursor: not-allowed; }
.stTextArea textarea::placeholder, .stTextInput input::placeholder, [data-baseweb="textarea"] textarea::placeholder {
  color: var(--input-placeholder) !important; -webkit-text-fill-color: var(--input-placeholder) !important; opacity: 1 !important; }
.stTextArea textarea::selection, .stTextInput input::selection { background: var(--primary-soft); color: var(--input-text); -webkit-text-fill-color: var(--input-text); }
.stTextArea textarea:-webkit-autofill, .stTextInput input:-webkit-autofill {
  -webkit-box-shadow: 0 0 0 1000px var(--input-bg) inset !important; -webkit-text-fill-color: var(--input-text) !important; }
/* the "Press Ctrl+Enter to apply" hint under inputs */
[data-testid="InputInstructions"], [data-testid="InputInstructions"] * { color: var(--muted) !important; background: transparent !important; }

/* ---- file uploader (dropzone, button, uploaded-file row) ---- */
[data-testid="stFileUploader"] { color-scheme: inherit; }
[data-testid="stFileUploaderDropzone"] {
  background-color: var(--drop-bg) !important; border: 1.5px dashed var(--drop-border) !important; border-radius: 14px !important; padding: 1.5rem 1rem !important; }
[data-testid="stFileUploaderDropzone"] > div, [data-testid="stFileUploaderDropzoneInstructions"], [data-testid="stFileUploaderDropzoneInstructions"] > div {
  background-color: transparent !important; }
[data-testid="stFileUploaderDropzone"] *, [data-testid="stFileUploaderDropzone"] span, [data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzoneInstructions"] * { color: var(--drop-text) !important; -webkit-text-fill-color: var(--drop-text) !important; }
[data-testid="stFileUploaderDropzone"] svg { color: var(--primary) !important; fill: currentColor; }
[data-testid="stFileUploaderDropzone"] button, [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] {
  background-color: var(--surface) !important; border: 1px solid var(--border-strong) !important; border-radius: 9px !important; box-shadow: none !important; }
[data-testid="stFileUploaderDropzone"] button *, [data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] * {
  color: var(--text) !important; -webkit-text-fill-color: var(--text) !important; }
[data-testid="stFileUploaderDropzone"] button:hover { border-color: var(--primary) !important; }
[data-testid="stFileUploaderDropzone"] button:hover * { color: var(--primary) !important; -webkit-text-fill-color: var(--primary) !important; }
[data-testid="stFileUploaderFile"], [data-testid="stFileUploaderFile"] > div { background-color: transparent !important; }
[data-testid="stFileUploaderFile"] *, [data-testid="stFileUploaderFileName"], [data-testid="stFileUploaderFile"] small {
  color: var(--text) !important; -webkit-text-fill-color: var(--text) !important; }
[data-testid="stFileUploaderFile"] svg { color: var(--muted) !important; }
[data-testid="stFileUploaderDeleteBtn"] button { background-color: transparent !important; border: none !important; }

/* uploaded-file chip shown inside the dropzone (newer Streamlit renders it dark by default) */
[data-testid="stFileChip"] { background-color: var(--surface) !important; border: 1px solid var(--border-strong) !important; border-radius: 10px !important; }
[data-testid="stFileChip"] *, [data-testid^="stFileChip"] { color: var(--text) !important; -webkit-text-fill-color: var(--text) !important; }
[data-testid="stFileChip"] [data-testid="stFileChipDeleteBtn"] button, [data-testid="stFileChipDeleteBtn"] button { background-color: transparent !important; border: none !important; }
[data-testid="stFileChip"] svg { color: var(--muted) !important; fill: currentColor; }

/* ---- expander ---- */
[data-testid="stExpander"] { border: 1px solid var(--border) !important; border-radius: 12px !important; background-color: var(--surface-2) !important; }
[data-testid="stExpander"] details, [data-testid="stExpander"] summary { background-color: transparent !important; color: var(--text) !important; }
[data-testid="stExpander"] summary:hover { background-color: var(--surface-2) !important; }
[data-testid="stExpander"] summary p, [data-testid="stExpander"] summary span { color: var(--text) !important; font-weight: 600; }
[data-testid="stExpander"] summary svg { color: var(--muted) !important; }

/* segmented radio groups (main area) */
[data-testid="stMain"] div[role="radiogroup"], section.main div[role="radiogroup"] { gap: .4rem; flex-wrap: wrap; }
[data-testid="stMain"] div[role="radiogroup"] > label, section.main div[role="radiogroup"] > label {
  background: var(--surface); border: 1px solid var(--border-strong); border-radius: 9px; padding: .38rem .95rem; margin: 0; cursor: pointer; transition: border-color .15s, background .15s; }
[data-testid="stMain"] div[role="radiogroup"] > label:hover, section.main div[role="radiogroup"] > label:hover { border-color: var(--primary); }
[data-testid="stMain"] div[role="radiogroup"] > label > div:first-child, section.main div[role="radiogroup"] > label > div:first-child,
[data-testid="stMain"] label[data-baseweb="radio"] > div:first-child { display: none; }
[data-testid="stMain"] div[role="radiogroup"] > label:has(input:checked), section.main div[role="radiogroup"] > label:has(input:checked) { background: var(--primary-soft); border-color: var(--primary); }
[data-testid="stMain"] div[role="radiogroup"] > label:has(input:checked) p, section.main div[role="radiogroup"] > label:has(input:checked) p { color: var(--primary) !important; font-weight: 600; }

/* ---- toggles (visible track in both modes) ---- */
label[data-baseweb="checkbox"] > span:first-child, label[data-baseweb="checkbox"] > div:first-child { background-color: var(--border-strong) !important; }
label[data-baseweb="checkbox"]:has(input:checked) > span:first-child, label[data-baseweb="checkbox"]:has(input:checked) > div:first-child { background-color: var(--primary) !important; }

/* ---- sliders ---- */
[data-testid="stSlider"] [data-testid="stTickBarMin"], [data-testid="stSlider"] [data-testid="stTickBarMax"],
[data-testid="stSlider"] [data-testid="stSliderThumbValue"] { color: var(--muted) !important; }

/* ---- tabs (one paraphrase version per tab) ---- */
[data-baseweb="tab-list"] { gap: .25rem; background-color: transparent !important; }
[data-baseweb="tab-border"] { background-color: var(--border) !important; }
[data-baseweb="tab-highlight"] { background-color: var(--primary) !important; }
[data-baseweb="tab"] { background-color: transparent !important; }
[data-baseweb="tab"] p, [data-baseweb="tab"] span { color: var(--muted) !important; font-weight: 600; }
[data-baseweb="tab"]:hover p { color: var(--text) !important; }
[data-baseweb="tab"][aria-selected="true"] p { color: var(--primary) !important; }
[data-baseweb="tab-panel"] { background-color: transparent !important; padding-top: .75rem; }

/* ---- buttons ---- */
.stButton > button, .stDownloadButton > button { min-height: 2.6rem; border-radius: 10px; font-weight: 600; padding: .45rem 1rem; border: 1px solid var(--border-strong); background: var(--surface); color: var(--text); transition: border-color .15s, color .15s, background .15s; }
.stButton > button:hover, .stDownloadButton > button:hover { border-color: var(--primary); color: var(--primary); }
.stButton > button p, .stDownloadButton > button p { color: inherit; }
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] { background: var(--btn); border: 1px solid var(--btn); color: #fff; }
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover { background: var(--btn-hover); border-color: var(--btn-hover); color: #fff; }
.stButton > button[kind="primary"] p, .stButton > button[data-testid="stBaseButton-primary"] p { color: #fff !important; }
.stButton > button:disabled, .stDownloadButton > button:disabled { opacity: .5; cursor: not-allowed; }
.tm-copy { width: 100%; min-height: 2.6rem; border-radius: 10px; border: 1px solid var(--border-strong); background: var(--surface); color: var(--text); font: 600 .875rem 'Inter', -apple-system, 'Segoe UI', sans-serif; cursor: pointer; transition: border-color .15s, color .15s; }
.tm-copy:hover { border-color: var(--primary); color: var(--primary); }

/* ---- typography blocks ---- */
.tm-page-head { margin: 0 0 1.25rem; }
.tm-eyebrow { font-size: .8rem; font-weight: 600; color: var(--primary); margin-bottom: .35rem; }
.tm-page-title { font-size: clamp(1.6rem, 2.6vw, 2.1rem); font-weight: 750; letter-spacing: -.03em; line-height: 1.15; color: var(--text); margin: 0; }
.tm-page-desc { max-width: 800px; font-size: .96rem; line-height: 1.6; color: var(--muted); margin: .45rem 0 0; }
.tm-hero-title { font-size: clamp(1.7rem, 3vw, 2.4rem); font-weight: 780; letter-spacing: -.035em; line-height: 1.12; color: var(--text); margin: 0 0 .5rem; }
.tm-hero-text { max-width: 640px; color: var(--muted); line-height: 1.65; margin: 0 0 1.1rem; }
.tm-panel-title { font-size: 1rem; font-weight: 650; color: var(--text); letter-spacing: -.01em; margin-bottom: .1rem; }
.tm-panel-sub { font-size: .82rem; color: var(--muted); margin-bottom: .7rem; }
.tm-gap { height: 1rem; }
.tm-right { text-align: right; }

/* ---- UI elements ---- */
.tm-chips { display: flex; flex-wrap: wrap; gap: .4rem; margin: .55rem 0 .8rem; }
.tm-chip { background: var(--surface-2); border: 1px solid var(--border); color: var(--muted); border-radius: 999px; padding: .14rem .7rem; font-size: .78rem; }
.tm-chip b { color: var(--text); font-weight: 600; }
.tm-pill { display: inline-block; border-radius: 999px; padding: .14rem .75rem; font-size: .78rem; font-weight: 600; border: 1px solid transparent; white-space: nowrap; }
.tm-pill-ok { color: var(--ok); background: var(--ok-soft); border-color: var(--ok); }
.tm-pill-warn { color: var(--warn); background: var(--warn-soft); border-color: var(--warn); }
.tm-pill-bad { color: var(--bad); background: var(--bad-soft); border-color: var(--bad); }
.tm-pill-neutral { color: var(--muted); background: var(--surface-2); border-color: var(--border); }
.tm-callout { border-radius: 11px; padding: .75rem 1rem; border: 1px solid var(--border); margin: .4rem 0 .8rem; font-size: .9rem; line-height: 1.5; color: var(--text); background: var(--surface-2); }
.tm-callout-title { font-weight: 600; margin-bottom: .1rem; }
.tm-callout-error { background: var(--bad-soft); border-color: var(--bad); }
.tm-callout-warn { background: var(--warn-soft); border-color: var(--warn); }
.tm-callout-success { background: var(--ok-soft); border-color: var(--ok); }
.tm-callout-info { background: var(--primary-soft); border-color: var(--primary); }
.tm-empty { text-align: center; padding: 3rem 1rem; border: 1.5px dashed var(--border-strong); border-radius: 12px; color: var(--muted); }
.tm-empty svg { color: var(--border-strong); }
.tm-empty-title { color: var(--text); font-weight: 600; margin: .6rem 0 .2rem; }
.tm-ico { width: 38px; height: 38px; border-radius: 10px; background: var(--primary-soft); color: var(--primary); display: flex; align-items: center; justify-content: center; margin-bottom: .75rem; }
.tm-action-title { font-size: 1.02rem; font-weight: 650; color: var(--text); margin-bottom: .25rem; }
.tm-action-desc { font-size: .86rem; color: var(--muted); line-height: 1.5; margin-bottom: .8rem; min-height: 2.6rem; }
.tm-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: .75rem; margin: .2rem 0 .9rem; }
.tm-stat { background: var(--surface-2); border: 1px solid var(--border); border-radius: 11px; padding: .75rem .95rem; }
.tm-stat-label { font-size: .78rem; color: var(--muted); font-weight: 500; }
.tm-stat-value { font-size: 1.4rem; font-weight: 700; letter-spacing: -.02em; color: var(--text); margin-top: .15rem; }
.tm-stat-sub { font-size: .74rem; color: var(--muted); margin-top: .1rem; }
.tm-mix { display: flex; height: 8px; border-radius: 999px; overflow: hidden; background: var(--surface-2); margin: .5rem 0 .4rem; }
.tm-mix-a { background: var(--primary); } .tm-mix-b { background: #38BDF8; }
.tm-legend { font-size: .8rem; color: var(--muted); display: flex; gap: 1rem; flex-wrap: wrap; }
.tm-legend i { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: .35rem; }
.tm-table-wrap { overflow-x: auto; }
.tm-table { width: 100%; border-collapse: collapse; font-size: .87rem; }
.tm-table th { text-align: left; color: var(--muted); font-weight: 600; font-size: .78rem; padding: .55rem .65rem; border-bottom: 1px solid var(--border); background: var(--surface-2); white-space: nowrap; }
.tm-table td { padding: .65rem; border-bottom: 1px solid var(--border); color: var(--text); white-space: nowrap; }
.tm-formats { display: flex; gap: .4rem; flex-wrap: wrap; margin-bottom: .7rem; }
.tm-format { font-size: .74rem; font-weight: 650; padding: .15rem .6rem; border-radius: 6px; background: var(--surface-2); border: 1px solid var(--border-strong); color: var(--text); }
.tm-file { display: flex; align-items: center; gap: .8rem; padding: .75rem .95rem; margin: .7rem 0 .3rem; background: var(--surface-2); border: 1px solid var(--border); border-radius: 12px; }
.tm-file .tm-ico { margin: 0; flex: 0 0 auto; }
.tm-file-name { font-weight: 600; color: var(--text); overflow-wrap: anywhere; font-size: .92rem; }
.tm-file-meta { font-size: .8rem; color: var(--muted); margin-top: .1rem; }
.tm-version-head { display: flex; align-items: center; justify-content: space-between; gap: .6rem; flex-wrap: wrap; margin-bottom: .55rem; }
.tm-version-title { font-weight: 650; color: var(--text); }
.tm-version-meta { display: flex; gap: .4rem; flex-wrap: wrap; }
.tm-version-body { max-height: 420px; overflow-y: auto; white-space: pre-wrap; overflow-wrap: anywhere; color: var(--text); line-height: 1.7; font-size: .94rem; background: var(--input-bg); border: 1px solid var(--border); border-radius: 11px; padding: .85rem 1rem; margin-bottom: .75rem; }
.tm-svc-head { display: flex; align-items: flex-start; justify-content: space-between; gap: .8rem; margin-bottom: .7rem; }
.tm-svc-title { font-size: 1.02rem; font-weight: 650; color: var(--text); }
.tm-svc-desc { font-size: .84rem; color: var(--muted); margin-top: .15rem; line-height: 1.45; }
.tm-kv { margin: .3rem 0 .8rem; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.tm-kv-row { display: flex; justify-content: space-between; gap: 1rem; padding: .5rem .8rem; font-size: .85rem; border-bottom: 1px solid var(--border); }
.tm-kv-row:last-child { border-bottom: none; }
.tm-kv-key { color: var(--muted); } .tm-kv-val { color: var(--text); text-align: right; overflow-wrap: anywhere; }
.tm-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin: .4rem 0 1rem; }
.tm-info { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1.1rem 1.2rem; box-shadow: var(--shadow); }
.stApp .tm-info h4 { margin: 0 0 .35rem; font-size: 1rem; color: var(--text); }
.stApp .tm-info p, .stApp .tm-info li { color: var(--muted); font-size: .88rem; line-height: 1.55; }
.stApp .tm-info ul { padding-left: 1.05rem; margin: .4rem 0 0; }
.tm-step-n { width: 26px; height: 26px; border-radius: 50%; background: var(--primary); color: #fff; font-size: .8rem; font-weight: 700; display: flex; align-items: center; justify-content: center; margin-bottom: .6rem; }
.tm-footer { text-align: center; color: var(--muted); font-size: .8rem; padding: 1.4rem 0 .4rem; border-top: 1px solid var(--border); margin-top: 2rem; }

@media (max-width: 900px) {
  .block-container { padding-left: 1.1rem; padding-right: 1.1rem; }
  /* stack the input / result panels earlier than Streamlit's own breakpoint so neither gets cramped */
  [data-testid="stHorizontalBlock"]:has([class*="st-key-card_input_"]) { flex-wrap: wrap; }
  [data-testid="stHorizontalBlock"]:has([class*="st-key-card_input_"]) > div { min-width: 100% !important; flex: 1 1 100% !important; }
}
@media (max-width: 640px) {
  .block-container { padding-left: .85rem; padding-right: .85rem; padding-top: 1.1rem; }
  .st-key-card_hero { padding: 1.2rem; }
  .tm-svc-head { flex-direction: column; }
  .tm-action-desc { min-height: 0; }
}
"""


def build_css(dark: bool) -> str:
    tokens = _DARK if dark else _LIGHT
    scheme = "dark" if dark else "light"
    # color-scheme makes native widgets (scrollbars, text selection, form controls) follow OUR theme,
    # not the browser/OS theme, so a dark OS can't turn the light-mode inputs black.
    root = (":root,.stApp,[data-testid='stAppViewContainer'],[data-testid='stSidebar']{"
            + f"color-scheme:{scheme};" + "".join(f"--{k}:{v};" for k, v in tokens.items()) + "}")
    return ("<style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');"
            + root + _CSS + "</style>")


_ICON_PATHS = {
    "summarize": "<path d='M4 6h16M4 12h10M4 18h6'/>",
    "paraphrase": "<path d='M17 3l4 4-4 4'/><path d='M3 11V9a2 2 0 0 1 2-2h16'/><path d='M7 21l-4-4 4-4'/><path d='M21 13v2a2 2 0 0 1-2 2H3'/>",
    "document": "<path d='M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z'/><path d='M14 3v5h5M9 13h6M9 17h4'/>",
    "shield": "<path d='M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z'/><path d='M9 12l2 2 4-4'/>",
    "cloud": "<path d='M7 18a4 4 0 0 1-.5-7.97A6 6 0 0 1 18 9a4.5 4.5 0 0 1-.5 9z'/>",
    "bolt": "<path d='M13 2L4 14h7l-1 8 9-12h-7z'/>",
}


def icon(name: str, size: int = 20) -> str:
    return (f"<svg width='{size}' height='{size}' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' "
            f"stroke-linecap='round' stroke-linejoin='round'>{_ICON_PATHS.get(name, _ICON_PATHS['document'])}</svg>")


def logo_mark(size: int = 34) -> str:
    return (f"<svg width='{size}' height='{size}' viewBox='0 0 40 40' fill='none' xmlns='http://www.w3.org/2000/svg' aria-label='TextMorph'>"
            "<rect width='40' height='40' rx='11' fill='#4F46E5'/><path d='M11 13h18M20 13v15' stroke='#fff' stroke-width='3' stroke-linecap='round'/>"
            "<circle cx='29' cy='28' r='2.8' fill='#BAE6FD'/></svg>")


def page_header(title: str, description: str, eyebrow: str = ""):
    eb = f"<div class='tm-eyebrow'>{eyebrow}</div>" if eyebrow else ""
    st.markdown(f"<div class='tm-page-head'>{eb}<h1 class='tm-page-title'>{title}</h1>"
                f"<p class='tm-page-desc'>{description}</p></div>", unsafe_allow_html=True)


def gap():
    st.markdown("<div class='tm-gap'></div>", unsafe_allow_html=True)


def panel_title(title: str, sub: str = ""):
    s = f"<div class='tm-panel-sub'>{sub}</div>" if sub else ""
    st.markdown(f"<div class='tm-panel-title'>{title}</div>{s}", unsafe_allow_html=True)


def empty_state(title: str, message: str) -> str:
    return (f"<div class='tm-empty'>{icon('document', 38)}<div class='tm-empty-title'>{title}</div><div>{message}</div></div>")


def stat_grid(items) -> str:
    cells = ""
    for label, value, sub in items:
        s = f"<div class='tm-stat-sub'>{helpers.esc(sub)}</div>" if sub else ""
        cells += (f"<div class='tm-stat'><div class='tm-stat-label'>{helpers.esc(label)}</div>"
                  f"<div class='tm-stat-value'>{helpers.esc(value)}</div>{s}</div>")
    return f"<div class='tm-stats'>{cells}</div>"


def dot_row(name: str, label: str, tone: str) -> str:
    tone = tone if tone in ("ok", "warn", "bad", "neutral") else "neutral"
    return (f"<div class='tm-dotrow'><span class='tm-dot tm-dot-{tone}'></span><span class='tm-dot-name'>{helpers.esc(name)}</span>"
            f"<span class='tm-dot-label'>{helpers.esc(label)}</span></div>")


def format_size(num_bytes) -> str:
    size = float(num_bytes or 0)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{int(size)} B" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{num_bytes} B"


def file_card(uploaded) -> str:
    name = getattr(uploaded, "name", "document")
    ext = name.rsplit(".", 1)[-1].upper() if "." in name else "FILE"
    return (f"<div class='tm-file'><div class='tm-ico'>{icon('document')}</div><div>"
            f"<div class='tm-file-name'>{helpers.esc(name)}</div>"
            f"<div class='tm-file-meta'>{helpers.esc(ext)} &middot; {helpers.esc(format_size(getattr(uploaded, 'size', 0)))}</div></div></div>")


_VERSION_SPLIT = re.compile(r"(?im)^[ \t]*(?:\*\*)?version[ \t]*\d+(?:\*\*)?[ \t]*[:.\-][ \t]*(?:\*\*)?")


def split_versions(text: str):
    """Split 'Version 1: ... Version 2: ...' output into separate texts (empty list if not labelled)."""
    parts = _VERSION_SPLIT.split(text or "")
    versions = [p.strip() for p in parts[1:] if p.strip()]
    return versions if len(versions) >= 2 else []


def display_text(text: str) -> str:
    """Display-only: if the backend text holds literal backslash-n pairs and no real line breaks, show real ones."""
    if "\\n" in text and "\n" not in text:
        return text.replace("\\n", "\n")
    return text


def render_copy_button(text: str, uid: str, label: str = "Copy output"):
    """Copy-to-clipboard button (st.html with JavaScript, as before). Every button needs a unique id."""
    uid = re.sub(r"[^A-Za-z0-9_-]", "", uid) or "tmcopy"
    markup = (
        f'<button type="button" class="tm-copy" id="{uid}">{html.escape(label)}</button><script>(function(){{'
        f'var b=document.getElementById("{uid}");if(!b||b.getAttribute("data-bound")){{return;}}b.setAttribute("data-bound","1");'
        f'var T={json.dumps(text).replace("</", "<" + chr(92) + "/")},L={json.dumps(label)};'
        'function done(ok){b.textContent=ok?"Copied":"Copy failed - select the text manually";setTimeout(function(){b.textContent=L;},1800);}'
        'function fb(){try{var a=document.createElement("textarea");a.value=T;a.style.position="fixed";a.style.opacity="0";'
        'document.body.appendChild(a);a.select();var ok=document.execCommand("copy");document.body.removeChild(a);done(ok);}catch(e){done(false);}}'
        'b.addEventListener("click",function(){if(navigator.clipboard&&window.isSecureContext){'
        'navigator.clipboard.writeText(T).then(function(){done(true);},fb);}else{fb();}});})();</script>'
    )
    try:
        st.html(markup, unsafe_allow_javascript=True)
    except TypeError:
        st.caption("Copy is not available in this Streamlit version. Use Download instead.")


# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
def init_state():
    defaults = {
        "input_text": "",
        "results": {},          # mode -> latest result dict
        "history": [],          # real, per-session processing log
        "api_verify": None,     # result of the live token check
        "api_last": None,       # result of the last real pipeline request
        "dark_mode": False,
        "nav_page": NAV_PAGES[0],
        "uploader_n": 0,
        "upload_msg": None,
        "w_method": "Extractive",
        "w_length": "Medium",
        "w_doc_task": "Summarize",
        "w_chunking": True,
        "w_chunk_words": 600,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# Widget keys that should survive navigation between pages.
_KEEP = ("w_method", "w_length", "w_doc_task", "w_chunking", "w_chunk_words", "dark_mode")


def keep_alive():
    for key in _KEEP:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]


init_state()
keep_alive()
st.markdown(build_css(bool(st.session_state.dark_mode)), unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Callbacks (run before the script reruns, so they may set widget state)
# --------------------------------------------------------------------------
def set_input_everywhere(text: str):
    st.session_state.input_text = text
    for m in EDITOR_MODES:
        st.session_state[f"editor_{m}"] = text


def goto(page: str):
    st.session_state.nav_page = page


def clear_input():
    set_input_everywhere("")
    st.session_state.uploader_n += 1
    st.session_state.upload_msg = None


def clear_output(mode: str):
    st.session_state.results.pop(mode, None)


def on_upload(ukey: str):
    uploaded = st.session_state.get(ukey)
    if uploaded is None:
        return
    try:
        text, meta = helpers.extract_text_from_upload(uploaded.name, uploaded.getvalue())
    except helpers.ExtractionError as exc:
        st.session_state.upload_msg = ("error", str(exc))
        return
    except Exception as exc:  # defensive: never crash the app on a bad file
        st.session_state.upload_msg = ("error", f"Unexpected error while reading the file: {exc}")
        return
    set_input_everywhere(text)
    pages = f", {meta['pages']} pages" if "pages" in meta else ""
    st.session_state.upload_msg = (
        "success",
        f"Extracted {meta['words']:,} words from {uploaded.name} ({meta['format']}{pages}). Review the text below before processing.",
    )


def direct_hf_check(key: str) -> str:
    """Independent, real request to Hugging Face (whoami). Returns a one-line outcome for the status page."""
    req = urllib.request.Request(
        "https://huggingface.co/api/whoami-v2",
        headers={"Authorization": f"Bearer {key}", "User-Agent": "TextMorph"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        who = data.get("name") if isinstance(data, dict) else None
        return f"accepted by Hugging Face (HTTP 200{', account: ' + str(who) if who else ''})"
    except urllib.error.HTTPError as exc:
        return f"rejected by Hugging Face (HTTP {exc.code})"
    except urllib.error.URLError as exc:
        return f"could not reach huggingface.co ({exc.reason})"
    except Exception as exc:  # never let a diagnostic crash the page
        return f"check failed ({type(exc).__name__})"


def do_verify():
    result = api_status.verify_hf_token(HF_API_KEY)  # unchanged verification
    note = direct_hf_check(HF_API_KEY)               # second opinion: same token, direct request
    if isinstance(result, dict):
        result = dict(result)
        result["detail"] = f"{result.get('detail', '')} Direct check: {note}.".strip()
    st.session_state.api_verify = result


def record_api_result(state: str, detail: str):
    st.session_state.api_last = {"state": state, "detail": detail, "ts": time.time()}


# --------------------------------------------------------------------------
# API key + pipeline (same sources as the original; secrets are a fallback)
# --------------------------------------------------------------------------
def get_api_key():
    """The single Hugging Face token chosen by resolve_hf_key() at startup (src/.env first)."""
    return HF_KEY_INFO["key"] or None


HF_API_KEY = get_api_key()

if not HF_API_KEY:
    st.markdown(f"<div class='tm-brand'>{logo_mark(40)}<div><div class='tm-brand-name'>TextMorph</div>"
                f"<div class='tm-brand-sub'>{theme.SUBTITLE}</div></div></div>", unsafe_allow_html=True)
    st.markdown(
        helpers.callout_html(
            "warn",
            "Hugging Face API key required",
            "Add HF_API_KEY=your_token to the file src/.env (or to Streamlit secrets) and restart the app. "
            "Create a token at https://huggingface.co/settings/tokens. "
            + " ".join(HF_KEY_INFO["notes"]),
        ),
        unsafe_allow_html=True,
    )
    st.stop()


@st.cache_resource
def load_pipeline(api_key: str):
    return SummarizationPipeline(api_key)


try:
    pipeline = load_pipeline(HF_API_KEY)
except Exception as exc:
    st.markdown(helpers.callout_html("error", "Failed to initialize the AI pipeline", str(exc)), unsafe_allow_html=True)
    st.stop()


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
def nav_label(page: str) -> str:
    return f":material/{NAV_ICONS[page]}: {page}" if HAS_MATERIAL else page


def current_api_state() -> str:
    candidates = []
    if st.session_state.api_last:
        candidates.append(st.session_state.api_last)
    if st.session_state.api_verify:
        candidates.append(st.session_state.api_verify)
    if candidates:
        return max(candidates, key=lambda c: c["ts"])["state"]  # most recent real evidence wins
    return "configured" if HF_API_KEY else "not_configured"


def groq_status():
    """(label, tone, detail) for the Groq key, from real evidence only."""
    if not os.getenv("GROQ_API_KEY"):
        return "Not configured", "neutral", "GROQ_API_KEY was not found."
    used = [h for h in st.session_state.history if h["task"] == "paraphrase" or "Abstractive" in h["detail"]]
    if used:
        return "Last request succeeded", "ok", f"Latest successful Groq-backed request at {used[-1]['time']}."
    return "Configured, not verified", "warn", "A key is present. Run an abstractive summary or a paraphrase to confirm it works."


def render_sidebar_status(slot):
    label, tone = api_status.state_info(current_api_state())
    g_label, g_tone, _ = groq_status()
    slot.markdown(dot_row("Service", label, tone) + dot_row("Groq key", g_label, g_tone), unsafe_allow_html=True)


with st.sidebar:
    st.markdown(f"<div class='tm-brand'>{logo_mark(36)}<div><div class='tm-brand-name'>TextMorph</div>"
                "<div class='tm-brand-sub'>Summarize and paraphrase with AI</div></div></div>", unsafe_allow_html=True)
    st.markdown("<div class='tm-nav-label'>Workspace</div>", unsafe_allow_html=True)
    st.radio("Navigation", NAV_PAGES, key="nav_page", format_func=nav_label, label_visibility="collapsed")
    st.markdown("<div class='tm-nav-label'>Service status</div>", unsafe_allow_html=True)
    status_slot = st.empty()
    st.markdown("<div class='tm-nav-label'>Appearance</div>", unsafe_allow_html=True)
    st.toggle("Dark mode", key="dark_mode")
    st.markdown("<div class='tm-side-foot'><b>AI-Based Advanced Text Summarization and Paraphrasing System</b><br>"
                f"Developed by {' &amp; '.join(theme.DEVELOPERS)}</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Processing
# --------------------------------------------------------------------------
class BackendFailure(Exception):
    pass


def call_backend(task: str, text: str, method: str, length: str) -> str:
    """Call the AI pipeline and reject invalid or empty results."""

    if task == "summarize":
        out = pipeline.summarize(
            text,
            method=method.lower(),
            length=length.lower()
        )
    else:
        out = pipeline.paraphrase(text)

    # Reject empty or invalid backend responses.
    if not isinstance(out, str) or not out.strip():
        raise BackendFailure(
            "The AI backend returned an empty response."
        )

    # Reject API errors returned as text.
    if helpers.is_backend_error(out):
        raise BackendFailure(
            helpers.clean_backend_message(out)
        )

    return out.strip()

def execute(mode, task, text, method, length, chunking, chunk_words):
    """Run a task and, for chunked paraphrasing, assemble 3 full-document versions."""
    rid = int(time.time() * 1000)
    orig_words = helpers.count_words(text)
    start = time.perf_counter()
    note, sections, bar = "", 1, None

    try:
        chunks = helpers.chunk_text(text, chunk_words) if chunking else [text]
        sections = len(chunks)

        if sections > 1:
            bar = st.progress(0.0, text="Preparing sections...")

        if sections == 1:
            output = call_backend(task, chunks[0], method, length)

        elif task == "summarize":
            partials = []
            for i, chunk in enumerate(chunks, 1):
                if bar:
                    bar.progress(
                        (i - 1) / (sections + 1),
                        text=f"Summarizing section {i} of {sections}...",
                    )
                try:
                    partials.append(call_backend("summarize", chunk, method, length))
                except BackendFailure as exc:
                    raise BackendFailure(f"Section {i} of {sections}: {exc}") from exc

            joined = " ".join(partials)
            if bar:
                bar.progress(
                    sections / (sections + 1),
                    text="Combining section summaries...",
                )
            try:
                output = call_backend("summarize", joined, method, length)
                note = (
                    f"Long text processed in {sections} sections, "
                    "then combined into one summary."
                )
            except BackendFailure:
                output = joined
                note = (
                    f"Processed in {sections} sections. The final combining step "
                    "failed, so the section summaries are shown joined together."
                )

        else:
            # Generate 3 versions per section, then join section 1 of each version
            # with section 2 of that same version, etc. This yields exactly 3
            # document-level versions instead of 3 outputs per section.
            version_parts = [[], [], []]

            for i, chunk in enumerate(chunks, 1):
                if bar:
                    bar.progress(
                        (i - 1) / sections,
                        text=f"Paraphrasing section {i} of {sections}...",
                    )

                versions = pipeline.paraphrase_versions(
                    chunk,
                    num_return_sequences=3,
                )

                if not isinstance(versions, list):
                    raise BackendFailure(
                        f"Section {i} of {sections}: paraphraser returned an invalid response."
                    )

                # Surface a backend/API error rather than hiding it behind a
                # generic 'not exactly 3 versions' message.
                error_prefixes = (
                    "API Error",
                    "Groq connection error",
                    "Groq returned",
                    "Could not read",
                    "Could not identify",
                    "Paraphraser unavailable",
                    "Error in paraphrasing",
                )
                if len(versions) == 1 and isinstance(versions[0], str) and versions[0].startswith(error_prefixes):
                    raise BackendFailure(
                        f"Section {i} of {sections}: {helpers.clean_backend_message(versions[0])}"
                    )

                if len(versions) != 3:
                    raise BackendFailure(
                        f"Section {i} of {sections}: expected 3 paraphrases, "
                        f"but received {len(versions)}."
                    )

                for version_index, variation in enumerate(versions):
                    if not isinstance(variation, str) or not variation.strip():
                        raise BackendFailure(
                            f"Section {i} of {sections}: Version {version_index + 1} was empty."
                        )
                    if helpers.is_backend_error(variation):
                        raise BackendFailure(
                            f"Section {i} of {sections}: "
                            f"{helpers.clean_backend_message(variation)}"
                        )
                    version_parts[version_index].append(variation.strip())

            output = "\\n\\n".join(
                f"Version {version_index + 1}:\\n" + " ".join(parts)
                for version_index, parts in enumerate(version_parts)
            )
            note = (
                f"Long text processed in {sections} sections. "
                "The matching section outputs were combined into exactly "
                "3 complete document-level paraphrase versions."
            )

    except BackendFailure as exc:
        msg = str(exc)
        state = api_status.classify_pipeline_error(msg)
        record_api_result(state, msg)
        return {
            "ok": False,
            "id": rid,
            "task": task,
            "error": msg,
            "state": state,
        }
    except Exception as exc:
        msg = f"{type(exc).__name__}: {exc}"
        state = api_status.classify_pipeline_error(msg)
        record_api_result(state, msg)
        return {
            "ok": False,
            "id": rid,
            "task": task,
            "error": msg,
            "state": state,
        }
    finally:
        if bar:
            bar.empty()

    elapsed = time.perf_counter() - start
    out_words = helpers.count_words(output)
    record_api_result("success", f"{task} completed in {elapsed:.1f}s")

    if task == "summarize":
        change = f"{helpers.compression_percent(orig_words, out_words)}% compression"
    else:
        change = f"{(out_words / orig_words - 1) * 100:+.1f}% length" if orig_words else "n/a"

    detail = f"{method} / {length}" if task == "summarize" else "Paraphrase"
    st.session_state.history.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "feature": MODE_LABEL[mode],
        "task": task,
        "detail": detail,
        "orig": orig_words,
        "out": out_words,
        "change": change,
        "compression": helpers.compression_percent(orig_words, out_words),
        "seconds": round(elapsed, 1),
    })
    st.session_state.history = st.session_state.history[-200:]

    return {
        "ok": True,
        "id": rid,
        "task": task,
        "output": output,
        "orig_words": orig_words,
        "elapsed": elapsed,
        "sections": sections,
        "note": note,
    }


# --------------------------------------------------------------------------
# Workspace pages (summarization / paraphrasing / documents)
# --------------------------------------------------------------------------
MODES = {
    "summarize": {
        "title": "Text Summarization",
        "desc": "Condense articles, papers and notes. Choose extractive (selects key sentences) or abstractive (writes a new summary) and a target length.",
        "button": "Generate summary", "task": "summarize", "eyebrow": "Summarize",
    },
    "paraphrase": {
        "title": "Text Paraphrasing",
        "desc": "Rewrite text in different words while keeping the original meaning. Results appear as separate versions when the backend returns several.",
        "button": "Paraphrase text", "task": "paraphrase", "eyebrow": "Rewrite",
    },
    "document": {
        "title": "Document Processing",
        "desc": "Upload a PDF, DOCX or TXT file, review the extracted text, then summarize or paraphrase it. Long documents can be processed in sections.",
        "button": "Process document", "task": "summarize", "eyebrow": "Documents",
    },
}


def render_result(mode: str, res: dict):
    """Successful result: summary / single text block, or separate paraphrase version cards."""
    orig = res["orig_words"]
    output = display_text(res["output"])
    if res["note"]:
        st.markdown(helpers.callout_html("info", res["note"]), unsafe_allow_html=True)

    versions = split_versions(output) if res["task"] == "paraphrase" else []
    if versions:
        counts = [helpers.count_words(v) for v in versions]
        st.markdown(stat_grid([
            ("Original words", f"{orig:,}", ""), ("Versions", f"{len(versions)}", ""),
            ("Avg. words per version", f"{sum(counts) / len(counts):,.0f}", ""),
            ("Processing time", f"{res['elapsed']:.1f} s", ""),
        ]), unsafe_allow_html=True)
        # One tab per version keeps the result panel about as tall as the input panel, however many
        # long versions come back (stacked cards left a large empty area beside the input).
        tabs = st.tabs([f"Version {n}" for n in range(1, len(versions) + 1)])
        for i, (tab, version, words) in enumerate(zip(tabs, versions, counts), 1):
            change = f"{(words / orig - 1) * 100:+.1f}% length" if orig else ""
            with tab:
                with card(f"ver_{mode}_{i}"):
                    st.markdown(
                        f"<div class='tm-version-head'><span class='tm-version-title'>Version {i}</span>"
                        f"<span class='tm-version-meta'><span class='tm-chip'><b>{words:,}</b> words</span>"
                        f"<span class='tm-chip'><b>{helpers.esc(change)}</b></span></span></div>"
                        f"<div class='tm-version-body'>{helpers.esc(version)}</div>", unsafe_allow_html=True)
                    v1, v2 = st.columns(2)
                    with v1:
                        render_copy_button(version, f"tmcopy_{mode}_{res['id']}_{i}", f"Copy version {i}")
                    with v2:
                        st.download_button(f"Download version {i}", data=version, file_name=f"textmorph_paraphrase_v{i}.txt",
                                           mime="text/plain", key=f"dlv_{mode}_{i}", **STRETCH)
        d1, d2 = st.columns(2)
        with d1:
            st.download_button("Download all versions", data=output, file_name=f"textmorph_{res['task']}.txt",
                               mime="text/plain", key=f"dl_{mode}", **STRETCH)
        with d2:
            st.button("Clear output", key=f"clearout_{mode}", on_click=clear_output, args=(mode,), **STRETCH)
        return

    final_text = st.text_area("Generated output", value=output, height=300,
                              key=f"out_{res['id']}", label_visibility="collapsed")
    out_stats = helpers.text_stats(final_text)
    if res["task"] == "summarize":
        third = ("Compression", f"{helpers.compression_percent(orig, out_stats['words'])}%", "shorter than the original")
    else:
        change = (out_stats["words"] / orig - 1) * 100 if orig else 0
        third = ("Length change", f"{change:+.1f}%", "vs. the original")
    st.markdown(stat_grid([
        ("Original words", f"{orig:,}", ""), ("Output words", f"{out_stats['words']:,}", ""), third,
        ("Characters", f"{out_stats['chars']:,}", ""), ("Sentences", f"{out_stats['sentences']:,}", ""),
        ("Processing time", f"{res['elapsed']:.1f} s", ""),
    ]), unsafe_allow_html=True)
    a1, a2, a3 = st.columns(3)
    with a1:
        render_copy_button(final_text, f"tmcopy_{mode}_{res['id']}", "Copy output")
    with a2:
        st.download_button("Download .txt", data=final_text, file_name=f"textmorph_{res['task']}.txt",
                           mime="text/plain", key=f"dl_{mode}", **STRETCH)
    with a3:
        st.button("Clear output", key=f"clearout_{mode}", on_click=clear_output, args=(mode,), **STRETCH)


def render_workspace(mode: str):
    cfg = MODES[mode]
    task = cfg["task"]
    chunking, chunk_words = False, 600
    page_header(cfg["title"], cfg["desc"], cfg["eyebrow"])

    # ---- document upload (document page) ----
    if mode == "document":
        with card("doc_upload"):
            panel_title("Upload a document", "Drag and drop a file, or browse. Scanned PDFs are not supported (no OCR).")
            st.markdown("<div class='tm-formats'><span class='tm-format'>PDF</span><span class='tm-format'>DOCX</span>"
                        "<span class='tm-format'>TXT</span></div>", unsafe_allow_html=True)
            ukey = f"upload_{mode}_{st.session_state.uploader_n}"
            uploaded = st.file_uploader("Document", type=["pdf", "docx", "txt"], key=ukey,
                                        on_change=on_upload, args=(ukey,), label_visibility="collapsed")
            msg = st.session_state.upload_msg
            if uploaded is not None and msg and msg[0] == "success":
                st.markdown(file_card(uploaded), unsafe_allow_html=True)
            if msg:
                st.markdown(helpers.callout_html(msg[0], msg[1]), unsafe_allow_html=True)
        gap()

    # ---- settings ----
    if mode in ("summarize", "document"):
        with card(f"settings_{mode}"):
            panel_title("Settings" if mode == "summarize" else "Choose what to do")
            if mode == "document":
                st.radio("Action", ["Summarize", "Paraphrase"], key="w_doc_task", horizontal=True)
                task = "summarize" if st.session_state.w_doc_task == "Summarize" else "paraphrase"
            if task == "summarize":
                c1, c2 = st.columns([1, 1.2])
                with c1:
                    st.radio(
                        "Method", ["Extractive", "Abstractive"], key="w_method", horizontal=True,
                        help="Extractive selects key sentences from the original. Abstractive generates new sentences with AI.",
                    )
                with c2:
                    st.radio("Summary length", ["Short", "Medium", "Long"], key="w_length", horizontal=True)
            if mode == "document":
                c3, c4 = st.columns(2)
                with c3:
                    st.toggle("Process long text in sections", key="w_chunking",
                              help="Splits the text into sections, processes each one, and (for summaries) combines the results.")
                with c4:
                    st.slider("Words per section", 200, 1500, step=50, key="w_chunk_words",
                              disabled=not st.session_state.w_chunking)
                chunking = bool(st.session_state.w_chunking)
                chunk_words = int(st.session_state.w_chunk_words)
        gap()
    method, length = st.session_state.w_method, st.session_state.w_length

    left, right = st.columns(2, gap="large")

    # ---- input panel ----
    with left:
        with card(f"input_{mode}"):
            panel_title("Extracted text" if mode == "document" else "Input text",
                        "Review and edit before processing." if mode == "document" else "Paste or type your text.")
            if mode != "document":
                ukey = f"upload_{mode}_{st.session_state.uploader_n}"
                with st.expander("Upload a document (PDF, DOCX, TXT)"):
                    st.file_uploader("Document", type=["pdf", "docx", "txt"], key=ukey,
                                     on_change=on_upload, args=(ukey,), label_visibility="collapsed")
                    msg = st.session_state.upload_msg
                    if msg:
                        st.markdown(helpers.callout_html(msg[0], msg[1]), unsafe_allow_html=True)
            ekey = f"editor_{mode}"
            if ekey not in st.session_state:
                st.session_state[ekey] = st.session_state.input_text
            text = st.text_area(
                "Input text", key=ekey, height=420 if mode == "document" else 320, label_visibility="collapsed",
                placeholder="Paste or type your text here, or upload a document...",
            )
            st.session_state.input_text = text
            st.markdown(helpers.chips_html(helpers.text_stats(text)), unsafe_allow_html=True)
            b1, b2 = st.columns([2, 1])
            label = cfg["button"]
            if mode == "document":
                label = "Summarize document" if task == "summarize" else "Paraphrase document"
            with b1:
                run = st.button(label, type="primary", key=f"run_{mode}", disabled=not text.strip(), **STRETCH)
            with b2:
                st.button("Clear", key=f"clear_{mode}", on_click=clear_input, **STRETCH)

    # ---- output panel ----
    with right:
        with card(f"output_{mode}"):
            t_col, s_col = st.columns([3, 2])
            with t_col:
                panel_title("Result")
            status_pill = s_col.empty()

            if run:
                with st.spinner("Processing with AI..."):
                    st.session_state.results[mode] = execute(mode, task, text, method, length, chunking, chunk_words)
            res = st.session_state.results.get(mode)

            if res is None:
                status_pill.markdown("<div class='tm-right'>" + helpers.pill_html("Ready", "neutral") + "</div>", unsafe_allow_html=True)
                st.markdown(empty_state("No result yet", "Add text on the left and run the action. Your result appears here."),
                            unsafe_allow_html=True)
            elif not res["ok"]:
                status_pill.markdown("<div class='tm-right'>" + helpers.pill_html("Failed", "bad") + "</div>", unsafe_allow_html=True)
                st.markdown(helpers.callout_html("error", "The request did not complete", res["error"][:500]), unsafe_allow_html=True)
                label_s, _ = api_status.state_info(res["state"])
                st.markdown(helpers.callout_html("warn", label_s, api_status.GUIDANCE[res["state"]]), unsafe_allow_html=True)
            else:
                status_pill.markdown("<div class='tm-right'>" + helpers.pill_html("Completed", "ok") + "</div>", unsafe_allow_html=True)
                render_result(mode, res)


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
def render_dashboard():
    hist = st.session_state.history
    sums = [h for h in hist if h["task"] == "summarize"]
    paras = [h for h in hist if h["task"] == "paraphrase"]

    with card("hero"):
        st.markdown("<div class='tm-eyebrow'>TextMorph workspace</div>"
                    "<h1 class='tm-hero-title'>Turn long text into clear ideas</h1>"
                    "<p class='tm-hero-text'>Summarize content, rewrite it with confidence, and process whole documents "
                    "in one focused workspace.</p>", unsafe_allow_html=True)
        h1, h2, _ = st.columns([1, 1, 2])
        with h1:
            st.button("Start summarizing", type="primary", key="dash_hero_sum", on_click=goto, args=("Text Summarization",), **STRETCH)
        with h2:
            st.button("Process a document", key="dash_hero_doc", on_click=goto, args=("Document Processing",), **STRETCH)
    gap()

    panel_title("Tools")
    items = [
        ("summarize", "Text summarization", "Extract the key ideas from articles, notes and reports.", "Text Summarization"),
        ("paraphrase", "Text paraphrasing", "Rewrite text in new words and compare several versions.", "Text Paraphrasing"),
        ("document", "Document processing", "Upload PDF, DOCX or TXT files and process their content.", "Document Processing"),
    ]
    for col, (ico, title, desc, page_name) in zip(st.columns(3, gap="medium"), items):
        with col:
            with card(f"action_{ico}"):
                st.markdown(f"<div class='tm-ico'>{icon(ico)}</div><div class='tm-action-title'>{title}</div>"
                            f"<div class='tm-action-desc'>{desc}</div>", unsafe_allow_html=True)
                st.button("Open workspace", key=f"dash_go_{page_name}", on_click=goto, args=(page_name,), **STRETCH)
    gap()

    with card("dash_stats"):
        panel_title("Session overview", "Figures are calculated from the requests you run in this session.")
        st.markdown(stat_grid([
            ("Requests", f"{len(hist)}", ""),
            ("Summaries", f"{len(sums)}", ""),
            ("Paraphrases", f"{len(paras)}", ""),
            ("Words processed", f"{sum(h['orig'] for h in hist):,}", ""),
            ("Avg. compression", f"{sum(h['compression'] for h in sums) / len(sums):.1f}%" if sums else "-", "summaries only"),
            ("Avg. processing time", f"{sum(h['seconds'] for h in hist) / len(hist):.1f} s" if hist else "-", ""),
        ]), unsafe_allow_html=True)
        total = len(sums) + len(paras)
        if total:
            a = round(len(sums) * 100 / total)
            st.markdown(f"<div class='tm-mix'><span class='tm-mix-a' style='width:{a}%'></span>"
                        f"<span class='tm-mix-b' style='width:{100 - a}%'></span></div>"
                        f"<div class='tm-legend'><span><i style='background:var(--primary)'></i>Summaries {len(sums)}</span>"
                        f"<span><i style='background:#38BDF8'></i>Paraphrases {len(paras)}</span></div>", unsafe_allow_html=True)
    gap()

    with card("dash_history"):
        panel_title("Recent activity")
        if not hist:
            st.markdown(empty_state("Your activity will appear here", "Run your first summary or paraphrase to start building your session history."),
                        unsafe_allow_html=True)
        else:
            rows = [[h["time"], h["feature"], h["detail"], f"{h['orig']:,}", f"{h['out']:,}", h["change"], f"{h['seconds']}s"]
                    for h in reversed(hist[-8:])]
            st.markdown(helpers.table_html(["Time", "Tool", "Settings", "Input words", "Output words", "Change", "Duration"], rows),
                        unsafe_allow_html=True)
        st.caption("Activity is stored for this browser session only and resets when the session ends.")


# --------------------------------------------------------------------------
# About
# --------------------------------------------------------------------------
def render_about():
    page_header("About TextMorph",
                f"{theme.PROJECT_FULL}. Developed by {' &amp; '.join(theme.DEVELOPERS)} as a B.Tech 5th-semester Cornerstone Project.",
                "Project")
    st.markdown(f"""
<div class='tm-grid'>
  <div class='tm-info'><div class='tm-ico'>{icon('summarize')}</div><h4>Extractive summarization</h4>
    <p>Selects the most important sentences from the original text and keeps their exact wording.</p></div>
  <div class='tm-info'><div class='tm-ico'>{icon('bolt')}</div><h4>Abstractive summarization</h4>
    <p>Uses AI to write new sentences that capture the meaning of the text.</p></div>
  <div class='tm-info'><div class='tm-ico'>{icon('paraphrase')}</div><h4>Paraphrasing</h4>
    <p>Rewrites text in different words while keeping its meaning, and can present several versions.</p></div>
  <div class='tm-info'><div class='tm-ico'>{icon('cloud')}</div><h4>Cloud-based AI</h4>
    <p>Abstractive summarization and paraphrasing run through the Groq API, so no local models need to be downloaded. An internet connection and API keys are required.</p></div>
</div>
<div class='tm-grid'>
  <div class='tm-info'><div class='tm-step-n'>1</div><h4>Add your text</h4><p>Paste text or upload a PDF, DOCX or TXT file.</p></div>
  <div class='tm-info'><div class='tm-step-n'>2</div><h4>Choose an action</h4><p>Pick a summarization method and length, or paraphrase.</p></div>
  <div class='tm-info'><div class='tm-step-n'>3</div><h4>Review and export</h4><p>Check the metrics, then copy or download the result.</p></div>
</div>
<div class='tm-grid'>
  <div class='tm-info'><h4>Where it helps</h4>
    <ul><li>News articles and research papers</li><li>Book chapters, essays and reports</li><li>Business documents and meeting notes</li><li>Emails that need a different tone</li></ul></div>
  <div class='tm-info'><h4>Technology</h4>
    <ul><li>Python and Streamlit</li><li>Groq API (abstractive summarization, paraphrasing)</li><li>Hugging Face API (token verification)</li><li>SummarizationPipeline (extractive, abstractive, paraphrase)</li><li>pypdf and python-docx for document text extraction</li></ul></div>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# API / service status
# --------------------------------------------------------------------------
def render_status():
    page_header("API / Service Status",
                "Statuses come from evidence: whether a key exists, whether the provider accepted it, and whether a real "
                "request worked. Nothing is marked connected just because a key is present.", "Service health")
    verify, last = st.session_state.api_verify, st.session_state.api_last

    def when(item):
        return datetime.fromtimestamp(item["ts"]).strftime("%H:%M:%S") if item else "-"

    left, right = st.columns(2, gap="large")
    with left:
        with card("svc_hf"):
            key_label, key_tone = ("Configured", "ok") if HF_API_KEY else ("Missing", "bad")
            v_label, v_tone = api_status.state_info(verify["state"]) if verify else ("Not checked yet", "neutral")
            l_label, l_tone = api_status.state_info(last["state"]) if last else ("No request yet", "neutral")
            st.markdown("<div class='tm-svc-head'><div><div class='tm-svc-title'>Hugging Face API</div>"
                        "<div class='tm-svc-desc'>Token required at startup. Key name: HF_API_KEY.</div></div></div>",
                        unsafe_allow_html=True)
            rows = [
                ("API key (HF_API_KEY)", helpers.pill_html(key_label, key_tone), "Presence only. Says nothing about validity."),
                ("Key source", helpers.pill_html("src/.env" if HF_KEY_INFO["source"].startswith("src/.env") else "Other source",
                                                 "ok" if HF_KEY_INFO["source"].startswith("src/.env") and not HF_KEY_INFO["notes"] else "warn"),
                 f"Loaded from {HF_KEY_INFO['source']}; {len(HF_API_KEY or '')} characters. " + " ".join(HF_KEY_INFO["notes"])),
                ("Connection verification", helpers.pill_html(v_label, v_tone),
                 f"{verify['detail']} (checked {when(verify)})" if verify else "Click Verify connection."),
                ("Last real request", helpers.pill_html(l_label, l_tone),
                 (last["detail"][:200] + f" ({when(last)})") if last else "Run a summary or paraphrase."),
            ]
            body = "".join(
                f"<tr><td>{helpers.esc(name)}</td><td>{pill}</td><td style='white-space:normal'>{helpers.esc(detail)}</td></tr>"
                for name, pill, detail in rows)
            st.markdown("<div class='tm-table-wrap'><table class='tm-table'><thead><tr><th>Check</th><th>Status</th><th>Details</th></tr></thead>"
                        f"<tbody>{body}</tbody></table></div>", unsafe_allow_html=True)
            gap()
            st.button("Verify connection", key="verify_btn", type="primary", on_click=do_verify)
            st.caption("Verification asks Hugging Face whether the token is accepted. It does not prove the summarization model is "
                       "online; only a successful real request does.")
    with right:
        with card("svc_groq"):
            g_label, g_tone, g_detail = groq_status()
            st.markdown("<div class='tm-svc-head'><div><div class='tm-svc-title'>Groq API</div>"
                        "<div class='tm-svc-desc'>Powers abstractive summarization and paraphrasing. Key name: GROQ_API_KEY.</div></div>"
                        f"{helpers.pill_html(g_label, g_tone)}</div>", unsafe_allow_html=True)
            st.markdown("<div class='tm-kv'>"
                        f"<div class='tm-kv-row'><span class='tm-kv-key'>API key</span><span class='tm-kv-val'>{'Configured' if os.getenv('GROQ_API_KEY') else 'Not configured'}</span></div>"
                        f"<div class='tm-kv-row'><span class='tm-kv-key'>Evidence</span><span class='tm-kv-val'>{helpers.esc(g_detail)}</span></div>"
                        "</div>", unsafe_allow_html=True)
            st.caption("This card shows key presence and the app's own request history. A live Groq check is not available "
                       "without changing the backend modules. Extractive summaries do not contact Groq.")
    gap()

    state = current_api_state()
    label, _ = api_status.state_info(state)
    with card("status_help"):
        panel_title("Current assessment and next step")
        kind = {"ok": "success", "warn": "warn", "bad": "error", "neutral": "info"}[api_status.state_info(state)[1]]
        st.markdown(helpers.callout_html(kind, label, api_status.GUIDANCE[state]), unsafe_allow_html=True)
        st.caption("API keys are never displayed in the interface.")


# --------------------------------------------------------------------------
# Router
# --------------------------------------------------------------------------
page = st.session_state.nav_page
if page == "Dashboard":
    render_dashboard()
elif page == "Text Summarization":
    render_workspace("summarize")
elif page == "Text Paraphrasing":
    render_workspace("paraphrase")
elif page == "Document Processing":
    render_workspace("document")
elif page == "About TextMorph":
    render_about()
else:
    render_status()

st.markdown(f"<div class='tm-footer'>{theme.PROJECT_FULL}<br>Developed by {' &amp; '.join(theme.DEVELOPERS)} &middot; B.Tech Cornerstone Project</div>",
            unsafe_allow_html=True)
render_sidebar_status(status_slot)  # filled last so it reflects requests made during this run