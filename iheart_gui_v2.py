"""
iHeart Recorder - Minimal Control Panel Edition
A clean, professional interface for scheduled radio recording.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QListWidget, QFrame,
    QTimeEdit, QGroupBox, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer, QTime, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

# Import backend modules
try:
    import main
    import config
except ImportError:
    main = None
    config = None
    logging.warning("Backend modules not found. UI will run in demo mode.")

# ============================================================================
# THEME CONSTANTS
# ============================================================================
COLORS = {
    'bg_primary': '#1a1a1a',
    'bg_secondary': '#252525',
    'bg_input': '#0d0d0d',
    'accent': '#00aaff',
    'accent_hover': '#33bbff',
    'text_primary': '#ffffff',
    'text_secondary': '#888888',
    'text_dim': '#555555',
    'success': '#00ff88',
    'danger': '#ff3333',
    'warning': '#ffaa00',
    'border': '#333333',
}

FONTS = {
    'primary': 'Segoe UI',
    'mono': 'Consolas',
}


# ============================================================================
# STATUS INDICATOR WIDGET
# ============================================================================
class StatusIndicator(QFrame):
    """Large circular status indicator with elapsed time display."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_recording = False
        self.recording_start_time = None
        
        self.setFixedSize(280, 200)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Status label (● STANDBY or ● RECORDING)
        self.status_label = QLabel("● STANDBY")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"""
            color: {COLORS['text_dim']};
            font-size: 18px;
            font-weight: bold;
            font-family: '{FONTS['primary']}';
        """)
        layout.addWidget(self.status_label)
        
        # Elapsed time display
        self.time_label = QLabel("00:00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet(f"""
            color: {COLORS['success']};
            font-size: 48px;
            font-weight: bold;
            font-family: '{FONTS['mono']}';
            background-color: {COLORS['bg_input']};
            border: 2px solid {COLORS['border']};
            border-radius: 4px;
            padding: 10px;
        """)
        layout.addWidget(self.time_label)
        
        # Next scheduled time
        self.next_label = QLabel("Next: --:--")
        self.next_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 14px;
            font-family: '{FONTS['primary']}';
        """)
        layout.addWidget(self.next_label)
        
        # Update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_display)
        self.timer.start(1000)
    
    def set_recording(self, is_recording: bool):
        """Update recording state."""
        self.is_recording = is_recording
        if is_recording:
            self.recording_start_time = datetime.now()
            self.status_label.setText("● RECORDING")
            self.status_label.setStyleSheet(f"""
                color: {COLORS['danger']};
                font-size: 18px;
                font-weight: bold;
                font-family: '{FONTS['primary']}';
            """)
        else:
            self.recording_start_time = None
            self.status_label.setText("● STANDBY")
            self.status_label.setStyleSheet(f"""
                color: {COLORS['text_dim']};
                font-size: 18px;
                font-weight: bold;
                font-family: '{FONTS['primary']}';
            """)
            self.time_label.setText("00:00:00")
    
    def set_next_time(self, time_str: str):
        """Update next scheduled time display."""
        self.next_label.setText(f"Next: {time_str}")
    
    def _update_display(self):
        """Update elapsed time if recording."""
        if self.is_recording and self.recording_start_time:
            elapsed = datetime.now() - self.recording_start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")


