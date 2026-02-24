# R.A.S -- Rider Assist System

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![CUDA](https://img.shields.io/badge/GPU-CUDA-green)
![Build](https://img.shields.io/badge/Build-Standalone%20EXE-red)

AI-powered motorcycle video intelligence overlay system for
rider-centric content creation.

R.A.S enhances rider POV footage by detecting vehicles, pedestrians, and
road elements frame-by-frame and applying intelligent threat-based
visual overlays --- while preserving original audio.

------------------------------------------------------------------------

## 🚀 Download (Windows -- No Setup Required)

### ✅ Recommended for Most Users

1.  Go to the **Releases** section of this repository\
2.  Download the latest `RAS.exe`\
3.  Double-click\
4.  Load your video\
5.  Render AI-enhanced output

✔ No Python installation required\
✔ No FFmpeg installation required\
✔ Everything is bundled

------------------------------------------------------------------------

## 🎯 Core Features

-   Frame-by-frame object detection (YOLOv8)
-   Threat-level classification (Red / Yellow / White)
-   Pulse animation for high-risk objects
-   Cinematic glow rendering
-   4K video processing support
-   Original audio preserved during export
-   GPU acceleration (CUDA auto-detected)
-   Live FPS telemetry during render
-   Graceful render cancellation
-   Hardcore racing aesthetic UI

------------------------------------------------------------------------

## 🏍 Designed For

-   Moto vloggers\
-   High-speed POV riders\
-   Mountain riding cinematography\
-   Urban riding analysis\
-   AI-enhanced content creators

------------------------------------------------------------------------

## 🎬 Example Output

![R.A.S Demo Case Car](assets/demo-1.png)\
![R.A.S Demo Case Bike](assets/demo-2.png)\
![R.A.S Demo Case Animals](assets/demo-3.png)\
![R.A.S Demo Case Bus](assets/demo-4.png)\
![R.A.S Demo Case Human](assets/demo-5.png)\
![R.A.S Demo Case Multiple Vehicles](assets/demo-6.png)\
![R.A.S Demo Case Different Objects Tracking](assets/demo-7.png)

------------------------------------------------------------------------

## 💻 Running From Source (Developers)

### Requirements

-   Python 3.9+
-   NVIDIA GPU (recommended)
-   CUDA-enabled PyTorch (optional but recommended)

### Installation

``` bash
git clone https://github.com/cybergears/ras-ai.git
cd ras-ai
pip install -r requirements.txt
```

### Run Desktop UI

``` bash
python main.py
```

### Run CLI Mode

``` bash
python ras_cli.py --input input.mp4 --output output.mp4
```

With profile:

``` bash
python ras_cli.py --input input.mp4 --output output.mp4 --profile profiles/motorcycle.json
```

------------------------------------------------------------------------

## ⚡ GPU Support

R.A.S automatically detects CUDA-enabled GPUs.

To test GPU availability:

``` bash
python -c "import torch; print(torch.cuda.is_available())"
```

If `True`, detection runs on GPU automatically.

------------------------------------------------------------------------

## 🧠 How It Works

1.  Video frames are decoded via FFmpeg\
2.  YOLOv8 performs object detection\
3.  Threat levels are calculated based on bounding box area\
4.  Visual overlays are rendered frame-by-frame\
5.  Original audio is preserved and muxed back\
6.  Final output is encoded using GPU acceleration

------------------------------------------------------------------------

## 📂 Project Structure

    ras/
     ├── engine.py
     ├── detection.py
     ├── renderer.py
     ├── config.py

    ras_ui/
     ├── hardcore_window.py
     ├── worker.py

    profiles/
     ├── motorcycle.json

------------------------------------------------------------------------

## 📌 Roadmap

-   [x] Desktop UI (PyQt6)
-   [x] Audio-preserving render
-   [x] GPU acceleration
-   [x] Live FPS telemetry
-   [ ] Preset system
-   [ ] Lean angle detection
-   [ ] Motion-based telemetry overlay
-   [ ] Real-time live camera mode
-   [ ] Racing profile pack
-   [ ] macOS build

------------------------------------------------------------------------

## ⚠ Disclaimer

R.A.S is a post-processing video enhancement tool.\
It is not a real-world rider assist, collision detection, or safety
system.

Use responsibly.

------------------------------------------------------------------------

## 📄 License

MIT License\
Copyright (c) 2026 Shahrukh Sheikh
