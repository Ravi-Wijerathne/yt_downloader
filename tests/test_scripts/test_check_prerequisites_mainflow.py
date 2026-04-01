from types import SimpleNamespace

import pytest

import check_prerequisites as cp


@pytest.mark.unit
def test_check_git_missing(monkeypatch):
    monkeypatch.setattr(cp.shutil, "which", lambda _name: None)

    ok, msg = cp.check_git()

    assert ok is False
    assert "optional" in msg.lower()


@pytest.mark.unit
def test_check_disk_space_handles_exception(monkeypatch):
    monkeypatch.setattr(cp.platform, "system", lambda: "Linux")
    monkeypatch.setattr(cp.os, "statvfs", lambda *_: (_ for _ in ()).throw(OSError("boom")), raising=False)

    ok, msg = cp.check_disk_space()

    assert ok is True
    assert "could not check" in msg.lower()


@pytest.mark.unit
def test_ffmpeg_install_instructions_for_windows(monkeypatch):
    monkeypatch.setattr(cp.platform, "system", lambda: "Windows")

    msg = cp.get_ffmpeg_install_instructions()

    assert "winget" in msg.lower()


@pytest.mark.unit
def test_main_returns_success_when_required_checks_pass(monkeypatch):
    monkeypatch.setattr(cp, "check_python_version", lambda: (True, "ok"))
    monkeypatch.setattr(cp, "check_pip", lambda: (True, "ok"))
    monkeypatch.setattr(cp, "check_ffmpeg", lambda: (True, "ok"))
    monkeypatch.setattr(cp, "check_git", lambda: (True, "ok"))
    monkeypatch.setattr(cp, "check_virtual_env", lambda: (True, "ok"))
    monkeypatch.setattr(cp, "check_disk_space", lambda: (True, "ok"))
    monkeypatch.setattr(cp, "check_internet_connectivity", lambda: (True, "ok"))

    assert cp.main() == 0


@pytest.mark.unit
def test_main_returns_failure_when_required_checks_fail(monkeypatch):
    monkeypatch.setattr(cp, "check_python_version", lambda: (False, "bad"))
    monkeypatch.setattr(cp, "check_pip", lambda: (False, "bad"))
    monkeypatch.setattr(cp, "check_ffmpeg", lambda: (False, "bad"))
    monkeypatch.setattr(cp, "check_git", lambda: (False, "bad"))
    monkeypatch.setattr(cp, "check_virtual_env", lambda: (False, "bad"))
    monkeypatch.setattr(cp, "check_disk_space", lambda: (False, "bad"))
    monkeypatch.setattr(cp, "check_internet_connectivity", lambda: (False, "bad"))

    assert cp.main() == 1
