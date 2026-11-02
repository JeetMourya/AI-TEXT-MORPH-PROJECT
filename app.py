"""TextMorph - AI-Based Advanced Text Summarization and Paraphrasing System.

Streamlit front end. The AI backend (src/combinedPipeline.py -> SummarizationPipeline)
is used exactly as before: pipeline.summarize(text, method=..., length=...) and
pipeline.paraphrase(text). Nothing here fakes or hardcodes an AI result.
"""
import inspect
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# Add src folder to Python path (unchanged from the original app)
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Existing backend (unchanged)
from src.combinedPipeline import SummarizationPipeline
from dotenv import load_dotenv

from tm_ui import api_status, helpers, theme

# Load environment variables from src folder (unchanged)
env_path = src_path / ".env"
load_dotenv(dotenv_path=env_path)
try:
    if not os.getenv("HF_API_KEY"):
        hf_key = st.secrets.get("HF_TOKEN") or st.secrets.get("HF_API_KEY")
        if hf_key:
            os.environ["HF_API_KEY"] = hf_key

    if not os.getenv("GROQ_API_KEY"):
        groq_key = st.secrets.get("GROQ_API_KEY")
        if groq_key:
            os.environ["GROQ_API_KEY"] = groq_key

except Exception as e:
    print(f"Cloud secrets loading issue: {e}")

try:
    if not os.getenv("HF_API_KEY"):
        hf_key = st.secrets.get("HF_API_KEY")
        if hf_key:
            os.environ["HF_API_KEY"] = hf_key

    if not os.getenv("GROQ_API_KEY"):
        groq_key = st.secrets.get("GROQ_API_KEY")
        if groq_key:
            os.environ["GROQ_API_KEY"] = groq_key

except Exception as e:
    print(f"Cloud secrets loading issue: {e}")

try:
    if not os.getenv("GROQ_API_KEY"):
        groq_key = st.secrets.get("GROQ_API_KEY")
        if groq_key:
            os.environ["GROQ_API_KEY"] = groq_key
