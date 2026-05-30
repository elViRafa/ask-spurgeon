"""
Language support constants and utilities for Ask Spurgeon.

Currently focused on adding Portuguese support while keeping the architecture
extensible to other languages.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

# Supported languages (we can expand this over time)
LanguageCode = Literal["en", "pt", "es", "fr", "de"]

@dataclass(frozen=True)
class Language:
    code: LanguageCode
    name: str
    native_name: str
    flag: str  # Emoji flag for UI

SUPPORTED_LANGUAGES: dict[LanguageCode, Language] = {
    "en": Language("en", "English", "English", "🇬🇧"),
    "pt": Language("pt", "Portuguese", "Português", "🇧🇷"),
    # Future languages (commented for now)
    # "es": Language("es", "Spanish", "Español", "🇪🇸"),
    # "fr": Language("fr", "French", "Français", "🇫🇷"),
    # "de": Language("de", "German", "Deutsch", "🇩🇪"),
}

DEFAULT_LANGUAGE: LanguageCode = "en"


def get_language(code: str) -> Language:
    """Get language info by code. Falls back to English."""
    return SUPPORTED_LANGUAGES.get(code.lower(), SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE])


def is_supported_language(code: str) -> bool:
    return code.lower() in SUPPORTED_LANGUAGES


def get_language_options() -> list[tuple[str, str]]:
    """Return list of (code, display_name) for UI selectors."""
    return [
        (lang.code, f"{lang.flag} {lang.native_name}")
        for lang in SUPPORTED_LANGUAGES.values()
    ]


# Simple language detection helper (can be improved later with langdetect or similar)
def detect_language(text: str) -> LanguageCode:
    """
    Very basic language detection.
    For production, consider using `langdetect` or `fasttext` library.
    """
    text_lower = text.lower()

    # Very rough Portuguese heuristics
    portuguese_markers = [
        "o que", "como", "por que", "porque", "deus", "jesus", "espírito",
        "graça", "salvação", "pecado", "oração", "sofrimento", "soberania"
    ]
    if any(marker in text_lower for marker in portuguese_markers):
        # Count Portuguese-specific characters/words
        pt_score = sum(1 for marker in portuguese_markers if marker in text_lower)
        if pt_score >= 2:
            return "pt"

    return "en"


# =============================================================================
# Full UI Translations for bilingual interface (English / Portuguese)
# All static labels, headers, help texts, buttons, messages, disclaimers etc.
# =============================================================================

UI_TEXT = {
    "en": {
        # Language selector
        "language_header": "Language",
        "language_help": "Choose the language for the interface and answers.",
        "language_select_label": "Interface & Answers",

        # Filters
        "filters_header": "Filters",
        "author_label": "Author",
        "author_help": "Author-aware infrastructure ready for future additions (Edwards, Lloyd-Jones, etc.)",
        "volume_label": "Volume range",
        "year_label": "Year preached",
        "bible_book_label": "Bible book referenced",
        "bible_book_help": "Filters sermons that reference this book anywhere in the text",
        "sermon_num_label": "Specific sermon number(s)",
        "sermon_num_placeholder": "e.g. 42 or 100, 101",
        "sermon_num_help": "Comma-separated list",

        # Sources / results
        "sources_title": "### Sources",
        "sources_title_pt": "### Sources (Original in English)",
        "view_original": "📜 View original English answer",
        "sermon_label": "Sermon",
        "vol_label": "Vol.",

        # Chat
        "chat_placeholder": "Ask about faith, grace, suffering, prayer, election, or any Scripture...",
        "initial_greeting": "Hello! How can I help you explore the sermons of Charles Spurgeon today?",
        "searching": "Searching the sermons...",

        # Examples
        "try_questions": "**Try one of these questions:**",

        # Rate limiting
        "rate_limit_msg": "You have reached the free-tier limit of {limit} queries per hour. Please try again shortly.",
        "queries_remaining": "Queries remaining this hour: **{remaining}** / {max} (Groq free tier)",

        # Errors / warnings
        "invalid_sermon_nums": "Invalid sermon numbers — ignoring.",
        "rate_limited_error": "Groq is currently rate-limited. Please wait 30–60 seconds and try again.",
        "generic_error": "An error occurred while generating the answer: {err_msg}",
        "collection_missing": """The vector database collection has not been created yet.

