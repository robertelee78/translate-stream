#!/usr/bin/env python3
"""
Soniox transcription tool for real-time multilingual transcription.

Usage:
    transcribe [OPTIONS]
    transcribe audio.mp3
    transcribe --translate

Options:
    -i, --input      Input source: 'mic' (default) or file path
    -l, --language   Language hint: auto (default) or specific language code
    -o, --output     Output format: text (default), json, csv
    -t, --translate  Enable bidirectional translation
    --primary-language    Primary language code (default from env: PRIMARY_LANGUAGE)
    --foreign-language    Foreign language code (default from env: FOREIGN_LANGUAGE)
    --help           Show this help message
"""

# Standard library imports
import asyncio
import os
import sys

# Third-party imports
import click
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@click.command()
@click.option('-i', '--input', 'input_source', default='mic',
              help='Input source: mic (default) or file path')
@click.option('-l', '--language', default='auto',
              help='Language hint: auto (default) or specific language code')
@click.option('-o', '--output', type=click.Choice(['text', 'json', 'csv']), default='text',
              help='Output format')
@click.option('-t', '--translate', is_flag=True,
              help='Enable bidirectional translation')
@click.option('--primary-language', envvar='PRIMARY_LANGUAGE',
              help='Primary language code (e.g., en, es, fr)')
@click.option('--foreign-language', envvar='FOREIGN_LANGUAGE',
              help='Foreign language code (e.g., hr, de, it)')
@click.option('--api-key', envvar='SONIOX_API_KEY',
              help='Soniox API key (or set SONIOX_API_KEY env var)')
@click.option('--debug', is_flag=True,
              help='Enable debug output')
def main(input_source, language, output, translate, primary_language, foreign_language, api_key, debug):
    """Real-time transcription using Soniox with configurable language support."""
    
    from .soniox_transcribe import SonioxTranscribe
    
    # Use defaults from environment if not provided
    primary_lang = primary_language or os.getenv('PRIMARY_LANGUAGE', 'en')
    foreign_lang = foreign_language or os.getenv('FOREIGN_LANGUAGE', 'hr')
    
    # Create transcription instance
    stream = SonioxTranscribe(
        input_source=input_source,
        language=language,
        output_format=output,
        translate=translate,
        primary_language=primary_lang,
        foreign_language=foreign_lang,
        api_key=api_key,
        debug=debug
    )
    
    # Run the async stream
    try:
        asyncio.run(stream.run())
    except KeyboardInterrupt:
        # Silent exit on Ctrl+C
        pass
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()