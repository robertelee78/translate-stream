"""Text translation module using OpenAI API for configurable language pairs."""

import os
import json
from typing import Optional, Tuple
from openai import OpenAI


class TextTranslator:
    """Translate text between configured language pairs using OpenAI GPT-5."""
    
    def __init__(self, api_key: Optional[str] = None, 
                 primary_language: Optional[str] = None,
                 foreign_language: Optional[str] = None,
                 primary_language_name: Optional[str] = None,
                 foreign_language_name: Optional[str] = None):
        """Initialize OpenAI client."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.getenv('DEFAULT_TRANSLATE_MODEL', 'gpt-5')
        
        # Use ONLY the parameters passed in - NO environment variables for languages!
        # The GUI gets everything from JSON, not environment
        self.primary_language = primary_language if primary_language is not None else 'en'
        self.foreign_language = foreign_language if foreign_language is not None else 'hr'
        self.primary_language_name = primary_language_name if primary_language_name is not None else 'English'
        self.foreign_language_name = foreign_language_name if foreign_language_name is not None else 'Croatian'
    
    def detect_language(self, text: str) -> str:
        """Detect if text is primary or foreign language."""
        # For Croatian, check for specific characters
        if self.foreign_language == 'hr':
            croatian_chars = set('čćžšđČĆŽŠĐ')
            if any(char in croatian_chars for char in text):
                return self.foreign_language
        
        # Use GPT for more accurate detection
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for detection
                messages=[
                    {"role": "system", "content": f"You are a language detector. Reply with ONLY '{self.primary_language}' for {self.primary_language_name} or '{self.foreign_language}' for {self.foreign_language_name}."},
                    {"role": "user", "content": f"What language is this: {text[:100]}"}  # First 100 chars
                ],
                temperature=0,
                max_tokens=5
            )
            
            result = response.choices[0].message.content.strip().lower()
            return self.foreign_language if self.foreign_language in result else self.primary_language
        except:
            # Default to primary language if detection fails
            return self.primary_language
    
    def translate(self, text: str, source_lang: Optional[str] = None, target_lang: Optional[str] = None) -> Tuple[str, str, str]:
        """
        Translate text between configured language pairs.
        
        Args:
            text: Text to translate
            source_lang: Source language, auto-detected if None
            target_lang: Target language, auto-determined if None
            
        Returns:
            Tuple of (translated_text, source_language, target_language)
        """
        # Detect source language if not provided
        if not source_lang:
            source_lang = self.detect_language(text)
        
        # Determine target language
        if not target_lang:
            target_lang = self.foreign_language if source_lang == self.primary_language else self.primary_language
        
        # Skip if source and target are the same
        if source_lang == target_lang:
            return text, source_lang, target_lang
        
        # Determine language names for prompt
        source_name = self.primary_language_name if source_lang == self.primary_language else self.foreign_language_name
        target_name = self.foreign_language_name if target_lang == self.foreign_language else self.primary_language_name
        
        # Set up translation prompt
        system_prompt = f"You are a professional {source_name} to {target_name} translator. Translate the following text accurately and naturally to {target_name}. Reply with ONLY the translation, no explanations."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,  # Low temperature for consistent translations
                max_tokens=500
            )
            
            translated = response.choices[0].message.content.strip()
            return translated, source_lang, target_lang
            
        except Exception as e:
            # Return error message but don't crash
            return f"[Translation error: {str(e)}]", source_lang, target_lang
    
    def translate_for_gui(self, text: str, input_language: str) -> dict:
        """
        Translate text and format for GUI display.
        
        Args:
            text: Text to translate
            input_language: Language of input panel ('en' or 'hr')
            
        Returns:
            Dict with messages for both panels
        """
        # Translate the text
        translated, detected_lang, target_lang = self.translate(text, source_lang=input_language)
        
        # Format for GUI - original goes to input panel, translation to other panel
        result = {
            'original': {
                'text': text,
                'language': input_language,
                'role': 'original'
            },
            'translation': {
                'text': translated,
                'language': target_lang,
                'role': 'translation'
            }
        }
        
        return result


# Singleton instance
_translator = None

def get_translator():
    """Get or create the singleton translator instance."""
    global _translator
    if _translator is None:
        _translator = TextTranslator()
    return _translator
