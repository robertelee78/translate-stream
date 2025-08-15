"""
Audio Visualizer Widget for real-time audio activity display
Creates animated bars and waveforms to show recording/translation activity
"""

import math
import random
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, Ellipse, PushMatrix, PopMatrix, Rotate
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import ListProperty, NumericProperty, BooleanProperty
from kivy.metrics import dp
from kivy.utils import get_color_from_hex


class AudioVisualizer(Widget):
    """Animated audio visualizer widget"""

    # Properties
    color = ListProperty([0.13, 0.59, 0.95, 1])  # Default blue
    bar_count = NumericProperty(8)
    is_active = BooleanProperty(False)
    animation_speed = NumericProperty(1.0)

    def __init__(self, color=None, bar_count=8, **kwargs):
        super().__init__(**kwargs)

        if color:
            self.color = color
        self.bar_count = bar_count

        # Animation state
        self.bars_heights = [0.1] * int(self.bar_count)
        self.animation_phase = 0
        self.animation_event = None

        # Visual elements
        self.bars = []

        # Create visualization
        self.create_visualizer()

        # Bind size changes
        self.bind(size=self.update_visualizer, pos=self.update_visualizer)

    def create_visualizer(self):
        """Create the visual elements"""
        with self.canvas:
            Color(*self.color)
            # Will be populated by update_visualizer

        self.update_visualizer()

    def update_visualizer(self, *args):
        """Update visualizer graphics"""
        if not self.canvas:
            return

        self.canvas.clear()
        self.bars.clear()

        # Calculate bar dimensions
        bar_width = (self.width - dp(10)) / self.bar_count
        max_height = self.height - dp(10)

        with self.canvas:
            Color(*self.color)

            # Create bars
            for i in range(int(self.bar_count)):
                x = self.pos[0] + dp(5) + i * bar_width
                height = max_height * self.bars_heights[i]
                y = self.pos[1] + (self.height - height) / 2

                bar_rect = Rectangle(
                    pos=(x + bar_width * 0.1, y),
                    size=(bar_width * 0.8, height)
                )
                self.bars.append(bar_rect)

    def start_animation(self):
        """Start the audio visualization animation"""
        self.is_active = True
        if self.animation_event:
            self.animation_event.cancel()

        self.animation_event = Clock.schedule_interval(self.update_animation, 1/30.0)  # 30 FPS

    def pulse_once(self):
        """Do a single pulse animation"""
        if not self.is_active:
            self.start_animation()
            Clock.schedule_once(lambda dt: self.stop_animation(), 0.5)

    def stop_animation(self):
        """Stop the audio visualization animation"""
        self.is_active = False
        if self.animation_event:
            self.animation_event.cancel()
            self.animation_event = None

        # Fade out animation
        self.fade_out_bars()

    def update_animation(self, dt):
        """Update animation frame"""
        if not self.is_active:
            return False

        self.animation_phase += dt * self.animation_speed * 5

        # Update bar heights with sine wave pattern
        for i in range(int(self.bar_count)):
            # Create varying sine waves for each bar
            base_freq = 2.0 + i * 0.3
            noise = random.uniform(0.7, 1.3)  # Add randomness

            # Calculate height (0.1 to 1.0 range)
            height = 0.3 + 0.6 * abs(math.sin(self.animation_phase * base_freq)) * noise
            height += 0.1 * math.sin(self.animation_phase * 8 + i)  # Fast variation

            self.bars_heights[i] = max(0.1, min(1.0, height))

        # Update graphics
        self.update_bar_graphics()

        return self.is_active

    def update_bar_graphics(self):
        """Update individual bar graphics"""
        if not self.bars or len(self.bars) != len(self.bars_heights):
            return

        bar_width = (self.width - dp(10)) / self.bar_count
        max_height = self.height - dp(10)

        for i, bar in enumerate(self.bars):
            height = max_height * self.bars_heights[i]
            y = self.pos[1] + (self.height - height) / 2

            bar.size = (bar_width * 0.8, height)
            bar.pos = (
                self.pos[0] + dp(5) + i * bar_width + bar_width * 0.1,
                y
            )

    def fade_out_bars(self):
        """Fade out bars smoothly"""
        def fade_step(dt, step_count=[0]):
            step_count[0] += 1
            progress = min(1.0, step_count[0] * 0.1)

            for i in range(len(self.bars_heights)):
                self.bars_heights[i] = 0.1 + (self.bars_heights[i] - 0.1) * (1 - progress)

            self.update_bar_graphics()

            if progress >= 1.0:
                return False  # Stop the event
            return True

        Clock.schedule_interval(fade_step, 1/30.0)

    def pulse_animation(self):
        """Single pulse animation for notifications"""
        if self.is_active:
            return  # Don't interrupt active animation

        # Quick pulse effect
        for i in range(len(self.bars_heights)):
            self.bars_heights[i] = random.uniform(0.3, 0.9)

        self.update_bar_graphics()

        # Fade out after pulse
        Clock.schedule_once(lambda dt: self.fade_out_bars(), 0.2)


