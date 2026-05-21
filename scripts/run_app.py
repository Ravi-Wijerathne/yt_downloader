#!/usr/bin/env python3
"""
YouTube Downloader - Automated Runner
Creates a virtual environment, installs dependencies, and launches the application.

Run this script to start the YouTube Downloader application.
It will automatically set up a venv if one doesn't exist.
"""

import sys
import os
import subprocess
import importlib
import platform
import shutil
import venv
from pathlib import PureWindowsPath


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


if platform.system() == 'Windows':
    os.system('')


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VENV_DIR = os.path.join(PROJECT_ROOT, '.venv')


def _get_venv_python() -> str:
    """Get the path to the Python executable inside the venv."""
    if platform.system() == 'Windows':
        return str(PureWindowsPath(VENV_DIR) / 'Scripts' / 'python.exe')
    return os.path.join(VENV_DIR, 'bin', 'python')


def _get_bundled_ffmpeg_candidates() -> list[str]:
    """Return likely FFmpeg binary locations bundled with the project."""
    binary_names = ['ffmpeg.exe', 'ffmpeg'] if platform.system() == 'Windows' else ['ffmpeg', 'ffmpeg.exe']
    # Prefer project-level `ffmpeg/` folder so platform-native binaries are
    # discovered before any architecture-specific assets bundles.
    bundle_roots = [
        os.path.join(PROJECT_ROOT, 'ffmpeg'),
        os.path.join(PROJECT_ROOT, 'assets', 'ffmpeg'),
        os.path.join(PROJECT_ROOT, 'assets', 'ffmpeg', 'ffmpeg-8.0.1-essentials_build', 'bin'),
    ]

    candidates = []
    for root in bundle_roots:
        for binary_name in binary_names:
            candidates.append(os.path.join(root, binary_name))
    return candidates


def _find_bundled_ffmpeg() -> str | None:
    """Find a bundled FFmpeg binary if the project ships one."""
    for candidate in _get_bundled_ffmpeg_candidates():
        if os.path.isfile(candidate):
            return candidate
    return None


def _is_running_in_venv() -> bool:
    """Check if the current interpreter is the venv's Python."""
    venv_python = os.path.realpath(_get_venv_python())
    current_python = os.path.realpath(sys.executable)
    return current_python == venv_python


def _ensure_venv_and_relaunch():
    """
    Ensure the venv exists, then re-launch this script inside it.
    This function is called when we detect we are NOT running inside the venv.
    It never returns — it replaces the current process (or exits with the child's code).
    """
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}   YouTube Downloader - Automated Launcher{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")

    version = sys.version_info
    if not (version.major >= 3 and version.minor >= 11):
        print(f"  {Colors.RED}✗ Python 3.11+ required (found {version.major}.{version.minor}){Colors.END}")
        print(f"\n{Colors.RED}Please install Python 3.11 or higher.{Colors.END}")
        sys.exit(1)
    print(f"  {Colors.GREEN}✓ Python {version.major}.{version.minor}.{version.micro}{Colors.END}")

    venv_python = _get_venv_python()
    if not os.path.isfile(venv_python):
        print(f"\n{Colors.BLUE}{Colors.BOLD}▸ Creating Virtual Environment{Colors.END}")
        print(f"  {'-'*40}")
        print(f"  {Colors.BLUE}⟳{Colors.END} {Colors.BLUE}Creating venv at .venv ...{Colors.END}")
        try:
            venv.create(VENV_DIR, with_pip=True)
            print(f"  {Colors.GREEN}✓{Colors.END} {Colors.GREEN}Virtual environment created{Colors.END}")
        except Exception as e:
            print(f"  {Colors.RED}✗{Colors.END} {Colors.RED}Failed to create venv: {e}{Colors.END}")
            sys.exit(1)
    else:
        print(f"\n{Colors.BLUE}{Colors.BOLD}▸ Virtual Environment{Colors.END}")
        print(f"  {'-'*40}")
        print(f"  {Colors.GREEN}✓{Colors.END} {Colors.GREEN}Virtual environment found at .venv{Colors.END}")

    print(f"\n  {Colors.BLUE}⟳{Colors.END} {Colors.BLUE}Re-launching inside venv ...{Colors.END}\n")

    script = os.path.abspath(__file__)
    result = subprocess.run([venv_python, script] + sys.argv[1:])
    sys.exit(result.returncode)


if __name__ == "__main__" and not _is_running_in_venv():
    try:
        _ensure_venv_and_relaunch()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Interrupted by user.{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.END}")
        sys.exit(1)


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
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', None)
        if version:
            return True, version

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
    command = [sys.executable, '-m', 'pip', 'install', package_name, '--quiet', '--disable-pip-version-check', '--no-input']
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0 and _looks_like_pip_certificate_error(result):
            if _repair_pip_installation():
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '--trusted-host', 'pypi.org', '--trusted-host', 'files.pythonhosted.org', package_name, '--quiet', '--disable-pip-version-check', '--no-input'],
                    capture_output=True,
                    text=True,
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
        command = [sys.executable, '-m', 'pip', 'install', '-r', requirements_file, '--quiet', '--disable-pip-version-check', '--no-input']
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0 and _looks_like_pip_certificate_error(result):
            if _repair_pip_installation():
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '--trusted-host', 'pypi.org', '--trusted-host', 'files.pythonhosted.org', '-r', requirements_file, '--quiet', '--disable-pip-version-check', '--no-input'],
                    capture_output=True,
                    text=True,
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


