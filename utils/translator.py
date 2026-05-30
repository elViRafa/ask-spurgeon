"""
Translation utilities for Ask Spurgeon multilingual support.

Currently uses Groq (same provider as the main LLM) for translations.
This keeps the stack simple and consistent.

Design goals:
- Translate user questions (non-English → English) for better retrieval.
- Translate final answers (English → target language) while trying to preserve
  theological meaning and (as much as possible) Spurgeon's tone.
"""

from __future__ import annotations
from typing import Optional

from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.llms.groq import Groq

from config import GROQ_API_KEY, PRIMARY_MODEL, FALLBACK_MODEL
from utils.language import get_language, LanguageCode


# Use the stronger model for translation to better follow strict tone instructions
_TRANSLATION_MODEL = PRIMARY_MODEL  # llama-3.3-70b-versatile for better instruction adherence


def _get_translator_llm() -> Groq:
    """Get a Groq client configured for translation tasks."""
    return Groq(
        model=_TRANSLATION_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0.2,  # Low temperature for more consistent translations
        max_tokens=2048,
    )


def translate_to_english(text: str, source_lang: LanguageCode = "pt") -> str:
    """
    Translate text from source language to English.
    This is used to improve retrieval quality when the user asks in another language.
    """
    if source_lang == "en":
        return text

    llm = _get_translator_llm()

    lang_info = get_language(source_lang)

    prompt = f"""You are a precise translator. Translate the following text from {lang_info.native_name} into clear, natural, modern English.

Translate literally and objectively. Do not add warmth or change the tone.

Text to translate:
{text}

English translation:"""

    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content="You are a precise and literal translator. Translate objectively without adding tone or warmth."),
        ChatMessage(role=MessageRole.USER, content=prompt)
    ]
    response = llm.chat(messages)
    text = str(response).strip()
    # Remove common chat prefixes that sometimes appear
    for prefix in ["assistant:", "Assistant:", "Resposta:", "Tradução:"]:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()
    return text


def translate_to_language(
    english_text: str,
    target_lang: LanguageCode = "pt",
) -> str:
    """
    Translate an English answer into the target language.
    The translation should be clear, natural, and theologically accurate.
    """
    if target_lang == "en":
        return english_text

    llm = _get_translator_llm()
    lang_info = get_language(target_lang)

    prompt = f"""You are a precise, literal translator. Your only job is to translate the given English text into {lang_info.native_name} as accurately and neutrally as possible.

CRITICAL RULES - Follow them strictly:
- Translate the text literally and objectively. Do NOT add warmth, friendliness, or pastoral tone.
- Do NOT use any of these expressions in Portuguese:
  - "Meus queridos irmãos", "Amados", "Irmãos", "Queridos", "Meus amados", "Caros irmãos", "Meus irmãos", "Irmão"
- Do NOT rephrase sentences to sound more friendly or caring.
- For statements about not finding information, use only dry, factual language:
  Good examples:
    - "Os sermões disponíveis não abordam diretamente esta questão."
    - "Não há informações suficientes nos trechos consultados."
    - "Os trechos disponíveis não contêm elementos para responder a esta pergunta."
  Bad examples (never use):
    - "Não encontrei..."
    - "Meus queridos irmãos, não encontrei..."
    - Any sentence that starts with a personal or fraternal address.

- Keep the exact meaning and tone of the original English text.
- Use clear, modern, professional Portuguese.

English text to translate:
{english_text}

Output ONLY the {lang_info.native_name} translation. Do not add explanations or notes."""

    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content="You are a precise and literal translator. Follow all instructions exactly. Never add warmth, friendliness, or change the original tone."),
        ChatMessage(role=MessageRole.USER, content=prompt)
    ]
    response = llm.chat(messages)
    text = str(response).strip()
    # Remove common chat prefixes that sometimes appear
    for prefix in ["assistant:", "Assistant:", "Resposta:", "Tradução:"]:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()
    return text


def detect_and_translate_query(question: str, assumed_lang: Optional[LanguageCode] = None) -> tuple[str, LanguageCode]:
    """
    Detects language (if not provided) and translates the question to English if needed.

    Returns:
        (english_question, detected_or_assumed_language)
    """
    from utils.language import detect_language

    lang = assumed_lang or detect_language(question)

    if lang == "en":
        return question, "en"

    english_question = translate_to_english(question, source_lang=lang)
    return english_question, lang