Run `python ingest.py --source markdown --limit 50` locally (or on a powerful machine), then push the collection to your Qdrant Cloud instance.""",
        "no_results_message": "I do not find any sermons in the current collection that speak directly to this question. You may wish to broaden your filters or try a different wording.",
        "example_button_help": "Click to ask this question",

        # Disclaimer (HTML content)
        "disclaimer": """<strong>Public domain sermons</strong> (Charles Haddon Spurgeon, 1834–1892) • 
            AI-generated answers may contain hallucinations or inaccuracies. 
            <strong>Not officially affiliated</strong> with any Spurgeon society or publisher. 
            Always verify against the original published sermons. 
            This is a free educational tool built for the church.""",
    },
    "pt": {
        # Language selector
        "language_header": "Idioma",
        "language_help": "Escolha o idioma da interface e das respostas.",
        "language_select_label": "Interface e Respostas",

        # Filters
        "filters_header": "Filtros",
        "author_label": "Autor",
        "author_help": "Infraestrutura preparada para futuros autores (Edwards, Lloyd-Jones, etc.)",
        "volume_label": "Faixa de volumes",
        "year_label": "Ano pregado",
        "bible_book_label": "Livro bíblico referenciado",
        "bible_book_help": "Filtra sermões que referenciam este livro em qualquer parte do texto",
        "sermon_num_label": "Número(s) específico(s) do sermão",
        "sermon_num_placeholder": "ex: 42 ou 100, 101",
        "sermon_num_help": "Lista separada por vírgulas",

        # Sources / results
        "sources_title": "### Fontes",
        "sources_title_pt": "### Fontes (Original em Inglês)",
        "view_original": "📜 Ver resposta original em inglês",
        "sermon_label": "Sermão",
        "vol_label": "Vol.",

        # Chat
        "chat_placeholder": "Pergunte sobre fé, graça, sofrimento, oração, eleição ou qualquer passagem da Escritura...",
        "initial_greeting": "Olá! Como posso ajudar você a explorar os sermões de Charles Spurgeon hoje?",
        "searching": "Buscando nos sermões...",

        # Examples
        "try_questions": "**Experimente uma destas perguntas:**",

        # Rate limiting
        "rate_limit_msg": "Você atingiu o limite gratuito de {limit} consultas por hora. Tente novamente em breve.",
        "queries_remaining": "Consultas restantes nesta hora: **{remaining}** / {max} (tier gratuito Groq)",

        # Errors / warnings
        "invalid_sermon_nums": "Números de sermão inválidos — ignorando.",
        "rate_limited_error": "Groq está com limite de taxa no momento. Aguarde 30–60 segundos e tente novamente.",
        "generic_error": "Ocorreu um erro ao gerar a resposta: {err_msg}",
        "collection_missing": """A coleção do banco de dados vetorial ainda não foi criada.

Execute `python ingest.py --source markdown --limit 50` localmente (ou em uma máquina potente), depois envie a coleção para sua instância do Qdrant Cloud.""",
        "no_results_message": "Não encontrei sermões na coleção atual que tratem diretamente desta pergunta. Você pode ampliar os filtros ou tentar uma formulação diferente.",
        "example_button_help": "Clique para fazer esta pergunta",

        # Disclaimer (HTML content)
        "disclaimer": """<strong>Sermões de domínio público</strong> (Charles Haddon Spurgeon, 1834–1892) • 
            Respostas geradas por IA podem conter alucinações ou imprecisões. 
            <strong>Não afiliado oficialmente</strong> a nenhuma sociedade ou editora de Spurgeon. 
            Sempre verifique com os sermões originais publicados. 
            Esta é uma ferramenta educacional gratuita feita para a igreja.""",
    }
}


def get_ui_text(key: str, lang: str = "en", **kwargs) -> str:
    """Get translated UI string. Falls back gracefully to English then the key itself."""
    texts = UI_TEXT.get(lang, UI_TEXT["en"])
    text = texts.get(key, UI_TEXT["en"].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass  # avoid breaking UI on bad format
    return text
