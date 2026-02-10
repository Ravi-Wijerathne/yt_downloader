#!/usr/bin/env python3
"""
YouTube Downloader - Automated Runner
Checks dependencies, installs them if missing, and launches the application.

Run this script to start the YouTube Downloader application.
"""

import sys
import os
import subprocess
import importlib
import platform
import shutil

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

# Project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def print_header():
    """Print script header"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}   YouTube Downloader - Automated Launcher{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")


def print_status(message: str, status: str = "info"):
    """Print status message with color"""
    if status == "success":
        icon = f"{Colors.GREEN}✓{Colors.END}"
        color = Colors.GREEN
    elif status == "error":
        icon = f"{Colors.RED}✗{Colors.END}"
        color = Colors.RED
    elif status == "warning":
        icon = f"{Colors.YELLOW}⚠{Colors.END}"
        color = Colors.YELLOW
    elif status == "working":
        icon = f"{Colors.BLUE}⟳{Colors.END}"
        color = Colors.BLUE
    else:
        icon = f"{Colors.CYAN}•{Colors.END}"
        color = Colors.CYAN
    
    print(f"  {icon} {color}{message}{Colors.END}")


def print_section(title: str):
    """Print section header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}▸ {title}{Colors.END}")
    print(f"  {'-'*40}")


def check_python_version() -> bool:
    """Verify Python version is 3.11+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        return True
    print_status(f"Python 3.11+ required (found {version.major}.{version.minor})", "error")
    return False


def get_installed_packages() -> dict:
    """Get dictionary of installed packages and versions"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'list', '--format=json'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            import json
            packages = json.loads(result.stdout)
            return {pkg['name'].lower(): pkg['version'] for pkg in packages}
    except Exception:
        pass
    return {}


def check_package_installed(package_name: str, import_name: str = None) -> tuple[bool, str]:
    """
    Check if a package is installed and importable.
    Returns (is_installed, version_or_error)
    """
    import_name = import_name or package_name.replace('-', '_')
    
    try:
        # Try to import the module
        module = importlib.import_module(import_name)
        
        # Try to get version
        version = getattr(module, '__version__', None)
        if version:
            return True, version
        
        # If no __version__, check via pip
        installed = get_installed_packages()
        pkg_lower = package_name.lower()
        if pkg_lower in installed:
            return True, installed[pkg_lower]
        
        return True, "installed"
    except ImportError:
        return False, "not installed"


def install_package(package_name: str) -> bool:
    """Install a package using pip"""
    print_status(f"Installing {package_name}...", "working")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', package_name, '--quiet'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_status(f"Successfully installed {package_name}", "success")
            return True
        else:
            print_status(f"Failed to install {package_name}: {result.stderr}", "error")
            return False
    except Exception as e:
        print_status(f"Error installing {package_name}: {str(e)}", "error")
        return False