def _looks_like_pip_certificate_error(result: subprocess.CompletedProcess) -> bool:
    """Detect certificate-bundle failures that are common on fresh macOS venvs."""
    output = f"{result.stdout}\n{result.stderr}".lower()
    return any(
        token in output
        for token in (
            'could not find a suitable tls ca certificate bundle',
            'invalid path',
            'cacert.pem',
            'certificate bundle',
        )
    )


def _repair_pip_installation() -> bool:
    """Repair a broken pip bootstrap before retrying dependency installation."""
    print_status("pip certificate bundle looks broken; trying to repair bootstrap...", "warning")

    ensurepip_result = subprocess.run(
        [sys.executable, '-m', 'ensurepip', '--upgrade', '--default-pip'],
        capture_output=True,
        text=True,
    )

    if ensurepip_result.returncode != 0:
        return False

    upgrade_result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '--trusted-host', 'pypi.org', '--trusted-host', 'files.pythonhosted.org', '--upgrade', '--disable-pip-version-check', '--no-input', 'pip', 'setuptools', 'wheel', 'certifi'],
        capture_output=True,
        text=True,
    )
    return upgrade_result.returncode == 0


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available"""
    # Require FFmpeg to be installed system-wide and available on PATH.
    if shutil.which('ffmpeg'):
        print_status("FFmpeg found in system PATH", "success")
        return True

    print_status("FFmpeg not found. FFmpeg is required for full functionality.", "error")
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

    os.chdir(PROJECT_ROOT)

    try:
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)

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
    """Main function - check dependencies and run application (runs inside venv)"""
    print_header()

    print_status(f"Running inside venv: {VENV_DIR}", "success")
    print_status(f"Python: {sys.executable}", "info")

    print_section("Checking Python Version")
    if not check_python_version():
        print(f"\n{Colors.RED}Please install Python 3.11 or higher.{Colors.END}")
        return 1
    print_status(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", "success")

    print_section("Checking Project Structure")
    if not check_project_structure():
        print(f"\n{Colors.RED}Project structure is incomplete. Please re-download the project.{Colors.END}")
        return 1

    print_section("Checking Dependencies")
    all_ok, missing = verify_dependencies()

    if not all_ok:
        print_section("Installing Missing Dependencies")

        if os.path.exists(os.path.join(PROJECT_ROOT, 'requirements.txt')):
            install_requirements()
        else:
            for package in missing:
                install_package(package)

        print_section("Verifying Installation")
        all_ok, still_missing = verify_dependencies()

        if not all_ok:
            print(f"\n{Colors.RED}Failed to install required dependencies:{Colors.END}")
            for pkg in still_missing:
                print(f"   - {pkg}")
            print(f"\n{Colors.YELLOW}Try manually running:{Colors.END}")
            print(f"  {_get_venv_python()} -m pip install -r requirements.txt")
            return 1

    print_section("Checking FFmpeg")
    ffmpeg_ok = check_ffmpeg()
    if not ffmpeg_ok:
        print(f"\n{Colors.RED}FFmpeg is required to run this application.\nPlease install FFmpeg using your package manager and re-run this script.{Colors.END}")
        print("  Windows (Chocolatey): choco install ffmpeg -y")
        print("  Windows (WinGet): winget install ffmpeg")
        print("  macOS (Homebrew): brew install ffmpeg")
        print("  Debian/Ubuntu: sudo apt update && sudo apt install -y ffmpeg")
        return 1

    print(f"\n{Colors.GREEN}{Colors.BOLD}All checks passed!{Colors.END}")

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
