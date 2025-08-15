# Translate-Stream

Real-time audio transcription and translation system using Soniox for configurable language pairs.

## Features

- **Real-time transcription** using Soniox WebSocket API
- **Configurable language pairs** (default: English↔Croatian)
- **Bidirectional translation** in the same stream
- **Multiple input sources**: Microphone or audio files (MP3/WAV)
- **Multiple output formats**: Text, JSON, CSV
- **Modern GUI** with dual-panel display (Kivy-based)
- **Live audio visualization** in the GUI

## Architecture

```
Input (Mic/File) → Soniox API → Transcription → Translation → Output (Text/JSON/CSV/GUI)
```

The system uses a modular architecture:
- **Input Layer**: Captures audio from microphone or files
- **Transcription Layer**: Soniox WebSocket API for real-time speech-to-text
- **Translation Layer**: Optional bidirectional translation between language pairs
- **Output Layer**: Multiple format support including GUI visualization

## Quick Start

### 1. Setup Environment

#### Get API Keys

1. **Soniox API Key** (Required for transcription):
   - Sign up at https://soniox.com/
   - Navigate to your dashboard
   - Copy your API key

2. **OpenAI API Key** (Optional - only for GUI translation):
   - Sign up at https://openai.com/
   - Go to https://platform.openai.com/api-keys
   - Create a new API key

#### Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
vi .env
# Add your keys:
# SONIOX_API_KEY=your_actual_soniox_key_here
# OPENAI_API_KEY=your_actual_openai_key_here  # Optional

# Install dependencies
pip install -r requirements.txt
```
### 2. Command Line Usage

```bash
# Basic transcription from microphone
./translate-stream.sh

# Transcribe with translation
./translate-stream.sh --translate

# Transcribe an audio file
./translate-stream.sh -i audio.mp3

# Output as JSON
./translate-stream.sh -o json

# Foreign language mode
./translate-stream.sh -l hr

# Override language configuration (English-French with translation)
./translate-stream.sh --primary-language en --foreign-language fr -i mic -o json -t

# Spanish-German transcription with translation
./translate-stream.sh --primary-language es --foreign-language de -i mic -o json -t

# Use environment defaults (from .env file)
./translate-stream.sh -i mic -o json -t

```

### 3. GUI Usage

```bash
# Run the GUI application
cd translation_gui
python main.py
```

## Project Structure

```
translate-stream/
├── translate-stream.sh          # Main entry point script
├── src/transcribe/
│   ├── __main__.py              # CLI interface
│   ├── soniox_transcribe.py    # Soniox implementation
│   ├── text_translator.py      # OpenAI translation (GUI only)
│   └── providers/
│       └── soniox_provider.py  # Soniox WebSocket handler
└── translation_gui/
    ├── main.py                  # GUI application
    └── widgets/                 # Custom Kivy widgets
```

## Output Formats

### Text Format (default)
```
Hello, this is a test.
```

### JSON Format
```json
{
  "type": "completed",
  "text": "Hello, this is a test.",
  "language": "en",
  "confidence": 0.95,
  "message_id": "msg_123",
  "role": "original"
}
```

## Language Configuration

The system supports any language pair that Soniox supports. Common examples:

| Primary | Foreign | Use Case |
|---------|---------|----------|
| en | hr | English-Croatian (default) |
| en | es | English-Spanish |
| en | de | English-German |
| en | fr | English-French |
| es | pt | Spanish-Portuguese |
| de | nl | German-Dutch |

You can configure languages in three ways:
1. **Environment variables** in `.env` file (recommended)
2. **Command-line options** `--primary-language` and `--foreign-language`
3. **Default fallback** to English-Croatian if not configured

### Translation Output
When using `--translate`, you get both original and translated text:
```json
{
  "type": "completed",
  "text": "Hello",
  "language": "en",
  "role": "original",
  "message_id": "msg_123"
}
{
  "type": "completed", 
  "text": "Pozdrav",
  "language": "hr",
  "role": "translation",
  "message_id": "msg_123"
}
```

## Requirements

- Python 3.8+
- FFmpeg (for audio conversion)
- PyAudio (microphone access)
- Soniox API key
- OpenAI API key (only for GUI translation features)

## Installation

### Prerequisites

1. **Python 3.8+**
   ```bash
   python3 --version
   ```

2. **FFmpeg** (for audio processing)
   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

3. **PyAudio dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install portaudio19-dev python3-pyaudio
   
   # macOS
   brew install portaudio
   
   # Windows
   # PyAudio wheel will be installed automatically
   ```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

### GUI Dependencies (Optional)

For the GUI interface:
```bash
pip install -r translation_gui/requirements.txt
```

## API Keys Setup

### Soniox (Required)
1. Go to https://soniox.com/
2. Click "Sign Up" or "Get Started"
3. Complete registration
4. Navigate to your dashboard/account settings
5. Find and copy your API key
6. Add to `.env`: `SONIOX_API_KEY=your_key_here`

### OpenAI (Optional - for GUI translation)
1. Go to https://openai.com/
2. Sign up or log in
3. Visit https://platform.openai.com/api-keys
4. Click "Create new secret key"
5. Copy the key immediately (it won't be shown again)
6. Add to `.env`: `OPENAI_API_KEY=your_key_here`

**Note**: The OpenAI key is only required if you want to use the GUI's translation feature. The basic transcription works with just the Soniox key.

## Troubleshooting

### Common Issues

1. **PyAudio installation fails**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-pyaudio
   
   # macOS
   brew install portaudio
   pip install pyaudio
   ```

2. **FFmpeg not found**
   - Ensure FFmpeg is in your PATH
   - Test with: `ffmpeg -version`

3. **Microphone permissions**
   - macOS: System Preferences → Security & Privacy → Microphone
   - Windows: Settings → Privacy → Microphone
   - Linux: Check PulseAudio/ALSA settings

4. **GUI issues**
   - Ensure Kivy is properly installed: `pip install kivy[base]`
   - For high-DPI displays, set: `export KIVY_DPI=96`

## Performance Tips

- **Reduce latency**: Use wired internet connection
- **Improve accuracy**: Use a good quality microphone
- **Optimize for your language**: Set language hints in `.env`
- **GUI performance**: Reduce animation FPS if needed

## Notes

- Soniox works best with 16kHz audio
- The system supports real-time streaming with low latency
- Translation is bidirectional and automatic
- Supports over 30 languages (see LANGUAGE_CODES.md)

## Contributing

Contributions are welcome! Please ensure:
1. Code follows existing style conventions
2. All tests pass
3. Documentation is updated
4. No API keys or secrets are committed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

The MIT License is a permissive license that allows:
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use

With minimal requirements:
- Include the original copyright notice
- Include a copy of the license
