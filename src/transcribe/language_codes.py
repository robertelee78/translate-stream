"""Language code to name mappings."""

# ISO 639-1 language code to name mapping
LANGUAGE_NAMES = {
    # European Languages
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'nl': 'Dutch',
    'el': 'Greek',
    'hr': 'Croatian',
    'sr': 'Serbian',
    'bg': 'Bulgarian',
    'ro': 'Romanian',
    'hu': 'Hungarian',
    'cs': 'Czech',
    'sk': 'Slovak',
    'pl': 'Polish',
    'sv': 'Swedish',
    'no': 'Norwegian',
    'da': 'Danish',
    'fi': 'Finnish',
    'et': 'Estonian',
    'lv': 'Latvian',
    'lt': 'Lithuanian',
    'sl': 'Slovenian',
    'mk': 'Macedonian',
    'sq': 'Albanian',
    'is': 'Icelandic',
    'ga': 'Irish',
    'cy': 'Welsh',
    'eu': 'Basque',
    'ca': 'Catalan',
    'gl': 'Galician',
    
    # Asian Languages
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'hi': 'Hindi',
    'ar': 'Arabic',
    'he': 'Hebrew',
    'tr': 'Turkish',
    'th': 'Thai',
    'vi': 'Vietnamese',
    'id': 'Indonesian',
    'ms': 'Malay',
    'tl': 'Filipino',
    'ur': 'Urdu',
    'fa': 'Persian',
    'bn': 'Bengali',
    'ta': 'Tamil',
    'te': 'Telugu',
    'mr': 'Marathi',
    'gu': 'Gujarati',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'pa': 'Punjabi',
    'ne': 'Nepali',
    'si': 'Sinhala',
    'km': 'Khmer',
    'lo': 'Lao',
    'my': 'Burmese',
    'ka': 'Georgian',
    'hy': 'Armenian',
    'az': 'Azerbaijani',
    'kk': 'Kazakh',
    'ky': 'Kyrgyz',
    'uz': 'Uzbek',
    'tg': 'Tajik',
    'mn': 'Mongolian',
    
    # African Languages
    'sw': 'Swahili',
    'af': 'Afrikaans',
    'am': 'Amharic',
    'ha': 'Hausa',
    'yo': 'Yoruba',
    'ig': 'Igbo',
    'zu': 'Zulu',
    'xh': 'Xhosa',
    'st': 'Sotho',
    'rw': 'Kinyarwanda',
    'so': 'Somali',
    
    # Other Languages
    'ru': 'Russian',
    'uk': 'Ukrainian',
    'be': 'Belarusian',
    'eo': 'Esperanto',
    'mt': 'Maltese',
    'lb': 'Luxembourgish',
    'yi': 'Yiddish',
    'gd': 'Scottish Gaelic',
    'br': 'Breton',
    'fo': 'Faroese',
    'la': 'Latin',
}

def get_language_name(code: str) -> str:
    """Get the language name for a given ISO 639-1 code.
    
    Args:
        code: ISO 639-1 language code (e.g., 'en', 'es', 'fr')
        
    Returns:
        Language name (e.g., 'English', 'Spanish', 'French')
        If code not found, returns the code itself capitalized.
    """
    return LANGUAGE_NAMES.get(code.lower(), code.upper())