except Exception:
    pass

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
    "Voice Input",
    "About TextMorph",
    "API / Service Status",
]
NAV_ICONS = {
    "Dashboard": "dashboard",
    "Text Summarization": "summarize",
    "Text Paraphrasing": "edit_note",
    "Document Processing": "description",
    "Voice Input": "mic",
    "About TextMorph": "info",
    "API / Service Status": "monitor_heart",
}
VOICE_LANGS = {"English (India)": "en-IN", "English (US)": "en-US", "English (UK)": "en-GB", "Hindi": "hi-IN"}
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
# Session state
# --------------------------------------------------------------------------
def init_state():
    defaults = {
        "input_text": "",
        "results": {},          # mode -> latest result dict
        "history": [],          # real, per-session processing log
        "api_verify": None,     # result of the live token check
        "api_last": None,       # result of the last real pipeline request
        "dark_mode": True,
        "nav_page": NAV_PAGES[0],
        "voice_text": "",
        "voice_last_id": None,
        "uploader_n": 0,
        "upload_msg": None,
        "w_method": "Extractive",
        "w_length": "Medium",
        "w_doc_task": "Summarize",
        "w_chunking": True,
        "w_chunk_words": 600,
        "w_voice_lang": "English (India)",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# Widget keys that should survive navigation between pages.
_KEEP = ("w_method", "w_length", "w_doc_task", "w_chunking", "w_chunk_words", "w_voice_lang", "voice_text", "dark_mode")


def keep_alive():
    for key in _KEEP:
        if key in st.session_state:
            st.session_state[key] = st.session_state[key]


init_state()
keep_alive()
st.markdown(theme.get_css(bool(st.session_state.dark_mode)), unsafe_allow_html=True)


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


def send_voice_to(page: str):
    text = st.session_state.voice_text.strip()
    if text:
        set_input_everywhere(text)
        st.session_state.nav_page = page


def clear_voice():
    st.session_state.voice_text = ""
    st.session_state.voice_last_id = None


def do_verify():
    st.session_state.api_verify = api_status.verify_hf_token(HF_API_KEY)


def record_api_result(state: str, detail: str):
    st.session_state.api_last = {"state": state, "detail": detail, "ts": time.time()}


# --------------------------------------------------------------------------
# API key + pipeline (same sources as the original; secrets are a fallback)
# --------------------------------------------------------------------------
def get_api_key():
    key = os.getenv("HF_API_KEY")  # loaded from src/.env, as before
    if key:
        return key
    try:
        return st.secrets.get("HF_API_KEY")  # optional Streamlit secrets fallback
    except Exception:
        return None


HF_API_KEY = get_api_key()

if not HF_API_KEY:
    st.markdown(theme.header_html(), unsafe_allow_html=True)
    st.markdown(
        helpers.callout_html(
            "warn",
            "Hugging Face API key required",
            "Add HF_API_KEY=your_token to the file src/.env (or to Streamlit secrets) and restart the app. "
            "Create a token at https://huggingface.co/settings/tokens",
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


def render_sidebar_status(slot):
    state = current_api_state()
    label, tone = api_status.state_info(state)
    slot.markdown(
        helpers.pill_html(label, tone) + "<div style='height:.4rem'></div>",
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown(theme.sidebar_brand_html(), unsafe_allow_html=True)
    st.radio("Navigation", NAV_PAGES, key="nav_page", format_func=nav_label, label_visibility="collapsed")
    st.markdown("<div class='tm-side-label'>Service status</div>", unsafe_allow_html=True)
    status_slot = st.empty()
    st.markdown(theme.sidebar_footer_html(), unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
h_left, h_right = st.columns([6, 1.3])
with h_left:
    st.markdown(theme.header_html(), unsafe_allow_html=True)
with h_right:
    st.toggle("Dark mode", key="dark_mode")


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
        "button": "Generate summary", "task": "summarize",
    },
    "paraphrase": {
        "title": "Text Paraphrasing",
        "desc": "Rewrite text in different words while keeping the original meaning.",
        "button": "Paraphrase text", "task": "paraphrase",
    },
    "document": {
        "title": "Document Processing",
        "desc": "Upload a PDF, DOCX or TXT file, review the extracted text, then summarize or paraphrase it. Long documents can be processed in sections.",
        "button": "Process document", "task": "summarize",
    },
}


def render_workspace(mode: str):
    cfg = MODES[mode]
    dark = bool(st.session_state.dark_mode)
    task = cfg["task"]
    chunking, chunk_words = False, 600
    st.markdown(
        f"<div class='tm-page-title'>{cfg['title']}</div><div class='tm-page-desc'>{cfg['desc']}</div>",
        unsafe_allow_html=True,
    )

    # ---- settings ----
    if mode in ("summarize", "document"):
        with card(f"settings_{mode}"):
            if mode == "document":
                st.radio("Action", ["Summarize", "Paraphrase"], key="w_doc_task", horizontal=True)
                task = "summarize" if st.session_state.w_doc_task == "Summarize" else "paraphrase"
            if task == "summarize":
                c1, c2 = st.columns([1, 1.4])
                with c1:
                    st.radio(
                        "Method", ["Extractive", "Abstractive"], key="w_method", horizontal=True,
                        help="Extractive selects key sentences from the original. Abstractive generates new sentences with AI.",
                    )
                with c2:
                    st.select_slider("Summary length", options=["Short", "Medium", "Long"], key="w_length")
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
    method, length = st.session_state.w_method, st.session_state.w_length

    left, right = st.columns(2, gap="large")

    # ---- input panel ----
    with left:
        with card(f"input_{mode}"):
            st.markdown("<div class='tm-section-title'>Input text</div>", unsafe_allow_html=True)
            ukey = f"upload_{mode}_{st.session_state.uploader_n}"
            with st.expander("Upload a document (PDF, DOCX, TXT)", expanded=(mode == "document")):
                st.file_uploader("Document", type=["pdf", "docx", "txt"], key=ukey,
                                 on_change=on_upload, args=(ukey,), label_visibility="collapsed")
                msg = st.session_state.upload_msg
                if msg:
                    st.markdown(helpers.callout_html(msg[0], msg[1]), unsafe_allow_html=True)
            ekey = f"editor_{mode}"
            if ekey not in st.session_state:
                st.session_state[ekey] = st.session_state.input_text
            text = st.text_area(
                "Input text", key=ekey, height=320, label_visibility="collapsed",
                placeholder="Paste or type your text here, upload a document, or use Voice Input...",
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
                st.markdown("<div class='tm-section-title'>Output</div>", unsafe_allow_html=True)
            status_pill = s_col.empty()

            if run:
                with st.spinner("Processing with AI..."):
                    st.session_state.results[mode] = execute(mode, task, text, method, length, chunking, chunk_words)
            res = st.session_state.results.get(mode)

            if res is None:
                status_pill.markdown("<div style='text-align:right'>" + helpers.pill_html("Ready", "neutral") + "</div>", unsafe_allow_html=True)
                st.markdown(theme.empty_state_html("No output yet", "Add text on the left and run the action. Results appear here."),
                            unsafe_allow_html=True)
            elif not res["ok"]:
                status_pill.markdown("<div style='text-align:right'>" + helpers.pill_html("Failed", "bad") + "</div>", unsafe_allow_html=True)
                st.markdown(helpers.callout_html("error", "The request did not complete", res["error"][:500]), unsafe_allow_html=True)
                label_s, _ = api_status.state_info(res["state"])
                st.markdown(helpers.callout_html("warn", label_s, api_status.GUIDANCE[res["state"]]), unsafe_allow_html=True)
            else:
                status_pill.markdown("<div style='text-align:right'>" + helpers.pill_html("Completed", "ok") + "</div>", unsafe_allow_html=True)
                if res["note"]:
                    st.markdown(helpers.callout_html("info", res["note"]), unsafe_allow_html=True)
                final_text = st.text_area("Generated output", value=res["output"], height=320,
                                          key=f"out_{res['id']}", label_visibility="collapsed")
                out_stats = helpers.text_stats(final_text)
                orig = res["orig_words"]
                m1, m2, m3 = st.columns(3)
                m1.metric("Original words", f"{orig:,}")
                m2.metric("Output words", f"{out_stats['words']:,}")
                if res["task"] == "summarize":
                    m3.metric("Compression", f"{helpers.compression_percent(orig, out_stats['words'])}%",
                              help="How much shorter the summary is than the original text.")
                else:
                    change = (out_stats["words"] / orig - 1) * 100 if orig else 0
                    m3.metric("Length change", f"{change:+.1f}%", help="Output length compared with the original text.")
                m4, m5, m6 = st.columns(3)
                m4.metric("Characters", f"{out_stats['chars']:,}")
                m5.metric("Sentences", f"{out_stats['sentences']:,}")
                m6.metric("Processing time", f"{res['elapsed']:.1f} s")
                st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
                a1, a2, a3 = st.columns(3)
                with a1:
                    st.html(helpers.copy_button_html(final_text, dark), unsafe_allow_javascript=True)
                with a2:
                    st.download_button("Download .txt", data=final_text, file_name=f"textmorph_{res['task']}.txt",
                                       mime="text/plain", key=f"dl_{mode}", **STRETCH)
                with a3:
                    st.button("Clear output", key=f"clearout_{mode}", on_click=clear_output, args=(mode,), **STRETCH)


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
def render_dashboard():
    st.markdown("<div class='tm-page-title'>Dashboard</div>"
                "<div class='tm-page-desc'>Choose a tool to get started. All figures below are calculated from the requests you run in this session.</div>",
                unsafe_allow_html=True)
    with card("dash_actions"):
        st.markdown("<div class='tm-section-title'>Quick start</div>", unsafe_allow_html=True)
        cols = st.columns(4)
        for col, page in zip(cols, ["Text Summarization", "Text Paraphrasing", "Document Processing", "Voice Input"]):
            with col:
                st.button(page, key=f"dash_go_{page}", on_click=goto, args=(page,), **STRETCH)

    hist = st.session_state.history
    summaries = [h for h in hist if h["task"] == "summarize"]
    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Requests this session", f"{len(hist)}")
    k2.metric("Words processed", f"{sum(h['orig'] for h in hist):,}")
    k3.metric("Average compression", f"{sum(h['compression'] for h in summaries) / len(summaries):.1f}%" if summaries else "-",
              help="Average over summarization requests only.")
    k4.metric("Average processing time", f"{sum(h['seconds'] for h in hist) / len(hist):.1f} s" if hist else "-")

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    with card("dash_history"):
        st.markdown("<div class='tm-section-title'>Recent activity</div>", unsafe_allow_html=True)
        if not hist:
            st.markdown(theme.empty_state_html("No activity yet", "Run a summary or paraphrase and it will be listed here."),
                        unsafe_allow_html=True)
        else:
            rows = [[h["time"], h["feature"], h["detail"], f"{h['orig']:,}", f"{h['out']:,}", h["change"], f"{h['seconds']} s"]
                    for h in reversed(hist[-8:])]
            st.markdown(helpers.table_html(["Time", "Feature", "Settings", "Original words", "Output words", "Change", "Time taken"], rows),
                        unsafe_allow_html=True)
        st.caption("Session data lives in memory only and resets when the browser tab is refreshed.")


# --------------------------------------------------------------------------
# Voice input
# --------------------------------------------------------------------------
try:
    _VOICE = components.declare_component(
        "textmorph_voice_input", path=str(Path(__file__).parent / "components" / "voice_input"))
except Exception:  # missing folder, etc. - the page explains this instead of crashing
    _VOICE = None


def render_voice():
    st.markdown("<div class='tm-page-title'>Voice Input</div>"
                "<div class='tm-page-desc'>Dictate text with your microphone, correct the transcript, then send it to summarization or paraphrasing.</div>",
                unsafe_allow_html=True)
    if _VOICE is None:
        st.markdown(helpers.callout_html(
            "error", "Voice component not found",
            "Expected the folder components/voice_input/ (with index.html) next to app.py."), unsafe_allow_html=True)
        return

    with card("voice_capture"):
        st.markdown("<div class='tm-section-title'>1. Capture speech</div>", unsafe_allow_html=True)
        st.radio("Recognition language", list(VOICE_LANGS), key="w_voice_lang", horizontal=True)
        # Must run before the transcript text_area below so new speech can be written into its state.
        value = _VOICE(lang=VOICE_LANGS[st.session_state.w_voice_lang], dark=bool(st.session_state.dark_mode),
                       key="tm_voice", default=None)
        if isinstance(value, dict) and value.get("id") and value["id"] != st.session_state.voice_last_id:
            st.session_state.voice_last_id = value["id"]
            st.session_state.voice_text = (st.session_state.voice_text + " " + str(value.get("text", ""))).strip()
        st.markdown(helpers.callout_html(
            "info", "How this works",
            "Speech is recognised by your browser's built-in speech service (works in Google Chrome and Microsoft Edge; "
            "not in Firefox). In Chrome, the audio is sent to Google's speech servers for recognition, so an internet "
            "connection is required. TextMorph itself never records or stores audio. Your browser will ask for "
            "microphone permission the first time; the page must be opened via localhost or HTTPS."), unsafe_allow_html=True)

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    with card("voice_edit"):
        st.markdown("<div class='tm-section-title'>2. Review and edit the transcript</div>", unsafe_allow_html=True)
        transcript = st.text_area("Transcript", key="voice_text", height=220, label_visibility="collapsed",
                                  placeholder="Recognised speech appears here. You can also type or correct it.")
        st.markdown(helpers.chips_html(helpers.text_stats(transcript)), unsafe_allow_html=True)
        st.markdown("<div class='tm-section-title'>3. Send it to a tool</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        empty = not transcript.strip()
        with c1:
            st.button("Send to Summarization", key="voice_to_sum", type="primary", disabled=empty,
                      on_click=send_voice_to, args=("Text Summarization",), **STRETCH)
        with c2:
            st.button("Send to Paraphrasing", key="voice_to_par", disabled=empty,
                      on_click=send_voice_to, args=("Text Paraphrasing",), **STRETCH)
        with c3:
            st.button("Clear transcript", key="voice_clear", on_click=clear_voice, **STRETCH)


# --------------------------------------------------------------------------
# About
# --------------------------------------------------------------------------
def render_about():
    st.markdown("<div class='tm-page-title'>About TextMorph</div>"
                f"<div class='tm-page-desc'>{theme.PROJECT_FULL}. Developed by {' &amp; '.join(theme.DEVELOPERS)} as a B.Tech 5th-semester Cornerstone Project.</div>",
                unsafe_allow_html=True)
    st.markdown("""
<div class='tm-grid'>
  <div class='tm-info-card'><h4>Extractive summarization</h4>
    <p>Selects the most important sentences from the original text and keeps their exact wording.</p>
    <ul><li>Preserves original phrasing</li><li>Fast processing</li><li>Well suited to factual content</li></ul></div>
  <div class='tm-info-card'><h4>Abstractive summarization</h4>
    <p>Uses AI to write new sentences that capture the meaning of the text.</p>
    <ul><li>Reads more like a human summary</li><li>Generates new phrasing</li><li>Better for narrative content</li></ul></div>
  <div class='tm-info-card'><h4>Paraphrasing</h4>
    <p>Rewrites text in different words while keeping its meaning.</p>
    <ul><li>Natural language output</li><li>Keeps context and meaning</li><li>Useful for clarity and originality</li></ul></div>
  <div class='tm-info-card'><h4>Cloud-based processing</h4>
    <p>All AI processing runs through the Hugging Face Inference API, so no local models need to be downloaded.</p>
    <ul><li>No GPU required</li><li>Light installation</li><li>Needs an internet connection and an API key</li></ul></div>
</div>
<div class='tm-grid'>
  <div class='tm-info-card'><h4>Where it helps</h4>
    <ul><li>News articles and research papers</li><li>Book chapters, essays and reports</li><li>Business documents and meeting notes</li><li>Emails that need a different tone</li></ul></div>
  <div class='tm-info-card'><h4>Technology</h4>
    <ul><li>Python and Streamlit</li><li>Hugging Face Inference API</li><li>SummarizationPipeline (extractive, abstractive, paraphrase)</li><li>Browser speech recognition for voice typing</li><li>pypdf and python-docx for document text extraction</li></ul></div>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# API / service status
# --------------------------------------------------------------------------
def render_status():
    st.markdown("<div class='tm-page-title'>API / Service Status</div>"
                "<div class='tm-page-desc'>Three separate checks: whether a key exists, whether Hugging Face accepts it, and whether a real request worked.</div>",
                unsafe_allow_html=True)
    verify, last = st.session_state.api_verify, st.session_state.api_last

    def when(item):
        return datetime.fromtimestamp(item["ts"]).strftime("%H:%M:%S") if item else "-"

    with card("status_checks"):
        st.markdown("<div class='tm-section-title'>Checks</div>", unsafe_allow_html=True)
        key_label, key_tone = ("Configured", "ok") if HF_API_KEY else ("Missing", "bad")
        v_label, v_tone = api_status.state_info(verify["state"]) if verify else ("Not checked yet", "neutral")
        l_label, l_tone = api_status.state_info(last["state"]) if last else ("No request yet", "neutral")
        rows = [
            ("API key (HF_API_KEY)", helpers.pill_html(key_label, key_tone), "Presence only. Says nothing about validity."),
            ("Connection verification", helpers.pill_html(v_label, v_tone),
             f"{verify['detail']} (checked {when(verify)})" if verify else "Click Verify connection."),
            ("Last real request", helpers.pill_html(l_label, l_tone), (last["detail"][:200] + f" ({when(last)})") if last else "Run a summary or paraphrase."),
        ]
        body = "".join(
            f"<tr><td>{helpers.esc(name)}</td><td>{pill}</td><td style='white-space:normal'>{helpers.esc(detail)}</td></tr>"
            for name, pill, detail in rows)
        st.markdown("<div class='tm-table-wrap'><table class='tm-table'><thead><tr><th>Check</th><th>Status</th><th>Details</th></tr></thead>"
                    f"<tbody>{body}</tbody></table></div>", unsafe_allow_html=True)
        st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
        st.button("Verify connection", key="verify_btn", type="primary", on_click=do_verify)
        st.caption("Verification asks Hugging Face whether the token is accepted. It does not prove the summarization model is "
                   "online; only a successful real request does.")

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    state = current_api_state()
    label, _ = api_status.state_info(state)
    with card("status_help"):
        st.markdown("<div class='tm-section-title'>Current assessment and next step</div>", unsafe_allow_html=True)
        kind = {"ok": "success", "warn": "warn", "bad": "error", "neutral": "info"}[api_status.state_info(state)[1]]
        st.markdown(helpers.callout_html(kind, label, api_status.GUIDANCE[state]), unsafe_allow_html=True)
        st.markdown("<div class='tm-page-desc'>Provider: Hugging Face Inference API (unchanged from the original project). "
                    "The API key is never displayed in the interface.</div>", unsafe_allow_html=True)


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
elif page == "Voice Input":
    render_voice()
elif page == "About TextMorph":
    render_about()
else:
    render_status()

st.markdown(theme.footer_html(), unsafe_allow_html=True)
render_sidebar_status(status_slot)  # filled last so it reflects requests made during this run