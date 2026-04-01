from types import SimpleNamespace

import pytest

import run_app


@pytest.mark.unit
def test_get_venv_python_windows_path(monkeypatch):
    monkeypatch.setattr(run_app.platform, "system", lambda: "Windows")

    path = run_app._get_venv_python()

    assert path.endswith(".venv\\Scripts\\python.exe")


@pytest.mark.unit
def test_is_running_in_venv_true(monkeypatch):
    monkeypatch.setattr(run_app, "_get_venv_python", lambda: run_app.sys.executable)

    assert run_app._is_running_in_venv() is True


@pytest.mark.unit
def test_check_python_version_ok(monkeypatch):
    monkeypatch.setattr(run_app.sys, "version_info", SimpleNamespace(major=3, minor=11, micro=1))

    assert run_app.check_python_version() is True


@pytest.mark.unit
def test_check_project_structure_missing(monkeypatch):
    monkeypatch.setattr(run_app.os.path, "exists", lambda _p: False)

    ok = run_app.check_project_structure()

    assert ok is False


@pytest.mark.unit
def test_verify_dependencies_reports_missing(monkeypatch):
    monkeypatch.setattr(run_app, "check_package_installed", lambda name, imp: (False, "missing"))

    all_ok, missing = run_app.verify_dependencies()

    assert all_ok is False
    assert "yt-dlp" in missing
    assert "PyQt6" in missing


@pytest.mark.unit
def test_check_ffmpeg_via_system(monkeypatch):
    monkeypatch.setattr(run_app.os.path, "exists", lambda _p: False)
    monkeypatch.setattr(run_app.shutil, "which", lambda _cmd: "C:/ffmpeg.exe")

    assert run_app.check_ffmpeg() is True


@pytest.mark.unit
def test_install_requirements_missing_file(monkeypatch):
    monkeypatch.setattr(run_app.os.path, "exists", lambda _p: False)

    assert run_app.install_requirements() is False
