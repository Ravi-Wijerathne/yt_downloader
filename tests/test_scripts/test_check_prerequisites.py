from types import SimpleNamespace

import pytest

import check_prerequisites as cp


@pytest.mark.unit
def test_check_python_version_passes_for_311_plus(monkeypatch):
    monkeypatch.setattr(cp.sys, "version_info", SimpleNamespace(major=3, minor=11, micro=2))

    ok, msg = cp.check_python_version()

    assert ok is True
    assert "3.11.2" in msg


@pytest.mark.unit
def test_check_python_version_fails_for_low_version(monkeypatch):
    monkeypatch.setattr(cp.sys, "version_info", SimpleNamespace(major=3, minor=10, micro=9))

    ok, msg = cp.check_python_version()

    assert ok is False
    assert "3.10.9" in msg


@pytest.mark.unit
def test_check_pip_success(monkeypatch):
    class Result:
        returncode = 0
        stdout = "pip 25.0 from path"

    monkeypatch.setattr(cp.subprocess, "run", lambda *a, **k: Result())

    ok, msg = cp.check_pip()

    assert ok is True
    assert "pip 25.0" in msg


@pytest.mark.unit
def test_check_ffmpeg_prefers_bundled(monkeypatch):
    monkeypatch.setattr(cp.os.path, "exists", lambda p: p.endswith("ffmpeg.exe"))

    ok, msg = cp.check_ffmpeg()

    assert ok is True
    assert "bundled" in msg.lower()


@pytest.mark.unit
def test_check_virtual_env_detects_active(monkeypatch):
    monkeypatch.setattr(cp.sys, "real_prefix", "venv", raising=False)

    ok, msg = cp.check_virtual_env()

    assert ok is True
    assert "active" in msg.lower()


@pytest.mark.unit
def test_check_internet_connectivity_failure(monkeypatch):
    import urllib.request

    monkeypatch.setattr(urllib.request, "urlopen", lambda *_a, **_k: (_ for _ in ()).throw(OSError("offline")))

    ok, msg = cp.check_internet_connectivity()

    assert ok is False
    assert "cannot reach" in msg.lower()
