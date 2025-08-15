#!/usr/bin/env python3
"""
Translation GUI Launcher Script
Easy way to start the Kivy translation interface
"""

import sys
import os
from pathlib import Path

# Add the parent directory to Python path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Set environment variables for better Kivy performance
os.environ['KIVY_WINDOW'] = 'sdl2'
os.environ['KIVY_GL_BACKEND'] = 'gl'

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []

    try:
        import kivy
    except ImportError:
        missing_deps.append('kivy')

    try:
        import pyaudio
    except ImportError:
        print("Warning: PyAudio not found. Audio recording may not work.")
        print("Install with: pip install PyAudio")

    try:
        import numpy
    except ImportError:
        missing_deps.append('numpy')

    if missing_deps:
        print(f"Missing required dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install -r requirements.txt")
        return False

    return True

def main():
    """Main launcher function"""
    print("🚀 Starting Translation GUI...")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Import and run the main app
    try:
        from main import TranslationApp

        print("✅ Dependencies OK")
        print("📱 Launching Kivy GUI...")
        print("🎤 Click 'Start Recording' to begin translation")
        print("🔄 Toggle language with English/Croatian buttons")
        print("🗑️ Use Clear button to reset conversations")
        print("⚙️ Press Ctrl+C to exit")
        print()

        # Run the app
        app = TranslationApp()
        app.run()

    except KeyboardInterrupt:
        print("\n👋 Translation GUI closed by user")
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        print("💡 Make sure you're in the translation_gui directory")
        print("💡 Install dependencies: pip install -r requirements.txt")
        sys.exit(1)

if __name__ == '__main__':
    main()