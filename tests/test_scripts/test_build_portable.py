import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load_module():
    root = Path(__file__).resolve().parents[2]
    module_path = root / "build" / "build_portable.py"
    spec = importlib.util.spec_from_file_location("build_portable", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_clean_build_calls_rmtree_for_existing_dirs(monkeypatch):
    bp = _load_module()
    removed = []

    monkeypatch.setattr(bp.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(bp.shutil, "rmtree", lambda p: removed.append(p))

    bp.clean_build()

    assert len(removed) >= 2


@pytest.mark.unit
def test_check_dependencies_returns_false_when_missing_pyinstaller(monkeypatch):
    bp = _load_module()
    original_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "PyInstaller":
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    assert bp.check_dependencies() is False


@pytest.mark.unit
def test_build_executable_runs_pyinstaller(monkeypatch):
    bp = _load_module()
    captured = {}

    def fake_run(cmd, cwd=None):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(bp.subprocess, "run", fake_run)

    assert bp.build_executable() is True
    assert "PyInstaller" in " ".join(captured["cmd"])


@pytest.mark.unit
def test_create_zip_archive_returns_none_for_missing_path():
    bp = _load_module()

    result = bp.create_zip_archive("C:/does/not/exist")

    assert result is None