# ============================================================================
# SCHEDULE PANEL
# ============================================================================
class SchedulePanel(QGroupBox):
    """Schedule configuration panel."""
    
    schedule_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("SCHEDULE", parent)
        self.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['text_secondary']};
                font-size: 12px;
                font-weight: bold;
                font-family: '{FONTS['primary']}';
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(12)
        
        time_edit_style = f"""
            QTimeEdit {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['accent']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 16px;
                font-family: '{FONTS['mono']}';
            }}
            QTimeEdit::up-button, QTimeEdit::down-button {{
                background-color: {COLORS['bg_secondary']};
                border: none;
                width: 20px;
            }}
        """
        
        # Start time
        start_row = QHBoxLayout()
        start_lbl = QLabel("Start:")
        start_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        start_lbl.setFixedWidth(50)
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm")
        self.start_time.setTime(QTime(23, 6))
        self.start_time.setStyleSheet(time_edit_style)
        start_row.addWidget(start_lbl)
        start_row.addWidget(self.start_time)
        layout.addLayout(start_row)
        
        # Stop time
        stop_row = QHBoxLayout()
        stop_lbl = QLabel("Stop:")
        stop_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        stop_lbl.setFixedWidth(50)
        self.stop_time = QTimeEdit()
        self.stop_time.setDisplayFormat("HH:mm")
        self.stop_time.setTime(QTime(3, 4))
        self.stop_time.setStyleSheet(time_edit_style)
        stop_row.addWidget(stop_lbl)
        stop_row.addWidget(self.stop_time)
        layout.addLayout(stop_row)
        
        # Timezone dropdown
        tz_row = QHBoxLayout()
        tz_lbl = QLabel("Zone:")
        tz_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        tz_lbl.setFixedWidth(50)
        self.timezone = QComboBox()
        self.timezone.addItems(["America/Phoenix", "America/Los_Angeles", "America/New_York", "Pacific/Honolulu"])
        self.timezone.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{
                border: none;
                background: {COLORS['bg_secondary']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['accent']};
            }}
        """)
        tz_row.addWidget(tz_lbl)
        tz_row.addWidget(self.timezone)
        layout.addLayout(tz_row)
        
        # Duration display
        self.duration_label = QLabel("Duration: 3h 58m")
        self.duration_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 12px;")
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.duration_label)
        
        # Connect signals
        self.start_time.timeChanged.connect(self._update_duration)
        self.stop_time.timeChanged.connect(self._update_duration)
    
    def _update_duration(self):
        """Calculate and display duration."""
        start = self.start_time.time()
        stop = self.stop_time.time()
        
        start_minutes = start.hour() * 60 + start.minute()
        stop_minutes = stop.hour() * 60 + stop.minute()
        
        if stop_minutes <= start_minutes:
            stop_minutes += 24 * 60  # Next day
        
        duration_minutes = stop_minutes - start_minutes
        hours = duration_minutes // 60
        minutes = duration_minutes % 60
        
        self.duration_label.setText(f"Duration: {hours}h {minutes}m")
        self.schedule_changed.emit()
    
    def get_start_datetime(self) -> datetime:
        """Get start time as datetime for today."""
        t = self.start_time.time()
        now = datetime.now()
        return now.replace(hour=t.hour(), minute=t.minute(), second=0, microsecond=0)
    
    def get_duration_seconds(self) -> int:
        """Get duration in seconds."""
        start = self.start_time.time()
        stop = self.stop_time.time()
        
        start_minutes = start.hour() * 60 + start.minute()
        stop_minutes = stop.hour() * 60 + stop.minute()
        
        if stop_minutes <= start_minutes:
            stop_minutes += 24 * 60
        
        return (stop_minutes - start_minutes) * 60


# ============================================================================
# ACTIVITY LOG
# ============================================================================
class ActivityLog(QGroupBox):
    """Activity log panel."""
    
    def __init__(self, parent=None):
        super().__init__("ACTIVITY LOG", parent)
        self.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['text_secondary']};
                font-size: 12px;
                font-weight: bold;
                font-family: '{FONTS['primary']}';
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 10)
        
        self.log_list = QListWidget()
        self.log_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_secondary']};
                border: none;
                font-size: 11px;
                font-family: '{FONTS['mono']}';
            }}
            QListWidget::item {{
                padding: 4px;
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        self.log_list.setMaximumHeight(150)
        layout.addWidget(self.log_list)
    
    def add_log(self, message: str):
        """Add a log entry with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_list.addItem(f"[{timestamp}] {message}")
        self.log_list.scrollToBottom()


