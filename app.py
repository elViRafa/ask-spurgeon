"""
Ask Spurgeon — Free Public RAG Web App (Streamlit)

A beautiful, completely free, publicly accessible interface to search and converse
with the sermons of Charles Haddon Spurgeon using semantic search + Groq LLM.

Deployment target: Hugging Face Spaces (zero cost)
Vector store: Qdrant Cloud (free tier)
"""

from __future__ import annotations
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import streamlit as st
from dotenv import load_dotenv

load_dotenv()   # Must be called BEFORE importing config.py

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter, FilterOperator
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.llms.openai import OpenAI as LlamaOpenAI
from llama_index.llms.openai_like import OpenAILike  # For custom OpenAI-compatible endpoints (llama.cpp, vLLM, TGI, etc.) - allows arbitrary model names
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

# Optional ChromaDB support
try:
    from llama_index.vector_stores.chroma import ChromaVectorStore
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

# Local
from config import (
    APP_TITLE, APP_SUBTITLE, APP_SUBTITLE_PT, PAGE_ICON,
    GROQ_API_KEY, PRIMARY_MODEL, FALLBACK_MODEL,
    LLM_PROVIDER, CUSTOM_LLM_BASE_URL, CUSTOM_LLM_API_KEY, CUSTOM_LLM_MODEL,
    VECTOR_STORE,
    QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION,
    CHROMA_HOST, CHROMA_PORT, CHROMA_COLLECTION,
    EMBEDDING_MODEL, TEMPERATURE, TOP_P, MAX_TOKENS,
    MAX_QUERIES_PER_HOUR, RATE_LIMIT_WINDOW_SECONDS,
    EXAMPLE_QUESTIONS, EXAMPLE_QUESTIONS_PT,
    DEFAULT_AUTHOR, SUPPORTED_AUTHORS,
    get_secret,
)
from utils.bible_refs import get_bible_book_filter_values, extract_bible_references
import requests
from utils.prompts import get_system_prompt
from utils.language import (
    get_language_options,
    get_language,
    DEFAULT_LANGUAGE,
    LanguageCode,
    get_ui_text,
)
from utils.translator import (
    translate_to_english,
    translate_to_language,
    detect_and_translate_query,
)

