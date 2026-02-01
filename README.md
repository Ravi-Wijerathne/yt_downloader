# YouTube Downloader

A cross-platform YouTube video and audio downloader with a modern GUI built using Python, yt-dlp, and PyQt6.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- Download videos in various qualities (144p to 4K)
- Extract audio as MP3, M4A, AAC, WAV, FLAC
- Support for YouTube Shorts and playlists
- Real-time progress tracking
- Queue system for multiple downloads
- Modern dark theme GUI

## Requirements

- Python 3.11 or higher
- FFmpeg (optional, for merging audio/video)

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Ravi-Wijerathne/yt_downloader.git
   cd yt_downloader
   ```

2. **Run the application:**
   ```bash
   python run_app.py
   ```
   
   The script will automatically:
   - Check all dependencies
   - Install missing packages
   - Verify FFmpeg installation
   - Launch the application

## Optional: Manual Setup

If you prefer manual setup:

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
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

- **FFmpeg not found**: Install FFmpeg and add to PATH, or place in the `ffmpeg/` folder
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
