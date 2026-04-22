import sys
import os
import time 
import logging
import threading
from datetime import datetime, timedelta
import math
import random

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox, QCheckBox, QSystemTrayIcon, 
    QMenu, QMessageBox, QFileDialog, QProgressBar, QGridLayout,
    QFrame, QSizePolicy, QListWidget, QListWidgetItem, QLineEdit,
    QDialog, QDateTimeEdit, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QUrl, QDateTime, QPoint, QRectF, QPointF, QTime
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor, QBrush, QPen, QImage, QAction, QCursor, QRadialGradient, QLinearGradient, QConicalGradient, QPainterPath, QBitmap

# Import main logic
import main
import config
from browser_automation import BrowserController

# Setup logging
logging.basicConfig(
    filename='iheart_recorder_gui.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(threadName)s - %(message)s'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

# Paths
RESOURCES_DIR = getattr(config, 'RESOURCES_DIR', os.path.join(os.path.dirname(__file__), "resources"))

# Constants for Cockpit Theme
FONT_STENCIL = "Courier New" 
COLOR_TEXT_GLOW = "#ffb84d" 
COLOR_TEXT_GREEN = "#33ff33" 
COLOR_METAL_DARK = "#2b2b2b"
IMG_BG = "ui_background_metal.png"

class CockpitSwitch(QWidget):
    """
    Vertical Plate Switch with Red Guard (SS 2 Style).
    Text is drawn vertically on the plate.
    """
    toggled = pyqtSignal(bool)

    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        self.is_on = False
        self.label_text = label_text
        self.setFixedSize(60, 160) # Increased height for text
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # ===== DROP SHADOW =====
        shadow_grad = QRadialGradient(w/2 + 5, h/2 + 5, max(w, h) * 0.6)
        shadow_grad.setColorAt(0, QColor(0, 0, 0, 80))
        shadow_grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(shadow_grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(8, 8, 52, 152, 6, 6)
        
        # ===== MAIN PLATE =====
        plate_rect = QRectF(5, 5, 50, 150)
        
        # Worn metal gradient
        grad = QLinearGradient(0, 0, 60, 0)
        grad.setColorAt(0, QColor("#b0b0b0"))
        grad.setColorAt(0.15, QColor("#d8d8d8"))
        grad.setColorAt(0.5, QColor("#c0c0c0"))
        grad.setColorAt(0.85, QColor("#a8a8a8"))
        grad.setColorAt(1, QColor("#909090"))
        
        painter.setBrush(grad)
        painter.setPen(QPen(QColor("#555"), 2))
        painter.drawRoundedRect(plate_rect, 6, 6)
        
        # ===== EDGE BEVELS =====
        # Top highlight
        painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
        painter.drawLine(8, 7, 52, 7)
        # Bottom shadow
        painter.setPen(QPen(QColor(0, 0, 0, 80), 1))
        painter.drawLine(8, 153, 52, 153)
        
        # ===== SCRATCHES & WEAR =====
        painter.setPen(QPen(QColor(0, 0, 0, 40), 1))
        for i in range(8):
            x1 = random.randint(10, 50)
            y1 = random.randint(10, 150)
            x2 = x1 + random.randint(-15, 15)
            y2 = y1 + random.randint(-25, 25)
            painter.drawLine(x1, y1, x2, y2)
        
        # Rust spots
        painter.setPen(Qt.PenStyle.NoPen)
        for _ in range(3):
            rx, ry = random.randint(12, 48), random.randint(20, 140)
            rs = random.randint(2, 5)
            rust = QRadialGradient(rx, ry, rs)
            rust.setColorAt(0, QColor(100, 50, 30, 60))
            rust.setColorAt(1, QColor(80, 40, 20, 0))
            painter.setBrush(rust)
            painter.drawEllipse(rx-rs, ry-rs, rs*2, rs*2)
        
        # ===== SCREWS WITH DEPTH =====
        def draw_screw(x, y):
            # Shadow
            painter.setBrush(QColor(0, 0, 0, 100))
            painter.drawEllipse(x+1, y+1, 6, 6)
            # Body
            screw_grad = QRadialGradient(x+3, y+3, 4)
            screw_grad.setColorAt(0, QColor("#666"))
            screw_grad.setColorAt(1, QColor("#222"))
            painter.setBrush(screw_grad)
            painter.drawEllipse(x, y, 6, 6)
            # Slot
            painter.setPen(QPen(QColor("#111"), 1))
            painter.drawLine(x+1, y+3, x+5, y+3)
        
        draw_screw(9, 9)
        draw_screw(45, 9)
        draw_screw(9, 145)
        draw_screw(45, 145)
        
        # ===== BLACK INSET (RECESSED) =====
        inset_rect = QRectF(10, 32, 40, 56)
        # Inner shadow
        painter.setBrush(QColor("#0a0a0a"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(inset_rect, 4, 4)
        # Highlight edge (bottom)
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawLine(12, 86, 48, 86)
        
        # ===== RED GUARD =====
        guard_rect = QRectF(10, 12, 40, 18)
        guard_grad = QLinearGradient(0, 12, 0, 30)
        guard_grad.setColorAt(0, QColor("#dd2020"))
        guard_grad.setColorAt(0.5, QColor("#aa0000"))
        guard_grad.setColorAt(1, QColor("#660000"))
        painter.setBrush(guard_grad)
        painter.setPen(QPen(QColor("#330000"), 1))
        painter.drawRoundedRect(guard_rect, 3, 3)
        
        # Guard wear
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.drawLine(12, 14, 48, 14)
        
        # ===== TOGGLE SWITCH =====
        cx, cy = 30, 60
        offset = -18 if self.is_on else 18
        
        # Base nut
        nut_grad = QRadialGradient(cx, cy, 12)
        nut_grad.setColorAt(0, QColor("#888"))
        nut_grad.setColorAt(1, QColor("#444"))
        painter.setBrush(nut_grad)
        painter.setPen(QPen(QColor("#222"), 1))
        painter.drawEllipse(QPointF(cx, cy), 11, 11)
        
        # Lever
        lever_grad = QLinearGradient(cx-5, cy, cx+5, cy+offset)
        lever_grad.setColorAt(0, QColor("#e8e8e8"))
        lever_grad.setColorAt(0.5, QColor("#c0c0c0"))
        lever_grad.setColorAt(1, QColor("#a0a0a0"))
        painter.setBrush(lever_grad)
        painter.setPen(QPen(QColor("#555"), 1))
        
        path = QPainterPath()
        path.moveTo(cx-4, cy)
        path.lineTo(cx+4, cy)
        path.lineTo(cx+6, cy+offset)
        path.arcTo(cx-6, cy+offset-6, 12, 12, 0, 180 if self.is_on else -180)
        path.lineTo(cx-4, cy)
        painter.drawPath(path)
        
        # Tip highlight
        tip_y = cy + offset
        painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
        painter.drawArc(int(cx-5), int(tip_y-5), 10, 10, 45*16, 90*16)
        
        # ===== VERTICAL TEXT =====
        painter.save()
        painter.translate(cx, 132)
        painter.rotate(-90)
        
        font_size = 9 if len(self.label_text) > 6 else 11
        painter.setFont(QFont("Arial", font_size, QFont.Weight.Bold))
        
        # Shadow
        painter.setPen(QColor(0, 0, 0, 150))
        painter.drawText(QRectF(-48, -12, 96, 26), Qt.AlignmentFlag.AlignCenter, self.label_text)
        # Main text
        painter.setPen(QColor("#1a1a1a"))
        painter.drawText(QRectF(-49, -13, 96, 26), Qt.AlignmentFlag.AlignCenter, self.label_text)
        painter.restore()

    def mousePressEvent(self, event):
        self.set_checked(not self.is_on)
        self.toggled.emit(self.is_on)

    def set_checked(self, checked):
        self.is_on = checked
        self.update()

class CockpitLever(QWidget):
    """Custom Arm Mission Lever (Red Box Style)."""
    triggered = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_armed = False
        self.setFixedSize(110, 140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # ===== DEEP DROP SHADOW =====
        shadow = QRadialGradient(w/2 + 8, h/2 + 8, max(w, h) * 0.7)
        shadow.setColorAt(0, QColor(0, 0, 0, 120))
        shadow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(shadow)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(10, 10, 100, 130, 6, 6)
        
        # ===== MAIN PLATE =====
        plate_rect = QRectF(5, 5, 100, 130)
        
        # Worn brushed metal
        plate_grad = QLinearGradient(0, 0, 110, 0)
        plate_grad.setColorAt(0, QColor("#a0a0a0"))
        plate_grad.setColorAt(0.15, QColor("#d0d0d0"))
        plate_grad.setColorAt(0.5, QColor("#b8b8b8"))
        plate_grad.setColorAt(0.85, QColor("#989898"))
        plate_grad.setColorAt(1, QColor("#808080"))
        
        painter.setBrush(plate_grad)
        painter.setPen(QPen(QColor("#444"), 2))
        painter.drawRoundedRect(plate_rect, 6, 6)
        
        # Edge highlights/bevels
        painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
        painter.drawLine(8, 7, 102, 7)  # Top
        painter.drawLine(7, 8, 7, 132)  # Left
        painter.setPen(QPen(QColor(0, 0, 0, 60), 1))
        painter.drawLine(8, 133, 102, 133)  # Bottom
        painter.drawLine(103, 8, 103, 132)  # Right
        
        # ===== HEAVY PATINA =====
        painter.setPen(QPen(QColor(0, 0, 0, 50), 1))
        for _ in range(12):
            x1 = random.randint(10, 100)
            y1 = random.randint(10, 130)
            x2 = x1 + random.randint(-20, 20)
            y2 = y1 + random.randint(-30, 30)
            painter.drawLine(x1, y1, x2, y2)
        
        # Rust spots
        painter.setPen(Qt.PenStyle.NoPen)
        for _ in range(5):
            rx, ry = random.randint(12, 98), random.randint(12, 128)
            rs = random.randint(3, 8)
            rust = QRadialGradient(rx, ry, rs)
            rust.setColorAt(0, QColor(110, 55, 25, 70))
            rust.setColorAt(1, QColor(70, 35, 15, 0))
            painter.setBrush(rust)
            painter.drawEllipse(rx-rs, ry-rs, rs*2, rs*2)
        
        # ===== 3D SCREWS =====
        def draw_screw(x, y):
            painter.setBrush(QColor(0, 0, 0, 120))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(x+2, y+2, 8, 8)
            screw_grad = QRadialGradient(x+4, y+4, 5)
            screw_grad.setColorAt(0, QColor("#777"))
            screw_grad.setColorAt(1, QColor("#333"))
            painter.setBrush(screw_grad)
            painter.drawEllipse(x, y, 8, 8)
            painter.setPen(QPen(QColor("#1a1a1a"), 1))
            painter.drawLine(x+2, y+4, x+6, y+4)
        
        draw_screw(8, 8)
        draw_screw(92, 8)
        draw_screw(8, 122)
        draw_screw(92, 122)
        
        if not self.is_armed:
            # ===== SAFE COVER (Closed) =====
            cover_rect = QRectF(15, 22, 80, 96)
            
            # Cover shadow
            painter.setBrush(QColor(0, 0, 0, 100))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(cover_rect.adjusted(4, 4, 4, 4), 4, 4)
            
            # Red cover with worn gradient
            cover_grad = QLinearGradient(15, 22, 15, 118)
            cover_grad.setColorAt(0, QColor("#dd3030"))
            cover_grad.setColorAt(0.3, QColor("#cc1010"))
            cover_grad.setColorAt(0.7, QColor("#990000"))
            cover_grad.setColorAt(1, QColor("#660000"))
            painter.setBrush(cover_grad)
            painter.setPen(QPen(QColor("#330000"), 2))
            painter.drawRoundedRect(cover_rect, 4, 4)
            
            # White stripes (dirty/worn)
            painter.save()
            painter.setClipRect(cover_rect)
            painter.setPen(QPen(QColor(230, 225, 210, 200), 7))
            for i in range(-30, 150, 22):
                painter.drawLine(10, i, 120, i + 30)
            painter.restore()
            
            # Worn edges on cover
            painter.setPen(QPen(QColor(255, 255, 255, 40), 1))
            painter.drawLine(17, 24, 93, 24)  # Top highlight
            
            # "SAFE" text
            painter.setFont(QFont("Arial Black", 18, QFont.Weight.Bold))
            # Shadow
            painter.setPen(QColor(0, 0, 0, 200))
            painter.drawText(cover_rect.adjusted(2, 2, 2, 2), Qt.AlignmentFlag.AlignCenter, "SAFE")
            # Main
            painter.setPen(QColor("#fff"))
            painter.drawText(cover_rect, Qt.AlignmentFlag.AlignCenter, "SAFE")
            
        else:
            # ===== ARMED STATE (Cover Open) =====
            # Recessed area
            recess_rect = QRectF(18, 28, 74, 88)
            painter.setBrush(QColor("#0a0a0a"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(recess_rect, 4, 4)
            # Inner shadow
            painter.setPen(QPen(QColor(0, 0, 0, 150), 2))
            painter.drawLine(20, 30, 90, 30)
            
            # Yellow toggle
            toggle_grad = QLinearGradient(45, 35, 65, 35)
            toggle_grad.setColorAt(0, QColor("#f0d000"))
            toggle_grad.setColorAt(0.5, QColor("#e8c800"))
            toggle_grad.setColorAt(1, QColor("#d0b000"))
            painter.setBrush(toggle_grad)
            painter.setPen(QPen(QColor("#887700"), 2))
            painter.drawRoundedRect(42, 38, 26, 68, 6, 6)
            
            # Toggle highlight
            painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
            painter.drawLine(44, 40, 66, 40)
            
            # Warning glow
            glow = QRadialGradient(55, 115, 35)
            glow.setColorAt(0, QColor(255, 50, 0, 200))
            glow.setColorAt(0.5, QColor(255, 0, 0, 80))
            glow.setColorAt(1, QColor(255, 0, 0, 0))
            painter.setBrush(glow)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(22, 82, 66, 66)

    def mousePressEvent(self, event):
        self.is_armed = not self.is_armed
        self.update()
        self.triggered.emit(self.is_armed)

    def set_checked(self, checked):
        """Programmatically set the armed state."""
        if self.is_armed != checked:
            self.is_armed = checked
            self.update()
            self.triggered.emit(self.is_armed)

class AnalogGauge(QWidget):
    """
    Square Gauge with Cream Face (SS 1 Style).
    """
    def __init__(self, label_text="VU", parent=None):
        super().__init__(parent)
        self.value = 0 
        self.label_text = label_text
        self.setFixedSize(140, 140)

    def set_value(self, val):
        self.value = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        cx, cy = 70, 100 # Pivot point lower for arc
        
        # 1. Square Case (Dark Grey/Black with rounded corners)
        case_rect = QRectF(5, 5, 130, 130)
        grad_case = QLinearGradient(0, 0, 140, 140)
        grad_case.setColorAt(0, QColor("#444"))
        grad_case.setColorAt(1, QColor("#222"))
        painter.setBrush(grad_case)
        painter.setPen(QPen(QColor("#111"), 2))
        painter.drawRoundedRect(case_rect, 15, 15)
        
        # Screws in corners
        painter.setBrush(QColor("#111"))
        for x, y in [(15, 15), (125, 15), (15, 125), (125, 125)]:
            painter.drawEllipse(QPointF(x, y), 3, 3)
            
        # 2. Gauge Face (Cream/Yellow, "D" shape window)
        # We can draw a large circle clip or just a complex shape
        face_rect = QRectF(15, 15, 110, 110)
        painter.setBrush(QColor("#f5e6bb")) # Cream yellow
        painter.setPen(QPen(QColor("#000"), 2))
        painter.drawEllipse(face_rect)
        
        # 3. Ticks & Scale
        # Arc from approx 150 deg to 30 deg (spanning top)
        # Needle pivot is at approx (70, 70) if centered, let's say center is (70,70)
        cx, cy = 70, 70
        radius = 45 
        
        painter.setPen(QPen(QColor("#000"), 2))
        painter.setFont(QFont("Arial", 7))
        
        for i in range(-20, 4, 1): # dB Scale
            angle_deg = -135 + ((i + 20) * 4) # Map range
            rad = math.radians(angle_deg)
            
            p1 = QPointF(cx + radius * math.cos(rad), cy + radius * math.sin(rad))
            p2 = QPointF(cx + (radius+5) * math.cos(rad), cy + (radius+5) * math.sin(rad))
            
            if i % 5 == 0:
                painter.drawLine(p1, p2)
                # Label
                tp = QPointF(cx + (radius-10) * math.cos(rad), cy + (radius-10) * math.sin(rad))
                painter.drawText(QRectF(tp.x()-10, tp.y()-10, 20, 20), Qt.AlignmentFlag.AlignCenter, str(i))
            else:
                p2_short = QPointF(cx + (radius+3) * math.cos(rad), cy + (radius+3) * math.sin(rad))
                painter.drawLine(p1, p2_short)
                
        # "VU" Label
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(QRectF(0, 80, 140, 30), Qt.AlignmentFlag.AlignCenter, "VU")
        painter.setFont(QFont("Arial", 8))
        painter.drawText(QRectF(10, 100, 30, 20), Qt.AlignmentFlag.AlignCenter, "VO")
        painter.drawText(QRectF(100, 100, 30, 20), Qt.AlignmentFlag.AlignCenter, "VU")

        # 4. Needle
        painter.save()
        painter.translate(cx, cy)
        # Map dB value (-20 to +3) to specific angles per the tick marks drawn above
        clamped_val = max(-22, min(4, self.value))
        needle_angle = -135 + ((clamped_val + 20) * 4) 
        painter.rotate(needle_angle)
        
        painter.setBrush(QColor("#222"))
        painter.setPen(Qt.PenStyle.NoPen)
        # Thin needle
        painter.drawConvexPolygon([QPointF(-1, 0), QPointF(1, 0), QPointF(0, -45)])
        painter.restore()
        
        # Center Cap
        painter.setBrush(QColor("#333"))
        painter.drawEllipse(QPointF(cx, cy), 8, 8)
        
        # Glass Reflection
        grad_glass = QLinearGradient(0, 0, 0, 70)
        grad_glass.setColorAt(0, QColor(255, 255, 255, 50))
        grad_glass.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(grad_glass)
        painter.drawEllipse(face_rect)


class VintagePlate(QWidget):
    """
    Stamped Metal Name Plate.
    """
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
        self.setFixedHeight(24)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Metal Plate Gradient
        grad = QLinearGradient(0, 0, 0, rect.height())
        grad.setColorAt(0, QColor("#888"))
        grad.setColorAt(0.5, QColor("#e0e0e0"))
        grad.setColorAt(1, QColor("#999"))
        painter.setBrush(grad)
        painter.setPen(QPen(QColor("#222"), 1))
        painter.drawRoundedRect(rect.adjusted(2,2,-2,-2), 2, 2)
        
        # Rivets
        painter.setBrush(QColor("#333"))
        painter.drawEllipse(5, 10, 3, 3)
        painter.drawEllipse(rect.width()-8, 10, 3, 3)
        
        # Stamped Text (Debossed effect)
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        
        # Highlight (Bottom-Right)
        painter.setPen(QColor(255, 255, 255, 120))
        painter.drawText(rect.adjusted(1, 1, 0, 0), Qt.AlignmentFlag.AlignCenter, self.text)
        
        # Shadow (Top-Left)
        painter.setPen(QColor(0, 0, 0, 180))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text)

class CockpitClipboard(QWidget):
    """
    Flight Plan Clipboard - Shows recording schedule and status updates.
    Bolted to the dash, holding worn paper with mission orders.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 420)
        
        # Layout to hold the transparent list widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 85, 25, 25)  # Top margin for clip
        
        # Title label
        self.title_lbl = QLabel("FLIGHT PLAN")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_lbl.setStyleSheet("""
            color: #303030;
            font-family: 'Courier New';
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 2px;
            text-decoration: underline;
        """)
        layout.addWidget(self.title_lbl)
        layout.addSpacing(5)
        
        self.log_list = QListWidget()
        self.log_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.log_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Transparent background, Courier font to look like typed/stamped text
        self.log_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                font-family: 'Courier New';
                font-size: 12px;
                font-weight: bold;
                color: #202020;
                outline: none;
            }
            QListWidget::item {
                padding: 3px 0px;
                border-bottom: 1px dashed #ccc;
            }
        """)
        layout.addWidget(self.log_list)
    
    def set_schedule(self, start_time, stop_time, station_name="iHeart"):
        """Display the recording schedule on the clipboard."""
        self.log_list.clear()
        
        # Format times
        start_str = start_time.strftime("%H:%M") if hasattr(start_time, 'strftime') else str(start_time)
        stop_str = stop_time.strftime("%H:%M") if hasattr(stop_time, 'strftime') else str(stop_time)
        date_str = start_time.strftime("%b %d") if hasattr(start_time, 'strftime') else "TODAY"
        
        # Calculate duration
        from datetime import timedelta
        if hasattr(start_time, 'replace') and hasattr(stop_time, 'replace'):
            if stop_time <= start_time:
                duration = (stop_time + timedelta(days=1)) - start_time
            else:
                duration = stop_time - start_time
            hours, remainder = divmod(int(duration.total_seconds()), 3600)
            minutes = remainder // 60
            dur_str = f"{hours}h {minutes}m"
        else:
            dur_str = "—"
        
        # Add schedule entries
        self.log_list.addItem(f"DATE: {date_str.upper()}")
        self.log_list.addItem(f"————————————————")
        self.log_list.addItem(f"START: {start_str}")
        self.log_list.addItem(f"STOP:  {stop_str}")
        self.log_list.addItem(f"DURATION: {dur_str}")
        self.log_list.addItem(f"————————————————")
        self.log_list.addItem(f"TARGET: {station_name[:18]}")
        self.log_list.addItem("")
        self.log_list.addItem("STATUS: READY")
    
    def add_status(self, status_text):
        """Add a status update to the clipboard."""
        # Find and update STATUS line, or add new line
        for i in range(self.log_list.count()):
            item = self.log_list.item(i)
            if item and item.text().startswith("STATUS:"):
                item.setText(f"STATUS: {status_text}")
                return
        # If no STATUS line found, add one
        self.log_list.addItem(f"STATUS: {status_text}")
    
    def add_log(self, message):
        """Add a log message to the clipboard."""
        # Truncate long messages
        if len(message) > 28:
            message = message[:25] + "..."
        self.log_list.addItem(message)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        w, h = rect.width(), rect.height()
        
        # 1. Wood Board (Backing)
        # Dark Mahogany Gradient
        wood_grad = QLinearGradient(0, 0, w, 0)
        wood_grad.setColorAt(0, QColor("#3e2723")) # Dark Brown
        wood_grad.setColorAt(0.3, QColor("#5d4037")) # Lighter Brown
        wood_grad.setColorAt(0.6, QColor("#4e342e"))
        wood_grad.setColorAt(1, QColor("#3e2723"))
        painter.setBrush(wood_grad)
        painter.setPen(QPen(QColor("#1b0000"), 2))
        painter.drawRoundedRect(5, 5, w-10, h-10, 4, 4)
        
        # Grain Lines (Simple Code-drawn texture)
        painter.setPen(QColor(0, 0, 0, 40))
        for i in range(0, w, 5):
            # Wobbly vertical lines
            path = QPainterPath()
            path.moveTo(i, 5)
            path.cubicTo(i+random.randint(-5,5), h/3, i+random.randint(-5,5), 2*h/3, i, h-5)
            painter.drawPath(path)

        # 2. Bolts (Mounting to Dash)
        painter.setBrush(QColor("#111")) # Bolt head
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(10, 10, 8, 8)
        painter.drawEllipse(w-18, 10, 8, 8)
        painter.drawEllipse(10, h-18, 8, 8)
        painter.drawEllipse(w-18, h-18, 8, 8)
        
        # 3. Worn Paper
        paper_rect = QRectF(20, 40, w-40, h-60)
        painter.setBrush(QColor("#fdfae0")) # Base parchmnent
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(paper_rect)
        
        # Paper Aging (Gradient Overlay)
        age_grad = QRadialGradient(w/2, h/2, h/1.5)
        age_grad.setColorAt(0, QColor(255, 255, 255, 0))
        age_grad.setColorAt(1, QColor(139, 69, 19, 50)) # Brown stain edges
        painter.setBrush(age_grad)
        painter.drawRect(paper_rect)
        
        # Wrinkles / Use marks
        painter.setPen(QPen(QColor(0, 0, 0, 30), 1))
        painter.drawLine(QPointF(20, 100), QPointF(50, 110))
        painter.drawLine(QPointF(w-20, 300), QPointF(w-60, 290))
        
        # 4. Pewter Clip (Top)
        clip_rect = QRectF(60, 15, w-120, 50)
        
        # Metal Gradient (Worn Pewter: Grey/Blueish with noise)
        pewter_grad = QLinearGradient(0, 15, 0, 65)
        pewter_grad.setColorAt(0, QColor("#5a6065"))
        pewter_grad.setColorAt(0.2, QColor("#9ba0a5")) # Highlight
        pewter_grad.setColorAt(0.5, QColor("#5a6065"))
        pewter_grad.setColorAt(0.9, QColor("#3f4448")) # Shadow
        painter.setBrush(pewter_grad)
        painter.setPen(QPen(QColor("#222"), 2))
        
        # Draw Clip Shape (Rounded at bottom)
        clip_path = QPainterPath()
        clip_path.addRoundedRect(clip_rect, 10, 10)
        painter.drawPath(clip_path)
        
        # Rust/Grime on Clip
        painter.setBrush(QColor(100, 50, 0, 30))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(clip_rect.adjusted(5, 30, -5, -5), 5, 5) # Bottom part dirtier
        
        # Spring Mechanism / Rivets on Clip
        painter.setBrush(QColor("#222"))
        painter.drawEllipse(70, 25, 8, 8)
        painter.drawEllipse(w-78, 25, 8, 8)

class FlipClockWidget(QWidget):
    """
    Split-Flap Style Display (SS 3).
    Heavy frame, individual character tiles.
    Interactive: Scroll to change values.
    Now includes START TIME, STOP TIME, and SOURCE TIMEZONE for DST adjustment.
    """
    # Timezone mapping for DST calculation
    TIMEZONES = {
        "PACIFIC": "America/Los_Angeles",
        "MOUNTAIN": "America/Denver", 
        "CENTRAL": "America/Chicago",
        "EASTERN": "America/New_York",
        "HAWAII": "Pacific/Honolulu",
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 380)  # Increased for timezone selector
        self.mission_time = datetime.now()
        
        # Source timezone for broadcast
        self.source_tz_name = "PACIFIC"  # Default
        
        # Default start/stop times in SOURCE timezone (not Phoenix)
        # These are the times the show AIRS in the source timezone
        from datetime import timedelta
        self.source_start_hour = 23  # 11 PM in source TZ
        self.source_start_min = 6
        self.source_stop_hour = 3   # 3 AM in source TZ
        self.source_stop_min = 4
        
        # Calculate Phoenix-adjusted times
        self._calculate_phoenix_times()
        
        # Main Frame Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(2)
        
        # Top Row: Date
        self.plate_date = VintagePlate("MISSION DATE")
        self.date_lbl = QLabel(self.mission_time.strftime("%b %d %Y").upper())
        self.date_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_lbl.setStyleSheet(self._flap_style())
        
        # Row 2: Current Time
        self.plate_time = VintagePlate("TIME")
        self.time_lbl = QLabel(self.mission_time.strftime("%H:%M:%S"))
        self.time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_lbl.setStyleSheet(self._flap_style())
        
        # Row 3: Start Time (Phoenix local)
        self.plate_start = VintagePlate("START TIME")
        self.start_lbl = QLabel(self.start_time.strftime("%H:%M"))
        self.start_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.start_lbl.setStyleSheet(self._flap_style_small())
        self.start_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_lbl.mousePressEvent = lambda e: self.edit_start_time()
        
        # Row 4: Stop Time (Phoenix local)
        self.plate_stop = VintagePlate("STOP TIME")
        self.stop_lbl = QLabel(self.stop_time.strftime("%H:%M"))
        self.stop_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stop_lbl.setStyleSheet(self._flap_style_small())
        self.stop_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_lbl.mousePressEvent = lambda e: self.edit_stop_time()
        
        layout.addWidget(self.plate_date)
        layout.addWidget(self.date_lbl)
        layout.addSpacing(4)
        layout.addWidget(self.plate_time)
        layout.addWidget(self.time_lbl)
        layout.addSpacing(6)
        
        # Start/Stop time row (horizontal layout)
        time_row = QHBoxLayout()
        time_row.setSpacing(10)
        
        start_col = QVBoxLayout()
        start_col.addWidget(self.plate_start)
        start_col.addWidget(self.start_lbl)
        
        stop_col = QVBoxLayout()
        stop_col.addWidget(self.plate_stop)
        stop_col.addWidget(self.stop_lbl)
        
        time_row.addLayout(start_col)
        time_row.addLayout(stop_col)
        layout.addLayout(time_row)
        
        layout.addSpacing(8)
        
        # Source Timezone Selector Row
        tz_row = QVBoxLayout()
        self.plate_tz = VintagePlate("BROADCAST ZONE")
        
        self.tz_combo = QComboBox()
        self.tz_combo.addItems(list(self.TIMEZONES.keys()))
        self.tz_combo.setCurrentText(self.source_tz_name)
        self.tz_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #1a1a1a;
                color: #ff8844;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #444;
                border-radius: 3px;
                padding: 4px 8px;
            }}
            QComboBox::drop-down {{
                border: none;
                background: #333;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #ff8844;
            }}
            QComboBox QAbstractItemView {{
                background-color: #222;
                color: #ff8844;
                selection-background-color: #444;
            }}
        """)
        self.tz_combo.currentTextChanged.connect(self._on_timezone_changed)
        
        # DST indicator
        self.dst_lbl = QLabel("")
        self.dst_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dst_lbl.setStyleSheet("color: #888; font-size: 10px;")
        self._update_dst_indicator()
        
        tz_row.addWidget(self.plate_tz)
        tz_row.addWidget(self.tz_combo)
        tz_row.addWidget(self.dst_lbl)
        layout.addLayout(tz_row)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _calculate_phoenix_times(self):
        """Calculate Phoenix-local start/stop times based on source timezone DST."""
        try:
            import pytz
            source_tz = pytz.timezone(self.TIMEZONES[self.source_tz_name])
            phoenix_tz = pytz.timezone("America/Phoenix")
            
            # Create source time (today at the source hour)
            now = datetime.now()
            source_start = source_tz.localize(
                now.replace(hour=self.source_start_hour, minute=self.source_start_min, second=0, microsecond=0)
            )
            source_stop = source_tz.localize(
                (now + timedelta(days=1)).replace(hour=self.source_stop_hour, minute=self.source_stop_min, second=0, microsecond=0)
            )
            
            # Convert to Phoenix
            self.start_time = source_start.astimezone(phoenix_tz).replace(tzinfo=None)
            self.stop_time = source_stop.astimezone(phoenix_tz).replace(tzinfo=None)
            
        except ImportError:
            # Fallback if pytz not available - use simple offset
            self.start_time = self.mission_time.replace(
                hour=self.source_start_hour, minute=self.source_start_min, second=0, microsecond=0
            )
            self.stop_time = (self.mission_time + timedelta(days=1)).replace(
                hour=self.source_stop_hour, minute=self.source_stop_min, second=0, microsecond=0
            )
    
    def _on_timezone_changed(self, tz_name):
        """Handle timezone dropdown change."""
        self.source_tz_name = tz_name
        self._calculate_phoenix_times()
        self.start_lbl.setText(self.start_time.strftime("%H:%M"))
        self.stop_lbl.setText(self.stop_time.strftime("%H:%M"))
        self._update_dst_indicator()
    
    def _update_dst_indicator(self):
        """Update DST status indicator."""
        try:
            import pytz
            source_tz = pytz.timezone(self.TIMEZONES[self.source_tz_name])
            now = datetime.now(source_tz)
            if now.dst() and now.dst().total_seconds() > 0:
                self.dst_lbl.setText("● DST ACTIVE (+1 HR)")
                self.dst_lbl.setStyleSheet("color: #ffaa00; font-size: 10px; font-weight: bold;")
            else:
                self.dst_lbl.setText("● STANDARD TIME")
                self.dst_lbl.setStyleSheet("color: #00aa66; font-size: 10px; font-weight: bold;")
        except ImportError:
            self.dst_lbl.setText("(pytz required for DST)")
            self.dst_lbl.setStyleSheet("color: #666; font-size: 10px;")

    def _flap_style(self):
        # CSS to simulate split flaps
        return """
            QLabel {
                background-color: #222;
                color: #eaeaea;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 26px;
                font-weight: bold;
                border-radius: 4px;
                border: 1px solid #000;
                padding: 2px;
                qproperty-alignment: AlignCenter;
            }
        """
    
    def _flap_style_small(self):
        # Smaller flap style for start/stop times
        return """
            QLabel {
                background-color: #1a1a1a;
                color: #00ff88;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 18px;
                font-weight: bold;
                border-radius: 3px;
                border: 1px solid #333;
                padding: 4px 8px;
                qproperty-alignment: AlignCenter;
            }
            QLabel:hover {
                background-color: #2a2a2a;
                color: #33ffaa;
            }
        """

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # 1. Outer Frame (Heavy Metal)
        grad_frame = QLinearGradient(0, 0, 0, rect.height())
        grad_frame.setColorAt(0, QColor("#555"))
        grad_frame.setColorAt(0.5, QColor("#222"))
        grad_frame.setColorAt(1, QColor("#555"))
        
        painter.setBrush(grad_frame)
        painter.setPen(QPen(QColor("#111"), 3))
        painter.drawRoundedRect(rect, 8, 8)
        
        # Inner recess for logic
        # We don't draw inner recess here because widgets cover it, 
        # but we can draw a border around the widget area if we want.

    def wheelEvent(self, event):
        """Handle scroll wheel to adjust time/date."""
        delta = event.angleDelta().y()
        pos = event.position()
        
        # Logic: Top half = Date, Bottom half = Time
        height_midpoint = self.height() / 2
        
        from datetime import timedelta
        
        if pos.y() < height_midpoint:
            # Adjust Date (by days)
            if delta > 0:
                self.mission_time += timedelta(days=1)
            else:
                self.mission_time -= timedelta(days=1)
        else:
            # Adjust Time (by minutes)
            if delta > 0:
                self.mission_time += timedelta(minutes=1)
            else:
                self.mission_time -= timedelta(minutes=1)
                
        self.update_labels()
        event.accept()

    def mousePressEvent(self, event):
        # Keep click-to-edit as fallback/precise option
        self.edit_time()

    def edit_time(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Set Mission Time")
        layout = QVBoxLayout(dialog)
        
        dt_edit = QDateTimeEdit(self.mission_time)
        dt_edit.setDisplayFormat("MMM dd yyyy HH:mm:ss")
        dt_edit.setCalendarPopup(True)
        layout.addWidget(QLabel("Select Date & Time:"))
        layout.addWidget(dt_edit)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)
        
        if dialog.exec():
            qdt = dt_edit.dateTime()
            self.mission_time = qdt.toPyDateTime()
            self.update_labels()

    def update_labels(self):
        d_str = self.mission_time.strftime("%b %d %Y").upper()
        t_str = self.mission_time.strftime("%H:%M:%S")
        self.date_lbl.setText(d_str)
        self.time_lbl.setText(t_str)
        # Also update start/stop labels
        self.start_lbl.setText(self.start_time.strftime("%H:%M"))
        self.stop_lbl.setText(self.stop_time.strftime("%H:%M"))

    def get_time(self):
        return self.mission_time
    
    def get_start_time(self):
        """Return the configured start time."""
        return self.start_time
    
    def get_stop_time(self):
        """Return the configured stop time."""
        return self.stop_time
    
    def get_duration_seconds(self):
        """Calculate recording duration in seconds."""
        from datetime import timedelta
        # Handle overnight recordings (stop time is next day)
        if self.stop_time <= self.start_time:
            # Stop is next day
            duration = (self.stop_time + timedelta(days=1)) - self.start_time
        else:
            duration = self.stop_time - self.start_time
        return int(duration.total_seconds())
    
    def edit_start_time(self):
        """Open dialog to edit start time."""
        from PyQt6.QtWidgets import QTimeEdit
        dialog = QDialog(self)
        dialog.setWindowTitle("Set Start Time")
        dialog.setStyleSheet("background-color: #2a2a2a; color: #eee;")
        layout = QVBoxLayout(dialog)
        
        time_edit = QTimeEdit()
        time_edit.setTime(QTime(self.start_time.hour, self.start_time.minute))
        time_edit.setDisplayFormat("HH:mm")
        time_edit.setStyleSheet("font-size: 18px; padding: 5px;")
        
        layout.addWidget(QLabel("Recording Start Time:"))
        layout.addWidget(time_edit)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)
        
        if dialog.exec():
            qt = time_edit.time()
            self.start_time = self.start_time.replace(hour=qt.hour(), minute=qt.minute(), second=0)
            self.start_lbl.setText(self.start_time.strftime("%H:%M"))
    
    def edit_stop_time(self):
        """Open dialog to edit stop time."""
        from PyQt6.QtWidgets import QTimeEdit
        dialog = QDialog(self)
        dialog.setWindowTitle("Set Stop Time")
        dialog.setStyleSheet("background-color: #2a2a2a; color: #eee;")
        layout = QVBoxLayout(dialog)
        
        time_edit = QTimeEdit()
        time_edit.setTime(QTime(self.stop_time.hour, self.stop_time.minute))
        time_edit.setDisplayFormat("HH:mm")
        time_edit.setStyleSheet("font-size: 18px; padding: 5px;")
        
        layout.addWidget(QLabel("Recording Stop Time:"))
        layout.addWidget(time_edit)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)
        
        if dialog.exec():
            qt = time_edit.time()
            self.stop_time = self.stop_time.replace(hour=qt.hour(), minute=qt.minute(), second=0)
            self.stop_lbl.setText(self.stop_time.strftime("%H:%M"))

class RadarScreen(QWidget):
    """
    Enlarged CRT Radar (260x260).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(260, 260)
        self.active = False
        self.scan_angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scan)
        self.timer.start(40) 
        
    def set_active(self, active):
        self.active = active
        self.update()

    def update_scan(self):
        if self.active:
            self.scan_angle = (self.scan_angle + 4) % 360
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # rect = self.rect()
        cx, cy = 130, 130
        
        # 1. Bezel (Dark Industrial)
        grad_bezel = QRadialGradient(cx, cy, 130)
        grad_bezel.setColorAt(0.9, QColor("#222"))
        grad_bezel.setColorAt(1.0, QColor("#111"))
        painter.setBrush(grad_bezel)
        painter.setPen(QPen(QColor("#444"), 5))
        painter.drawEllipse(5, 5, 250, 250)
        
        # Bolts
        painter.setBrush(QBrush(QColor("#333")))
        for i in range(0, 360, 45):
            rad = math.radians(i)
            bx = cx + 120 * math.cos(rad)
            by = cy + 120 * math.sin(rad)
            painter.drawEllipse(QPointF(bx-3, by-3), 6, 6)

        # 2. CRT Glass
        painter.setBrush(QBrush(QColor("#001500")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(20, 20, 220, 220)
        
        # Clip
        path = QPainterPath()
        path.addEllipse(QRectF(20, 20, 220, 220))
        painter.setClipPath(path)
        
        # 3. Grid
        painter.setPen(QPen(QColor(0, 100, 0), 1))
        for r in range(30, 110, 30):
            painter.drawEllipse(QPointF(cx, cy), r, r)
        painter.drawLine(20, 130, 240, 130)
        painter.drawLine(130, 20, 130, 240)
        
        if self.active:
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(self.scan_angle)
            
            # Sweep
            scan_grad = QConicalGradient(0, 0, 0)
            scan_grad.setColorAt(0, QColor(0, 255, 0, 200)) 
            scan_grad.setColorAt(0.15, QColor(0, 255, 0, 0))
            scan_grad.setColorAt(1, QColor(0, 255, 0, 0))
            
            painter.setBrush(scan_grad)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(-110, -110, 220, 220) 
            
            painter.restore()
            
            # Waveform
            painter.setPen(QPen(QColor(100, 255, 100), 2))
            pts = []
            t = time.time() * 5
            for x in range(40, 220, 2):
                nx = (x - 130) / 90.0
                val = math.sin(nx * 5 + t) * math.exp(-nx*nx*2) * 50
                noise = random.randint(-5, 5)
                pts.append(QPointF(x, 130 + val + noise))
            
            for i in range(len(pts)-1):
                painter.drawLine(pts[i], pts[i+1])
                
        else:
             painter.setBrush(QBrush(QColor(0, 150, 0)))
             painter.drawEllipse(128, 128, 4, 4)

class RecordingStatusPanel(QWidget):
    """
    Recording Status Panel - Shows current recording info.
    Replaces the pinup image with functional status display.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 280)
        
        # Status variables
        self.is_recording = False
        self.recording_start_time = None
        self.current_file = "—"
        self.file_size_mb = 0.0
        self.upload_status = "STANDBY"
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("REC STATUS")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            color: #888; 
            font-family: '{FONT_STENCIL}'; 
            font-size: 12px; 
            font-weight: bold;
            letter-spacing: 2px;
        """)
        layout.addWidget(title)
        
        # Recording indicator (blinking dot)
        self.rec_indicator = QLabel("● STANDBY")
        self.rec_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rec_indicator.setStyleSheet("color: #666; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.rec_indicator)
        
        # Duration display
        self.duration_lbl = QLabel("00:00:00")
        self.duration_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.duration_lbl.setStyleSheet("""
            color: #00ff88;
            font-family: 'Consolas', monospace;
            font-size: 32px;
            font-weight: bold;
            background-color: #1a1a1a;
            border: 2px solid #333;
            border-radius: 4px;
            padding: 8px;
        """)
        layout.addWidget(self.duration_lbl)
        
        # File info
        file_title = QLabel("CURRENT FILE")
        file_title.setStyleSheet("color: #666; font-size: 10px;")
        self.file_lbl = QLabel("—")
        self.file_lbl.setStyleSheet("color: #aaa; font-size: 11px; font-family: 'Consolas';")
        self.file_lbl.setWordWrap(True)
        layout.addWidget(file_title)
        layout.addWidget(self.file_lbl)
        
        # Size and Upload status row
        status_row = QHBoxLayout()
        
        size_col = QVBoxLayout()
        size_title = QLabel("SIZE")
        size_title.setStyleSheet("color: #666; font-size: 10px;")
        self.size_lbl = QLabel("0.0 MB")
        self.size_lbl.setStyleSheet("color: #ffaa00; font-size: 14px; font-weight: bold;")
        size_col.addWidget(size_title)
        size_col.addWidget(self.size_lbl)
        
        upload_col = QVBoxLayout()
        upload_title = QLabel("UPLOAD")
        upload_title.setStyleSheet("color: #666; font-size: 10px;")
        self.upload_lbl = QLabel("STANDBY")
        self.upload_lbl.setStyleSheet("color: #888; font-size: 14px; font-weight: bold;")
        upload_col.addWidget(upload_title)
        upload_col.addWidget(self.upload_lbl)
        
        status_row.addLayout(size_col)
        status_row.addLayout(upload_col)
        layout.addLayout(status_row)
        
        # Update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Dark metal frame
        grad = QLinearGradient(0, 0, 0, rect.height())
        grad.setColorAt(0, QColor("#3a3a3a"))
        grad.setColorAt(0.5, QColor("#222"))
        grad.setColorAt(1, QColor("#3a3a3a"))
        
        painter.setBrush(grad)
        painter.setPen(QPen(QColor("#111"), 3))
        painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 8, 8)
        
        # Screws
        painter.setBrush(QColor("#444"))
        for x, y in [(12, 12), (rect.width()-12, 12), 
                     (12, rect.height()-12), (rect.width()-12, rect.height()-12)]:
            painter.drawEllipse(x-4, y-4, 8, 8)
    
    def set_recording(self, is_recording, filename=None):
        self.is_recording = is_recording
        if is_recording:
            self.recording_start_time = datetime.now()
            self.current_file = filename or "Recording..."
            self.rec_indicator.setText("● RECORDING")
            self.rec_indicator.setStyleSheet("color: #ff3333; font-size: 14px; font-weight: bold;")
            self.file_lbl.setText(os.path.basename(self.current_file) if filename else "...")
        else:
            self.recording_start_time = None
            self.rec_indicator.setText("● STANDBY")
            self.rec_indicator.setStyleSheet("color: #666; font-size: 14px; font-weight: bold;")
    
    def set_upload_status(self, status):
        self.upload_status = status
        self.upload_lbl.setText(status)
        if status == "UPLOADING":
            self.upload_lbl.setStyleSheet("color: #ffaa00; font-size: 14px; font-weight: bold;")
        elif status == "COMPLETE":
            self.upload_lbl.setStyleSheet("color: #00ff88; font-size: 14px; font-weight: bold;")
        else:
            self.upload_lbl.setStyleSheet("color: #888; font-size: 14px; font-weight: bold;")
    
    def set_file_size(self, size_mb):
        self.file_size_mb = size_mb
        self.size_lbl.setText(f"{size_mb:.1f} MB")
    
    def update_display(self):
        if self.is_recording and self.recording_start_time:
            elapsed = datetime.now() - self.recording_start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.duration_lbl.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

class IHeartRecorderGUI(QMainWindow):
    def __init__(self, auto_arm=False):
        super().__init__()
        self.setWindowTitle("iHeart Recorder - Cockpit Edition")
        self.setFixedSize(1200, 800) # Increased height for taller switches
        # self.setFixedSize(1200, 800) # Increased height for taller switches
        self.setMinimumSize(1000, 850)
        self.resize(1100, 900)
        
        self.browser_thread = None
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Background
        self.bg_pixmap = QPixmap()
        bg_path = os.path.join(RESOURCES_DIR, IMG_BG)
        if os.path.exists(bg_path):
             self.bg_pixmap.load(bg_path)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Left Panel (Gauges/Switches)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setFixedWidth(280)
        
        gauges_layout = QHBoxLayout()
        self.vu_left = AnalogGauge("L")
        self.vu_right = AnalogGauge("R")
        gauges_layout.addWidget(self.vu_left)
        gauges_layout.addWidget(self.vu_right)
        left_layout.addLayout(gauges_layout)
        
        # Styling for Inputs to match Vintage Theme
        input_style = f"""
            QLineEdit, QComboBox {{
                background-color: #1a1a1a; 
                color: {COLOR_TEXT_GLOW}; 
                border: 2px solid #555; 
                border-radius: 2px; 
                font-family: '{FONT_STENCIL}'; 
                font-size: 14px;
                padding: 4px;
                selection-background-color: #a60;
            }}
            QComboBox::drop-down {{
                border: none;
                background: #333;
            }}
        """
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("TARGET FREQUENCY (URL)")
        self.url_input.setText("https://www.iheart.com/live/newsradio-830-khvh-4748/")
        self.url_input.setStyleSheet(input_style)
        
        self.device_combo = QComboBox()
        self.device_combo.setStyleSheet(input_style)

        # Move Inputs below gauges
        left_layout.addSpacing(20)
        left_layout.addWidget(QLabel("MISSION TARGET", styleSheet=f"color: #888; font-weight:bold; font-family: {FONT_STENCIL}"))
        left_layout.addWidget(self.url_input)
        left_layout.addSpacing(10)
        left_layout.addWidget(QLabel("AUDIO INPUT", styleSheet=f"color: #888; font-weight:bold; font-family: {FONT_STENCIL}"))
        left_layout.addWidget(self.device_combo)
        
        left_layout.addStretch() # Push switches to bottom
        
        switches_layout = QHBoxLayout()
        switches_layout.setSpacing(10)
        self.sw_power = CockpitSwitch("POWER")
        self.sw_record = CockpitSwitch("RECORD")
        self.sw_upload = CockpitSwitch("UPLOAD") # Shortened for fitting
        switches_layout.addWidget(self.sw_power)
        switches_layout.addWidget(self.sw_record)
        switches_layout.addWidget(self.sw_upload)
        left_layout.addLayout(switches_layout)
        left_layout.addSpacing(15)
        
        # ARM Mission Lever (moved from center panel)
        self.arm_lever = CockpitLever()
        left_layout.addWidget(self.arm_lever, alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(QLabel("ARM MISSION", styleSheet=f"color: #a00; font-size: 14px; font-weight:bold; font-family: {FONT_STENCIL}"), alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addSpacing(10) # Bottom padding
        
        # Center Panel
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        self.radar = RadarScreen()
        center_layout.addWidget(self.radar, alignment=Qt.AlignmentFlag.AlignCenter)
        center_layout.addSpacing(20)
        self.clock = FlipClockWidget()
        center_layout.addWidget(self.clock, alignment=Qt.AlignmentFlag.AlignCenter)
        center_layout.addStretch()
        
        # Right Panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setFixedWidth(300)
        
        self.clipboard = CockpitClipboard()
        self.mission_log = self.clipboard.log_list  # Alias for easy access
        
        # Populate schedule from clock widget
        self.clipboard.set_schedule(
            self.clock.get_start_time(),
            self.clock.get_stop_time(),
            "KHVH Newsradio 830"
        )
        right_layout.addWidget(self.clipboard, alignment=Qt.AlignmentFlag.AlignCenter)
        
        right_layout.addSpacing(20)
        
        # Recording Status Panel (replaces pinup image)
        self.rec_status_panel = RecordingStatusPanel()
        right_layout.addWidget(self.rec_status_panel, alignment=Qt.AlignmentFlag.AlignCenter)


        main_layout.addWidget(left_panel)
        main_layout.addWidget(center_panel)
        main_layout.addWidget(right_panel)

        self.sw_power.toggled.connect(self.toggle_stream)
        self.sw_record.toggled.connect(self.toggle_manual_recording)
        self.sw_upload.toggled.connect(self.toggle_autoupload)
        self.arm_lever.triggered.connect(self.arm_mission)
        self.populate_device_list()
        
        self.vu_timer = QTimer(self)
        self.vu_timer.timeout.connect(self.update_vu)
        self.vu_timer.start(100)
        
        # Auto-Arm Mechanism
        if auto_arm:
            self.mission_log.addItem("AUTO-SEQUENCE INITIATED...")
            # Trigger arming after a short delay to let things load
            QTimer.singleShot(2000, lambda: self.auto_arm_sequence())

    def auto_arm_sequence(self):
        """Automatically switch the lever and arm the mission."""
        if hasattr(self.arm_lever, 'set_checked'):
             self.arm_lever.set_checked(True) # Visual toggle + emits signal to arm
        else:
             # Fallback if method missing (shouldn't happen with fix)
             self.arm_lever.is_armed = True
             self.arm_lever.update()
             self.arm_mission(True)
        # self.vu_timer.timeout.connect(self.update_vu)  # Now started in init
        # self.vu_timer.start(100)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        w, h = rect.width(), rect.height()
        
        # ============ 1. BASE METAL ============
        # Gunship Gray with subtle vertical gradient (simulating overhead light)
        base_grad = QLinearGradient(0, 0, 0, h)
        base_grad.setColorAt(0, QColor("#454a50"))   # Lighter top (light source)
        base_grad.setColorAt(0.3, QColor("#383b40")) # Mid
        base_grad.setColorAt(1, QColor("#1e2023"))   # Darker bottom
        painter.setBrush(base_grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(rect)
        
        # ============ 2. HEAVY GRIME & TEXTURE ============
        # More dots, varying sizes
        random.seed(42) # Consistent texture
        for _ in range(800):
            x = random.randint(0, w)
            y = random.randint(0, h)
            op = random.randint(8, 30)
            size = random.randint(1, 5)
            painter.setBrush(QColor(0, 0, 0, op))
            painter.drawEllipse(x, y, size, size)
        
        # ============ 3. SCRATCHES (Fine white lines) ============
        painter.setPen(QPen(QColor(255, 255, 255, 20), 1))
        for _ in range(80):
            x1 = random.randint(0, w)
            y1 = random.randint(0, h)
            length = random.randint(20, 80)
            angle = random.randint(-45, 45)
            x2 = x1 + int(length * math.cos(math.radians(angle)))
            y2 = y1 + int(length * math.sin(math.radians(angle)))
            painter.drawLine(x1, y1, x2, y2)
        
        # ============ 4. RUST SPOTS ============
        painter.setPen(Qt.PenStyle.NoPen)
        for _ in range(15):
            x = random.randint(0, w)
            y = random.randint(0, h)
            rad = random.randint(5, 25)
            rust_grad = QRadialGradient(x, y, rad)
            rust_grad.setColorAt(0, QColor(120, 60, 30, 80))  # Brown rust center
            rust_grad.setColorAt(0.5, QColor(80, 40, 20, 40))
            rust_grad.setColorAt(1, QColor(60, 30, 15, 0))
            painter.setBrush(rust_grad)
            painter.drawEllipse(x-rad, y-rad, rad*2, rad*2)
        
        # ============ 5. OIL/GREASE STAINS ============
        for _ in range(8):
            x = random.randint(0, w)
            y = random.randint(0, h)
            rad = random.randint(40, 120)
            stain_grad = QRadialGradient(x, y, rad)
            stain_grad.setColorAt(0, QColor(0, 0, 0, 50))
            stain_grad.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(stain_grad)
            painter.drawEllipse(x-rad, y-rad, rad*2, rad*2)
        
        # ============ 6. PANEL SEAMS (Recessed lines) ============
        # Draw dark line then light highlight for 3D effect
        seam_dark = QPen(QColor(0, 0, 0, 180), 3)
        seam_light = QPen(QColor(100, 100, 100, 80), 1)
        
        # Horizontal seam at top
        painter.setPen(seam_dark)
        painter.drawLine(0, 100, w, 100)
        painter.setPen(seam_light)
        painter.drawLine(0, 102, w, 102)
        
        # Vertical seams
        for x_pos in [280, 600]:
            painter.setPen(seam_dark)
            painter.drawLine(x_pos, 0, x_pos, h)
            painter.setPen(seam_light)
            painter.drawLine(x_pos + 2, 0, x_pos + 2, h)
        
        # ============ 7. RIVETS WITH SHADOWS ============
        def draw_rivet(x, y):
            # Shadow
            painter.setBrush(QColor(0, 0, 0, 100))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(x-3, y-2, 10, 10)
            # Rivet body
            rivet_grad = QRadialGradient(x+2, y+2, 6)
            rivet_grad.setColorAt(0, QColor("#5a5e65"))
            rivet_grad.setColorAt(0.5, QColor("#3a3e45"))
            rivet_grad.setColorAt(1, QColor("#2a2e35"))
            painter.setBrush(rivet_grad)
            painter.drawEllipse(x-4, y-4, 8, 8)
            # Highlight
            painter.setPen(QPen(QColor(255, 255, 255, 60), 1))
            painter.drawArc(x-4, y-4, 8, 8, 45*16, 90*16)
        
        # Rivets along horizontal seam
        for i in range(30, w, 50):
            draw_rivet(i, 92)
            draw_rivet(i, 108)
        
        # Rivets along vertical seams
        for y_pos in range(120, h, 50):
            draw_rivet(275, y_pos)
            draw_rivet(285, y_pos)
            draw_rivet(595, y_pos)
            draw_rivet(605, y_pos)
        
        # ============ 8. EDGE WEAR (Chipped paint on corners) ============
        painter.setPen(Qt.PenStyle.NoPen)
        for _ in range(30):
            # Random edge positions
            edge = random.choice(['top', 'bottom', 'left', 'right'])
            if edge == 'top':
                x, y = random.randint(0, w), random.randint(0, 15)
            elif edge == 'bottom':
                x, y = random.randint(0, w), random.randint(h-15, h)
            elif edge == 'left':
                x, y = random.randint(0, 15), random.randint(0, h)
            else:
                x, y = random.randint(w-15, w), random.randint(0, h)
            
            size = random.randint(3, 12)
            painter.setBrush(QColor(30, 30, 30, 100))
            painter.drawEllipse(x, y, size, size)
        
        # ============ 9. VIGNETTE (Darkened edges) ============
        vignette = QRadialGradient(w/2, h/2, max(w, h) * 0.7)
        vignette.setColorAt(0, QColor(0, 0, 0, 0))
        vignette.setColorAt(0.7, QColor(0, 0, 0, 0))
        vignette.setColorAt(1, QColor(0, 0, 0, 120))
        painter.setBrush(vignette)
        painter.drawRect(rect)
        
        # ============ 10. OVERHEAD LIGHT REFLECTION ============
        # Subtle highlight at top center
        highlight = QRadialGradient(w/2, 50, 300)
        highlight.setColorAt(0, QColor(255, 255, 255, 15))
        highlight.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(highlight)
        painter.drawEllipse(int(w/2 - 300), -200, 600, 400)

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

    def toggle_stream(self, checked):
        if checked:
            self.mission_log.addItem(f"[{datetime.now().strftime('%H:%M')}] POWER ON.")
            self.radar.set_active(True)
            target = self.url_input.text()
            self.browser_thread = BrowserController(target)
            self.browser_thread.status_update.connect(self.log_message)
            self.browser_thread.start()
        else:
            self.mission_log.addItem(f"[{datetime.now().strftime('%H:%M')}] POWER OFF.")
            self.radar.set_active(False)
            if self.browser_thread:
                self.browser_thread.stop()
                self.browser_thread = None

    def toggle_manual_recording(self, checked):
        device_idx = self.device_combo.currentData()
        target = self.url_input.text()
        if checked:
            self.mission_log.addItem(f"[{datetime.now().strftime('%H:%M')}] REC STARTED")
            self.mission_log.addItem(f"TARGET LOADED: {target[:22]}")
            if main.start_manual_recording(device_index=device_idx):
                self.mission_log.addItem(">> STREAM RECORDING <<")
                self.rec_status_panel.set_recording(True, "MANUAL_RECORD.wav")
            else:
                self.mission_log.addItem("REC START FAILED.")
                self.sw_record.set_checked(False) 
        else:
            self.mission_log.addItem(f"[{datetime.now().strftime('%H:%M')}] REC STOPPED")
            main.stop_manual_recording()
            self.mission_log.addItem("FILE SAVED.")
            self.rec_status_panel.set_recording(False)
            
    def toggle_autoupload(self, checked):
        config.ENABLE_GOOGLE_DRIVE_UPLOAD = checked
        state = "ENABLED" if checked else "DISABLED"
        self.mission_log.addItem(f"AUTO-UPLOAD {state}")

    def arm_mission(self, armed):
        if armed:
            target_url = self.url_input.text()
            # Use configured START TIME and DURATION from the clock widget
            run_time = self.clock.get_start_time()
            duration = self.clock.get_duration_seconds()
            device_idx = self.device_combo.currentData()
            
            self.mission_log.addItem( "------------------")
            self.mission_log.addItem(f"MISSION ARMED")
            self.mission_log.addItem(f"TGT: {run_time.strftime('%H:%M')}")
            self.mission_log.addItem(f"DUR: {duration // 60}m")
            
            if main.schedule_one_off_mission(run_time, target_url, duration, device_idx):
                 self.mission_log.addItem("SCHEDULE CONFIRMED.")
                 # Popup removed for automation/cockpit immersion
                 # QMessageBox.information(self, "Mission Armed", f"Mission scheduled for:\n{run_time}\nTarget: {target_url}")
            else:
                 self.mission_log.addItem("SCHEDULING FAILED.")
                 self.arm_lever.is_armed = False 
                 self.arm_lever.update()
        else:
            self.mission_log.addItem("MISSION ABORTED")

    def log_message(self, msg):
        self.mission_log.addItem(msg)
        self.mission_log.scrollToBottom()

    def update_vu(self):
        # Determine if we are recording and grab the active recorder's VU
        vu_level = -40
        is_rec = False
        if main.manual_recorder_instance and getattr(main.manual_recorder_instance, 'is_recording', False):
            vu_level = getattr(main.manual_recorder_instance, 'current_vu', -40)
            is_rec = True
        elif main.scheduled_recorder_instance and getattr(main.scheduled_recorder_instance, 'is_recording', False):
            vu_level = getattr(main.scheduled_recorder_instance, 'current_vu', -40)
            is_rec = True
            
        if is_rec or self.radar.active:
            import random
            if is_rec:
                # Add tiny jitter to real audio for mechanical feel
                base_val = vu_level + random.uniform(-0.5, 0.5)
            else:
                # Idle wobble at bottom of scale when power is ON but not recording
                base_val = -20 + random.uniform(-1, 2)
                
            self.vu_left.set_value(base_val)
            self.vu_right.set_value(max(-22, base_val - random.uniform(0, 1.5)))
        else:
            self.vu_left.set_value(-22) # Rest securely at the bottom
            self.vu_right.set_value(-22)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="iHeart Recorder Cockpit Edition")
    parser.add_argument("--auto-schedule", action="store_true", help="Automatically arm the mission on startup")
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = IHeartRecorderGUI(auto_arm=args.auto_schedule)
    window.show()
    sys.exit(app.exec())
