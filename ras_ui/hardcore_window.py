import sys
import os
import time
import subprocess
import torch

from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

APP_VERSION = "v1.0.0"
POWERED_BY = "Cybergears"
WEBSITE_URL = "https://shahrukhsheikh.in"

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog,
    QProgressBar, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ras.config import load_profile
from ras.engine import RASEngine


# =====================================================
# Worker Thread
# =====================================================

class RenderWorker(QThread):
    finished_signal = pyqtSignal()
    progress_signal = pyqtSignal(int, int, float)
    error_signal = pyqtSignal(str)

    def __init__(self, input_path, output_path, profile):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.profile = profile
        self.engine = None

    def run(self):
        try:
            self.engine = RASEngine(self.profile)

            def progress_callback(percent, frame_count, elapsed):
                self.progress_signal.emit(percent, frame_count, elapsed)

            self.engine.process(
                self.input_path,
                self.output_path,
                progress_callback=progress_callback
            )

            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(str(e))

    def stop(self):
        if self.engine:
            self.engine.request_stop()

    


# =====================================================
# Main Window
# =====================================================

class HardcoreWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("R.A.S // HARDCORE BUILD v1.0")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(self.hardcore_style())

        self.input_path = ""
        self.output_path = ""
        self.fps_history = []
        self.was_cancelled = False
        self.worker = None

        self.init_ui()

    def open_website(self):
        QDesktopServices.openUrl(QUrl(WEBSITE_URL))

    # =====================================================
    # Utility
    # =====================================================

    def get_base_path(self):
        if getattr(sys, "frozen", False):
            return sys._MEIPASS
        return os.path.abspath(".")

    # =====================================================
    # UI Layout
    # =====================================================

    def init_ui(self):

        main_layout = QVBoxLayout()

        # =========================
        # TITLE + VERSION
        # =========================

        title = QLabel(f"R.A.S  //  RIDER ASSIST SYSTEM  {APP_VERSION}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("title")
        main_layout.addWidget(title)

        divider = QLabel("")
        divider.setFixedHeight(2)
        divider.setStyleSheet("background-color: #222222;")
        main_layout.addWidget(divider)

        # =========================
        # INFO STRIP
        # =========================

        info_layout = QHBoxLayout()

        gpu_status = "CUDA DETECTED" if torch.cuda.is_available() else "CPU MODE"

        self.gpu_label = QLabel(f"GPU: {gpu_status}")
        self.model_label = QLabel("MODEL: YOLOv8n")
        self.profile_label = QLabel("PROFILE: MOTORCYCLE")
        self.resolution_label = QLabel("RESOLUTION: -")

        for lbl in [self.gpu_label, self.model_label, self.profile_label, self.resolution_label]:
            lbl.setObjectName("infoLabel")
            info_layout.addWidget(lbl)

        main_layout.addLayout(info_layout)

        # =========================
        # CENTER LAYOUT
        # =========================

        center_layout = QHBoxLayout()

        # LEFT PANEL
        left_panel = QVBoxLayout()

        self.input_btn = QPushButton("LOAD INPUT VIDEO")
        self.input_btn.clicked.connect(self.select_input)
        left_panel.addWidget(self.input_btn)

        self.output_btn = QPushButton("SET OUTPUT DESTINATION")
        self.output_btn.clicked.connect(self.select_output)
        left_panel.addWidget(self.output_btn)

        left_panel.addStretch()

        # RIGHT PANEL
        right_panel = QVBoxLayout()

        self.status_label = QLabel("ENGINE: IDLE")
        self.status_label.setObjectName("status")
        right_panel.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        right_panel.addWidget(self.progress)

        self.frame_label = QLabel("FRAMES: 0")
        self.frame_label.setObjectName("infoLabel")
        right_panel.addWidget(self.frame_label)

        self.fps_label = QLabel("LIVE FPS: 0.00")
        self.fps_label.setObjectName("infoLabel")
        right_panel.addWidget(self.fps_label)

        right_panel.addStretch()

        center_layout.addLayout(left_panel, 1)
        center_layout.addLayout(right_panel, 1)

        main_layout.addLayout(center_layout)

        # =========================
        # CONSOLE
        # =========================

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        main_layout.addWidget(self.log_console, 2)

        # =========================
        # BUTTONS
        # =========================

        self.start_btn = QPushButton("START RENDER")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.start_render)
        main_layout.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("CANCEL RENDER")
        self.cancel_btn.clicked.connect(self.cancel_render)
        self.cancel_btn.setEnabled(False)
        main_layout.addWidget(self.cancel_btn)

        # =========================
        # FOOTER (BRANDING)
        # =========================

        footer_layout = QHBoxLayout()

        self.version_label = QLabel(f"Version: {APP_VERSION}")
        self.version_label.setObjectName("footerLabel")

        self.powered_label = QLabel(
            f'Powered by <a href="{WEBSITE_URL}">{POWERED_BY}</a>'
        )
        self.powered_label.setObjectName("footerLabel")
        self.powered_label.setOpenExternalLinks(False)
        self.powered_label.linkActivated.connect(self.open_website)

        footer_layout.addWidget(self.version_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.powered_label)

        main_layout.addLayout(footer_layout)

        self.setLayout(main_layout)

    # =====================================================
    # File Selection
    # =====================================================

    def select_input(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Video")
        if file:
            self.input_path = file
            self.log_console.append(f"INPUT LOADED: {file}")

            # Use bundled ffprobe in EXE mode
            base_path = self.get_base_path()
            ffprobe_path = os.path.join(base_path, "ffprobe.exe")

            try:
                probe_cmd = [
                    ffprobe_path,
                    "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=width,height",
                    "-of", "csv=p=0",
                    file
                ]
                probe = subprocess.check_output(probe_cmd).decode().strip().split(",")
                width, height = probe[0], probe[1]
                self.resolution_label.setText(f"RESOLUTION: {width}x{height}")
            except:
                self.resolution_label.setText("RESOLUTION: UNKNOWN")

    def select_output(self):
        file, _ = QFileDialog.getSaveFileName(self, "Save Output", "output.mp4")
        if file:
            self.output_path = file
            self.log_console.append(f"OUTPUT SET: {file}")

    # =====================================================
    # Rendering
    # =====================================================

    def start_render(self):

        if self.worker and self.worker.isRunning():
            return

        if not self.input_path or not self.output_path:
            QMessageBox.warning(self, "Missing Input", "Select input and output files first.")
            return

        base_path = self.get_base_path()
        profile_path = os.path.join(base_path, "profiles", "motorcycle.json")

        profile = load_profile(profile_path)

        self.start_btn.setEnabled(False)
        self.input_btn.setEnabled(False)
        self.output_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        self.status_label.setText("ENGINE: RENDERING")
        self.progress.setValue(0)
        self.fps_history = []
        self.was_cancelled = False

        self.worker = RenderWorker(self.input_path, self.output_path, profile)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.render_finished)
        self.worker.error_signal.connect(self.render_error)

        self.worker.start()

    def update_progress(self, percent, frame_count, elapsed):

        self.progress.setValue(percent)
        self.frame_label.setText(f"FRAMES: {frame_count}")

        current_time = time.time()
        self.fps_history.append((frame_count, current_time))

        self.fps_history = [
            item for item in self.fps_history
            if current_time - item[1] <= 1.0
        ]

        if len(self.fps_history) >= 2:
            f1, t1 = self.fps_history[0]
            f2, t2 = self.fps_history[-1]

            if t2 - t1 > 0:
                fps = (f2 - f1) / (t2 - t1)
                self.fps_label.setText(f"LIVE FPS: {fps:.2f}")

    def render_finished(self):

        if self.was_cancelled:
            self.status_label.setText("ENGINE: CANCELLED")
            self.log_console.append("Render cancelled.")
        else:
            self.status_label.setText("ENGINE: COMPLETE")
            self.log_console.append("Render complete.")

        self.reset_ui()

    def render_error(self, message):
        self.status_label.setText("ENGINE: ERROR")
        self.log_console.append(f"ERROR: {message}")
        QMessageBox.critical(self, "Render Error", message)
        self.reset_ui()

    def cancel_render(self):
        if self.worker and self.worker.isRunning():
            self.was_cancelled = True
            self.status_label.setText("ENGINE: STOPPING...")
            self.worker.stop()

    def reset_ui(self):
        self.start_btn.setEnabled(True)
        self.input_btn.setEnabled(True)
        self.output_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress.setValue(100)

    # =====================================================
    # Style
    # =====================================================

    def hardcore_style(self):
        return """
        QWidget {
            background-color: #0f0f0f;
            color: #e0e0e0;
            font-family: Consolas;
            font-size: 13px;
        }

        QLabel#title {
            font-size: 22px;
            font-weight: bold;
            color: #ff2c2c;
            padding: 15px;
        }

        QLabel#status {
            font-weight: bold;
            color: #00e5ff;
            padding: 5px;
        }

        QLabel#infoLabel {
            color: #00e5ff;
            padding: 5px;
            font-weight: bold;
        }

        QPushButton {
            background-color: #1c1c1c;
            border: 2px solid #ff2c2c;
            padding: 12px;
            font-weight: bold;
            letter-spacing: 1px;
        }

        QPushButton:hover {
            background-color: #ff2c2c;
            color: black;
        }

        QPushButton#startBtn {
            background-color: #ff2c2c;
            color: black;
            font-weight: bold;
        }

        QProgressBar {
            border: 1px solid #ff2c2c;
            background-color: #1c1c1c;
            height: 28px;
            font-weight: bold;
            text-align: center;
            color: #000000;
        }

        QProgressBar::chunk {
            background-color: #ff2c2c;
        }

        QTextEdit {
            background-color: #141414;
            border: 1px solid #222222;
        }
        QLabel#footerLabel {
            color: #888888;
            font-size: 11px;
            padding: 6px;
        }

        QLabel#footerLabel:hover {
            color: #00e5ff;
        }
        """


# =====================================================
# Entry
# =====================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HardcoreWindow()
    window.show()
    sys.exit(app.exec())