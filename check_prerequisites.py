#!/usr/bin/env python3
"""
Prerequisites Checker for YouTube Downloader
Checks if all system-level prerequisites are installed correctly.

Run this script first before setting up the project.
"""

import sys
import os
import subprocess
import shutil
import platform

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

# For Windows, enable ANSI colors
if platform.system() == 'Windows':
    os.system('')  # Enable ANSI escape sequences


def print_header():
    """Print script header"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}   YouTube Downloader - Prerequisites Checker{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")


def print_status(name: str, status: bool, message: str = ""):
    """Print status of a check"""
    icon = f"{Colors.GREEN}✓{Colors.END}" if status else f"{Colors.RED}✗{Colors.END}"
    status_text = f"{Colors.GREEN}OK{Colors.END}" if status else f"{Colors.RED}MISSING{Colors.END}"
    print(f"  {icon} {name}: {status_text}")
    if message:
        print(f"      {Colors.YELLOW}→ {message}{Colors.END}")


def print_section(title: str):
    """Print section header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}▸ {title}{Colors.END}")
    print(f"  {'-'*40}")


def check_python_version() -> tuple[bool, str]:
    """Check if Python version is 3.11 or higher"""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major >= 3 and version.minor >= 11:
        return True, f"Python {version_str} installed"
    else:
        return False, f"Python {version_str} found, but 3.11+ required"


def check_pip() -> tuple[bool, str]:
    """Check if pip is available"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', '--version'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # Extract pip version from output
            pip_info = result.stdout.strip().split()[1]
            return True, f"pip {pip_info} installed"
        return False, "pip not working properly"
    except Exception as e:
        return False, f"pip check failed: {str(e)}"


def check_ffmpeg() -> tuple[bool, str]:
    """Check if FFmpeg is installed"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Check bundled FFmpeg first
    bundled_paths = [
        os.path.join(project_root, 'ffmpeg', 'ffmpeg.exe'),
        os.path.join(project_root, 'ffmpeg', 'ffmpeg'),
    ]
    
    for path in bundled_paths:
        if os.path.exists(path):
            return True, f"Found bundled FFmpeg at: {os.path.dirname(path)}"
    
    # Check system FFmpeg
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # Extract version from first line
                first_line = result.stdout.split('\n')[0]
                return True, f"System FFmpeg: {first_line}"
        except Exception:
            pass
        return True, f"Found at: {ffmpeg_path}"
    
    return False, "FFmpeg not found in PATH or ffmpeg/ folder"


