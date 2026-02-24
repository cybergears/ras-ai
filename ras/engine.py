import subprocess
import numpy as np
import cv2
import math
from .detection import Detector
from .renderer import draw_hud_box, apply_glow


class RASEngine:

    def __init__(self, profile):
        self.profile = profile
        self.detector = Detector()
        self.frame_count = 0

    def process(self, input_path, output_path):

        probe_cmd = [
            "ffprobe","-v","error",
            "-select_streams","v:0",
            "-show_entries","stream=width,height,r_frame_rate",
            "-of","csv=p=0",
            input_path
        ]

        probe = subprocess.check_output(probe_cmd).decode().strip().split(",")

        width = int(probe[0])
        height = int(probe[1])
        fps = eval(probe[2])

        decode_cmd = [
            "ffmpeg","-i",input_path,
            "-f","rawvideo",
            "-pix_fmt","bgr24","-"
        ]

        encoder_cmd = [
            "ffmpeg","-y",
            "-f","rawvideo",
            "-pix_fmt","bgr24",
            "-s",f"{width}x{height}",
            "-r",str(int(fps)),
            "-i","-",
            "-c:v","h264_nvenc",
            "-preset","p4",
            "-rc","vbr",
            "-cq","18",
            "-pix_fmt","yuv420p",
            output_path
        ]

        decoder = subprocess.Popen(decode_cmd, stdout=subprocess.PIPE)
        encoder = subprocess.Popen(encoder_cmd, stdin=subprocess.PIPE)

        frame_size = width * height * 3

        while True:
            raw_frame = decoder.stdout.read(frame_size)
            if len(raw_frame) != frame_size:
                break

            frame = np.frombuffer(raw_frame, np.uint8).reshape((height,width,3)).copy()
            overlay = frame.copy()

            self.frame_count += 1

            results = self.detector.detect(frame)

            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    class_name = self.detector.model.names[cls_id]

                    if class_name not in self.profile["allowed_classes"]:
                        continue

                    x1,y1,x2,y2 = map(int, box.xyxy[0])

                    if y2 > height * self.profile["dashboard_ignore_ratio"]:
                        continue

                    area = (x2-x1)*(y2-y1)
                    closeness = area/(width*height)

                    if closeness > self.profile["red_threshold"]:
                        color = (0,0,255)
                        thickness = 4 + int(2 * abs(math.sin(self.frame_count*self.profile["pulse_speed"])))
                        cv2.rectangle(overlay,(x1,y1),(x2,y2),color, thickness+8)
                    elif closeness > self.profile["yellow_threshold"]:
                        color = (0,255,255)
                        thickness = 3
                    else:
                        color = (255,255,255)
                        thickness = 2

                    draw_hud_box(frame,x1,y1,x2,y2,color,thickness)

            frame = apply_glow(frame, overlay, self.profile["glow_kernel"])
            encoder.stdin.write(frame.tobytes())

        decoder.stdout.close()
        encoder.stdin.close()
        encoder.wait()