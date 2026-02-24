from ultralytics import YOLO
import torch

class Detector:
    def __init__(self, model_path="yolov8n.pt"):
        self.device = 0 if torch.cuda.is_available() else "cpu"
        self.model = YOLO(model_path)
        self.model.to(self.device)

    def detect(self, frame):
        return self.model(frame, device=self.device, verbose=False)