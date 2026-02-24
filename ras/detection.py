from ultralytics import YOLO
import torch
import os
import sys


class Detector:
    def __init__(self, model_name="yolov8n.pt"):

        self.device = 0 if torch.cuda.is_available() else "cpu"

        # Handle PyInstaller onefile mode
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        model_path = os.path.join(base_path, "yolov8n.pt")

        self.model = YOLO(model_path)
        self.model.to(self.device)

    def detect(self, frame):
        return self.model(frame, device=self.device, verbose=False)