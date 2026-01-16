# 🎬 YouTube Downloader

A cross-platform YouTube video and audio downloader with a modern GUI built using Python, yt-dlp, and PyQt6.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)

## ✨ Features

- 📹 **Video Downloads** - Download YouTube videos in various qualities (144p to 4K)
- 🎵 **Audio Extraction** - Extract audio as MP3, M4A, AAC, WAV, FLAC
- 📱 **YouTube Shorts** - Full support for YouTube Shorts
- 📋 **Playlist Support** - Download entire playlists
- 🎯 **Quality Selection** - Choose from 144p to 4K (8K)
- 📊 **Progress Tracking** - Real-time progress, speed, and ETA
- 🗂️ **Queue System** - Queue multiple downloads
- 🌗 **Dark Theme** - Modern dark UI design
- 🖥️ **Cross-Platform** - Works on Windows and Linux

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- FFmpeg (for merging video/audio streams)

### Step 1: Clone the Repository

```bash
git clone https://github.com/Ravi-Wijerathne/yt_downloader.git
cd yt_downloader
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install FFmpeg

**Windows:**
1. Download from [FFmpeg Official Site](https://ffmpeg.org/download.html)
2. Extract and add to PATH, or place in the `ffmpeg/` folder

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

## 🚀 Usage

### Check Prerequisites (Optional)

Before running the application, you can verify all system requirements are installed:

```bash
python check_prerequisites.py
```

This script checks:
- Python version (3.11+)
- FFmpeg installation
- Required Python packages
- System compatibility

### Running the Application

**Recommended Method (Auto-setup):**
```bash
python run_app.py
```

This automated launcher will:
- Check all dependencies
- Install missing Python packages automatically
- Set up FFmpeg if needed
- Launch the application

**Direct Launch (if dependencies are installed):**
```bash
python main.py
```

### Quick Start

1. **Paste URL** - Copy a YouTube URL and click "Paste" or Ctrl+V
2. **Analyze** - Click "Analyze" to fetch video information
3. **Configure** - Select quality, format, and output location
4. **Download** - Click "Download" and watch the progress!

## 🗂️ Project Structure

```
yt_downloader/
│
├── main.py                 # Application entry point
├── run_app.py              # Automated launcher (checks/installs deps)
├── check_prerequisites.py  # System requirements checker
├── requirements.txt        # Python dependencies
├── README.md
│
├── gui/
│   ├── __init__.py
│   └── main_window.py     # Main GUI window
│
├── core/
│   ├── __init__.py
│   ├── downloader.py      # yt-dlp wrapper
│   ├── formats.py         # Format handling
│   └── progress.py        # Progress tracking
│
├── assets/
│   └── icon.png           # App icon
│
└── ffmpeg/                # Bundled FFmpeg (optional)
```

## ⚙️ Configuration Options

### Video Quality Options
| Quality | Resolution | Description |
|---------|------------|-------------|
| Best | Auto | Best available quality |
| 2160p | 3840×2160 | 4K Ultra HD |
| 1440p | 2560×1440 | 2K QHD |
| 1080p | 1920×1080 | Full HD |
| 720p | 1280×720 | HD |
| 480p | 854×480 | SD |
| 360p | 640×360 | Low |
| 240p | 426×240 | Very Low |
| 144p | 256×144 | Minimum |

### Output Formats
**Video:** MP4, MKV, WebM, AVI, MOV  
**Audio:** MP3, M4A, AAC, WAV, FLAC, Opus

## 📦 Building Executable

Create a standalone executable using PyInstaller:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable (Windows)
pyinstaller --onefile --windowed --icon=assets/icon.png --name="YouTubeDownloader" main.py

# Build executable (Linux)
pyinstaller --onefile --windowed --name="YouTubeDownloader" main.py
```

The executable will be created in the `dist/` folder.

### Bundling FFmpeg

To include FFmpeg in your build:

1. Place FFmpeg binaries in the `ffmpeg/` folder
2. Update PyInstaller command:

```bash
pyinstaller --onefile --windowed --add-data "ffmpeg;ffmpeg" --name="YouTubeDownloader" main.py
```

## 🔧 Troubleshooting

### Common Issues

**"FFmpeg not found"**
- Install FFmpeg and add to system PATH
- Or place FFmpeg in the `ffmpeg/` folder

**"yt-dlp not found"**
```bash
pip install --upgrade yt-dlp
```

**"Private video" error**
- Private videos cannot be downloaded
- Video must be public or unlisted

**"Age-restricted" error**
- Age-restricted videos may require login
- This feature is not currently supported

**Download stuck at 0%**
- Check your internet connection
- Try a different quality option
- Update yt-dlp: `pip install --upgrade yt-dlp`

## 📜 Legal Disclaimer

⚠️ **Important Notice:**

This tool is provided for **personal use only**. Please respect:

- YouTube's Terms of Service
- Copyright laws in your jurisdiction
- Content creators' rights

**Do not:**
- Download copyrighted content without permission
- Re-upload downloaded content
- Use for commercial purposes

The developers are not responsible for misuse of this software.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📋 Roadmap

- [x] Basic video/audio download
- [x] Quality selection
- [x] Progress tracking
- [x] Dark theme UI
- [ ] Subtitle download
- [ ] Playlist batch download
- [ ] Channel download
- [ ] Download history
- [ ] SponsorBlock integration
- [ ] Metadata editor

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The powerful download engine
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [FFmpeg](https://ffmpeg.org/) - Media processing

---

Made with ❤️ with Python
