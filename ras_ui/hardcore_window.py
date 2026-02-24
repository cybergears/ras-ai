import sys
import time
import subprocess
import torch

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QProgressBar,
    QTextEdit
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
    log_signal = pyqtSignal(str)

    def __init__(self, input_path, output_path, profile):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.profile = profile
        self.engine = None
        

    def run(self):
        try:
            engine = RASEngine(self.profile)
            self.engine = engine

            
            def progress_callback(percent, frame_count, elapsed):
                self.progress_signal.emit(percent, frame_count, elapsed)

            engine.process(
                self.input_path,
                self.output_path,
                progress_callback=progress_callback
            )

            self.finished_signal.emit()

        except Exception as e:
            self.log_signal.emit(f"ERROR: {str(e)}")

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

        self.init_ui()

    # =====================================================
    # UI Layout
    # =====================================================

    def init_ui(self):

        main_layout = QVBoxLayout()

        # Title
        title = QLabel("R.A.S  //  RIDER ASSIST SYSTEM")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("title")
        main_layout.addWidget(title)

        divider = QLabel("")
        divider.setFixedHeight(2)
        divider.setStyleSheet("background-color: #222222;")
        main_layout.addWidget(divider)

        # Info Strip
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

        # Center Layout
        center_layout = QHBoxLayout()

        # Left Panel
        left_panel = QVBoxLayout()

        self.input_btn = QPushButton("LOAD INPUT VIDEO")
        self.input_btn.clicked.connect(self.select_input)
        left_panel.addWidget(self.input_btn)

        self.output_btn = QPushButton("SET OUTPUT DESTINATION")
        self.output_btn.clicked.connect(self.select_output)
        left_panel.addWidget(self.output_btn)

        left_panel.addStretch()

        # Right Panel
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

        # Console
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        main_layout.addWidget(self.log_console, 2)

        # Start Button
        self.start_btn = QPushButton("START RENDER")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.start_render)
        main_layout.addWidget(self.start_btn)

        # Cancel Button
        self.cancel_btn = QPushButton("CANCEL RENDER")
        self.cancel_btn.clicked.connect(self.cancel_render)
        self.cancel_btn.setEnabled(False)
        main_layout.addWidget(self.cancel_btn)

        self.setLayout(main_layout)

    # =====================================================
    # Actions
    # =====================================================

    def select_input(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Video")
        if file:
            self.input_path = file
            self.log_console.append(f"INPUT LOADED: {file}")

            try:
                probe_cmd = [
                    "ffprobe",
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

    def start_render(self):
        if not self.input_path or not self.output_path:
            self.log_console.append("ERROR: Input or Output not selected.")
            return

        self.start_btn.setEnabled(False)
        self.input_btn.setEnabled(False)
        self.output_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

        self.status_label.setText("ENGINE: RENDERING")
        self.start_btn.setText("RENDERING...")
        self.progress.setValue(0)

        self.fps_history = []

        profile = load_profile("profiles/motorcycle.json")

        self.worker = RenderWorker(self.input_path, self.output_path, profile)
        self.worker.finished_signal.connect(self.render_finished)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.start()

    def update_progress(self, percent, frame_count, elapsed):
        self.progress.setValue(percent)
        self.frame_label.setText(f"FRAMES: {frame_count}")

        current_time = time.time()
        self.fps_history.append((frame_count, current_time))

        # Keep last 1 second of history
        self.fps_history = [
            item for item in self.fps_history
            if current_time - item[1] <= 1.0
        ]

        if len(self.fps_history) >= 2:
            first_frame, first_time = self.fps_history[0]
            last_frame, last_time = self.fps_history[-1]

            time_diff = last_time - first_time
            frame_diff = last_frame - first_frame

            if time_diff > 0:
                fps = frame_diff / time_diff
                self.fps_label.setText(f"LIVE FPS: {fps:.2f}")

    def render_finished(self):

        if self.was_cancelled:
            self.status_label.setText("ENGINE: CANCELLED")
            self.log_console.append("RENDER CANCELLED.")
        else:
            self.status_label.setText("ENGINE: COMPLETE")
            self.log_console.append("RENDER COMPLETE.")

        self.was_cancelled = False
        self.progress.setValue(100)
        self.start_btn.setText("START RENDER")

        self.start_btn.setEnabled(True)
        self.input_btn.setEnabled(True)
        self.output_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

    def closeEvent(self, event):
        if hasattr(self, "worker") and self.worker.isRunning():
            from PyQt6.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                self,
                "Render In Progress",
                "Rendering is still in progress.\nAre you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.worker.stop()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def cancel_render(self):
        if hasattr(self, "worker") and self.worker.isRunning():
            self.status_label.setText("ENGINE: STOPPING...")
            self.log_console.append("Stopping render...")
            self.was_cancelled = True
            self.worker.stop()

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
        """


# =====================================================
# Entry
# =====================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HardcoreWindow()
    window.show()
    sys.exit(app.exec())