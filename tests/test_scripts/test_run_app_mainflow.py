from types import SimpleNamespace

import pytest

import scripts.run_app as run_app


@pytest.mark.unit
def test_get_installed_packages_returns_dict(monkeypatch):
    class Result:
        returncode = 0
        stdout = '[{"name": "yt-dlp", "version": "1.0"}]'

    monkeypatch.setattr(run_app.subprocess, "run", lambda *a, **k: Result())

    packages = run_app.get_installed_packages()

    assert packages["yt-dlp"] == "1.0"


@pytest.mark.unit
def test_check_package_installed_import_fails(monkeypatch):
    monkeypatch.setattr(run_app.importlib, "import_module", lambda *_: (_ for _ in ()).throw(ImportError("x")))

    ok, msg = run_app.check_package_installed("abc", "abc")

    assert ok is False
    assert msg == "not installed"


@pytest.mark.unit
def test_install_package_success(monkeypatch):
    class Result:
        returncode = 0
        stderr = ""

    monkeypatch.setattr(run_app.subprocess, "run", lambda *a, **k: Result())

    assert run_app.install_package("pytest") is True


@pytest.mark.unit
def test_install_requirements_success(monkeypatch):
    class Result:
        returncode = 0
        stderr = ""

    monkeypatch.setattr(run_app.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(run_app.subprocess, "run", lambda *a, **k: Result())

    assert run_app.install_requirements() is True


@pytest.mark.unit
def test_run_application_import_error(monkeypatch):
    monkeypatch.setattr(run_app.os, "chdir", lambda *_: None)
    monkeypatch.setattr(run_app.sys, "path", [])

    original_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "main":
            raise ImportError("boom")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    assert run_app.run_application() is False


@pytest.mark.unit
def test_main_success_path(monkeypatch):
    monkeypatch.setattr(run_app, "print_header", lambda: None)
    monkeypatch.setattr(run_app, "print_section", lambda _t: None)
    monkeypatch.setattr(run_app, "print_status", lambda *_a, **_k: None)
    monkeypatch.setattr(run_app, "check_python_version", lambda: True)
    monkeypatch.setattr(run_app, "check_project_structure", lambda: True)
    monkeypatch.setattr(run_app, "verify_dependencies", lambda: (True, []))
    monkeypatch.setattr(run_app, "check_ffmpeg", lambda: True)
    monkeypatch.setattr(run_app, "run_application", lambda: True)

    assert run_app.main() == 0


@pytest.mark.unit
def test_main_stops_when_user_declines_no_ffmpeg(monkeypatch):
    monkeypatch.setattr(run_app, "print_header", lambda: None)
    monkeypatch.setattr(run_app, "print_section", lambda _t: None)
    monkeypatch.setattr(run_app, "print_status", lambda *_a, **_k: None)
    monkeypatch.setattr(run_app, "check_python_version", lambda: True)
    monkeypatch.setattr(run_app, "check_project_structure", lambda: True)
    monkeypatch.setattr(run_app, "verify_dependencies", lambda: (True, []))
    monkeypatch.setattr(run_app, "check_ffmpeg", lambda: False)
    monkeypatch.setattr("builtins.input", lambda *_: "n")

    assert run_app.main() == 1


@pytest.mark.unit
def test_ensure_venv_and_relaunch_exits_with_child_code(monkeypatch):
    monkeypatch.setattr(run_app.sys, "version_info", SimpleNamespace(major=3, minor=11, micro=3))
    monkeypatch.setattr(run_app.os.path, "isfile", lambda _p: True)
    monkeypatch.setattr(run_app, "_get_venv_python", lambda: "C:/venv/python.exe")
    monkeypatch.setattr(run_app.subprocess, "run", lambda *_a, **_k: SimpleNamespace(returncode=7))
    monkeypatch.setattr(run_app.sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code)))

    with pytest.raises(SystemExit) as exc:
        run_app._ensure_venv_and_relaunch()

    assert exc.value.code == 7
