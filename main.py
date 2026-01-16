#!/usr/bin/env python3
"""
YouTube Downloader - Main Entry Point
A cross-platform YouTube video and audio downloader with GUI

Author: YouTube Downloader Team
License: MIT
"""

import sys
import os

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []
    
    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp")
        
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        missing.append("PyQt6")
        
    if missing:
        print("=" * 50)
        print("Missing required dependencies!")
        print("=" * 50)
        print("\nPlease install the following packages:")
        print(f"  pip install {' '.join(missing)}")
        print("\nOr run:")
        print("  pip install -r requirements.txt")
        print("=" * 50)
        sys.exit(1)


def check_ffmpeg():
    """Check if FFmpeg is available"""
    import shutil
    
    # Check bundled FFmpeg first
    bundled_paths = [
        os.path.join(PROJECT_ROOT, 'ffmpeg', 'ffmpeg.exe'),
        os.path.join(PROJECT_ROOT, 'ffmpeg', 'ffmpeg'),
    ]
    
    for path in bundled_paths:
        if os.path.exists(path):
            return True
            
    # Check system FFmpeg
    if shutil.which('ffmpeg'):
        return True
        
    print("=" * 50)
    print("WARNING: FFmpeg not found!")
    print("=" * 50)
    print("\nSome features may not work without FFmpeg:")
    print("  - Merging video and audio streams")
    print("  - Converting to MP3/M4A")
    print("  - High quality downloads")
    print("\nInstall FFmpeg:")
    print("  Windows: Download from https://ffmpeg.org/download.html")
    print("  Linux:   sudo apt install ffmpeg")
    print("  macOS:   brew install ffmpeg")
    print("=" * 50)
    print()
    return False


def main():
    """Main application entry point"""
    # Check dependencies first
    check_dependencies()
    
    # Check FFmpeg (warning only)
    check_ffmpeg()
    
    # Import after dependency check
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon
    from PyQt6.QtCore import Qt
    
    from gui.main_window import MainWindow
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Downloader")
    app.setOrganizationName("YT Downloader")
    app.setApplicationVersion("1.0.0")
    
    # Set application icon if available
    icon_path = os.path.join(PROJECT_ROOT, 'assets', 'icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
