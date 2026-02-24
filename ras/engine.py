import os
import sys
import subprocess
import numpy as np
import cv2
import math
import time

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

    def _get_base_path(self):
        if getattr(sys, "frozen", False):
            return sys._MEIPASS
        return os.path.abspath(".")

    def _select_video_encoder(self, ffmpeg_path):
        """
        Try NVENC first.
        If not available, fallback to libx264.
        """
        try:
            result = subprocess.run(
                [ffmpeg_path, "-encoders"],
                capture_output=True,
                text=True
            )
            if "h264_nvenc" in result.stdout:
                return ["-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", "18"]
        except:
            pass

        # Fallback
        return ["-c:v", "libx264", "-preset", "medium", "-crf", "18"]

    def process(self, input_path, output_path, progress_callback=None):

        base_path = self._get_base_path()

        ffmpeg_path = os.path.join(base_path, "ffmpeg.exe")
        ffprobe_path = os.path.join(base_path, "ffprobe.exe")

        self.stop_requested = False
        self.frame_count = 0
        start_time = time.time()

        # -------------------------
        # Probe video info
        # -------------------------
        probe_cmd = [
            ffprobe_path, "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
            "-of", "csv=p=0",
            input_path
        ]

        try:
            probe = subprocess.check_output(probe_cmd).decode().strip().split(",")
        except subprocess.CalledProcessError:
            raise RuntimeError("Failed to probe video. Ensure FFmpeg is bundled correctly.")

        width = int(probe[0])
        height = int(probe[1])

        num, denom = probe[2].split("/")
        fps = float(num) / float(denom)

        total_frames = None
        if len(probe) >= 4 and probe[3].isdigit():
            total_frames = int(probe[3])

        # -------------------------
        # Decoder (video frames)
        # -------------------------
        decode_cmd = [
            ffmpeg_path,
            "-i", input_path,
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-"
        ]

        # -------------------------
        # Encoder (processed video + original audio)
        # -------------------------
        video_encoder_settings = self._select_video_encoder(ffmpeg_path)

        encoder_cmd = [
            ffmpeg_path,
            "-y",

            # Processed raw video input
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
            *video_encoder_settings,

            "-pix_fmt", "yuv420p",

            # Audio copy
            "-c:a", "copy",

            # Sync safety
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

        # -------------------------
        # Frame Processing Loop
        # -------------------------
        while True:

            if self.stop_requested:
                break

            raw_frame = decoder.stdout.read(frame_size)
            if len(raw_frame) != frame_size:
                break

            frame = np.frombuffer(raw_frame, np.uint8).reshape((height, width, 3)).copy()
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

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    if y2 > height * self.profile["dashboard_ignore_ratio"]:
                        continue

                    area = (x2 - x1) * (y2 - y1)
                    closeness = area / (width * height)

                    if closeness > self.profile["red_threshold"]:
                        color = (0, 0, 255)
                        thickness = 4 + int(
                            2 * abs(math.sin(self.frame_count * self.profile["pulse_speed"]))
                        )
                        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, thickness + 8)
                    elif closeness > self.profile["yellow_threshold"]:
                        color = (0, 255, 255)
                        thickness = 3
                    else:
                        color = (255, 255, 255)
                        thickness = 2

                    draw_hud_box(frame, x1, y1, x2, y2, color, thickness)

            frame = apply_glow(frame, overlay, self.profile["glow_kernel"])

            try:
                encoder.stdin.write(frame.tobytes())
            except BrokenPipeError:
                break

            if total_frames and progress_callback:
                elapsed = time.time() - start_time
                percent = int((frame_count / total_frames) * 100)
                progress_callback(percent, frame_count, elapsed)

        # -------------------------
        # CLEAN SHUTDOWN
        # -------------------------

        if decoder.stdout:
            decoder.stdout.close()

        if encoder.stdin:
            encoder.stdin.close()

        if self.stop_requested:
            decoder.terminate()
            encoder.terminate()

        decoder.wait()
        encoder.wait()