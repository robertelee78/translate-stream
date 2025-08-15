"""Soniox provider with real-time multi-language support including Croatian."""

# Standard library imports
import asyncio
import json
import os
import sys
from typing import AsyncGenerator, Any, Dict, Optional

# Third-party imports
import websockets

# Local imports
from .soniox_file_transcriber import (
    convert_mp3_to_wav,
    create_file_audio_generator,
    group_tokens_by_language
)
from .soniox_provider_helpers import (
    build_soniox_config,
    clean_special_tokens,
    normalize_language_code,
    process_regular_tokens,
    process_translation_tokens
)


class SonioxProvider:
    """Soniox provider with real-time streaming and configurable language support."""
    
    def __init__(self, api_key: str, primary_language: str = 'en', foreign_language: str = 'hr', debug: bool = False):
        """Initialize Soniox client."""
        self.api_key = api_key
        self.primary_language = primary_language
        self.foreign_language = foreign_language
        self.debug = debug
        self.websocket_url = "wss://stt-rt.soniox.com/transcribe-websocket"
        
        # Audio configuration
        self.sample_rate = 16000  # Soniox prefers 16kHz
        self.channels = 1
        self.chunk_size = 4096  # Try smaller chunks for better segmentation
        
    async def transcribe_stream(
        self, 
        audio_stream: AsyncGenerator[bytes, None],
        language: Optional[str] = None,
        is_continuous: bool = False,
        translate: bool = False,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Transcribe audio stream using Soniox.
        
        Soniox supports Croatian and can handle multiple languages in the same stream.
        """
        # Build configuration using helper
        config = build_soniox_config(
            api_key=self.api_key,
            is_continuous=is_continuous,
            translate=translate or kwargs.get('translation', False),
            primary_language=self.primary_language,
            foreign_language=self.foreign_language,
            language=language
        )
        
        # Mark translation status for processing
        self._translation_enabled = translate or kwargs.get('translation', False)
        
        try:
            # Connect to Soniox WebSocket
            async with websockets.connect(self.websocket_url) as websocket:
                # Send configuration
                await websocket.send(json.dumps(config))
                
                # Create tasks for sending and receiving
                send_task = asyncio.create_task(self._send_audio(websocket, audio_stream, is_continuous))
                
                # Process transcripts as they come
                async for transcript in self._receive_transcripts(websocket, is_continuous):
                    yield transcript
                    
                # Cancel send task when done
                send_task.cancel()
                try:
                    await send_task
                except asyncio.CancelledError:
                    pass
                
        except Exception as e:
            yield {
                "text": f"[Soniox error: {str(e)}]",
                "language": None,
                "confidence": None,
                "is_final": True,
                "timestamp": None
            }
    
    async def _send_audio(self, websocket, audio_stream, is_continuous=False):
        """Send audio data to Soniox."""
        try:
            chunk_count = 0
            async for chunk in audio_stream:
                # Send raw audio bytes
                await websocket.send(chunk)
                chunk_count += 1
                
                # For continuous streams, yield control periodically
                if is_continuous and chunk_count % 10 == 0:
                    await asyncio.sleep(0.001)  # Tiny yield to allow receive task to run
            
            # Only send finalization for non-continuous streams (files)
            if not is_continuous:
                # After all audio is sent, send finalization message
                await websocket.send(json.dumps({"type": "finalize"}))
                # Wait a bit for final results
                await asyncio.sleep(0.5)
                # Then signal end of stream
                await websocket.send("")  # Empty message signals end
            
        except asyncio.CancelledError:
            # When cancelled (e.g., Ctrl+C), try to close gracefully
            try:
                await websocket.send(json.dumps({"type": "finalize"}))
                await asyncio.sleep(0.1)
                await websocket.send("")
            except websockets.exceptions.ConnectionClosed:
                # Connection already closed, this is expected
                pass
            except Exception as e:
                pass  # Silently ignore cancellation cleanup errors
        except websockets.exceptions.ConnectionClosed as e:
            # Connection was closed by server
            pass  # Connection closed is expected behavior
        except Exception as e:
            # Raise exceptions instead of just printing
            raise RuntimeError(f"Error sending audio: {e}") from e
    
    async def _receive_transcripts(self, websocket, is_continuous=False):
        """Receive and parse transcripts from Soniox."""
        # For continuous mode, track partial text to show updates
        last_partial = ""
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    # Check for error messages
                    if "error" in data or "error_code" in data:
                        error_msg = data.get("error") or data.get("error_message", "Unknown error")
                        yield {
                            "text": f"[Soniox error: {error_msg}]",
                            "language": None,
                            "confidence": None,
                            "is_final": True,
                            "timestamp": None
                        }
                        continue
                    
                    # Process tokens
                    tokens = data.get("tokens", [])
                    if not tokens:
                        continue
                    
                    # For continuous streaming, handle partial and final tokens differently
                    if is_continuous:
                        # When translation is enabled, process tokens individually
                        if self._translation_enabled:
                            # Initialize buffers if needed
                            if not hasattr(self, '_original_buffer'):
                                self._original_buffer = []
                                self._translation_buffer = []
                            
                            # Process translation tokens using helper
                            results, self._original_buffer, self._translation_buffer = process_translation_tokens(
                                tokens, 
                                self._original_buffer, 
                                self._translation_buffer,
                                self.debug
                            )
                            
                            for result in results:
                                yield result
                            
                            continue  # Skip the normal buffering logic
                        
                        # Normal processing without translation - use buffering
                        # Separate final and non-final tokens
                        final_tokens = [t for t in tokens if t.get("is_final", False)]
                        partial_tokens = [t for t in tokens if not t.get("is_final", False)]
                        
                        # Process final tokens - try to accumulate into more complete segments
                        if final_tokens:
                            # Buffer to accumulate tokens into larger segments
                            if not hasattr(self, '_final_buffer'):
                                self._final_buffer = []
                            
                            # Add tokens to buffer
                            self._final_buffer.extend(final_tokens)
                            
                            # Check if we should output (look for sentence endings or long accumulation)
                            accumulated_text = "".join(t.get("text", "") for t in self._final_buffer)
                            
                            # Output if we have a sentence ending or enough accumulated
                            if (accumulated_text.rstrip().endswith(('.', '!', '?', ':', ';')) or 
                                len(self._final_buffer) > 10 or  # Too many tokens accumulated
                                (len(self._final_buffer) > 0 and tokens[-1].get("is_final") and not partial_tokens)):  # Last token is final with no partials
                                
                                # Get language and normalize BS to HR
                                lang = self._final_buffer[0].get("language") if self._final_buffer else None
                                if lang == "bs":  # Bosnian detected, treat as Croatian
                                    lang = "hr"
                                
                                # Check if we have translation mixed in
                                # Soniox seems to concatenate original+translation in same text
                                # We need to detect and split them
                                if hasattr(self, '_translation_enabled') and self._translation_enabled:
                                    # For now, just mark that it contains both
                                    # The text likely contains both original and translation
                                    yield {
                                        "text": accumulated_text,
                                        "language": lang,
                                        "confidence": sum(t.get("confidence", 0) for t in self._final_buffer) / len(self._final_buffer),
                                        "is_final": True,
                                        "timestamp": self._final_buffer[0].get("start_ms", 0) / 1000.0,
                                        "contains_translation": True,
                                        "mixed_format": True  # Indicates original+translation are mixed
                                    }
                                else:
                                    yield {
                                        "text": accumulated_text,
                                        "language": lang,
                                        "confidence": sum(t.get("confidence", 0) for t in self._final_buffer) / len(self._final_buffer),
                                        "is_final": True,
                                        "timestamp": self._final_buffer[0].get("start_ms", 0) / 1000.0
                                    }
                                
                                # Clear buffer after outputting
                                self._final_buffer = []
                        
                        # Process partial tokens as a group
                        if partial_tokens:
                            partial_text = "".join(t.get("text", "") for t in partial_tokens)
                            if partial_text and partial_text != last_partial:
                                last_partial = partial_text
                                yield {
                                    "text": partial_text,
                                    "language": partial_tokens[0].get("language") if partial_tokens else None,
                                    "confidence": None,
                                    "is_final": False,
                                    "timestamp": partial_tokens[0].get("start_ms", 0) / 1000.0 if partial_tokens else 0
                                }
                    else:
                        # For file transcription, process all tokens together
                        text = "".join(token.get("text", "") for token in tokens)
                        if text:
                            yield {
                                "text": text,
                                "language": tokens[0].get("language") if tokens else None,
                                "confidence": sum(t.get("confidence", 0) for t in tokens) / len(tokens) if tokens else None,
                                "is_final": all(t.get("is_final", False) for t in tokens),
                                "timestamp": tokens[0].get("start_ms", 0) / 1000.0 if tokens else 0
                            }
                            
                except json.JSONDecodeError as e:
                    continue  # Skip malformed messages
                except Exception as e:
                    continue  # Skip problematic messages
        except websockets.exceptions.ConnectionClosed as e:
            pass  # Normal closure after end of speech
        except Exception as e:
            # Raise exceptions instead of silent failure
            raise RuntimeError(f"Error receiving transcripts: {e}") from e
    
    def transcribe_file(
        self,
        file_path: str,
        language: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Transcribe an audio file using Soniox by simulating streaming."""
        import asyncio
        import nest_asyncio
        
        # Convert MP3 to WAV if needed
        if file_path.endswith('.mp3'):
            audio_data = convert_mp3_to_wav(file_path, self.sample_rate, self.channels)
        else:
            # Read WAV file directly
            with open(file_path, 'rb') as f:
                audio_data = f.read()
        
        # Create async function to transcribe
        async def _transcribe():
            # Create audio stream generator using helper
            audio_gen = create_file_audio_generator(audio_data, self.chunk_size)
            
            # Collect all final tokens in order
            final_tokens = []
            
            try:
                async for result in self.transcribe_stream(audio_gen, language=language):
                    if result.get("text") and result.get("is_final"):
                        # For final results, collect them properly
                        token_data = {
                            "text": result["text"],
                            "timestamp": result.get("timestamp", 0),
                            "language": result.get("language", None)
                        }
                        final_tokens.append(token_data)
                        
            except Exception as e:
                return {"error": str(e)}
            
            if not final_tokens:
                return {"segments": []}
            
            # Group tokens by language using helper
            segments = group_tokens_by_language(final_tokens)
            return {"segments": segments}
        
        # Run async function synchronously
        import nest_asyncio
        nest_asyncio.apply()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_transcribe())
        finally:
            loop.close()