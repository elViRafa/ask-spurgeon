"""
Ask Spurgeon — Central Configuration
All tunable parameters, model names, prompts, and constants live here.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# =============================================================================
# Paths
# =============================================================================
ROOT_DIR = Path(__file__).parent.resolve()
DATA_DIR = ROOT_DIR / "data"
SERMONS_DIR = DATA_DIR / "sermons"           # for chs*.pdf files
MARKDOWN_DIR = DATA_DIR / "chspurgeon-sermons"  # clone of https://github.com/lyteword/chspurgeon-sermons

# =============================================================================
# Author Configuration (future-proof for multi-author RAG)
# =============================================================================
DEFAULT_AUTHOR = "Charles Haddon Spurgeon"
SUPPORTED_AUTHORS = [
    "Charles Haddon Spurgeon",
    # Future authors (placeholders — infrastructure ready):
    # "Jonathan Edwards",
    # "Martyn Lloyd-Jones",
    # "John Calvin",
    # "A.W. Tozer",
    # "Matthew Henry",
]

# =============================================================================
# Embedding Model
# =============================================================================
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))

# =============================================================================
# LLM Configuration
# =============================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "llama-3.3-70b-versatile")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "llama-3.1-8b-instant")

# --- Custom OpenAI-compatible LLM (e.g. your fine-tuned Spurgeon model via llama.cpp on HF Spaces) ---
# Set LLM_PROVIDER="openai" to use a custom endpoint instead of (or alongside) Groq.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()   # "groq" or "openai"

CUSTOM_LLM_BASE_URL = os.getenv("CUSTOM_LLM_BASE_URL", "")          # e.g. "https://your-space.hf.space/v1"
CUSTOM_LLM_API_KEY = os.getenv("CUSTOM_LLM_API_KEY", "hf_dummy")    # Any non-empty string works for most OpenAI-compatible servers (llama.cpp, vLLM, etc.)
CUSTOM_LLM_MODEL = os.getenv("CUSTOM_LLM_MODEL", "spurgeon-qa-v2")   # Ollama / llama.cpp model id

# Post-SFT evaluation judge. Keep credentials in .env; reports never persist the key.
SFT_EVAL_JUDGE_PROVIDER = os.getenv("SFT_EVAL_JUDGE_PROVIDER", "groq").lower()
_SFT_EVAL_JUDGE_DEFAULTS = {
    "groq": (
        "https://api.groq.com/openai/v1",
        GROQ_API_KEY,
        PRIMARY_MODEL,
    ),
    "openrouter": (
        "https://openrouter.ai/api/v1",
        os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY", ""),
        "nvidia/nemotron-3-super-120b-a12b:free",
    ),
    "cerebras": (
        "https://api.cerebras.ai/v1",
        os.getenv("CEREBRAS_API_KEY", ""),
        "gpt-oss-120b",
    ),
    "gemini": (
        "https://generativelanguage.googleapis.com/v1beta/openai",
        os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", ""),
        "gemini-3.5-flash-lite",
    ),
}
_SFT_EVAL_DEFAULT_BASE_URL, _SFT_EVAL_DEFAULT_API_KEY, _SFT_EVAL_DEFAULT_MODEL = (
    _SFT_EVAL_JUDGE_DEFAULTS.get(SFT_EVAL_JUDGE_PROVIDER, ("", "", ""))
)
SFT_EVAL_JUDGE_BASE_URL = os.getenv(
    "SFT_EVAL_JUDGE_BASE_URL", _SFT_EVAL_DEFAULT_BASE_URL
)
SFT_EVAL_JUDGE_API_KEY = os.getenv("SFT_EVAL_JUDGE_API_KEY", _SFT_EVAL_DEFAULT_API_KEY)
SFT_EVAL_JUDGE_MODEL = os.getenv("SFT_EVAL_JUDGE_MODEL", _SFT_EVAL_DEFAULT_MODEL)
SFT_EVAL_JUDGE_TIMEOUT = int(os.getenv("SFT_EVAL_JUDGE_TIMEOUT", "120"))

# Fine-tuned path (Qwen3.5 SFT v2) — used when LLM_PROVIDER=openai
FINE_TUNED_SIMILARITY_TOP_K = int(os.getenv("FINE_TUNED_SIMILARITY_TOP_K", "4"))
FINE_TUNED_MAX_SEQ_LENGTH = int(os.getenv("FINE_TUNED_MAX_SEQ_LENGTH", "4096"))
FINE_TUNED_HF_REPO = os.getenv("FINE_TUNED_HF_REPO", "rafaelvieirar1r/qwen3.5-4b-spurgeon-qa")
FINE_TUNED_GGUF_F16 = os.getenv("FINE_TUNED_GGUF_F16", "spurgeon-qa-v2.F16.gguf")
FINE_TUNED_GGUF_Q4 = os.getenv("FINE_TUNED_GGUF_Q4", "spurgeon-qa-v2.Q4_K_M.gguf")

# Temperature / generation settings tuned for Spurgeon voice
TEMPERATURE = 0.65
TOP_P = 0.92
MAX_TOKENS = 2048

# =============================================================================
# Vector Store Configuration
# =============================================================================
# Choose between "qdrant" (default, for production/HF Spaces) or "chroma" (local Docker)
VECTOR_STORE = os.getenv("VECTOR_STORE", "qdrant").lower()

# --- Qdrant (Production / HF Spaces) ---
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "spurgeon_sermons_v1")

# --- ChromaDB (Local Development with Docker) ---
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "spurgeon_sermons_v1")

# Pure local persistent ChromaDB (no Docker needed) - recommended for quick local testing
# Example: CHROMA_PERSIST_DIR=./chroma_db
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", None)

# =============================================================================
# Ingestion Settings
# =============================================================================
MAX_SERMONS = int(os.getenv("MAX_SERMONS", "0")) or None  # None = all
CHUNK_SIZE = 768
CHUNK_OVERLAP = 128
BATCH_SIZE = 64  # nodes per Qdrant upsert

# =============================================================================
# Rate Limiting (important for Groq free tier)
# =============================================================================
MAX_QUERIES_PER_HOUR = int(os.getenv("MAX_QUERIES_PER_HOUR", "8"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "3600"))

# =============================================================================
# Streamlit UI Settings
# =============================================================================
APP_TITLE = "Ask Spurgeon"
APP_SUBTITLE = "Search and explore the sermons of Charles Haddon Spurgeon"
APP_SUBTITLE_PT = "Busque e explore os sermões de Charles Haddon Spurgeon"
PAGE_ICON = "✝️"

# =============================================================================
# Prompt Templates (loaded from utils/prompts.py in practice)
# =============================================================================
# Canonical knowledge-assistant prompt for SFT (train / eval / Ollama Modelfile) and live RAG.
# Groq and the fine-tuned path share this string. Do not roleplay as Spurgeon.
SPURGEON_SFT_SYSTEM_PROMPT = """You are a theological Q&A assistant for the writings of Charles Haddon Spurgeon and the Puritans.

