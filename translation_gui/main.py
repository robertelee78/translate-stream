"""
Modern Kivy Translation GUI with Media Center Interface
Supports dual-panel layout with smooth animations and message bubbles
"""

# Standard library imports
import argparse
import asyncio
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Third-party imports
from dotenv import load_dotenv

# Local imports
from src.transcribe.logger import Logger

# Load environment variables
load_dotenv()

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.animation import Animation
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.metrics import dp
from kivy.utils import get_color_from_hex

# Import custom widgets
from widgets.message_bubble import MessageBubble
from widgets.conversation_panel import ConversationPanel
from widgets.audio_visualizer import AudioVisualizer

# Configure Kivy for modern UI
Config.set('graphics', 'width', '1400')
Config.set('graphics', 'height', '900')
Config.set('graphics', 'minimum_width', '1000')
Config.set('graphics', 'minimum_height', '600')


class TranslationInterface(BoxLayout):
    """Main translation interface with dual panels and controls"""

    # Theme colors (Material Design inspired)
    bg_primary = get_color_from_hex('#121212')      # Dark background
    bg_secondary = get_color_from_hex('#1E1E1E')    # Card background
    accent_blue = get_color_from_hex('#2196F3')     # Primary accent
    accent_teal = get_color_from_hex('#009688')     # Secondary accent
    text_primary = get_color_from_hex('#FFFFFF')    # Primary text
    text_secondary = get_color_from_hex('#B0B0B0')  # Secondary text
    success_color = get_color_from_hex('#4CAF50')   # Success/recording
    error_color = get_color_from_hex('#F44336')     # Error/stop

    def __init__(self, debug: bool = False, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        # Initialize logger
        self.logger = Logger(debug=debug)

        # Initialize with defaults - will be updated from JSON config
        self.primary_language = 'en'
        self.foreign_language = 'hr'
        self.primary_language_name = 'English'
        self.foreign_language_name = 'Croatian'

        # State management
        self.is_recording = False
        self.current_process = None
        self.message_queue = []

        # Create UI components
        self.create_header()
        self.create_main_content()
        self.create_footer()

        # Set background
        with self.canvas.before:
            Color(*self.bg_primary)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)

        self.bind(size=self.update_bg, pos=self.update_bg)

        # Schedule message processing
        Clock.schedule_interval(self.process_message_queue, 1/60)  # 60 FPS

    def update_bg(self, *args):
        """Update background rectangle"""
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

    def create_header(self):
        """Create the top header with controls and status"""
        header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(80),
            padding=[dp(20), dp(10)]
        )

        # Add background
        with header.canvas.before:
            Color(*self.bg_secondary)
            self.header_bg = RoundedRectangle(
                size=header.size,
                pos=header.pos,
                radius=[dp(10)]
            )

        header.bind(size=self.update_header_bg, pos=self.update_header_bg)

        # Title and status
        title_layout = BoxLayout(orientation='vertical', size_hint=(0.4, 1))

        title_label = Label(
            text='Real-Time Translation',
            font_size=dp(24),
            color=self.text_primary,
            halign='left',
            text_size=(None, None)
        )
        title_label.bind(size=title_label.setter('text_size'))

        self.status_label = Label(
            text='Ready to translate',
            font_size=dp(14),
            color=self.text_secondary,
            halign='left'
        )

        title_layout.add_widget(title_label)
        title_layout.add_widget(self.status_label)

        # Control buttons
        controls = BoxLayout(orientation='horizontal', size_hint=(0.6, 1), spacing=dp(10))

        # Language selector
        lang_layout = BoxLayout(orientation='horizontal', size_hint=(0.4, 1), spacing=dp(5))

        self.en_button = ToggleButton(
            text=self.primary_language_name,
            group='source_lang',
            state='down',
            background_normal='',
            background_down='',
            background_color=self.accent_blue,
            color=self.text_primary
        )

        self.hr_button = ToggleButton(
            text=self.foreign_language_name,
            group='source_lang',
            background_normal='',
            background_down='',
            background_color=self.accent_teal,
            color=self.text_primary
        )

        lang_layout.add_widget(self.en_button)
        lang_layout.add_widget(self.hr_button)

        # Record button
        self.record_button = Button(
            text='🎤 Start Recording',
            size_hint=(0.3, 1),
            background_normal='',
            background_color=self.success_color,
            color=self.text_primary,
            font_size=dp(16)
        )
        self.record_button.bind(on_press=self.toggle_recording)

        # Clear button
        clear_button = Button(
            text='🗑️ Clear',
            size_hint=(0.15, 1),
            background_normal='',
            background_color=self.error_color,
            color=self.text_primary
        )
        clear_button.bind(on_press=self.clear_conversations)

        # Settings button
        settings_button = Button(
            text='⚙️',
            size_hint=(0.15, 1),
            background_normal='',
            background_color=self.bg_secondary,
            color=self.text_primary
        )

        controls.add_widget(lang_layout)
        controls.add_widget(self.record_button)
        controls.add_widget(clear_button)
        controls.add_widget(settings_button)

        header.add_widget(title_layout)
        header.add_widget(controls)

        self.add_widget(header)

    def update_header_bg(self, instance, *args):
        """Update header background"""
        self.header_bg.size = instance.size
        self.header_bg.pos = instance.pos

    def create_main_content(self):
        """Create the dual-panel conversation area"""
        main_content = BoxLayout(
            orientation='horizontal',
            padding=[dp(20), dp(10)],
            spacing=dp(20)
        )

        # Left panel - Original language
        left_panel = BoxLayout(orientation='vertical', spacing=dp(10))

        # Primary language header
        en_header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50)
        )

        self.en_flag_label = Label(
            text='🇺🇸',
            size_hint=(None, 1),
            width=dp(40),
            font_size=dp(24)
        )

        self.en_title_label = Label(
            text=self.primary_language_name,
            color=self.text_primary,
            font_size=dp(18),
            halign='left'
        )
        self.en_title_label.bind(size=self.en_title_label.setter('text_size'))

        # Audio visualizer for primary language
        self.en_visualizer = AudioVisualizer(
            size_hint=(None, 1),
            width=dp(100),
            color=self.accent_blue
        )

        en_header.add_widget(self.en_flag_label)
        en_header.add_widget(self.en_title_label)
        en_header.add_widget(self.en_visualizer)

        # Primary language conversation panel
        self.en_panel = ConversationPanel(
            language=self.primary_language,
            accent_color=self.accent_blue,
            bg_color=self.bg_secondary
        )

        left_panel.add_widget(en_header)
        left_panel.add_widget(self.en_panel)

        # Right panel - Target language
        right_panel = BoxLayout(orientation='vertical', spacing=dp(10))

        # Foreign language header
        hr_header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50)
        )

        self.hr_flag_label = Label(
            text='🇭🇷',
            size_hint=(None, 1),
            width=dp(40),
            font_size=dp(24)
        )

        self.hr_title_label = Label(
            text=self.foreign_language_name,
            color=self.text_primary,
            font_size=dp(18),
            halign='left'
        )
        self.hr_title_label.bind(size=self.hr_title_label.setter('text_size'))

        # Audio visualizer for foreign language
        self.hr_visualizer = AudioVisualizer(
            size_hint=(None, 1),
            width=dp(100),
            color=self.accent_teal
        )

        hr_header.add_widget(self.hr_flag_label)
        hr_header.add_widget(self.hr_title_label)
        hr_header.add_widget(self.hr_visualizer)

        # Foreign language conversation panel
        self.hr_panel = ConversationPanel(
            language=self.foreign_language,
            accent_color=self.accent_teal,
            bg_color=self.bg_secondary
        )

        right_panel.add_widget(hr_header)
        right_panel.add_widget(self.hr_panel)

        main_content.add_widget(left_panel)
        main_content.add_widget(right_panel)

        self.add_widget(main_content)

    def create_footer(self):
        """Create footer with statistics and info"""
        footer = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40),
            padding=[dp(20), dp(5)]
        )

        # Connection status
        self.connection_label = Label(
            text='● Disconnected',
            color=self.error_color,
            size_hint=(0.25, 1),
            font_size=dp(12),
            halign='left'
        )

        # Message counts
        self.stats_label = Label(
            text='Messages: 0 EN, 0 HR',
            color=self.text_secondary,
            size_hint=(0.5, 1),
            font_size=dp(12),
            halign='center'
        )

        # Version info
        version_label = Label(
            text='Translation GUI v1.0',
            color=self.text_secondary,
            size_hint=(0.25, 1),
            font_size=dp(12),
            halign='right'
        )

        footer.add_widget(self.connection_label)
        footer.add_widget(self.stats_label)
        footer.add_widget(version_label)

        self.add_widget(footer)

    def toggle_recording(self, instance):
        """Toggle recording state"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start recording and transcription"""
        # Only start if not already recording
        if self.is_recording:
            return

        self.is_recording = True
        self.record_button.text = '⏹️ Stop Recording'
        self.record_button.background_color = self.error_color
        self.status_label.text = 'Recording and translating...'
        self.connection_label.text = '● Connected'
        self.connection_label.color = self.success_color

        # Start audio visualizers
        self.en_visualizer.start_animation()

        # Start transcription process in background thread
        source_lang = 'en' if self.en_button.state == 'down' else 'hr'
        self.transcription_thread = threading.Thread(
            target=self.run_transcription,
            args=(source_lang,),
            daemon=True
        )
        self.transcription_thread.start()

    def stop_recording(self):
        """Stop recording"""
        self.is_recording = False
        self.record_button.text = '🎤 Start Recording'
        self.record_button.background_color = self.success_color
        self.status_label.text = 'Ready to translate'
        self.connection_label.text = '● Disconnected'
        self.connection_label.color = self.error_color

        # Stop audio visualizers
        self.en_visualizer.stop_animation()
        self.hr_visualizer.stop_animation()

        # Terminate process if running
        if self.current_process:
            self.logger.debug_log("Terminating process {}", self.current_process.pid)
            self.current_process.terminate()
            try:
                self.current_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.logger.debug_log("Force killing process {}", self.current_process.pid)
                self.current_process.kill()
            self.current_process = None

    def run_transcription(self, source_lang: str):
        """Run transcription process in background"""
        try:
            # Build command for transcription with translation
            # Using the actual translate-stream.sh script
            cmd = [
                './translate-stream.sh',
                '-t',  # Enable translation
                '-i', 'mic',  # Input from microphone
                '-o', 'json'  # JSON output format
            ]

            # Debug: Print command and working directory
            project_root = Path(__file__).parent.parent
            self.logger.debug_log("Running command: {}", ' '.join(cmd))
            self.logger.debug_log("Working directory: {}", project_root)

            # Start process
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=project_root  # Go to project root
            )

            # Also monitor stderr for errors
            def read_stderr():
                for line in self.current_process.stderr:
                    self.logger.debug_log("stderr: {}", line.strip())
                    if "error" in line.lower() or "exception" in line.lower():
                        self.message_queue.append({
                            'type': 'error',
                            'text': f'Backend error: {line.strip()}',
                            'language': source_lang
                        })

            import threading
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            stderr_thread.start()

            # Read output line by line - simple approach that works
            self.logger.debug_log("Waiting for transcription output...")

            # Process stdout line by line
            for line in iter(self.current_process.stdout.readline, ''):
                if not self.is_recording:
                    break

                line = line.strip()
                if line:
                    self.logger.debug_log("stdout: {}", line)
                    try:
                        message = json.loads(line)
                        self.logger.debug_log("Parsed message: {}", message)
                        self.message_queue.append(message)
                    except json.JSONDecodeError as e:
                        self.logger.debug_log("JSON decode error: {} for line: {}", e, line)

                # Check if process has terminated
                if self.current_process.poll() is not None:
                    break

        except Exception as e:
            # Handle errors by updating UI
            self.logger.error("Exception in run_transcription: {}", e)
            self.message_queue.append({
                'type': 'error',
                'text': f'Transcription error: {str(e)}',
                'language': source_lang
            })

    def process_message_queue(self, dt):
        """Process queued messages from transcription thread"""
        while self.message_queue:
            message = self.message_queue.pop(0)
            self.handle_transcription_message(message)

    def handle_transcription_message(self, message: Dict[str, Any]):
        """Handle incoming transcription messages"""
        msg_type = message.get('type')

        # Handle configuration message
        if msg_type == 'config':
            self.update_language_config(message)
            return

        text = message.get('text', '')
        language = message.get('language', 'en')
        role = message.get('role', 'original')
        confidence = message.get('confidence', 1.0)
        direction = message.get('direction', '')

        if msg_type == 'completed' and text.strip():
            # Handle based on role (original or translation)
            if role == 'original':
                # Original speech - add to panel based on language
                if language == self.primary_language:
                    self.en_panel.add_message(text, 'original', confidence)
                    # Show foreign language visualizer is waiting for translation
                    self.hr_visualizer.pulse_once()
                elif language == self.foreign_language:
                    self.hr_panel.add_message(text, 'original', confidence)
                    # Show primary language visualizer is waiting for translation
                    self.en_visualizer.pulse_once()

            elif role == 'translation':
                # Translation - add to opposite panel
                source_lang = message.get('source_language', '')
                if language == self.primary_language:
                    # Foreign -> Primary translation
                    self.en_panel.add_message(text, 'translation', confidence)
                    self.en_visualizer.stop_animation()
                elif language == self.foreign_language:
                    # Primary -> Foreign translation
                    self.hr_panel.add_message(text, 'translation', confidence)
                    self.hr_visualizer.stop_animation()

            # Update statistics
            self.update_stats()

        elif msg_type == 'error':
            # Show error message
            self.status_label.text = f'Error: {text}'
            self.status_label.color = self.error_color

    def add_translated_message(self, original_text: str, from_lang: str, to_lang: str):
        """Add translated message (simulation)"""
        # In real implementation, call translation API here
        # For demo, we'll just add a placeholder translation

        if to_lang == self.foreign_language:
            # Add to foreign language panel
            translated_text = f"[Translated from {self.primary_language_name}] {original_text}"
            self.hr_panel.add_message(translated_text, 'translation')
            self.hr_visualizer.stop_animation()
        else:
            # Add to primary language panel
            translated_text = f"[Translated from {self.foreign_language_name}] {original_text}"
            self.en_panel.add_message(translated_text, 'translation')
            self.en_visualizer.stop_animation()

        self.update_stats()

    def clear_conversations(self, instance):
        """Clear all messages from both panels"""
        self.en_panel.clear_messages()
        self.hr_panel.clear_messages()
        self.update_stats()

    def update_language_config(self, config: Dict[str, Any]):
        """Update GUI based on language configuration from stream"""
        # Update language settings
        self.primary_language = config.get('primary_language', 'en')
        self.foreign_language = config.get('foreign_language', 'hr')
        self.primary_language_name = config.get('primary_language_name', 'English')
        self.foreign_language_name = config.get('foreign_language_name', 'Croatian')

        # Update panel headers with new language names
        self.update_panel_headers()

        # Translate UI labels using OpenAI
        self.translate_ui_labels()

        # Update stats display
        self.update_stats()

        self.logger.debug_log("Language config updated - Primary: {} ({}), Foreign: {} ({})",
                             self.primary_language_name, self.primary_language,
                             self.foreign_language_name, self.foreign_language)

    def update_panel_headers(self):
        """Update the language panel headers dynamically"""
        # Get language flag emojis
        flag_map = {
            'en': '🇺🇸', 'es': '🇪🇸', 'fr': '🇫🇷', 'de': '🇩🇪', 'it': '🇮🇹',
            'pt': '🇵🇹', 'nl': '🇳🇱', 'el': '🇬🇷', 'hr': '🇭🇷', 'sr': '🇷🇸',
            'bg': '🇧🇬', 'ro': '🇷🇴', 'hu': '🇭🇺', 'cs': '🇨🇿', 'sk': '🇸🇰',
            'pl': '🇵🇱', 'sv': '🇸🇪', 'no': '🇳🇴', 'da': '🇩🇰', 'fi': '🇫🇮',
            'et': '🇪🇪', 'lv': '🇱🇻', 'lt': '🇱🇹', 'sl': '🇸🇮', 'mk': '🇲🇰',
            'sq': '🇦🇱', 'is': '🇮🇸', 'ga': '🇮🇪', 'cy': '🏴󐁧󐁢󐁷󐁬󐁳󐁿', 'eu': '🏴',
            'ca': '🏴', 'gl': '🏴', 'zh': '🇨🇳', 'ja': '🇯🇵', 'ko': '🇰🇷',
            'hi': '🇮🇳', 'ar': '🇸🇦', 'he': '🇮🇱', 'tr': '🇹🇷', 'th': '🇹🇭',
            'vi': '🇻🇳', 'id': '🇮🇩', 'ms': '🇲🇾', 'uk': '🇺🇦', 'ru': '🇷🇺'
        }

        # Update primary language panel (left)
        if hasattr(self, 'en_flag_label'):
            self.en_flag_label.text = flag_map.get(self.primary_language, '🌐')
        if hasattr(self, 'en_title_label'):
            self.en_title_label.text = self.primary_language_name

        # Update foreign language panel (right)
        if hasattr(self, 'hr_flag_label'):
            self.hr_flag_label.text = flag_map.get(self.foreign_language, '🌐')
        if hasattr(self, 'hr_title_label'):
            self.hr_title_label.text = self.foreign_language_name

        # Update conversation panel empty states
        if hasattr(self, 'en_panel'):
            self.en_panel.language = self.primary_language
            # Update empty state if no messages
            if len(self.en_panel.messages) == 0:
                self.en_panel.clear_messages()  # This will recreate empty state with new language

        if hasattr(self, 'hr_panel'):
            self.hr_panel.language = self.foreign_language
            # Update empty state if no messages
            if len(self.hr_panel.messages) == 0:
                self.hr_panel.clear_messages()  # This will recreate empty state with new language

    def translate_ui_labels(self):
        """Translate UI labels using OpenAI"""
        try:
            # Import text translator
            from src.transcribe.text_translator import TextTranslator

            # Create translator with current languages
            translator = TextTranslator(
                primary_language=self.primary_language,
                foreign_language=self.foreign_language
            )

            # Note: TextInput fields would go here if the GUI had them
            # Currently the GUI uses microphone input only
            # Translate placeholder texts for input fields (if they existed)
            if hasattr(self, 'en_input') and hasattr(self, 'hr_input'):
                # Primary language input placeholder
                primary_placeholder = "Type to translate..."
                if self.primary_language != 'en':
                    translated, _, _ = translator.translate(
                        primary_placeholder,
                        source_lang='en',
                        target_lang=self.primary_language
                    )
                    self.en_input.hint_text = translated
                else:
                    self.en_input.hint_text = primary_placeholder

                # Foreign language input placeholder
                foreign_placeholder = "Type to translate..."
                translated, _, _ = translator.translate(
                    foreign_placeholder,
                    source_lang='en',
                    target_lang=self.foreign_language
                )
                self.hr_input.hint_text = translated

            self.logger.debug_log("UI labels translated for {} and {}", self.primary_language, self.foreign_language)

        except Exception as e:
            self.logger.debug_log("Could not translate UI labels: {}", e)
            # Fall back to basic translations
            self.fallback_ui_translations()

    def fallback_ui_translations(self):
        """Fallback UI translations if OpenAI is not available"""
        # Basic translations for common languages
        translations = {
            'el': {'Type to translate...': 'Πληκτρολογήστε για μετάφραση...'},
            'hr': {'Type to translate...': 'Upišite za prijevod...'},
            'es': {'Type to translate...': 'Escriba para traducir...'},
            'fr': {'Type to translate...': 'Tapez pour traduire...'},
            'de': {'Type to translate...': 'Zum Übersetzen eingeben...'},
            'it': {'Type to translate...': 'Digita per tradurre...'},
            'pt': {'Type to translate...': 'Digite para traduzir...'},
        }

        # Update placeholders with fallback translations
        if hasattr(self, 'en_input'):
            if self.primary_language in translations:
                self.en_input.hint_text = translations[self.primary_language].get(
                    'Type to translate...', 'Type to translate...'
                )

        if hasattr(self, 'hr_input'):
            if self.foreign_language in translations:
                self.hr_input.hint_text = translations[self.foreign_language].get(
                    'Type to translate...', 'Type to translate...'
                )

    def update_stats(self):
        """Update statistics display"""
        en_count = len(self.en_panel.messages) if hasattr(self, 'en_panel') else 0
        hr_count = len(self.hr_panel.messages) if hasattr(self, 'hr_panel') else 0

        # Use language codes from configuration
        primary_code = self.primary_language.upper()
        foreign_code = self.foreign_language.upper()
        self.stats_label.text = f'Messages: {en_count} {primary_code}, {hr_count} {foreign_code}'


class TranslationApp(App):
    """Main Kivy application"""

    def __init__(self, debug: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.debug = debug

    def build(self):
        """Build and return the root widget"""
        # Set window properties
        Window.clearcolor = (0.07, 0.07, 0.07, 1)  # Dark background
        Window.title = 'Real-Time Translation Interface'

        # Create and return main interface
        return TranslationInterface(debug=self.debug)

    def on_stop(self):
        """Cleanup when app closes"""
        root = self.root
        if hasattr(root, 'current_process') and root.current_process:
            root.current_process.terminate()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()

    TranslationApp(debug=args.debug).run()