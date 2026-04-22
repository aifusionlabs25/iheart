import sys
import os
import time
import logging
import math
import random
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QComboBox, QSizePolicy, QGraphicsDropShadowEffect, QGridLayout,
    QTimeEdit, QSpinBox, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath, QLinearGradient, QRadialGradient, QPolygonF

import main
import config
from browser_automation import BrowserController

# ----- CONSTANTS & COLORS -----
COLOR_VOID = "#000000"
COLOR_NEON_ORANGE = "#ff5500"
COLOR_NEON_GLOW = "#ff8833"
COLOR_WHITE = "#ffffff"
FONT_UI = "Segoe UI"
FONT_DOT_MATRIX = "Consolas" # Fallback for dot matrix look

def add_shadow(widget, blur=15, x=0, y=5, color=(0,0,0,150)):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(x)
    shadow.setYOffset(y)
    shadow.setColor(QColor(*color))
    widget.setGraphicsEffect(shadow)


class BoutiqueSwitch(QWidget):
    """Minimalist physical toggle switch, 3D metallic."""
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_on = False
        self.setFixedSize(52, 104)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Base recessed slot (Inner shadow effect)
        slot_grad = QLinearGradient(13, 13, 39, 91)
        slot_grad.setColorAt(0, QColor("#0a0a0c"))
        slot_grad.setColorAt(1, QColor("#333"))
        painter.setBrush(slot_grad)
        painter.setPen(QPen(QColor("#555"), 1))
        painter.drawRoundedRect(13, 13, 26, 78, 13, 13)
        
        # Toggle handle position
        cy = 32 if self.is_on else 71
        
        # Deep cast shadow from the handle
        painter.setBrush(QColor(0,0,0,200))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(13, cy-3, 26, 30)
        
        # 3D Metallic Sphere Handle
        grad = QRadialGradient(22, cy-4, 18) # Offset highlight
        if self.is_on:
            grad.setColorAt(0, QColor("#ffaa88"))
            grad.setColorAt(0.3, QColor(COLOR_NEON_ORANGE))
            grad.setColorAt(1, QColor("#882200"))
        else:
            grad.setColorAt(0, QColor("#ffffff"))
            grad.setColorAt(0.4, QColor("#aaaaaa"))
            grad.setColorAt(1, QColor("#333333"))
            
        painter.setBrush(grad)
        painter.setPen(QPen(QColor("#222"), 1))
        painter.drawEllipse(13, cy-13, 26, 26)
        
    def mousePressEvent(self, event):
        self.is_on = not self.is_on
        self.update()
        self.toggled.emit(self.is_on)
        
    def set_checked(self, checked):
        self.is_on = checked
        self.update()


class BoutiqueRecordButton(QWidget):
    """Large Record knob with intense neon glow and 3D bevel."""
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_on = False
        self.setFixedSize(130, 130)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cx, cy = 65, 65
        
        # Outer ring (metallic bevel)
        bevel = QLinearGradient(0, 0, 130, 130)
        bevel.setColorAt(0, QColor("#ffffff"))
        bevel.setColorAt(1, QColor("#666666"))
        painter.setBrush(bevel)
        painter.setPen(QPen(QColor("#222"), 1))
        painter.drawEllipse(cx-52, cy-52, 104, 104)
        
        # Inner recessed trench
        trench = QLinearGradient(0, 0, 130, 130)
        trench.setColorAt(0, QColor("#111"))
        trench.setColorAt(1, QColor("#444"))
        painter.setBrush(trench)
        painter.drawEllipse(cx-48, cy-48, 96, 96)
        
        # Inner Button
        if self.is_on:
            # Massive Intense Glow ring bleeding outside
            glow = QRadialGradient(cx, cy, 60)
            glow.setColorAt(0.5, QColor(255, 85, 0, 200)) # Core glow
            glow.setColorAt(1, QColor(255, 85, 0, 0))     # Fade
            painter.setBrush(glow)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx-60, cy-60, 120, 120)
            
            # Button Face (3D Neon)
            btn_grad = QRadialGradient(cx-10, cy-10, 45)
            btn_grad.setColorAt(0, QColor("#ffaa66"))
            btn_grad.setColorAt(0.4, QColor("#ff5500"))
            btn_grad.setColorAt(1, QColor("#aa2200"))
        else:
            # Button Face (3D Dark Plastic)
            btn_grad = QRadialGradient(cx-10, cy-10, 45)
            btn_grad.setColorAt(0, QColor("#666"))
            btn_grad.setColorAt(0.5, QColor("#333"))
            btn_grad.setColorAt(1, QColor("#111"))
            
        painter.setBrush(btn_grad)
        painter.setPen(QPen(QColor("#000"), 2))
        painter.drawEllipse(cx-39, cy-39, 78, 78)
        
        # Rec symbol (Engraved dot)
        if self.is_on:
            painter.setBrush(QColor("#ffffff"))
            painter.setPen(QPen(QColor("#ffaa66"), 1))
        else:
            painter.setBrush(QColor("#111"))
            painter.setPen(QPen(QColor("#444"), 1))
        painter.drawEllipse(cx-10, cy-10, 20, 20)

    def mousePressEvent(self, event):
        self.is_on = not self.is_on
        self.update()
        self.toggled.emit(self.is_on)
        
    def set_checked(self, checked):
        self.is_on = checked
        self.update()


