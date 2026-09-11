import pytest
import sys
import os

@pytest.mark.unit
def test_check_dependencies_success(monkeypatch):
    import main
    # Should not sys.exit if all dependencies are there
    main.check_dependencies()

@pytest.mark.unit
def test_check_dependencies_fails(monkeypatch):
    import main
    import builtins
    
    calls = []
    original_import = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", lambda name, *a, **k: (_ for _ in ()).throw(ImportError(name)) if name in ("yt_dlp", "PyQt6") else original_import(name, *a, **k))
    monkeypatch.setattr(sys, "exit", lambda code: calls.append(code))
    
    main.check_dependencies()
    assert 1 in calls

@pytest.mark.unit
def test_check_ffmpeg_missing(monkeypatch):
    import main
    import shutil
    monkeypatch.setattr(os.path, "exists", lambda p: False)
    monkeypatch.setattr(shutil, "which", lambda cmd: None)
    
    assert main.check_ffmpeg() is False

@pytest.mark.unit
def test_main_runs_app(monkeypatch):
    import main
    
    calls = []
    
    class FakeApp:
        def __init__(self, args):
            pass
        def setApplicationName(self, n): pass
        def setOrganizationName(self, n): pass
        def setApplicationVersion(self, n): pass
        def setWindowIcon(self, icon): pass
        @classmethod
        def setHighDpiScaleFactorRoundingPolicy(cls, p): pass
        @classmethod
        def instance(cls): return None
        def exec(self):
            calls.append("exec")
            return 0
            
    class FakeMainWindow:
        def show(self):
            calls.append("show")
    
    # Bypass dependency checks
    monkeypatch.setattr(main, "check_dependencies", lambda: None)
    monkeypatch.setattr(main, "check_ffmpeg", lambda: True)
    
    # Mock PyQt classes globally so `main()` local imports get the fakes
    import PyQt6.QtWidgets
    monkeypatch.setattr(PyQt6.QtWidgets, "QApplication", FakeApp)
    
    import gui.main_window
    monkeypatch.setattr(gui.main_window, "MainWindow", FakeMainWindow)
    
    monkeypatch.setattr(sys, "exit", lambda code: calls.append(f"exit_{code}"))
    
    main.main()
    
    assert calls == ["show", "exec", "exit_0"]
