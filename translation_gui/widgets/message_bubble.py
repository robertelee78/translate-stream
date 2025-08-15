"""
Message Bubble Widget for iMessage-style chat interface
Supports animations, different message types, and smooth transitions
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, PushMatrix, PopMatrix, Rotate
from kivy.animation import Animation
from kivy.properties import StringProperty, ListProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
import time


class MessageBubble(BoxLayout):
    """Individual message bubble with iMessage-style appearance"""

    # Properties
    message_text = StringProperty('')
    message_type = StringProperty('original')  # 'original' or 'translation'
    accent_color = ListProperty([0.13, 0.59, 0.95, 1])  # Default blue
    timestamp = NumericProperty(0)
    is_animating = BooleanProperty(False)

    def __init__(self, text: str, msg_type: str = 'original', accent_color=None, confidence: float = 1.0, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(60),
            padding=[dp(10), dp(5)],
            spacing=dp(10),
            **kwargs
        )

        # Set properties
        self.message_text = text
        self.message_type = msg_type
        self.confidence = confidence
        self.timestamp = time.time()

        if accent_color:
            self.accent_color = accent_color

        # Color scheme
        self.bg_original = get_color_from_hex('#2196F3')  # Blue for original
        self.bg_translation = get_color_from_hex('#009688')  # Teal for translation
        self.text_color = get_color_from_hex('#FFFFFF')
        self.shadow_color = get_color_from_hex('#00000030')  # Semi-transparent shadow

        # Create bubble content
        self.create_bubble_content()

        # Initial animation
        self.opacity = 0
        self.pos = (self.pos[0], self.pos[1] - dp(20))
        self.animate_in()

    def create_bubble_content(self):
        """Create the bubble content with proper alignment"""
        # Spacer for alignment (left for original, right for translation)
        if self.message_type == 'original':
            spacer_left = Widget(size_hint=(0.1, 1))
            self.add_widget(spacer_left)

        # Message container
        message_container = BoxLayout(
            orientation='vertical',
            size_hint=(0.8 if self.message_type == 'original' else 0.7, 1),
            padding=[dp(15), dp(8)],
            spacing=dp(2)
        )

        # Add background graphics
        with message_container.canvas.before:
            # Shadow
            Color(*self.shadow_color)
            self.shadow_rect = RoundedRectangle(
                size=(0, 0),
                pos=(0, 0),
                radius=[dp(18)]
            )

            # Main bubble background
            if self.message_type == 'original':
                Color(*self.bg_original)
            else:
                Color(*self.bg_translation)

            self.bg_rect = RoundedRectangle(
                size=(0, 0),
                pos=(0, 0),
                radius=[dp(18)]
            )

        # Message text
        message_label = Label(
            text=self.message_text,
            color=self.text_color,
            font_size=dp(14),
            text_size=(None, None),
            halign='left' if self.message_type == 'original' else 'right',
            valign='middle',
            markup=True
        )

        # Type indicator
        type_indicator = Label(
            text='🗣️ Original' if self.message_type == 'original' else '🌐 Translation',
            color=self.text_color,
            font_size=dp(10),
            opacity=0.7,
            size_hint=(1, None),
            height=dp(15),
            halign='left' if self.message_type == 'original' else 'right'
        )

        # Timestamp
        timestamp_label = Label(
            text=time.strftime('%H:%M', time.localtime(self.timestamp)),
            color=self.text_color,
            font_size=dp(9),
            opacity=0.5,
            size_hint=(1, None),
            height=dp(12),
            halign='left' if self.message_type == 'original' else 'right'
        )

        message_container.add_widget(type_indicator)
        message_container.add_widget(message_label)
        message_container.add_widget(timestamp_label)

        # Bind size updates
        message_container.bind(size=self.update_graphics, pos=self.update_graphics)
        message_label.bind(texture_size=self.update_text_size)

        self.add_widget(message_container)
        self.message_container = message_container
        self.message_label = message_label

        # Spacer for alignment
        if self.message_type == 'translation':
            spacer_right = Widget(size_hint=(0.2, 1))
            self.add_widget(spacer_right)

    def update_graphics(self, instance, *args):
        """Update bubble background graphics"""
        # Shadow (slightly offset)
        shadow_offset = dp(2)
        self.shadow_rect.size = instance.size
        self.shadow_rect.pos = (
            instance.pos[0] + shadow_offset,
            instance.pos[1] - shadow_offset
        )

        # Main background
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def update_text_size(self, instance, texture_size):
        """Update text size and bubble height based on content"""
        # Calculate required height
        padding = dp(40)  # Total vertical padding
        min_height = dp(60)
        content_height = texture_size[1] + padding

        new_height = max(min_height, content_height)

        # Update bubble height
        self.height = new_height

        # Update text_size for proper wrapping
        available_width = self.width * 0.7 - dp(30)  # Account for padding and margins
        instance.text_size = (available_width, None)

    def animate_in(self):
        """Animate bubble appearance"""
        self.is_animating = True

        # Slide up and fade in animation
        anim = Animation(
            opacity=1,
            y=self.y + dp(20),
            duration=0.3,
            transition='out_cubic'
        )

        # Scale animation for bounce effect
        scale_anim = Animation(
            duration=0.15,
            transition='out_back'
        )

        anim.bind(on_complete=self.on_animate_complete)
        anim.start(self)

    def animate_out(self, callback=None):
        """Animate bubble removal"""
        self.is_animating = True

        # Slide out and fade animation
        anim = Animation(
            opacity=0,
            x=self.x + (dp(50) if self.message_type == 'translation' else -dp(50)),
            duration=0.2,
            transition='in_cubic'
        )

        if callback:
            anim.bind(on_complete=callback)

        anim.start(self)

    def on_animate_complete(self, *args):
        """Called when animation completes"""
        self.is_animating = False

    def pulse_animation(self):
        """Pulse animation for emphasis"""
        if self.is_animating:
            return

        # Create pulse effect by scaling
        original_size = self.size
        pulse_anim = Animation(
            size=(original_size[0] * 1.05, original_size[1] * 1.05),
            duration=0.1,
            transition='out_sine'
        ) + Animation(
            size=original_size,
            duration=0.1,
            transition='in_sine'
        )

        pulse_anim.start(self)

    def typing_animation(self):
        """Show typing indicator animation"""
        # Add typing dots animation
        if hasattr(self, 'message_label'):
            original_text = self.message_label.text
            typing_text = "●●●"

            # Animate typing dots
            def update_dots(dt, counter=[0]):
                if not self.is_animating:
                    return False

                dots = "●" * (counter[0] % 3 + 1) + "○" * (2 - counter[0] % 3)
                self.message_label.text = dots
                counter[0] += 1
                return True

            self.is_animating = True
            Clock.schedule_interval(update_dots, 0.5)

            # Stop after 3 seconds and show final text
            def stop_typing(dt):
                self.is_animating = False
                self.message_label.text = original_text
                Clock.unschedule(update_dots)

            Clock.schedule_once(stop_typing, 3.0)


class TypingIndicator(BoxLayout):
    """Typing indicator for when translation is in progress"""

    def __init__(self, accent_color=None, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40),
            padding=[dp(20), dp(5)],
            **kwargs
        )

        self.accent_color = accent_color or [0.5, 0.5, 0.5, 1]

        # Create typing indicator
        self.create_indicator()

        # Start animation
        self.start_animation()

    def create_indicator(self):
        """Create the typing indicator elements"""
        # Spacer
        spacer = Widget(size_hint=(0.7, 1))
        self.add_widget(spacer)

        # Indicator container
        indicator_container = BoxLayout(
            orientation='horizontal',
            size_hint=(0.3, 1),
            spacing=dp(5)
        )

        # Add background
        with indicator_container.canvas.before:
            Color(*self.accent_color)
            self.bg_rect = RoundedRectangle(
                size=(0, 0),
                pos=(0, 0),
                radius=[dp(15)],
                opacity=0.3
            )

        indicator_container.bind(size=self.update_bg, pos=self.update_bg)

        # Typing dots
        self.dots = []
        for i in range(3):
            dot = Label(
                text='●',
                color=self.accent_color,
                font_size=dp(16),
                size_hint=(None, 1),
                width=dp(20)
            )
            self.dots.append(dot)
            indicator_container.add_widget(dot)

        self.add_widget(indicator_container)

    def update_bg(self, instance, *args):
        """Update background"""
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def start_animation(self):
        """Start the typing animation"""
        def animate_dot(dot_index):
            if dot_index < len(self.dots):
                dot = self.dots[dot_index]
                # Fade in/out animation
                anim = Animation(opacity=1, duration=0.3) + Animation(opacity=0.3, duration=0.3)
                anim.start(dot)

                # Schedule next dot
                Clock.schedule_once(lambda dt: animate_dot((dot_index + 1) % 3), 0.2)

        # Start the animation loop
        animate_dot(0)

    def stop_animation(self):
        """Stop the typing animation"""
        # Stop all animations
        for dot in self.dots:
            Animation.stop_all(dot)