class LedMatrixVuMeter(QWidget):
    """Digital LED dot-matrix style VU meter with extreme orange glow."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = -40 # dBFS
        self.setFixedSize(26, 156)
        
    def set_value(self, val):
        self.value = val
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background slot (deep recess)
        painter.setBrush(QColor("#050508"))
        painter.setPen(QPen(QColor("#444"), 1)) # Metal edge
        painter.drawRoundedRect(0, 0, 26, 156, 5, 5)
        
        # 16 LEDs
        num_leds = 16
        led_height = 156 / num_leds
        
        active_leds = int((self.value + 40) / 2.7)
        active_leds = max(0, min(num_leds, active_leds))
        
        for i in range(num_leds):
            y = 156 - (i + 1) * led_height + 2
            is_active = i < active_leds
            
            if is_active:
                if i >= num_leds - 2:
                    core_color = QColor(COLOR_WHITE)
                    glow_color = QColor(255, 255, 255, 150)
                else:
                    core_color = QColor(COLOR_NEON_ORANGE)
                    glow_color = QColor(255, 85, 0, 150)
                
                # Draw Halo Glow behind LED
                glow_rad = QRadialGradient(13, y + (led_height-4)/2, 12)
                glow_rad.setColorAt(0, glow_color)
                glow_rad.setColorAt(1, QColor(0,0,0,0))
                painter.setBrush(glow_rad)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(0, int(y-8), 26, int(led_height + 16))
                
                # Draw bright LED core
                painter.setBrush(core_color)
                painter.drawRect(5, int(y), 16, int(led_height - 4))
            else:
                painter.setBrush(QColor("#1a1a1a"))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(5, int(y), 16, int(led_height - 4))


class BoutiqueDimmerKnob(QWidget):
    """3D Machined Aluminum Rotary knob."""
    valueChanged = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(78, 78)
        self.level = 1.0 # 0.2 to 1.0
        self.is_dragging = False
        self.last_y = 0
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = 39, 39
        
        # Outer drop shadow
        painter.setBrush(QColor(0,0,0,150))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx-30, cy-28, 62, 62)
        
        # Metal Base ring (Silver bevel)
        base_grad = QLinearGradient(0,0,78,78)
        base_grad.setColorAt(0, QColor("#ffffff"))
        base_grad.setColorAt(1, QColor("#888888"))
        painter.setBrush(base_grad)
        painter.drawEllipse(cx-32, cy-32, 64, 64)
        
        # Machined aluminum Cone body
        cone_grad = QRadialGradient(cx-10, cy-10, 45)
        cone_grad.setColorAt(0, QColor("#f0f0f0"))
        cone_grad.setColorAt(0.5, QColor("#a0a0a0"))
        cone_grad.setColorAt(1, QColor("#444444"))
        painter.setBrush(cone_grad)
        painter.setPen(QPen(QColor("#222"), 1))
        painter.drawEllipse(cx-30, cy-30, 60, 60)
        
        # Indicator line (glowing orange recess)
        angle = -135 + ((self.level - 0.2) / 0.8) * 270 
        rad = math.radians(angle - 90)
        
        # Recess shadow
        painter.setPen(QPen(QColor("#111"), 6, cap=Qt.PenCapStyle.RoundCap))
        painter.drawLine(
            int(cx + 10 * math.cos(rad)), int(cy + 10 * math.sin(rad)),
            int(cx + 25 * math.cos(rad)), int(cy + 25 * math.sin(rad))
        )
        
        # Glow fill
        painter.setPen(QPen(QColor(COLOR_NEON_GLOW), 4, cap=Qt.PenCapStyle.RoundCap))
        painter.drawLine(
            int(cx + 11 * math.cos(rad)), int(cy + 11 * math.sin(rad)),
            int(cx + 24 * math.cos(rad)), int(cy + 24 * math.sin(rad))
        )
        
    def mousePressEvent(self, event):
        self.is_dragging = True
        self.last_y = event.position().y()
        
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            dy = self.last_y - event.position().y()
            self.level += dy * 0.01
            self.level = max(0.2, min(1.0, self.level))
            self.last_y = event.position().y()
            self.update()
            self.valueChanged.emit(self.level)
            
    def mouseReleaseEvent(self, event):
        self.is_dragging = False

class BoutiqueMainDisplay(QWidget):
    """OP-1 inspired central display with physical screen depth and complex waveform."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(650, 338)
        self.active = False
        self.time_str = "00:00:00"
        self.log_text = "STANDING BY..."
        self.target_text = ""
        self.phase = 0.0
        
        # Add internal drop shadow to simulate glass depth
        add_shadow(self, blur=20, x=0, y=0, color=(0,0,0,255))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Bezel / glass lip
        painter.setBrush(QColor("#111"))
        painter.setPen(QPen(QColor("#444"), 2))
        painter.drawRoundedRect(0, 0, 650, 338, 8, 8)
        
        # Actual Screen Base
        painter.setBrush(QColor("#050508"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(4, 4, 642, 330, 6, 6)
        
        # --- Waveform (Oscillator) ---
        if self.active:
            self.phase += 0.4
            
            path = QPainterPath()
            path.moveTo(4, 169)
            
            # Draw realistic chaotic waveform
            for x in range(4, 646, 4):
                # fundamental + noise + envelope
                envelope = math.sin(x * 0.005 + self.phase*0.2)
                val = math.sin(x * 0.04 + self.phase) * 60 * envelope
                val += math.sin(x * 0.1 - self.phase) * 15
                y = 169 + val
                path.lineTo(x, y)
                
            # Awesome Phosphor Glow Effect
            # Outer diffuse glow
            painter.setPen(QPen(QColor(255, 85, 0, 40), 12))
            painter.drawPath(path)
            # Mid glow
            painter.setPen(QPen(QColor(255, 85, 0, 100), 6))
            painter.drawPath(path)
            # Core bright white/orange line
            painter.setPen(QPen(QColor(255, 200, 150, 255), 2))
            painter.drawPath(path)
        else:
            # Flat line
            painter.setPen(QPen(QColor(255, 85, 0, 150), 3))
            painter.drawLine(4, 169, 646, 169)
            
        # --- Dot Matrix Time Code ---
        painter.setFont(QFont(FONT_DOT_MATRIX, 48, QFont.Weight.Bold))
        painter.setPen(QColor(COLOR_WHITE))
        painter.drawText(QRectF(26, 234, 598, 78), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, self.time_str)
        
        # --- Target / Log Overlay ---
        painter.setFont(QFont(FONT_UI, 18, QFont.Weight.Bold))
        painter.setPen(QColor(COLOR_NEON_ORANGE))
        painter.drawText(QRectF(26, 26, 598, 39), Qt.AlignmentFlag.AlignLeft, self.target_text)
        
        painter.setFont(QFont(FONT_UI, 15))
        painter.setPen(QColor("#cccccc"))
        painter.drawText(QRectF(26, 65, 598, 39), Qt.AlignmentFlag.AlignLeft, self.log_text)
        
    def set_active(self, active):
        self.active = active
        self.update()
        
    def set_log(self, text):
        self.log_text = text
        self.update()
        
    def set_target(self, text):
        self.target_text = f"> {text}" if text else ""
        self.update()
        
    def set_time(self, time_string):
        self.time_str = time_string
        self.update()


class IHeartBoutiqueGUI(QMainWindow):
    """The main Boutique UI Application."""
    def __init__(self, auto_arm=False):
        super().__init__()
        self.setWindowTitle("Recorder - Boutique Edition")
        self.setFixedSize(1560, 468) # Scaled up width for speaker grills
        
        # Base stylesheet for standard widgets to match the dark theme
        self.setStyleSheet(f"""
            QWidget {{ font-family: {FONT_UI}; font-size: 14px; text-transform: uppercase; }}
            QLabel {{ color: #111; font-weight: bold; }}
            QLineEdit, QComboBox, QTimeEdit, QSpinBox {{
                background-color: #1a1a1a; 
                color: {COLOR_NEON_ORANGE}; 
                border: 2px solid #555; 
                border-radius: 6px; 
                padding: 6px; 
                font-weight: bold;
            }}
            QComboBox::drop-down, QTimeEdit::up-button, QSpinBox::up-button {{ border: none; }}
        """)
        
        self.browser_thread = None
        self.stream_active = False
        
        # Global Dimmer Overlay Setup
        self.dimmer_overlay = QWidget(self)
        self.dimmer_overlay.resize(1560, 468)
        self.dimmer_overlay.setStyleSheet("background-color: black;")
        self.dimmer_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.dimmer_overlay.hide() 
        
        self.setup_ui()
        self.populate_device_list()
        
        # VU & Animation Timer
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_ui_state)
        self.anim_timer.start(50) 
        
        if auto_arm:
            self.display.set_log("AUTO-SEQUENCE INITIATED...")
            QTimer.singleShot(2000, lambda: self.btn_arm.setChecked(True))
            
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(100, 39, 100, 39)
        main_layout.setSpacing(26)
        
        # ---- LEFT: VU METERS ----
        vu_layout = QHBoxLayout()
        self.vu_left = LedMatrixVuMeter()
        self.vu_right = LedMatrixVuMeter()
        add_shadow(self.vu_left, 10, 2, 8)
        add_shadow(self.vu_right, 10, 2, 8)
        vu_layout.addWidget(self.vu_left)
        vu_layout.addWidget(self.vu_right)
        main_layout.addLayout(vu_layout)
        
        # ---- CENTER: MAIN DISPLAY ----
        self.display = BoutiqueMainDisplay()
        main_layout.addWidget(self.display)
        
        # ---- RIGHT: CONTROLS ----
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(20)
        
        # Target Input Area
        target_layout = QHBoxLayout()
        self.url_input = QLineEdit("https://www.iheart.com/live/newsradio-830-khvh-4748/")
        add_shadow(self.url_input, blur=5, y=3)
        lbl_src = QLabel("SOURCE")
        lbl_src.setStyleSheet("color: #333;")
        target_layout.addWidget(lbl_src)
        target_layout.addWidget(self.url_input)
        self.url_input.textChanged.connect(lambda t: self.display.set_target(t[:40]))
        controls_layout.addLayout(target_layout)
        
        # Device Combo
        dev_layout = QHBoxLayout()
        self.device_combo = QComboBox()
        add_shadow(self.device_combo, blur=5, y=3)
        lbl_dev = QLabel("DEVICE")
        lbl_dev.setStyleSheet("color: #333;")
        dev_layout.addWidget(lbl_dev)
        dev_layout.addWidget(self.device_combo)
        controls_layout.addLayout(dev_layout)
        
        # --- Scheduling Area ---
        sched_layout = QHBoxLayout()
        lbl_st = QLabel("START")
        lbl_st.setStyleSheet("color: #333;")
        sched_layout.addWidget(lbl_st)
        
        self.time_input = QTimeEdit()
        self.time_input.setDisplayFormat("HH:mm")
        self.time_input.setTime(datetime.now().time())
        add_shadow(self.time_input, blur=5, y=3)
        sched_layout.addWidget(self.time_input)
        
        lbl_dur = QLabel("DUR(M)")
        lbl_dur.setStyleSheet("color: #333;")
        sched_layout.addWidget(lbl_dur)
        
        self.dur_input = QSpinBox()
        self.dur_input.setRange(1, 1440)
        self.dur_input.setValue(60)
        add_shadow(self.dur_input, blur=5, y=3)
        sched_layout.addWidget(self.dur_input)
        
        self.btn_arm = QPushButton("ARM SEQ")
        self.btn_arm.setCheckable(True)
        self.btn_arm.setFixedSize(120, 40)
        self.btn_arm.setStyleSheet("""
            QPushButton { 
                background-color: #331100; color: #ff5500; border: 2px solid #ff5500; 
                border-radius: 6px; font-weight: bold; font-size: 15px;
            }
            QPushButton:checked { 
                background-color: #ff5500; color: #fff; border: 2px solid #fff;
            }
        """)
        add_shadow(self.btn_arm, blur=10, y=5)
        self.btn_arm.toggled.connect(self.arm_mission)
        sched_layout.addWidget(self.btn_arm)
        
        controls_layout.addLayout(sched_layout)
        
        # Button Grid (Dimmer, Power, Up, Record)
        btn_layout = QHBoxLayout()
        
        # Dimmer
        dim_layout = QVBoxLayout()
        self.dimmer = BoutiqueDimmerKnob()
        self.dimmer.valueChanged.connect(self.on_dimmer_changed)
        dim_layout.addWidget(self.dimmer, alignment=Qt.AlignmentFlag.AlignCenter)
        lbl_dim = QLabel("DIM")
        lbl_dim.setStyleSheet("color: #444; font-size: 12px;")
        dim_layout.addWidget(lbl_dim, alignment=Qt.AlignmentFlag.AlignCenter)
        btn_layout.addLayout(dim_layout)
        
        btn_layout.addStretch()
        
        # Power Switch
        pow_layout = QVBoxLayout()
        self.sw_power = BoutiqueSwitch()
        self.sw_power.toggled.connect(self.toggle_stream)
        pow_layout.addWidget(self.sw_power, alignment=Qt.AlignmentFlag.AlignCenter)
        lbl_pwr = QLabel("PWR")
        lbl_pwr.setStyleSheet("color: #444; font-size: 12px;")
        pow_layout.addWidget(lbl_pwr, alignment=Qt.AlignmentFlag.AlignCenter)
        btn_layout.addLayout(pow_layout)
        
        # Upload Switch
        up_layout = QVBoxLayout()
        self.sw_upload = BoutiqueSwitch()
        self.sw_upload.toggled.connect(self.toggle_autoupload)
        up_layout.addWidget(self.sw_upload, alignment=Qt.AlignmentFlag.AlignCenter)
        lbl_up = QLabel("SYNC")
        lbl_up.setStyleSheet("color: #444; font-size: 12px;")
        up_layout.addWidget(lbl_up, alignment=Qt.AlignmentFlag.AlignCenter)
        btn_layout.addLayout(up_layout)
        
        btn_layout.addStretch()
        
        # Record Button
        rec_layout = QVBoxLayout()
        self.btn_rec = BoutiqueRecordButton()
        add_shadow(self.btn_rec, blur=20, y=8)
        self.btn_rec.toggled.connect(self.toggle_manual_recording)
        rec_layout.addWidget(self.btn_rec, alignment=Qt.AlignmentFlag.AlignCenter)
        lbl_rec = QLabel("REC OVR")
        lbl_rec.setStyleSheet("color: #f50; font-size: 15px; font-weight: bold;")
        rec_layout.addWidget(lbl_rec, alignment=Qt.AlignmentFlag.AlignCenter)
        btn_layout.addLayout(rec_layout)
        
        controls_layout.addLayout(btn_layout)
        main_layout.addLayout(controls_layout)
        
        self.display.set_target(self.url_input.text()[:40])

    def populate_device_list(self):
        devices = main.AudioRecorder.get_audio_devices()
        self.device_combo.clear()
        default_index = 0
        for i, dev in enumerate(devices):
            name = dev['name']
            if "Stereo Mix" in name:
                default_index = i
            self.device_combo.addItem(name, dev['index'])
        self.device_combo.setCurrentIndex(default_index)

    def on_dimmer_changed(self, level):
        darkness = 1.0 - level
        if darkness > 0.05:
            self.dimmer_overlay.show()
            self.dimmer_overlay.setStyleSheet(f"background-color: rgba(0, 0, 0, {int(darkness * 255)});")
        else:
            self.dimmer_overlay.hide()

    def update_ui_state(self):
        self.display.set_time(datetime.now().strftime('%H:%M:%S'))
        self.display.update() 
        
        vu_level = -40
        is_rec = False
        
        if main.manual_recorder_instance and getattr(main.manual_recorder_instance, 'is_recording', False):
            vu_level = getattr(main.manual_recorder_instance, 'current_vu', -40)
            is_rec = True
        elif main.scheduled_recorder_instance and getattr(main.scheduled_recorder_instance, 'is_recording', False):
            vu_level = getattr(main.scheduled_recorder_instance, 'current_vu', -40)
            is_rec = True
            
        if is_rec or self.display.active:
            if is_rec:
                base_val = vu_level + random.uniform(-0.5, 0.5)
            else:
                base_val = -20 + random.uniform(-1, 2)
            self.vu_left.set_value(base_val)
            self.vu_right.set_value(max(-22, base_val - random.uniform(0, 1.5)))
        else:
            self.vu_left.set_value(-22)
            self.vu_right.set_value(-22)

    def toggle_stream(self, checked):
        self.stream_active = checked
        if checked:
            self.display.set_log("PWR ON: BOOTING BROWSER...")
            self.display.set_active(True)
            target = self.url_input.text()
            self.browser_thread = BrowserController(target)
            self.browser_thread.status_update.connect(self.display.set_log)
            self.browser_thread.start()
        else:
            self.display.set_log("PWR OFF: STREAM STOPPED.")
            self.display.set_active(False)
            if self.browser_thread:
                self.browser_thread.stop()
                self.browser_thread = None

    def toggle_manual_recording(self, checked):
        device_idx = self.device_combo.currentData()
        if checked:
            self.display.set_log(">> RECORDING ACTIVE <<")
            if not main.start_manual_recording(device_index=device_idx):
                self.display.set_log("REC FAILED.")
                self.btn_rec.set_checked(False) 
        else:
            self.display.set_log("REC STOPPED. FILE SAVED.")
            main.stop_manual_recording()
            
    def toggle_autoupload(self, checked):
        config.ENABLE_GOOGLE_DRIVE_UPLOAD = checked
        state = "ENABLED" if checked else "DISABLED"
        self.display.set_log(f"AUTO-UPLOAD {state}")

    def arm_mission(self, armed):
        if armed:
            target_url = self.url_input.text()
            run_time_q = self.time_input.time()
            now = datetime.now()
            target_time = datetime.combine(now.date(), run_time_q.toPyTime())
            if target_time < now:
                target_time += timedelta(days=1)
                
            duration = self.dur_input.value() * 60
            device_idx = self.device_combo.currentData()
            
            self.display.set_log(f"ARMED: {target_time.strftime('%H:%M')} for {duration//60}m")
            
            if not main.schedule_one_off_mission(target_time, target_url, duration, device_idx):
                self.display.set_log("SCHEDULING FAILED.")
                self.btn_arm.setChecked(False) 
        else:
            self.display.set_log("MISSION ABORTED")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Pure Black Void
        painter.setBrush(QColor(COLOR_VOID))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        
        # Main Floating Console Body (Silver Brushed Aluminum)
        body_rect = QRectF(20, 20, self.width()-40, self.height()-40)
        
        # 3D Bevel/Gradient for panel
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor("#f5f7fa")) # Bright silver top
        grad.setColorAt(1, QColor("#a8acb6")) # Darker cast silver bottom
        painter.setBrush(grad)
        
        # Highlight top edge and shadow bottom edge via pen
        painter.setPen(QPen(QColor("#ffffff"), 3)) # White rim highlight
        painter.drawRoundedRect(body_rect, 20, 20)
        
        # Brushed texture (Horizontal lines)
        painter.setClipRect(body_rect)
        painter.setPen(QPen(QColor(0, 0, 0, 12), 1))
        for y in range(20, self.height()-20, 3):
            painter.drawLine(20, y, self.width()-20, y)
        painter.setClipping(False)
        
        # Draw Speaker Grill Slots
        painter.setPen(QPen(QColor("#222"), 8, cap=Qt.PenCapStyle.RoundCap))
        
        # Left speaker
        for x in range(40, 100, 16):
            painter.drawLine(x, 60, x, self.height()-60)
            
        # Right speaker
        for x in range(self.width()-88, self.width()-30, 16):
            painter.drawLine(x, 60, x, self.height()-60)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="iHeart Recorder Boutique Edition")
    parser.add_argument("--auto-schedule", action="store_true", help="Automatically arm")
    args = parser.parse_args()
    
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = IHeartBoutiqueGUI(auto_arm=args.auto_schedule)
    window.show()
    sys.exit(app.exec())