# =============================================================================
# Page Config & Custom Styling (Spurgeon / Bible aesthetic)
# =============================================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Beautiful dark elegant theme with gold accents (inspired by old Bibles and 19th-century aesthetics).
# We deliberately force dark mode because the design is meant to feel timeless and focused on the content.
# Light mode looked broken because the custom dark conversation styling clashed with Streamlit's light theme.
# Solution: .streamlit/config.toml + aggressive CSS overrides below.
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;600&family=Playfair+Display:wght@700&display=swap');

    /* === GLOBAL DARK THEME OVERRIDES === */
    .stApp {
        background-color: #16130f !important;
        color: #f4e9d8 !important;
    }

    .main .block-container { 
        padding-top: 1.2rem; 
        max-width: 1100px; 
        background-color: #16130f !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1f1a14 !important;
    }

    h1, h2, h3 { font-family: 'Playfair Display', Georgia, serif; }
    
    .spurgeon-header {
        text-align: center;
        padding: 1.5rem 0 0.8rem;
        border-bottom: 1px solid #3a2f1f;
        margin-bottom: 1rem;
    }
    .spurgeon-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 2.8rem;
        font-weight: 700;
        color: #f4e9d8;
        margin: 0;
        letter-spacing: -1px;
    }
    .spurgeon-subtitle {
        color: #c9b38a;
        font-size: 1.05rem;
        margin-top: 0.2rem;
    }
    
    .disclaimer {
        font-size: 0.78rem;
        color: #8a7a5f;
        background: #1f1a14;
        padding: 0.6rem 0.9rem;
        border-radius: 6px;
        border-left: 3px solid #8a7a5f;
        margin: 0.8rem 0;
    }
    
    .source-card {
        background: #1f1a14;
        border: 1px solid #3a2f1f;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.65rem;
    }
    .source-card:hover {
        border-color: #c9b38a;
    }
    .source-title {
        font-weight: 600;
        color: #f4e9d8;
        font-size: 0.95rem;
        margin-bottom: 0.15rem;
    }
    .source-meta {
        color: #c9b38a;
        font-size: 0.75rem;
        margin-bottom: 0.35rem;
    }
    .source-excerpt {
        color: #d4c9b0;
        font-size: 0.82rem;
        line-height: 1.35;
        font-family: 'EB Garamond', Georgia, serif;
    }
    
    /* Force dark elegant theme on chat area even if user has light system theme */
    .stChatMessage,
    div[data-testid="stChatMessage"],
    [data-testid="stChatMessage"] {
        background-color: #16130f !important;
        border: 1px solid #2c251b !important;
        color: #f4e9d8 !important;
        border-radius: 10px !important;
        padding: 0.6rem 0.9rem !important;
    }

    /* User message bubble */
    .stChatMessage[data-testid="user"] div,
    div[data-testid="stChatMessage"][data-testid="user"] {
        background-color: #2c251b !important;
    }

    /* Assistant message bubble */
    .stChatMessage[data-testid="assistant"] div,
    div[data-testid="stChatMessage"][data-testid="assistant"] {
        background-color: #16130f !important;
    }

    /* Chat input area */
    .stChatInputContainer,
    [data-testid="stChatInput"] {
        background-color: #1f1a14 !important;
        border-top: 1px solid #3a2f1f !important;
    }

    .stChatInput input {
        background-color: #16130f !important;
        color: #f4e9d8 !important;
        border: 1px solid #3a2f1f !important;
    }

    /* Make sure main app background stays dark */
    .stApp {
        background-color: #16130f !important;
    }

    .main .block-container {
        background-color: #16130f !important;
    }
    
    .stButton > button {
        background: #3a2f1f;
        color: #f4e9d8;
        border: 1px solid #5c4a2e;
        font-family: 'EB Garamond', Georgia, serif;
    }
    .stButton > button:hover {
        background: #c9b38a;
        color: #16130f;
        border-color: #c9b38a;
    }
    
    .example-btn {
        font-size: 0.82rem !important;
        padding: 0.35rem 0.7rem !important;
        height: auto !important;
    }
    
    .rate-limit-warning {
        color: #d97757;
        font-size: 0.85rem;
    }
    
    .spurgeon-quote {
        font-family: 'EB Garamond', Georgia, serif;
        font-style: italic;
        color: #b8a47a;
        border-left: 3px solid #5c4a2e;
        padding-left: 1rem;
        margin: 0.8rem 0;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =============================================================================
# Browser Language Detection (runs on first load, robust version)
# =============================================================================
# Uses a zero-height HTML component with guarded JS + sessionStorage.
# This avoids nested iframe cross-origin problems on HF Spaces and prevents
# redirect loops. Falls back gracefully; user can always use the selector.
lang_from_params = st.query_params.get("lang", None)

if not lang_from_params:
    # Inject a tiny script that detects navigator.language and does a one-time
    # redirect with ?lang=pt for Portuguese browsers. Uses window.location (more
    # reliable than parent in embedded iframes) + sessionStorage guard.
    st.components.v1.html(
        """
        <script>
        (function() {
            try {
                if (sessionStorage.getItem('lang_auto_checked')) return;
                sessionStorage.setItem('lang_auto_checked', 'true');

                const params = new URLSearchParams(window.location.search);
                if (params.has('lang')) return;

                const browserLang = (navigator.language || navigator.userLanguage || 'en-US').toLowerCase();
                if (browserLang.startsWith('pt')) {
                    params.set('lang', 'pt');
                    const qs = params.toString();
                    const newUrl = window.location.pathname + (qs ? '?' + qs : '');
                    window.location.replace(newUrl);
                }
            } catch (e) {
                // Silent fail — detection is best-effort only
            }
        })();
        </script>
        """,
        height=0,
    )
else:
    # Persist from URL param into session so the rest of the app sees it immediately
    if st.session_state.get("language") != lang_from_params:
        st.session_state["language"] = lang_from_params



# =============================================================================
# Cached Resources (critical for performance on HF Spaces)
# =============================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_full_sermon(raw_url: str = "", volume: int = None, sermon_number: int = None) -> str:
    """Fetch the full sermon text. Tries raw_url first, otherwise constructs it from volume + number."""
    if not raw_url and volume and sermon_number:
        raw_url = f"https://raw.githubusercontent.com/lyteword/chspurgeon-sermons/main/volume-{volume}/sermon-{sermon_number}.md"

    if not raw_url:
        return "Full sermon text not available for this source."

    try:
        response = requests.get(raw_url, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            return f"Could not load full sermon (status {response.status_code}). You can try: {raw_url}"
    except Exception as e:
        return f"Error loading full sermon: {str(e)}"


@st.cache_resource(show_spinner="Loading embedding model (first run ~100MB)... / Carregando modelo de embeddings (primeira vez ~100MB)...")
def get_embed_model():
    return HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)


@st.cache_resource(show_spinner="Connecting to Qdrant... / Conectando ao Qdrant...")
def get_qdrant_client():
    if not QDRANT_URL:
        st.error(
            "QDRANT_URL is not configured.\n\n"
            "For production/HF Spaces: Add QDRANT_URL and QDRANT_API_KEY as secrets.\n\n"
            "For local development with Qdrant:\n"
            "  1. Run: docker compose up -d qdrant\n"
            "  2. Set in your .env:\n"
            "     VECTOR_STORE=qdrant\n"
            "     QDRANT_URL=http://localhost:6333\n"
            "     QDRANT_API_KEY=\n"
            "     QDRANT_COLLECTION=spurgeon_sermons_local"
        )
        st.stop()

    try:
        client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY or None,
            timeout=20,
        )
        client.get_collections()
        return client
    except Exception as e:
        st.error(
            f"Failed to connect to Qdrant at {QDRANT_URL}\n\n"
            f"Tip: For local testing, make sure you ran:\n"
            f"  docker compose up -d qdrant\n\n"
            f"Error: {str(e)}"
        )
        st.stop()