Answer using only the provided CONTEXT. Do not invent facts, quotes, or citations. Cite a heading only when it appears in CONTEXT (e.g. [Sermon N]).

You are not Spurgeon and you do not speak as him or as any Puritan. Do not address the reader with vocatives such as "Beloved", "My beloved", "Dear friends", or "My brethren". Do not use first-person preacher roleplay.

Aim for the knowledge and theological depth of these writers. A light touch of their register is welcome (scriptural cadence, concrete metaphor, careful distinction) so long as it never becomes costume or caricature.

If CONTEXT does not contain enough to answer, say so briefly and plainly. Do not speculate, and do not answer from memory of writers or works that are not in CONTEXT.

Respond in the same language as the user's question."""

SYSTEM_PROMPT_NEUTRAL = SPURGEON_SFT_SYSTEM_PROMPT

# Open theological chat (no retrieval). Separate from the RAG CONTEXT contract above.
# Used by the open-theology SFT slice only. Live RAG keeps SPURGEON_SFT_SYSTEM_PROMPT.
THEOLOGY_CHAT_SYSTEM_PROMPT = """You are a theological Q&A assistant for the writings of Charles Haddon Spurgeon, the Puritans, and the confessions and catechisms in that corpus.

Answer from that corpus. Cite the work by its catalog heading. Include one verbatim quotation from the source. Do not invent sermon numbers, quotes, or works.

You are not Spurgeon, Owen, Calvin, or any Puritan. Do not address the reader with vocatives such as "Beloved", "My beloved", "Dear friends", "My brethren", "amados", or "meus queridos irmãos". Do not use first-person preacher roleplay.

If the question is outside that corpus, say so briefly and plainly. Do not speculate.

Respond in the same language as the user's question."""

USER_PROMPT_TEMPLATE = """CONTEXT (excerpts from Spurgeon and, when present, Puritan or confession texts):

{context}

---

QUESTION: {question}

Answer based ONLY on the context above.
- Cite a heading only when it appears in CONTEXT (e.g. [Sermon N]).
- Do not address the reader with vocatives such as "Beloved", "My beloved", "Dear friends", or "My brethren".
- If the context is insufficient, say so plainly. Do not speculate or answer from memory of writers not in CONTEXT.
- Respond in the same language as the user's question.
"""

