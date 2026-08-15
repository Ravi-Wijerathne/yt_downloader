import pytest
from PyQt6.QtCore import Qt

from gui.main_window import MainWindow


@pytest.mark.gui
def test_window_initial_state(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.download_btn.isEnabled() is False
    assert window.cancel_btn.isEnabled() is False
    assert window.output_input.text()


@pytest.mark.gui
def test_url_change_enables_analyze(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.url_input.setText("https://youtube.com/watch?v=abc")

    assert window.analyze_btn.isEnabled() is True


@pytest.mark.gui
def test_type_change_to_audio_disables_quality(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.audio_radio.setChecked(True)

    assert window.quality_combo.isEnabled() is False
    assert window.format_combo.count() > 0


@pytest.mark.gui
def test_cookies_file_toggle_controls_fields(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.cookies_file_checkbox.setChecked(True)
    assert window.cookies_file_input.isEnabled() is True
    assert window.cookies_file_btn.isEnabled() is True

    window.cookies_file_checkbox.setChecked(False)
    assert window.cookies_file_input.isEnabled() is False
    assert window.cookies_file_btn.isEnabled() is False


@pytest.mark.gui
def test_invalid_url_in_analyze_shows_error(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    errors = []
    monkeypatch.setattr(window, "_show_error", errors.append)

    window.url_input.setText("https://example.com")
    window._analyze_url()

    assert errors
    assert "Invalid Video URL" in errors[0]


@pytest.mark.gui
def test_start_download_requires_cookie_file_when_enabled(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    errors = []
    monkeypatch.setattr(window, "_show_error", errors.append)

    window.url_input.setText("https://youtube.com/watch?v=abc")
    window.current_video_info = object()
    window.cookies_file_checkbox.setChecked(True)
    window.cookies_file_input.setText("")

    window._start_download()

    assert errors
    assert "cookies.txt" in errors[0]


@pytest.mark.gui
def test_add_and_clear_queue(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    monkeypatch.setattr(window, "_show_error", lambda *_: None)

    window.url_input.setText("https://youtube.com/watch?v=abc")
    window._add_to_queue()

    assert window.queue_list.count() == 1
    assert window.download_queue_btn.isEnabled() is True

    window._clear_queue()

    assert window.queue_list.count() == 0
    assert window.download_queue_btn.isEnabled() is False


@pytest.mark.gui
def test_progress_update_updates_widgets(qtbot):
    from core.progress import DownloadStatus, ProgressInfo

    window = MainWindow()
    qtbot.addWidget(window)

    progress = ProgressInfo(
        status=DownloadStatus.DOWNLOADING,
        downloaded_bytes=1024,
        total_bytes=2048,
        speed=1024,
        eta=10,
        percent=50.0,
        filename="x.mp4",
        elapsed=1.0,
    )

    window._on_progress_update(progress)

    assert window.progress_bar.value() == 50
    assert "50.0%" in window.status_bar.currentMessage()


@pytest.mark.gui
def test_valid_url_patterns():
    assert MainWindow._is_valid_url("https://youtube.com/watch?v=abc")
    assert MainWindow._is_valid_url("https://youtu.be/abc")
    assert MainWindow._is_valid_url("https://youtube.com/shorts/abc")
    assert MainWindow._is_valid_url("https://facebook.com/watch?v=123")
    assert MainWindow._is_valid_url("https://fb.watch/123")
    assert not MainWindow._is_valid_url("https://example.com/video")