# ============================================================================
# MAIN WINDOW
# ============================================================================
class IHeartRecorderMinimal(QMainWindow):
    """Main application window - Minimal Control Panel Edition."""
    
    def __init__(self, auto_arm=False):
        super().__init__()
        self.auto_arm = auto_arm
        self.browser_thread = None
        
        self.setWindowTitle("iHeart Recorder")
        self.setMinimumSize(500, 700)
        self.resize(550, 750)
        
        # Set dark palette
        self._apply_dark_theme()
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel("iHeart Recorder")
        title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 24px;
            font-weight: bold;
            font-family: '{FONTS['primary']}';
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Status indicator
        self.status_indicator = StatusIndicator()
        main_layout.addWidget(self.status_indicator, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Schedule panel
        self.schedule_panel = SchedulePanel()
        main_layout.addWidget(self.schedule_panel)
        
        # Station URL input
        url_group = QGroupBox("TARGET STATION")
        url_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['text_secondary']};
                font-size: 12px;
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        url_layout = QVBoxLayout(url_group)
        url_layout.setContentsMargins(15, 20, 15, 15)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.iheart.com/live/...")
        self.url_input.setText("https://www.iheart.com/live/newsradio-830-khvh-4748/")
        self.url_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['accent']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 10px;
                font-size: 12px;
                font-family: '{FONTS['mono']}';
            }}
        """)
        url_layout.addWidget(self.url_input)
        
        # Device dropdown
        device_row = QHBoxLayout()
        device_lbl = QLabel("Audio:")
        device_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        self.device_combo = QComboBox()
        self.device_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{
                border: none;
                background: {COLORS['bg_secondary']};
            }}
        """)
        device_row.addWidget(device_lbl)
        device_row.addWidget(self.device_combo, 1)
        url_layout.addLayout(device_row)
        
        main_layout.addWidget(url_group)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_record = QPushButton("● REC")
        self.btn_record.setCheckable(True)
        self.btn_record.setStyleSheet(self._get_button_style(COLORS['danger']))
        self.btn_record.clicked.connect(self._toggle_recording)
        
        # Upload button removed as requested
        
        self.btn_arm = QPushButton("ARM SCHEDULE")
        self.btn_arm.setStyleSheet(self._get_button_style(COLORS['accent'], primary=True))
        self.btn_arm.clicked.connect(self._arm_mission)
        
        btn_layout.addWidget(self.btn_record)
        # btn_layout.addWidget(self.btn_upload)
        btn_layout.addWidget(self.btn_arm)
        main_layout.addLayout(btn_layout)
        
        # Activity log
        self.activity_log = ActivityLog()
        main_layout.addWidget(self.activity_log)
        
        # Spacer
        main_layout.addStretch()
        
        # Initialize
        self._populate_devices()
        self.activity_log.add_log("Application started")
        
        # Auto-arm if requested
        if self.auto_arm:
            QTimer.singleShot(1500, self._arm_mission)
    
    def _apply_dark_theme(self):
        """Apply dark color palette."""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['bg_primary']};
            }}
            QWidget {{
                background-color: {COLORS['bg_primary']};
                color: {COLORS['text_primary']};
                font-family: '{FONTS['primary']}';
            }}
        """)
    
    def _get_button_style(self, color: str, primary: bool = False) -> str:
        """Generate button stylesheet."""
        if primary:
            return f"""
                QPushButton {{
                    background-color: {color};
                    color: {COLORS['bg_primary']};
                    border: none;
                    border-radius: 4px;
                    padding: 12px 20px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {color};
                }}
            """
        return f"""
            QPushButton {{
                background-color: {COLORS['bg_secondary']};
                color: {color};
                border: 1px solid {color};
                border-radius: 4px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_input']};
            }}
            QPushButton:checked {{
                background-color: {color};
                color: {COLORS['bg_primary']};
            }}
        """
    
    def _populate_devices(self):
        """Populate audio device dropdown."""
        self.device_combo.clear()
        
        if main:
            devices = main.AudioRecorder.get_audio_devices()
            default_index = 0
            for i, dev in enumerate(devices):
                name = dev['name']
                if "Stereo Mix" in name:
                    default_index = i
                self.device_combo.addItem(name, dev['index'])
            self.device_combo.setCurrentIndex(default_index)
        else:
            # Demo mode
            self.device_combo.addItem("Stereo Mix (Demo)", 0)
            self.device_combo.addItem("Microphone (Demo)", 1)
    
    def _toggle_recording(self, checked: bool):
        """Toggle manual recording."""
        device_idx = self.device_combo.currentData()
        
        if checked:
            self.activity_log.add_log("Manual recording started")
            self.status_indicator.set_recording(True)
            if main:
                main.start_manual_recording(device_index=device_idx)
        else:
            self.activity_log.add_log("Manual recording stopped")
            self.status_indicator.set_recording(False)
            if main:
                main.stop_manual_recording()
    
    def _toggle_upload(self, checked: bool):
        """Toggle auto-upload."""
        if config:
            config.ENABLE_GOOGLE_DRIVE_UPLOAD = checked
        state = "enabled" if checked else "disabled"
        self.activity_log.add_log(f"Auto-upload {state}")
    
    def _arm_mission(self):
        """Arm the scheduled recording mission."""
        target_url = self.url_input.text()
        run_time = self.schedule_panel.get_start_datetime()
        duration = self.schedule_panel.get_duration_seconds()
        device_idx = self.device_combo.currentData()
        
        self.activity_log.add_log("Mission armed")
        self.activity_log.add_log(f"Target: {run_time.strftime('%H:%M')}")
        self.activity_log.add_log(f"Duration: {duration // 60}m")
        
        self.status_indicator.set_next_time(run_time.strftime("%H:%M"))
        
        if main:
            if main.schedule_one_off_mission(run_time, target_url, duration, device_idx):
                self.activity_log.add_log("Schedule confirmed")
            else:
                self.activity_log.add_log("Schedule FAILED")


# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="iHeart Recorder - Minimal Edition")
    parser.add_argument("--auto-schedule", action="store_true", help="Auto-arm on startup")
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = IHeartRecorderMinimal(auto_arm=args.auto_schedule)
    window.show()
    
    sys.exit(app.exec())