# =============================================================================
# Example Questions (shown as clickable buttons)
# =============================================================================
EXAMPLE_QUESTIONS = [
    "What did Spurgeon teach about the immutability of God?",
    "How does Spurgeon explain Romans 8:28?",
    "What sermons reference Psalm 23?",
    "What did Spurgeon say about suffering and the sovereignty of God?",
    "Show me sermons on John 3:16 or 'whosoever believeth'.",
    "How does Spurgeon preach election and free grace together?",
    "What counsel does Spurgeon give to those under conviction of sin?",
    "Compare Spurgeon's view of prayer with what he says in his sermons on the subject.",
]

EXAMPLE_QUESTIONS_PT = [
    "O que Spurgeon ensinou sobre a imutabilidade de Deus?",
    "Como Spurgeon explica Romanos 8:28?",
    "Quais sermões fazem referência ao Salmo 23?",
    "O que Spurgeon disse sobre o sofrimento e a soberania de Deus?",
    "Mostre-me sermões sobre João 3:16 ou 'todo aquele que crê'.",
    "Como Spurgeon prega sobre a eleição e a graça livre juntos?",
    "Que conselho Spurgeon dá àqueles que estão sob convicção de pecado?",
    "Compare a visão de Spurgeon sobre a oração com o que ele diz em seus sermões sobre o tema.",
]

# =============================================================================
# Bible Books (for filtering + reference extraction)
# =============================================================================
BIBLE_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
    "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther",
    "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon",
    "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
    "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John",
    "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians",
    "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon",
    "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation",
]

# Common abbreviations map (used by bible_refs.py)
BIBLE_ABBREVS = {
    "gen": "Genesis", "ex": "Exodus", "lev": "Leviticus", "num": "Numbers", "deut": "Deuteronomy",
    "josh": "Joshua", "judg": "Judges", "ruth": "Ruth", "1sam": "1 Samuel", "2sam": "2 Samuel",
    "1kgs": "1 Kings", "2kgs": "2 Kings", "1chr": "1 Chronicles", "2chr": "2 Chronicles",
    "ezra": "Ezra", "neh": "Nehemiah", "esth": "Esther",
    "job": "Job", "ps": "Psalms", "psalm": "Psalms", "pss": "Psalms", "prov": "Proverbs",
    "eccl": "Ecclesiastes", "song": "Song of Solomon", "cant": "Song of Solomon",
    "isa": "Isaiah", "jer": "Jeremiah", "lam": "Lamentations", "ezek": "Ezekiel", "dan": "Daniel",
    "hos": "Hosea", "joel": "Joel", "amos": "Amos", "obad": "Obadiah", "jonah": "Jonah",
    "mic": "Micah", "nah": "Nahum", "hab": "Habakkuk", "zeph": "Zephaniah", "hag": "Haggai",
    "zech": "Zechariah", "mal": "Malachi",
    "matt": "Matthew", "mk": "Mark", "lk": "Luke", "jn": "John", "john": "John",
    "acts": "Acts",
    "rom": "Romans", "1cor": "1 Corinthians", "2cor": "2 Corinthians", "gal": "Galatians",
    "eph": "Ephesians", "phil": "Philippians", "col": "Colossians",
    "1thess": "1 Thessalonians", "2thess": "2 Thessalonians",
    "1tim": "1 Timothy", "2tim": "2 Timothy", "tit": "Titus", "phlm": "Philemon",
    "heb": "Hebrews", "jas": "James", "1pet": "1 Peter", "2pet": "2 Peter",
    "1jn": "1 John", "2jn": "2 John", "3jn": "3 John", "jude": "Jude", "rev": "Revelation",
}

# =============================================================================
# Metadata Schema (used in both ingestion and filtering)
# =============================================================================
@dataclass
class SermonMetadata:
    author: str = DEFAULT_AUTHOR
    sermon_number: Optional[int] = None
    title: str = ""
    volume: Optional[int] = None
    year: Optional[int] = None
    primary_scripture: str = ""
    bible_book: str = ""
    source_url: str = ""
    bible_references: list[str] = field(default_factory=list)  # normalized strings e.g. "Romans 8:28"

    def to_dict(self) -> dict:
        return {
            "author": self.author,
            "sermon_number": self.sermon_number,
            "title": self.title,
            "volume": self.volume,
            "year": self.year,
            "primary_scripture": self.primary_scripture,
            "bible_book": self.bible_book,
            "source_url": self.source_url,
            "bible_references": self.bible_references,
        }


# =============================================================================
# Helper to load secrets safely
# =============================================================================
def get_secret(key: str, default: str = "") -> str:
    """Get from environment (works in HF Spaces Secrets and local .env)."""
    return os.getenv(key, default)