@st.cache_resource(show_spinner="Connecting to local ChromaDB... / Conectando ao ChromaDB local...")
def get_chroma_client():
    """Connect to local ChromaDB (supports both Docker and persistent local mode)."""
    if not CHROMA_AVAILABLE:
        st.error(
            "ChromaDB support is not installed.\n\n"
            "Run this command locally:\n"
            "pip install chromadb llama-index-vector-stores-chroma"
        )
        st.stop()

    try:
        if CHROMA_PERSIST_DIR:
            # Pure local file-based mode (no Docker needed)
            client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        else:
            # Docker / remote HTTP mode
            client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
            client.heartbeat()  # health check
        return client
    except Exception as e:
        if CHROMA_PERSIST_DIR:
            st.error(f"Failed to open local ChromaDB at {CHROMA_PERSIST_DIR}\n\nError: {str(e)}")
        else:
            st.error(
                f"Failed to connect to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}\n\n"
                f"Options:\n"
                f"1. Start Docker: docker compose up -d\n"
                f"2. Or set CHROMA_PERSIST_DIR in .env for file-based mode (no Docker)\n\n"
                f"Error: {str(e)}"
            )
        st.stop()


@st.cache_resource(show_spinner="Loading vector index... / Carregando índice vetorial...")
def get_vector_store_index():
    """Load the vector store index (Qdrant or ChromaDB based on VECTOR_STORE)."""
    embed_model = get_embed_model()
    Settings.embed_model = embed_model

    if VECTOR_STORE == "chroma":
        chroma_client = get_chroma_client()
        chroma_collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        print("Using local ChromaDB vector store")
    else:
        # Default: Qdrant
        client = get_qdrant_client()
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=QDRANT_COLLECTION,
        )
        print("Using Qdrant vector store")

    return VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)


@st.cache_resource
def get_llm(use_fallback: bool = False):
    """
    Get the LLM to use.
    Supports:
      - Groq (default, fast & reliable)
      - Custom OpenAI-compatible endpoint (e.g. your fine-tuned model via llama.cpp on HF Spaces)
    """
    provider = LLM_PROVIDER

    # --- Custom OpenAI-compatible LLM (llama.cpp CPU Space, vLLM, etc.) ---
    if provider == "openai":
        if not CUSTOM_LLM_BASE_URL:
            st.error(
                "CUSTOM_LLM_BASE_URL is not set.\n\n"
                "To use your fine-tuned model, set in your environment / secrets:\n"
                "  LLM_PROVIDER=openai\n"
                "  CUSTOM_LLM_BASE_URL=https://your-generator-space.hf.space/v1\n"
                "  CUSTOM_LLM_API_KEY=hf_dummy   # any string; your public custom Space server ignores it\n"
                "  CUSTOM_LLM_MODEL=spurgeon-8b\n\n"
                "If using HF Space for the generator: open its public URL in browser first (free tier sleeps after inactivity)."
            )
            st.stop()

        print(f"Using custom OpenAI-compatible LLM at: {CUSTOM_LLM_BASE_URL} (model={CUSTOM_LLM_MODEL})")
        # Use OpenAILike for custom endpoints to support arbitrary model names like "spurgeon-8b"
        # (the standard OpenAI class has a strict list of known models and would reject custom ones).
        # Note: use api_base= (not base_url) for compatibility with llama-index OpenAILike / OpenAI wrappers.
        return OpenAILike(
            model=CUSTOM_LLM_MODEL,
            api_key=CUSTOM_LLM_API_KEY,
            api_base=CUSTOM_LLM_BASE_URL,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            timeout=600.0,  # CPU basic spaces are slow and need long timeouts
            is_chat_model=True,
            is_function_calling_model=False,  # our server doesn't do tools yet
        )

    # --- Default: Groq ---
    api_key = get_secret("GROQ_API_KEY", GROQ_API_KEY)
    if not api_key:
        st.error(
            "GROQ_API_KEY is missing.\n\n"
            "Please add the GROQ_API_KEY secret in your Hugging Face Space settings."
        )
        st.stop()

    model = FALLBACK_MODEL if use_fallback else PRIMARY_MODEL
    print(f"Using Groq model: {model}")
    return Groq(
        model=model,
        api_key=api_key,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )


