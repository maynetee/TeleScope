from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
from app.config import get_settings
from typing import Optional
import asyncio
import hashlib

settings = get_settings()


class TranslationService:
    def __init__(self):
        self.target_language = settings.preferred_language
        self.cache = {}  # Simple in-memory cache

    def detect_language(self, text: str) -> str:
        """Detect the language of given text"""
        try:
            if not text or len(text.strip()) < 10:
                return 'unknown'
            return detect(text)
        except LangDetectException:
            return 'unknown'

    def translate_sync(self, text: str, source_lang: Optional[str] = None, target_lang: Optional[str] = None) -> tuple[str, str]:
        """
        Translate text to target language (synchronous).
        Returns (translated_text, source_language)
        """
        if not text or len(text.strip()) == 0:
            return text, 'unknown'

        # Use default target language if not specified
        if not target_lang:
            target_lang = self.target_language

        # Detect source language if not provided
        if not source_lang or source_lang == 'unknown':
            source_lang = self.detect_language(text)

        # Don't translate if already in target language or detection failed
        if source_lang == target_lang or source_lang == 'unknown':
            return text, source_lang

        # Check cache (use MD5 for consistent hashing across sessions)
        text_hash = hashlib.md5(text.encode()).hexdigest()
        cache_key = f"{source_lang}:{target_lang}:{text_hash}"
        if cache_key in self.cache:
            return self.cache[cache_key], source_lang

        try:
            # Use Google Translate via deep-translator
            translator = GoogleTranslator(source=source_lang, target=target_lang)

            # Handle long texts by splitting
            if len(text) > 5000:
                # Split into chunks
                chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
                translated_chunks = [translator.translate(chunk) for chunk in chunks]
                translated_text = ''.join(translated_chunks)
            else:
                translated_text = translator.translate(text)

            # Cache result
            self.cache[cache_key] = translated_text

            return translated_text, source_lang
        except Exception as e:
            print(f"Translation failed: {e}")
            # Return original text if translation fails
            return text, source_lang

    async def translate(self, text: str, source_lang: Optional[str] = None, target_lang: Optional[str] = None) -> tuple[str, str]:
        """
        Translate text to target language (async wrapper).
        Returns (translated_text, source_language)
        """
        # Run synchronous translation in thread pool
        return await asyncio.to_thread(
            self.translate_sync, text, source_lang, target_lang
        )


# Singleton instance
translator = TranslationService()
