from types import SimpleNamespace

import pytest

import main


@pytest.mark.unit
def test_check_ffmpeg_returns_true_when_system_available(monkeypatch):
    monkeypatch.setattr(main.os.path, "exists", lambda p: False)
    monkeypatch.setattr("shutil.which", lambda cmd: "C:/ffmpeg.exe")

    assert main.check_ffmpeg() is True


@pytest.mark.unit
def test_check_ffmpeg_returns_false_when_missing(monkeypatch):
    monkeypatch.setattr(main.os.path, "exists", lambda p: False)
    monkeypatch.setattr("shutil.which", lambda cmd: None)

    assert main.check_ffmpeg() is False


@pytest.mark.unit
def test_check_dependencies_exits_on_missing_packages(monkeypatch):
    original_import = __import__

    def fake_import(name, *args, **kwargs):
        if name in {"yt_dlp", "PyQt6.QtWidgets"}:
            raise ImportError("missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    with pytest.raises(SystemExit):
        main.check_dependencies()


@pytest.mark.unit
def test_main_wires_qt_objects(monkeypatch):
    class FakeApp:
        def __init__(self, argv):
            self.argv = argv

        @staticmethod
        def setHighDpiScaleFactorRoundingPolicy(policy):
            return None

        def setApplicationName(self, *_):
            return None

        def setOrganizationName(self, *_):
            return None

        def setApplicationVersion(self, *_):
            return None

        def setWindowIcon(self, *_):
            return None

        def exec(self):
            return 0

    class FakeWindow:
        shown = False

        def show(self):
            FakeWindow.shown = True

    fake_widgets = SimpleNamespace(QApplication=FakeApp)
    fake_gui = SimpleNamespace(QIcon=lambda *_: None)
    fake_core = SimpleNamespace(Qt=SimpleNamespace(HighDpiScaleFactorRoundingPolicy=SimpleNamespace(PassThrough=1)))

    monkeypatch.setattr(main, "check_dependencies", lambda: None)
    monkeypatch.setattr(main, "check_ffmpeg", lambda: True)

    original_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "PyQt6.QtWidgets":
            return fake_widgets
        if name == "PyQt6.QtGui":
            return fake_gui
        if name == "PyQt6.QtCore":
            return fake_core
        if name == "gui.main_window":
            return SimpleNamespace(MainWindow=FakeWindow)
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", fake_import)
    monkeypatch.setattr(main.os.path, "exists", lambda p: False)
    monkeypatch.setattr(main.sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code)))

    with pytest.raises(SystemExit) as exc:
        main.main()

    assert exc.value.code == 0
    assert FakeWindow.shown is True
