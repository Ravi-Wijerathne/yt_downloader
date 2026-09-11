# Video Downloader

A cross-platform video and audio downloader (supporting YouTube and more) with a modern GUI built using Python, yt-dlp, and PyQt6.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- Download videos in various qualities (144p to 4K)
- Extract audio as MP3, M4A, AAC, WAV, FLAC
- Support for YouTube (Videos, Shorts, Playlists)
- Real-time progress tracking
- Queue system for multiple downloads
- Modern dark theme GUI

## Requirements

- Python 3.11 or higher
- FFmpeg (required for merging audio/video and full functionality)
- Git LFS if you want Git to download the bundled Windows FFmpeg executables

## Installation & Setup

### 1. Clone the repository:
```bash
git clone https://github.com/Ravi-Wijerathne/yt_downloader.git
cd yt_downloader
```

### 2. Create and activate a virtual environment:
- **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```
- **Windows:**
  ```cmd
  python -m venv .venv
  .venv\Scripts\activate
  ```

### 3. Install dependencies:
```bash
pip install -r requirements.txt
```
*(If `pip` command is not recognized, run `.venv/bin/python -m pip install -r requirements.txt` on macOS/Linux or `.venv\Scripts\python.exe -m pip install -r requirements.txt` on Windows)*

### 4. Install FFmpeg (Required):
FFmpeg is required for merging audio/video streams and format conversion. Ensure `ffmpeg` is installed and accessible in your system `PATH`:
- **macOS:** `brew install ffmpeg`
- **Windows:** `choco install ffmpeg` or `winget install ffmpeg` (or use Git LFS if retrieving bundled Windows binaries: `git lfs pull`)
- **Linux:** `sudo apt update && sudo apt install ffmpeg`

## Running the Application

Once dependencies are installed and your virtual environment is active:

```bash
python main.py
```

## Running Tests

After activating your virtual environment, run:

```bash
python -m pytest
```

To run tests with coverage:

```bash
python -m pytest --cov=core --cov=gui --cov=main --cov-report=term-missing
```

## Supported URLs

- YouTube videos: `https://www.youtube.com/watch?v=...`
- YouTube Shorts: `https://www.youtube.com/shorts/...`
- Playlists: `https://www.youtube.com/playlist?list=...`
- Shortened URLs: `https://youtu.be/...`

## Usage

1. Paste a YouTube URL into the URL field
2. Click "Analyze" to fetch video information
3. Select quality, format, and output location
4. Click "Download" to start

## Troubleshooting

 - **FFmpeg not found**: FFmpeg must be installed on the host and available on your `PATH`.
    Install it using your platform's package manager and re-run the launcher.
    - macOS (Homebrew): `brew install ffmpeg`
    - Windows (Chocolatey): `choco install ffmpeg -y`  
       or (WinGet): `winget install ffmpeg`
    - Debian/Ubuntu: `sudo apt update && sudo apt install -y ffmpeg`
    After installation, verify with `ffmpeg -version`.
- **Download fails**: Check internet connection, verify YouTube URL is correct
- **Application won't start**: Update packages with `pip install -r requirements.txt`

## Legal Notice

This tool is for **personal use only**. Please respect YouTube's Terms of Service and copyright laws.

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- [FFmpeg](https://ffmpeg.org/)