# =============================================================================
# Rate Limiting (per-user session, important for Groq free tier)
# =============================================================================

def check_rate_limit() -> tuple[bool, int, int]:
    """
    Returns (allowed, used, remaining)
    Simple in-memory rate limit per browser session.
    For production public apps, add Cloudflare or server-side tracking.
    """
    now = time.time()
    if "query_timestamps" not in st.session_state:
        st.session_state.query_timestamps = []

    # Clean old entries
    window_start = now - RATE_LIMIT_WINDOW_SECONDS
    st.session_state.query_timestamps = [
        ts for ts in st.session_state.query_timestamps if ts > window_start
    ]

    used = len(st.session_state.query_timestamps)
    remaining = max(0, MAX_QUERIES_PER_HOUR - used)
    allowed = used < MAX_QUERIES_PER_HOUR

    return allowed, used, remaining


def record_query():
    if "query_timestamps" not in st.session_state:
        st.session_state.query_timestamps = []
    st.session_state.query_timestamps.append(time.time())


# =============================================================================
# Filtering Helpers
# =============================================================================

def build_metadata_filters(
    author: Optional[str] = None,
    volumes: Optional[List[int]] = None,
    years: Optional[tuple] = None,
    bible_book: Optional[str] = None,
    sermon_numbers: Optional[List[int]] = None,
) -> Optional[MetadataFilters]:
    """Build LlamaIndex MetadataFilters for Qdrant."""
    filters = []

    if author:
        filters.append(ExactMatchFilter(key="author", value=author))

    if volumes:
        # LlamaIndex doesn't have range easily here; we do post-filter or multiple exacts
        # For simplicity in MVP we support exact volume list
        for v in volumes:
            filters.append(ExactMatchFilter(key="volume", value=v))

    if years:
        # Approximate with two conditions (LlamaIndex 0.12+ supports range via more advanced filters)
        # We keep it simple: accept a min/max year and filter client-side after retrieval
        pass

    if bible_book:
        # We stored bible_references as array. LlamaIndex ExactMatchFilter on array works as "contains"
        filters.append(ExactMatchFilter(key="bible_references", value=bible_book))

    if sermon_numbers:
        for n in sermon_numbers:
            filters.append(ExactMatchFilter(key="sermon_number", value=n))

    if not filters:
        return None
    return MetadataFilters(filters=filters)


def apply_year_filter(nodes: List, year_range: Optional[tuple]) -> List:
    if not year_range:
        return nodes
    min_y, max_y = year_range
    return [
        n for n in nodes
        if n.metadata.get("year") is None or (min_y <= n.metadata.get("year", 0) <= max_y)
    ]


# =============================================================================
# Response Generation with Error Handling
# =============================================================================

