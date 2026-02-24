import os

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
        self.stop_requested = False
    
    def request_stop(self):
        self.stop_requested = True

    def process(self, input_path, output_path, progress_callback=None):

        import sys

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        ffmpeg_path = os.path.join(base_path, "ffmpeg.exe")
        ffprobe_path = os.path.join(base_path, "ffprobe.exe")

        self.stop_requested = False
        self.frame_count = 0

        import time
        start_time = time.time()

        probe_cmd = [
            ffprobe_path,"-v","error",
            "-select_streams","v:0",
            "-show_entries","stream=width,height,r_frame_rate,nb_frames",
            "-of","csv=p=0",
            input_path
        ]

        try:
            probe = subprocess.check_output(probe_cmd).decode().strip().split(",")
        except subprocess.CalledProcessError:
            raise RuntimeError("Failed to probe video. Ensure FFmpeg is installed.")

        width = int(probe[0])
        height = int(probe[1])
        num, denom = probe[2].split("/")
        fps = float(num) / float(denom)

        total_frames = None
        if len(probe) >= 4 and probe[3].isdigit():
            total_frames = int(probe[3])

        decode_cmd = [
            ffmpeg_path,"-i",input_path,
            "-f","rawvideo",
            "-pix_fmt","bgr24","-"
        ]

        encoder_cmd = [
            ffmpeg_path, "-y",

            # Processed video from pipe
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{width}x{height}",
            "-r", str(int(fps)),
            "-i", "-",

            # Original input (for audio)
            "-i", input_path,

            # Mapping
            "-map", "0:v:0",
            "-map", "1:a?",

            # Video encoding
            "-c:v", "h264_nvenc",
            "-preset", "p4",
            "-rc", "vbr",
            "-cq", "18",
            "-pix_fmt", "yuv420p",

            # Audio copy
            "-c:a", "copy",

            # Ensure sync
            "-shortest",

            output_path
        ]

        decoder = subprocess.Popen(
            decode_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )

        encoder = subprocess.Popen(
            encoder_cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )

        frame_size = width * height * 3
        frame_count = 0

        while True:
            if self.stop_requested:
                break
            raw_frame = decoder.stdout.read(frame_size)
            if len(raw_frame) != frame_size:
                break

            frame = np.frombuffer(raw_frame, np.uint8).reshape((height,width,3)).copy()
            overlay = frame.copy()

            frame_count += 1
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
            try:
                encoder.stdin.write(frame.tobytes())
            except BrokenPipeError:
                break

            # ---- SINGLE CLEAN PROGRESS EMIT ----
            if total_frames and progress_callback:
                elapsed = time.time() - start_time
                percent = int((frame_count / total_frames) * 100)
                progress_callback(percent, frame_count, elapsed)

        try:
            decoder.stdout.close()
        except:
            pass

        try:
            encoder.stdin.close()
        except:
            pass

        decoder.terminate()
        encoder.terminate()

        decoder.wait()
        encoder.wait()