def install_requirements() -> bool:
    """Install all requirements from requirements.txt"""
    requirements_file = os.path.join(PROJECT_ROOT, 'requirements.txt')
    
    if not os.path.exists(requirements_file):
        print_status("requirements.txt not found!", "error")
        return False
    
    print_status("Installing from requirements.txt...", "working")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', requirements_file, '--quiet'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_status("All requirements installed successfully", "success")
            return True
        else:
            print_status(f"Some requirements failed: {result.stderr}", "warning")
            return False
    except Exception as e:
        print_status(f"Error installing requirements: {str(e)}", "error")
        return False


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available"""
    # Check bundled FFmpeg first
    bundled_paths = [
        os.path.join(PROJECT_ROOT, 'ffmpeg', 'ffmpeg.exe'),
        os.path.join(PROJECT_ROOT, 'ffmpeg', 'ffmpeg'),
    ]
    
    for path in bundled_paths:
        if os.path.exists(path):
            print_status(f"FFmpeg found: {os.path.dirname(path)}", "success")
            return True
    
    # Check system FFmpeg
    if shutil.which('ffmpeg'):
        print_status("FFmpeg found in system PATH", "success")
        return True
    
    print_status("FFmpeg not found (some features may not work)", "warning")
    return False


def verify_dependencies() -> tuple[bool, list]:
    """
    Verify all required dependencies are installed.
    Returns (all_ok, missing_packages)
    """
    required_packages = [
        ('yt-dlp', 'yt_dlp'),
        ('yt-dlp-ejs', 'yt_dlp_ejs'),
        ('PyQt6', 'PyQt6'),
    ]
    
    missing = []
    
    for package_name, import_name in required_packages:
        is_installed, version = check_package_installed(package_name, import_name)
        if is_installed:
            print_status(f"{package_name} ({version})", "success")
        else:
            print_status(f"{package_name} - {version}", "error")
            missing.append(package_name)
    
    return len(missing) == 0, missing


def check_project_structure() -> bool:
    """Verify project structure is complete"""
    required_files = [
        'main.py',
        'requirements.txt',
        os.path.join('gui', '__init__.py'),
        os.path.join('gui', 'main_window.py'),
        os.path.join('core', '__init__.py'),
        os.path.join('core', 'downloader.py'),
    ]
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(PROJECT_ROOT, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print_status("Missing project files:", "error")
        for f in missing_files:
            print(f"      - {f}")
        return False
    
    print_status("Project structure verified", "success")
    return True


def run_application():
    """Run the main application"""
    print_section("Launching Application")
    print_status("Starting YouTube Downloader...", "working")
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}\n")
    
    # Change to project directory
    os.chdir(PROJECT_ROOT)
    
    # Import and run main
    try:
        # Add project root to path
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)
        
        # Import main module
        from main import main
        main()
        
    except ImportError as e:
        print_status(f"Import error: {str(e)}", "error")
        print_status("Try running: python main.py", "info")
        return False
    except Exception as e:
        print_status(f"Error running application: {str(e)}", "error")
        return False
    
    return True


def main():
    """Main function - check dependencies and run application"""
    print_header()
    
    # Step 1: Check Python version
    print_section("Checking Python Version")
    if not check_python_version():
        print(f"\n{Colors.RED}Please install Python 3.11 or higher.{Colors.END}")
        return 1
    print_status(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", "success")
    
    # Step 2: Check project structure
    print_section("Checking Project Structure")
    if not check_project_structure():
        print(f"\n{Colors.RED}Project structure is incomplete. Please re-download the project.{Colors.END}")
        return 1
    
    # Step 3: Check dependencies
    print_section("Checking Dependencies")
    all_ok, missing = verify_dependencies()
    
    # Step 4: Install missing dependencies if any
    if not all_ok:
        print_section("Installing Missing Dependencies")
        
        # Try installing from requirements.txt first
        if os.path.exists(os.path.join(PROJECT_ROOT, 'requirements.txt')):
            install_requirements()
        else:
            # Install individually
            for package in missing:
                install_package(package)
        
        # Verify again after installation
        print_section("Verifying Installation")
        all_ok, still_missing = verify_dependencies()
        
        if not all_ok:
            print(f"\n{Colors.RED}Failed to install required dependencies:{Colors.END}")
            for pkg in still_missing:
                print(f"   - {pkg}")
            print(f"\n{Colors.YELLOW}Try manually running: pip install -r requirements.txt{Colors.END}")
            return 1
    
    # Step 5: Check FFmpeg
    print_section("Checking FFmpeg")
    ffmpeg_ok = check_ffmpeg()
    if not ffmpeg_ok:
        print(f"\n{Colors.YELLOW}Note: FFmpeg is required for full functionality.{Colors.END}")
        print(f"{Colors.YELLOW}The application will start, but some features may not work.{Colors.END}")
        
        # Ask user if they want to continue
        try:
            response = input(f"\n{Colors.CYAN}Continue anyway? (y/n): {Colors.END}").strip().lower()
            if response not in ('y', 'yes'):
                print(f"\n{Colors.YELLOW}Please install FFmpeg and run this script again.{Colors.END}")
                print("  Windows: winget install ffmpeg")
                print("  Linux:   sudo apt install ffmpeg")
                return 1
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Cancelled by user.{Colors.END}")
            return 1
    
    # Step 6: All checks passed - run the application
    print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All checks passed!{Colors.END}")
    
    # Run the application
    run_application()
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Interrupted by user.{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.END}")
        sys.exit(1)