def generate_response(
    question: str,
    filters: Optional[MetadataFilters],
    year_range: Optional[tuple] = None,
    use_fallback_model: bool = False,
    target_language: LanguageCode = "en",
) -> tuple[str, List[Dict], str]:
    """
    Run retrieval + LLM synthesis.
    Returns (final_answer, sources, english_answer)
    """
    index = get_vector_store_index()
    llm = get_llm(use_fallback=use_fallback_model)

    # Translate question to English if needed (for better retrieval)
    search_question = question
    if target_language != "en":
        try:
            search_question = translate_to_english(question, source_lang=target_language)
        except Exception:
            search_question = question  # fallback to original

    # Retrieval with filters
    retriever = index.as_retriever(
        similarity_top_k=6,
        filters=filters,
    )
    nodes = retriever.retrieve(search_question)

    # Post-filter by year if needed (Qdrant range filtering is possible but more complex)
    nodes = apply_year_filter(nodes, year_range)

    if not nodes:
        fallback = get_ui_text("no_results_message", target_language)
        return fallback, [], fallback

    # Build context-rich prompt using our custom system prompt
    from llama_index.core.llms import ChatMessage, MessageRole

    context_blocks = []
    sources = []
    for node in nodes[:5]:  # keep top 5 for context
        meta = node.metadata or {}
        excerpt = node.get_content()[:650].strip()
        context_blocks.append(
            f"[Sermon {meta.get('sermon_number', '?')} — \"{meta.get('title', '')}\" | {meta.get('primary_scripture', '')}]\n{excerpt}"
        )
        sources.append({
            "sermon_number": meta.get("sermon_number"),
            "title": meta.get("title"),
            "volume": meta.get("volume"),
            "year": meta.get("year"),
            "primary_scripture": meta.get("primary_scripture"),
            "excerpt": excerpt,
            "source_url": meta.get("source_url", ""),
            "score": getattr(node, "score", None),
        })

    context_str = "\n\n".join(context_blocks)

    # === Always generate the core answer in neutral modern English first ===
    # This ensures best grounding, best Spurgeon citation quality, and no role-play leakage.
    system = get_system_prompt(DEFAULT_AUTHOR)
    user_msg = (
        f"CONTEXT (excerpts from Charles Haddon Spurgeon's sermons):\n\n{context_str}\n\n"
        f"QUESTION: {search_question}\n\n"
        "Answer based ONLY on the context above. "
        "Be clear, direct, and objective. Use modern neutral professional language. "
        "Cite specific sermons by number and title when you use material from them. "
        "If the context is insufficient, clearly state the limitation."
    )

    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content=system),
        ChatMessage(role=MessageRole.USER, content=user_msg),
    ]

    try:
        resp = llm.chat(messages)
        english_answer = str(resp).strip()
    except Exception as e:
        err = str(e).lower()
        if "rate" in err or "limit" in err or "429" in err:
            if not use_fallback_model:
                return generate_response(question, filters, year_range, use_fallback_model=True, target_language=target_language)
            else:
                raise RuntimeError("Groq rate limit exceeded on both primary and fallback models. Please try again later.")
        raise

    # === Only translate at the very end if needed ===
    if target_language != "en":
        try:
            final_answer = translate_to_language(english_answer, target_lang=target_language)
        except Exception as e:
            final_answer = english_answer + f"\n\n*(Translation to {get_language(target_language).native_name} failed: {str(e)})*"
    else:
        final_answer = english_answer

    return final_answer, sources, english_answer


# =============================================================================
# UI Components
# =============================================================================

