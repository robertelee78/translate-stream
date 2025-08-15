"""Helper functions for Soniox provider."""

import sys
from typing import Dict, Any, List


def build_soniox_config(
    api_key: str,
    is_continuous: bool,
    translate: bool,
    primary_language: str,
    foreign_language: str,
    language: str = None
) -> Dict[str, Any]:
    """Build Soniox WebSocket configuration."""
    config = {
        "api_key": api_key,
        "model": "stt-rt-preview",
        "audio_format": "pcm_s16le" if is_continuous else "auto",
        "enable_speaker_diarization": False,
        "enable_non_final_tokens": True,
        "enable_endpoint_detection": not is_continuous,
        "enable_language_identification": True,
        "enable_automatic_punctuation": True,
        "enable_profanity_filter": False
    }
    
    # Add translation if requested
    if translate:
        config["translation"] = {
            "type": "two_way",
            "language_a": primary_language,
            "language_b": foreign_language
        }
    
    # Add PCM configuration when using microphone
    if is_continuous:
        config["num_channels"] = 1
        config["sample_rate"] = 16000
        config["speech_threshold"] = 0.5
        config["max_silence_ms"] = 2000
        config["silence_timeout_ms"] = 60000
        config["max_non_final_tokens_duration_ms"] = 4000
    
    # Handle language settings
    if language == "auto":
        config["language_hints"] = [primary_language, foreign_language]
    elif language == foreign_language:
        config["language_hints"] = [foreign_language]
    elif language == primary_language:
        config["language_hints"] = [primary_language]
    elif language:
        config["language_hints"] = [language]
    else:
        config["language_hints"] = [primary_language, foreign_language]
    
    return config


def process_translation_tokens(
    tokens: List[Dict[str, Any]],
    original_buffer: List[str],
    translation_buffer: List[str],
    debug: bool = False
) -> tuple[List[Dict[str, Any]], List[str], List[str]]:
    """Process tokens with translation status."""
    results = []
    
    for token in tokens:
        if not token.get("text"):
            continue
        
        translation_status = token.get("translation_status", "none")
        is_final = token.get("is_final", False)
        
        if translation_status == "original" and is_final:
            original_buffer.append(token["text"])
            text = "".join(original_buffer)
            
            if text.rstrip().endswith(('.', '!', '?', ',', ':')):
                lang = normalize_language_code(token.get("language"))
                results.append({
                    "text": text,
                    "language": lang,
                    "confidence": token.get("confidence"),
                    "is_final": True,
                    "timestamp": token.get("start_ms", 0) / 1000.0 if "start_ms" in token else None,
                    "translation_status": "original"
                })
                original_buffer.clear()
        
        elif translation_status == "translation" and is_final:
            translation_buffer.append(token["text"])
            text = "".join(translation_buffer)
            
            if text.rstrip().endswith(('.', '!', '?', ',', ':')):
                lang = normalize_language_code(token.get("language"))
                results.append({
                    "text": text,
                    "language": lang,
                    "confidence": token.get("confidence"),
                    "is_final": True,
                    "timestamp": token.get("start_ms", 0) / 1000.0 if "start_ms" in token else None,
                    "translation_status": "translation",
                    "source_language": token.get("source_language")
                })
                translation_buffer.clear()
    
    return results, original_buffer, translation_buffer


def process_regular_tokens(
    tokens: List[Dict[str, Any]],
    final_buffer: List[Dict[str, Any]]
) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Process regular tokens without translation."""
    result = None
    
    # Separate final and non-final tokens
    final_tokens = [t for t in tokens if t.get("is_final", False)]
    
    if final_tokens:
        final_buffer.extend(final_tokens)
        accumulated_text = "".join(t.get("text", "") for t in final_buffer)
        
        # Output if we have a sentence ending or enough accumulated
        if (accumulated_text.rstrip().endswith(('.', '!', '?', ':', ';')) or 
            len(final_buffer) > 10):
            
            lang = normalize_language_code(final_buffer[0].get("language") if final_buffer else None)
            
            result = {
                "text": accumulated_text,
                "language": lang,
                "confidence": sum(t.get("confidence", 0) for t in final_buffer) / len(final_buffer),
                "is_final": True,
                "timestamp": final_buffer[0].get("start_ms", 0) / 1000.0
            }
            final_buffer = []
    
    return result, final_buffer


def normalize_language_code(language: str) -> str:
    """Normalize language codes (e.g., BS to HR)."""
    if language == "bs":  # Bosnian detected, treat as Croatian
        return "hr"
    return language


def clean_special_tokens(text: str) -> str:
    """Remove special tokens from text."""
    special_tokens = ["<end>", "<fin>", "</s>", "[END]"]
    for token in special_tokens:
        text = text.replace(token, "").strip()
    return text