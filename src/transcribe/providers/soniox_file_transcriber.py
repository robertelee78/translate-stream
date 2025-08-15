"""File transcription utilities for Soniox provider."""

import asyncio
import subprocess
from typing import AsyncGenerator, Dict, Any, List
from .soniox_provider_helpers import clean_special_tokens


async def create_file_audio_generator(
    audio_data: bytes, 
    chunk_size: int
) -> AsyncGenerator[bytes, None]:
    """Create an async generator for file audio data."""
    for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i:i+chunk_size]
        yield chunk
        # Real-time streaming: simulate audio timing
        # 4096 bytes at 16kHz mono = 128ms of audio
        await asyncio.sleep(0.128)


def convert_mp3_to_wav(file_path: str, sample_rate: int, channels: int) -> bytes:
    """Convert MP3 file to WAV format."""
    cmd = [
        'ffmpeg', '-i', file_path,
        '-ar', str(sample_rate),
        '-ac', str(channels),
        '-f', 'wav',
        'pipe:1',
        '-loglevel', 'error'
    ]
    result = subprocess.run(cmd, capture_output=True, check=True)
    return result.stdout


def group_tokens_by_language(tokens: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Group tokens by language to create segments."""
    segments = []
    current_segment = None
    
    for token in tokens:
        # Skip special tokens
        if token["text"] in ["<end>", "<fin>", "</s>", "[END]"]:
            continue
        
        token_lang = token.get("language", "unknown")
        
        if current_segment is None or current_segment["language"] != token_lang:
            # Start new segment
            if current_segment:
                # Clean up and save previous segment
                current_segment["text"] = clean_special_tokens(current_segment["text"].strip())
                segments.append(current_segment)
            
            current_segment = {
                "text": token["text"],
                "language": token_lang
            }
        else:
            # Continue current segment
            current_segment["text"] += " " + token["text"]
    
    # Don't forget the last segment
    if current_segment:
        current_segment["text"] = clean_special_tokens(current_segment["text"].strip())
        segments.append(current_segment)
    
    return segments