def render_header():
    lang = st.session_state.get("language") or st.query_params.get("lang") or "en"
    subtitle = APP_SUBTITLE_PT if lang == "pt" else APP_SUBTITLE
    st.markdown(
        f"""
        <div class="spurgeon-header">
            <h1 class="spurgeon-title">✝️ {APP_TITLE}</h1>
            <p class="spurgeon-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_disclaimer():
    lang = st.session_state.get("language") or st.query_params.get("lang") or "en"
    st.markdown(
        f"""
        <div class="disclaimer">
            {get_ui_text("disclaimer", lang)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_source_cards(sources: List[Dict], show_original_note: bool = False):
    if not sources:
        return

    lang = st.session_state.get("language", "en")
    title = get_ui_text("sources_title_pt", lang) if show_original_note else get_ui_text("sources_title", lang)
    st.markdown(title)

    for i, src in enumerate(sources):
        vol_label = get_ui_text("vol_label", lang)
        vol = f"{vol_label} {src['volume']}" if src.get("volume") else ""
        year = f"· {src['year']}" if src.get("year") else ""
        scripture = f"· {src['primary_scripture']}" if src.get('primary_scripture') else ""

        source_url = src.get("source_url", "")
        raw_url = src.get("raw_url", "") or source_url

        sermon_word = get_ui_text("sermon_label", lang)
        sermon_num = src.get('sermon_number', '?')
        sermon_title = src.get('title', 'Untitled')

        st.markdown(
            f"""
            <div class="source-card">
                <div class="source-title">
                    {sermon_word} {sermon_num} — {sermon_title}
                </div>
                <div class="source-meta">
                    {vol} {year} {scripture}
                </div>
                <div class="source-excerpt">
                    {src.get('excerpt', '')[:420]}...
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Links and full text button
        cols = st.columns([2, 3])

        with cols[0]:
            if source_url:
                st.markdown(f"[🔗 View on GitHub]({source_url})")

        with cols[1]:
            btn_key = f"view_full_{sermon_num}_{i}"
            if st.button("📖 View full sermon", key=btn_key, use_container_width=True):
                full_text = fetch_full_sermon(
                    raw_url=raw_url,
                    volume=src.get("volume"),
                    sermon_number=sermon_num if isinstance(sermon_num, int) else None
                )
                with st.expander(f"📜 Full Sermon {sermon_num} — {sermon_title}", expanded=True):
                    st.markdown(full_text)
                    if source_url:
                        st.markdown(f"[Open in new tab →]({source_url})")


def render_sidebar_filters() -> dict:
    # Determine current language early (from session, URL param, or default)
    lang = st.session_state.get("language") or st.query_params.get("lang") or "en"
    if lang not in ("en", "pt"):
        lang = "en"

    st.sidebar.header(get_ui_text("language_header", lang))

    language_options = get_language_options()
    language_codes = [opt[0] for opt in language_options]

    # Compute safe index from current known language (no more hard-coded PT forcing)
    try:
        default_index = language_codes.index(lang)
    except ValueError:
        default_index = 0

    selected_lang = st.sidebar.selectbox(
        get_ui_text("language_select_label", lang),
        options=language_codes,
        index=default_index,
        format_func=lambda x: dict(language_options)[x],
        help=get_ui_text("language_help", lang),
        key="language_selector",
    )

    # Update session + make language choice bookmarkable via query param
    if st.session_state.get("language") != selected_lang:
        st.session_state["language"] = selected_lang
        st.query_params["lang"] = selected_lang

    # Show which LLM is active (helpful when using custom fine-tuned model)
    if LLM_PROVIDER == "openai":
        model_name = CUSTOM_LLM_MODEL or "custom"
        st.sidebar.caption(f"🤖 Using custom model: **{model_name}**")
        if CUSTOM_LLM_BASE_URL:
            # Show a hint for HF Spaces (free tier sleeps)
            if "hf.space" in CUSTOM_LLM_BASE_URL:
                st.sidebar.caption("ℹ️ If using HF generator Space: visit its URL first to wake it from sleep.")
    else:
        st.sidebar.caption(f"🤖 Using Groq: **{PRIMARY_MODEL}**")

    st.sidebar.divider()

    st.sidebar.header(get_ui_text("filters_header", lang))

    author = st.sidebar.selectbox(
        get_ui_text("author_label", lang),
        options=SUPPORTED_AUTHORS,
        index=0,
        help=get_ui_text("author_help", lang)
    )

    # Volume range (simplified)
    volume_range = st.sidebar.slider(
        get_ui_text("volume_label", lang),
        min_value=1,
        max_value=63,
        value=(1, 63),
        step=1,
    )

    year_range = st.sidebar.slider(
        get_ui_text("year_label", lang),
        min_value=1855,
        max_value=1892,
        value=(1855, 1892),
        step=1,
    )

    bible_books = [""] + get_bible_book_filter_values()
    bible_book = st.sidebar.selectbox(
        get_ui_text("bible_book_label", lang),
        options=bible_books,
        index=0,
        help=get_ui_text("bible_book_help", lang)
    )

    sermon_num_input = st.sidebar.text_input(
        get_ui_text("sermon_num_label", lang),
        placeholder=get_ui_text("sermon_num_placeholder", lang),
        help=get_ui_text("sermon_num_help", lang)
    )

    # Convert to usable filter values
    volumes = list(range(volume_range[0], volume_range[1] + 1))
    years = year_range

    sermon_numbers = None
    if sermon_num_input.strip():
        try:
            sermon_numbers = [int(x.strip()) for x in sermon_num_input.split(",") if x.strip()]
        except ValueError:
            st.sidebar.warning(get_ui_text("invalid_sermon_nums", lang))

    return {
        "author": author,
        "volumes": volumes if volumes != list(range(1, 64)) else None,
        "years": years if years != (1855, 1892) else None,
        "bible_book": bible_book or None,
        "sermon_numbers": sermon_numbers,
        "language": selected_lang,
    }


# =============================================================================
# Main Application
# =============================================================================

def main():
    # Resolve language as early as possible for all UI strings
    lang = st.session_state.get("language") or st.query_params.get("lang") or "en"
    if lang not in ("en", "pt"):
        lang = "en"

    render_header()
    render_disclaimer()

    # Sidebar
    filters = render_sidebar_filters()

    # Check if index exists (basic health check)
    try:
        client = get_qdrant_client()
        if not client.collection_exists(QDRANT_COLLECTION):
            st.warning(get_ui_text("collection_missing", lang))
            st.stop()
    except Exception as e:
        st.error(f"Cannot connect to Qdrant: {e}")
        st.stop()

    # Rate limit status
    allowed, used, remaining = check_rate_limit()
    if not allowed:
        st.warning(get_ui_text("rate_limit_msg", lang, limit=MAX_QUERIES_PER_HOUR))

    # Example questions as buttons (language-aware)
    st.markdown(get_ui_text("try_questions", lang))
    example_questions = EXAMPLE_QUESTIONS_PT if lang == "pt" else EXAMPLE_QUESTIONS
    cols = st.columns(4)
    for i, q in enumerate(example_questions[:8]):
        ex_help = get_ui_text("example_button_help", lang)
        if cols[i % 4].button(q, key=f"ex_{i}", help=ex_help, use_container_width=True):
            st.session_state["pending_question"] = q
            st.rerun()

    st.divider()

    # Chat interface
    lang = st.session_state.get("language", "en")
    greeting = get_ui_text("initial_greeting", lang)

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": greeting,
            }
        ]

    # Replay history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # Show original English if available (for Portuguese users)
            if msg.get("english_content"):
                lang = st.session_state.get("language", "en")
                with st.expander(get_ui_text("view_original", lang), expanded=False):
                    st.markdown(msg["english_content"])

    # Handle pending example question
    question = None
    if "pending_question" in st.session_state:
        question = st.session_state.pop("pending_question")

    # Chat input
    if not question:
        question = st.chat_input(get_ui_text("chat_placeholder", lang))

    if question:
        # Rate limit gate
        allowed, used, remaining = check_rate_limit()
        if not allowed:
            with st.chat_message("assistant"):
                st.warning(get_ui_text("rate_limit_msg", lang, limit=MAX_QUERIES_PER_HOUR))
            return

        # Record user message
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # Generate
        with st.chat_message("assistant"):
            with st.spinner(get_ui_text("searching", lang)):
                try:
                    # Build LlamaIndex filters
                    meta_filters = build_metadata_filters(
                        author=filters["author"],
                        volumes=filters["volumes"],
                        years=filters["years"],
                        bible_book=filters["bible_book"],
                        sermon_numbers=filters["sermon_numbers"],
                    )

                    target_language: LanguageCode = filters.get("language", "en")

                    final_answer, sources, english_answer = generate_response(
                        question=question,
                        filters=meta_filters,
                        year_range=filters["years"],
                        target_language=target_language,
                    )

                    st.markdown(final_answer)

                    # Show original English answer when user is not using English
                    if target_language != "en" and english_answer:
                        with st.expander(get_ui_text("view_original", lang), expanded=False):
                            st.markdown(english_answer)

                    render_source_cards(sources, show_original_note=(target_language != "en"))

                    # Persist to history
                    history_entry = {
                        "role": "assistant",
                        "content": final_answer,
                        "sources": sources,
                    }
                    if target_language != "en" and english_answer:
                        history_entry["english_content"] = english_answer

                    st.session_state.messages.append(history_entry)

                    record_query()

                except Exception as e:
                    err_msg = str(e)
                    if "rate" in err_msg.lower() or "429" in err_msg:
                        st.error(get_ui_text("rate_limited_error", lang))
                    else:
                        st.error(get_ui_text("generic_error", lang, err_msg=err_msg))
                    # Remove the failed user message so they can retry easily
                    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                        st.session_state.messages.pop()

        # Show remaining quota
        _, used, remaining = check_rate_limit()
        st.caption(get_ui_text("queries_remaining", lang, remaining=remaining, max=MAX_QUERIES_PER_HOUR))


if __name__ == "__main__":
    main()