class WaveformVisualizer(Widget):
    """Waveform-style audio visualizer"""

    color = ListProperty([0.13, 0.59, 0.95, 1])
    line_width = NumericProperty(2)
    is_active = BooleanProperty(False)

    def __init__(self, color=None, **kwargs):
        super().__init__(**kwargs)

        if color:
            self.color = color

        # Waveform data
        self.waveform_points = []
        self.animation_phase = 0
        self.animation_event = None

        # Create waveform
        self.create_waveform()

        self.bind(size=self.update_waveform, pos=self.update_waveform)

    def create_waveform(self):
        """Create waveform graphics"""
        with self.canvas:
            Color(*self.color)
            self.waveform_line = Line(points=[], width=self.line_width)

        self.update_waveform()

    def update_waveform(self, *args):
        """Update waveform points"""
        if not self.canvas:
            return

        # Generate base waveform points
        points = []
        point_count = max(20, int(self.width / dp(5)))

        for i in range(point_count):
            x = self.pos[0] + (i / (point_count - 1)) * self.width

            if self.is_active:
                # Animated sine wave
                phase = self.animation_phase + i * 0.2
                y_offset = dp(15) * math.sin(phase) * random.uniform(0.5, 1.5)
            else:
                # Flat line
                y_offset = 0

            y = self.pos[1] + self.height / 2 + y_offset

            points.extend([x, y])

        self.waveform_points = points
        self.waveform_line.points = points

    def start_animation(self):
        """Start waveform animation"""
        self.is_active = True
        if self.animation_event:
            self.animation_event.cancel()

        self.animation_event = Clock.schedule_interval(self.update_animation, 1/30.0)

    def stop_animation(self):
        """Stop waveform animation"""
        self.is_active = False
        if self.animation_event:
            self.animation_event.cancel()
            self.animation_event = None

        # Smooth fade to flat line
        self.fade_to_flat()

    def update_animation(self, dt):
        """Update waveform animation"""
        if not self.is_active:
            return False

        self.animation_phase += dt * 8  # Speed of wave movement
        self.update_waveform()

        return True

    def fade_to_flat(self):
        """Fade waveform to flat line"""
        def fade_step(dt, step_count=[0]):
            step_count[0] += 1
            progress = min(1.0, step_count[0] * 0.1)

            # Interpolate to flat line
            points = []
            point_count = len(self.waveform_points) // 2

            for i in range(point_count):
                x = self.waveform_points[i * 2]
                current_y = self.waveform_points[i * 2 + 1]
                target_y = self.pos[1] + self.height / 2

                y = current_y + (target_y - current_y) * progress
                points.extend([x, y])

            self.waveform_line.points = points

            if progress >= 1.0:
                return False
            return True

        Clock.schedule_interval(fade_step, 1/30.0)


class CircularVisualizer(Widget):
    """Circular/radial audio visualizer"""

    color = ListProperty([0.13, 0.59, 0.95, 1])
    is_active = BooleanProperty(False)

    def __init__(self, color=None, **kwargs):
        super().__init__(**kwargs)

        if color:
            self.color = color

        # Circle properties
        self.base_radius = dp(20)
        self.current_radius = self.base_radius
        self.animation_phase = 0
        self.animation_event = None

        # Graphics elements
        self.circle = None
        self.inner_circle = None

        self.create_circles()
        self.bind(size=self.update_circles, pos=self.update_circles)

    def create_circles(self):
        """Create circular visualizer"""
        with self.canvas:
            # Outer circle (animated)
            Color(*self.color, 0.3)
            self.outer_circle = Ellipse()

            # Inner circle (solid)
            Color(*self.color)
            self.inner_circle = Ellipse()

        self.update_circles()

    def update_circles(self, *args):
        """Update circle graphics"""
        if not self.canvas:
            return

        # Calculate center
        center_x = self.pos[0] + self.width / 2
        center_y = self.pos[1] + self.height / 2

        # Update outer circle (animated)
        outer_radius = self.current_radius
        self.outer_circle.pos = (
            center_x - outer_radius,
            center_y - outer_radius
        )
        self.outer_circle.size = (outer_radius * 2, outer_radius * 2)

        # Update inner circle (smaller, solid)
        inner_radius = self.base_radius * 0.6
        self.inner_circle.pos = (
            center_x - inner_radius,
            center_y - inner_radius
        )
        self.inner_circle.size = (inner_radius * 2, inner_radius * 2)

    def start_animation(self):
        """Start circular animation"""
        self.is_active = True
        if self.animation_event:
            self.animation_event.cancel()

        self.animation_event = Clock.schedule_interval(self.update_animation, 1/30.0)

    def stop_animation(self):
        """Stop circular animation"""
        self.is_active = False
        if self.animation_event:
            self.animation_event.cancel()
            self.animation_event = None

        # Shrink back to base size
        anim = Animation(current_radius=self.base_radius, duration=0.5, transition='out_cubic')
        anim.bind(on_progress=lambda *args: self.update_circles())
        anim.start(self)

    def update_animation(self, dt):
        """Update circular animation"""
        if not self.is_active:
            return False

        self.animation_phase += dt * 4

        # Pulsing radius
        pulse = 1.0 + 0.3 * abs(math.sin(self.animation_phase))
        self.current_radius = self.base_radius * pulse

        self.update_circles()
        return True