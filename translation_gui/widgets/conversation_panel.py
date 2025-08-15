"""
Conversation Panel Widget - Scrollable container for message bubbles
Features smooth scrolling, auto-scroll to bottom, and message management
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.animation import Animation
from kivy.properties import StringProperty, ListProperty, NumericProperty, ObjectProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.effects.scroll import ScrollEffect
from kivy.utils import get_color_from_hex
from typing import List, Dict, Any

from .message_bubble import MessageBubble, TypingIndicator


class SmoothScrollEffect(ScrollEffect):
    """Custom scroll effect with momentum and smooth scrolling"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Adjust scroll parameters for smoother feel
        self.friction = 0.05
        self.min_velocity = dp(0.5)


class ConversationPanel(BoxLayout):
    """Scrollable conversation panel with message bubbles"""

    # Properties
    language = StringProperty('en')
    accent_color = ListProperty([0.13, 0.59, 0.95, 1])
    bg_color = ListProperty([0.12, 0.12, 0.12, 1])

    def __init__(self, language: str = 'en', accent_color=None, bg_color=None, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        # Set properties
        self.language = language
        if accent_color:
            self.accent_color = accent_color
        if bg_color:
            self.bg_color = bg_color

        # Message storage
        self.messages: List[Dict[str, Any]] = []
        self.message_widgets: List[MessageBubble] = []
        self.typing_indicator: TypingIndicator = None

        # Colors
        self.border_color = get_color_from_hex('#333333')

        # Create the panel
        self.create_panel()

        # Auto-scroll flag
        self.auto_scroll = True

    def create_panel(self):
        """Create the conversation panel with scrollable content"""
        # Add background and border
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = RoundedRectangle(
                size=self.size,
                pos=self.pos,
                radius=[dp(15)]
            )

            # Border
            Color(*self.border_color)
            self.border_line = Line(
                rounded_rectangle=(
                    self.pos[0], self.pos[1],
                    self.size[0], self.size[1],
                    dp(15)
                ),
                width=1
            )

        self.bind(size=self.update_graphics, pos=self.update_graphics)

        # Create scroll view with custom effect
        self.scroll_view = ScrollView(
            effect_cls=SmoothScrollEffect,
            do_scroll_x=False,
            do_scroll_y=True,
            scroll_type=['content'],
            bar_width=dp(8),
            bar_color=self.accent_color,
            bar_inactive_color=(*self.accent_color[:3], 0.3)
        )

        # Message container
        self.message_layout = GridLayout(
            cols=1,
            spacing=dp(8),
            size_hint_y=None,
            padding=[dp(15), dp(15)]
        )
        self.message_layout.bind(minimum_height=self.message_layout.setter('height'))

        # Add empty state
        self.create_empty_state()

        self.scroll_view.add_widget(self.message_layout)
        self.add_widget(self.scroll_view)

        # Bind scroll events
        self.scroll_view.bind(scroll_y=self.on_scroll)

    def update_graphics(self, *args):
        """Update background graphics"""
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

        # Update border
        self.border_line.rounded_rectangle = (
            self.pos[0], self.pos[1],
            self.size[0], self.size[1],
            dp(15)
        )

    def create_empty_state(self):
        """Create empty state message"""
        empty_message = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(120),
            spacing=dp(10)
        )

        # Icon
        icon_label = Label(
            text='💬' if self.language == 'en' else '🗣️',
            font_size=dp(32),
            size_hint=(1, None),
            height=dp(40),
            color=(*self.accent_color[:3], 0.5)
        )

        # Text - Get language name from language code
        from src.transcribe.language_codes import get_language_name
        language_name = get_language_name(self.language)

        text_label = Label(
            text=f'{language_name} messages will appear here',
            font_size=dp(14),
            size_hint=(1, None),
            height=dp(30),
            color=(*self.accent_color[:3], 0.5),
            halign='center'
        )
        text_label.bind(size=text_label.setter('text_size'))

        # Instructions
        instruction_label = Label(
            text='🎤 Start recording to begin translation',
            font_size=dp(12),
            size_hint=(1, None),
            height=dp(25),
            color=(*self.accent_color[:3], 0.3),
            halign='center'
        )
        instruction_label.bind(size=instruction_label.setter('text_size'))

        empty_message.add_widget(Widget())  # Spacer
        empty_message.add_widget(icon_label)
        empty_message.add_widget(text_label)
        empty_message.add_widget(instruction_label)
        empty_message.add_widget(Widget())  # Spacer

        self.message_layout.add_widget(empty_message)
        self.empty_state = empty_message

    def add_message(self, text: str, message_type: str = 'original', confidence: float = 1.0, animate: bool = True):
        """Add a new message to the conversation"""
        # Remove empty state if this is the first message
        if len(self.messages) == 0 and hasattr(self, 'empty_state'):
            self.message_layout.remove_widget(self.empty_state)

        # Remove typing indicator if present
        if self.typing_indicator:
            self.remove_typing_indicator()

        # Create message data
        message_data = {
            'text': text,
            'type': message_type,
            'confidence': confidence,
            'timestamp': Clock.get_time()
        }
        self.messages.append(message_data)

        # Create message bubble
        bubble = MessageBubble(
            text=text,
            msg_type=message_type,
            accent_color=self.accent_color,
            confidence=confidence
        )

        # Add to layout
        self.message_layout.add_widget(bubble)
        self.message_widgets.append(bubble)

        # Auto-scroll to bottom
        if self.auto_scroll:
            Clock.schedule_once(self.scroll_to_bottom, 0.1)

        # Animate if requested
        if animate:
            self.animate_new_message(bubble)

    def add_typing_indicator(self):
        """Show typing indicator for pending translation"""
        if self.typing_indicator:
            return  # Already showing

        self.typing_indicator = TypingIndicator(accent_color=self.accent_color)
        self.message_layout.add_widget(self.typing_indicator)

        # Auto-scroll to show indicator
        Clock.schedule_once(self.scroll_to_bottom, 0.1)

    def remove_typing_indicator(self):
        """Remove typing indicator"""
        if self.typing_indicator:
            self.message_layout.remove_widget(self.typing_indicator)
            self.typing_indicator = None

    def animate_new_message(self, bubble: MessageBubble):
        """Animate the appearance of a new message"""
        # The bubble has its own animation, but we can add panel-level effects
        pass

    def scroll_to_bottom(self, dt=None):
        """Scroll to the bottom of the conversation"""
        if self.scroll_view.vbar:
            # Smooth scroll animation
            anim = Animation(scroll_y=0, duration=0.3, transition='out_cubic')
            anim.start(self.scroll_view)

    def scroll_to_top(self):
        """Scroll to the top of the conversation"""
        if self.scroll_view.vbar:
            anim = Animation(scroll_y=1, duration=0.5, transition='out_cubic')
            anim.start(self.scroll_view)

    def on_scroll(self, instance, scroll_y):
        """Handle scroll events"""
        # Disable auto-scroll if user scrolls up manually
        if scroll_y > 0.1:  # Not at bottom
            self.auto_scroll = False
        else:
            self.auto_scroll = True

    def clear_messages(self):
        """Clear all messages from the conversation"""
        # Remove all message widgets
        for widget in self.message_widgets:
            self.message_layout.remove_widget(widget)

        # Remove typing indicator
        if self.typing_indicator:
            self.remove_typing_indicator()

        # Clear data
        self.messages.clear()
        self.message_widgets.clear()

        # Restore empty state
        self.create_empty_state()

        # Reset auto-scroll
        self.auto_scroll = True

    def animate_clear(self, callback=None):
        """Animate clearing all messages"""
        if not self.message_widgets:
            if callback:
                callback()
            return

        # Animate all bubbles out
        animations = []
        for i, bubble in enumerate(reversed(self.message_widgets)):
            # Stagger the animations
            delay = i * 0.05

            def animate_bubble(bubble, delay):
                def start_anim(dt):
                    bubble.animate_out()
                Clock.schedule_once(start_anim, delay)

            animate_bubble(bubble, delay)

        # Clear after animations complete
        def complete_clear(dt):
            self.clear_messages()
            if callback:
                callback()

        total_delay = len(self.message_widgets) * 0.05 + 0.3
        Clock.schedule_once(complete_clear, total_delay)

    def filter_messages(self, message_type: str = None):
        """Filter visible messages by type"""
        for i, bubble in enumerate(self.message_widgets):
            if message_type is None or self.messages[i]['type'] == message_type:
                bubble.opacity = 1
                bubble.disabled = False
            else:
                bubble.opacity = 0.3
                bubble.disabled = True

    def highlight_message(self, index: int):
        """Highlight a specific message"""
        if 0 <= index < len(self.message_widgets):
            bubble = self.message_widgets[index]
            bubble.pulse_animation()

    def get_message_count(self) -> int:
        """Get total message count"""
        return len(self.messages)

    def get_messages_by_type(self, message_type: str) -> List[Dict[str, Any]]:
        """Get messages filtered by type"""
        return [msg for msg in self.messages if msg['type'] == message_type]

    def export_conversation(self) -> List[Dict[str, Any]]:
        """Export conversation data"""
        return self.messages.copy()

    def load_conversation(self, messages: List[Dict[str, Any]]):
        """Load conversation from data"""
        self.clear_messages()

        for msg in messages:
            self.add_message(
                msg['text'],
                msg.get('type', 'original'),
                animate=False
            )