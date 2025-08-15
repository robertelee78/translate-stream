"""Soniox-only transcription implementation."""

# Standard library imports
import asyncio
import json
import os
import sys
from typing import Optional

# Third-party imports
import pyaudio

# Local imports
from .language_codes import get_language_name
from .providers.soniox_provider import SonioxProvider
from .utils import suppress_alsa_warnings


class SonioxTranscribe:
    """Streamlined Soniox transcription interface."""
    
    def __init__(
        self,
        input_source: str = "mic",
        language: str = "auto",
        output_format: str = "text",
        translate: bool = False,
        primary_language: str = None,
        foreign_language: str = None,
        api_key: Optional[str] = None,
        debug: bool = False
    ):
        self.input_source = input_source
        self.language = language
        self.output_format = output_format
        self.translate = translate
        self.debug = debug
        self.current_message_id = None  # Track message ID for translation pairs
        
        # Get languages from parameters or environment
        self.primary_language = primary_language or os.getenv('PRIMARY_LANGUAGE', 'en')
        self.foreign_language = foreign_language or os.getenv('FOREIGN_LANGUAGE', 'hr')
        
        # Get API key from environment or parameter
        self.api_key = api_key or os.getenv('SONIOX_API_KEY')
        if not self.api_key:
            raise ValueError("Soniox API key required. Set SONIOX_API_KEY environment variable.")
        
        # Initialize Soniox provider with configured languages
        self.provider = SonioxProvider(
            self.api_key, 
            primary_language=self.primary_language,
            foreign_language=self.foreign_language,
            debug=self.debug
        )
    
    async def run(self):
        """Run the transcription."""
        if self.input_source == "mic":
            await self._run_mic_transcription()
        else:
            await self._run_file_transcription(self.input_source)
    
    async def _run_mic_transcription(self):
        """Run microphone transcription."""
        # Output initial configuration message for GUI
        if self.output_format == 'json':
            self._output_config()
        
        # Initialize PyAudio without ALSA warnings
        with suppress_alsa_warnings():
            p = pyaudio.PyAudio()
        
        try:
            # Open microphone stream
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,  # Soniox requires 16kHz
                input=True,
                frames_per_buffer=4096
            )
            
            # Create audio generator
            async def audio_generator():
                try:
                    while True:
                        # Read audio data
                        data = stream.read(4096, exception_on_overflow=False)
                        if data:
                            yield data
                        else:
                            await asyncio.sleep(0.01)
                except KeyboardInterrupt:
                    # Re-raise keyboard interrupt for clean shutdown
                    raise
                except Exception as e:
                    # Always raise other exceptions
                    raise
            
            # Transcribe stream
            async for result in self.provider.transcribe_stream(
                audio_generator(),
                language=self.language,
                is_continuous=True,
                translate=self.translate
            ):
                self._output_result(result)
                
        except KeyboardInterrupt:
            # User interrupted, clean exit
            raise
        except Exception as e:
            # Always raise exceptions for proper error handling
            raise
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
    
    async def _run_file_transcription(self, file_path: str):
        """Run file transcription."""
        # Output initial configuration message for GUI
        if self.output_format == 'json':
            self._output_config()
        
        # Use the provider's file transcription
        result = self.provider.transcribe_file(
            file_path,
            language=self.language
        )
        
        # Handle response
        if isinstance(result, dict):
            if "segments" in result:
                # Output each language segment
                for segment in result["segments"]:
                    self._output_segment(segment)
            elif "error" in result:
                print(f"[Transcription error: {result['error']}]")
            else:
                # Single segment
                self._output_segment({
                    "text": result.get("text", "[No transcription result]"),
                    "language": result.get("language", self.language)
                })
        else:
            # Just text
            self._output_segment({
                "text": result if result else "[No transcription result]",
                "language": self.language
            })
    
    def _output_config(self):
        """Output initial configuration message with language information."""
        config = {
            "type": "config",
            "primary_language": self.primary_language,
            "primary_language_name": get_language_name(self.primary_language),
            "foreign_language": self.foreign_language,
            "foreign_language_name": get_language_name(self.foreign_language),
            "translation_enabled": self.translate
        }
        print(json.dumps(config))
        sys.stdout.flush()
    
    def _output_segment(self, segment: dict):
        """Output a single language segment."""
        transcript = segment.get("text", "")
        language = segment.get("language", self.language)
        
        if self.output_format == "text":
            print(transcript)
            sys.stdout.flush()  # Force immediate output when piped
        elif self.output_format == "json":
            import json
            output = {
                "type": "completed",
                "text": transcript,
                "language": language
            }
            print(json.dumps(output))
            sys.stdout.flush()  # Force immediate output when piped
        elif self.output_format == "csv":
            import time
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f'"{timestamp}","user","{language}","{transcript}","1.0"')
    
    def _output_result(self, result: dict):
        """Output streaming transcription result."""
        if self.output_format == "text":
            text = result.get("text", "").strip()
            if not text:
                return
            
            if result.get("is_final"):
                sys.stdout.write(text)
                sys.stdout.write(" ")
                sys.stdout.flush()  # Already has flush, good!
            
        elif self.output_format == "json":
            # Only output final results
            if result.get("is_final"):
                import json
                import uuid
                
                # Check translation status to manage message IDs
                translation_status = result.get("translation_status")
                
                # Generate or reuse message ID for translation pairs
                if translation_status == "original":
                    # New original message - generate new ID
                    self.current_message_id = str(uuid.uuid4())
                    message_id = self.current_message_id
                elif translation_status == "translation":
                    # Translation - use same ID as original
                    message_id = self.current_message_id
                else:
                    # No translation status - generate new ID
                    message_id = str(uuid.uuid4())
                
                output = {
                    "type": "completed",
                    "text": result["text"],
                    "language": result.get("language", self.language),
                    "confidence": result.get("confidence"),
                    "message_id": message_id  # Include message ID
                }
                
                # Add translation info if present
                if translation_status == "original":
                    output["role"] = "original"
                elif translation_status == "translation":
                    output["role"] = "translation"
                    output["source_language"] = result.get("source_language")
                    if result.get("source_language") and result.get("language"):
                        output["direction"] = f"{result['source_language']}→{result['language']}"
                
                print(json.dumps(output, ensure_ascii=False))
                sys.stdout.flush()  # Force immediate output when piped
            
        elif self.output_format == "csv":
            if result.get("is_final"):
                import time
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                confidence = result.get("confidence", 1.0)
                print(f'"{timestamp}","user","{result.get("language", self.language)}","{result["text"]}","{confidence}"')
                sys.stdout.flush()  # Force immediate output when piped