def check_git() -> tuple[bool, str]:
    """Check if Git is installed (optional but recommended)"""
    git_path = shutil.which('git')
    if git_path:
        try:
            result = subprocess.run(
                ['git', '--version'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
        except Exception:
            pass
        return True, f"Found at: {git_path}"
    return False, "Git not installed (optional, but recommended)"


def check_virtual_env() -> tuple[bool, str]:
    """Check if running inside a virtual environment"""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if in_venv:
        venv_path = sys.prefix
        return True, f"Active: {venv_path}"
    return False, "Not in virtual environment (recommended to use one)"


def check_disk_space() -> tuple[bool, str]:
    """Check if there's enough disk space"""
    try:
        if platform.system() == 'Windows':
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(os.getcwd()),
                None, None,
                ctypes.pointer(free_bytes)
            )
            free_gb = free_bytes.value / (1024**3)
        else:
            statvfs = os.statvfs(os.getcwd())
            free_gb = (statvfs.f_frsize * statvfs.f_bavail) / (1024**3)
        
        if free_gb >= 1:
            return True, f"{free_gb:.1f} GB available"
        else:
            return False, f"Only {free_gb:.2f} GB available (need at least 1GB)"
    except Exception as e:
        return True, f"Could not check: {str(e)}"


def check_internet_connectivity() -> tuple[bool, str]:
    """Check if internet is available"""
    try:
        import urllib.request
        urllib.request.urlopen('https://www.youtube.com', timeout=5)
        return True, "Internet connection available"
    except Exception:
        return False, "Cannot reach YouTube (check internet connection)"


def get_ffmpeg_install_instructions() -> str:
    """Get FFmpeg installation instructions for current OS"""
    system = platform.system()
    
    if system == 'Windows':
        return """
    Option 1: Using winget (Windows Package Manager):
        winget install ffmpeg
    
    Option 2: Manual installation:
        1. Download from: https://ffmpeg.org/download.html
        2. Extract the archive
        3. Either:
           a) Add ffmpeg/bin folder to your system PATH, OR
           b) Copy ffmpeg.exe to the 'ffmpeg/' folder in this project
    
    Option 3: Using Chocolatey:
        choco install ffmpeg"""
    
    elif system == 'Darwin':  # macOS
        return """
    Using Homebrew:
        brew install ffmpeg
    
    Using MacPorts:
        sudo port install ffmpeg"""
    
    else:  # Linux
        return """
    Ubuntu/Debian:
        sudo apt update
        sudo apt install ffmpeg
    
    Fedora:
        sudo dnf install ffmpeg
    
    Arch Linux:
        sudo pacman -S ffmpeg"""


def main():
    """Main function to run all prerequisite checks"""
    print_header()
    
    all_passed = True
    warnings = []
    errors = []
    
    # System Information
    print_section("System Information")
    print(f"  • Operating System: {platform.system()} {platform.release()}")
    print(f"  • Architecture: {platform.machine()}")
    print(f"  • Python Path: {sys.executable}")
    print(f"  • Working Directory: {os.getcwd()}")
    
    # Required Prerequisites
    print_section("Required Prerequisites")
    
    # Python Version
    status, msg = check_python_version()
    print_status("Python 3.11+", status, msg)
    if not status:
        all_passed = False
        errors.append("Python 3.11 or higher is required")
    
    # pip
    status, msg = check_pip()
    print_status("pip", status, msg)
    if not status:
        all_passed = False
        errors.append("pip is required to install dependencies")
    
    # FFmpeg
    status, msg = check_ffmpeg()
    print_status("FFmpeg", status, msg)
    if not status:
        all_passed = False
        errors.append("FFmpeg is required for video/audio processing")
    
    # Optional Prerequisites
    print_section("Optional Prerequisites")
    
    # Git
    status, msg = check_git()
    print_status("Git", status, msg)
    if not status:
        warnings.append("Git is recommended for version control")
    
    # Virtual Environment
    status, msg = check_virtual_env()
    print_status("Virtual Environment", status, msg)
    if not status:
        warnings.append("Using a virtual environment is recommended")
    
    # System Checks
    print_section("System Checks")
    
    # Disk Space
    status, msg = check_disk_space()
    print_status("Disk Space", status, msg)
    if not status:
        warnings.append("Low disk space may cause issues during downloads")
    
    # Internet
    status, msg = check_internet_connectivity()
    print_status("Internet Connection", status, msg)
    if not status:
        warnings.append("Internet connection required for downloading videos")
    
    # Summary
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    
    if errors:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ ERRORS (Must Fix):{Colors.END}")
        for error in errors:
            print(f"   • {error}")
    
    if warnings:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  WARNINGS (Recommended):{Colors.END}")
        for warning in warnings:
            print(f"   • {warning}")
    
    # FFmpeg installation help if missing
    if "FFmpeg is required" in str(errors):
        print(f"\n{Colors.BLUE}{Colors.BOLD}📦 FFmpeg Installation Instructions:{Colors.END}")
        print(get_ffmpeg_install_instructions())
    
    # Final status
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    if all_passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All prerequisites are satisfied!{Colors.END}")
        print(f"\n{Colors.CYAN}Next Steps:{Colors.END}")
        print("   1. Create a virtual environment (if not already):")
        print("      python -m venv venv")
        print("      venv\\Scripts\\activate  (Windows)")
        print("   2. Run the dependency checker and launcher:")
        print("      python run_app.py")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Some prerequisites are missing!{Colors.END}")
        print(f"\n{Colors.YELLOW}Please install the missing prerequisites and run this script again.{Colors.END}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
