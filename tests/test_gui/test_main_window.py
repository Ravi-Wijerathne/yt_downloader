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

@pytest.mark.gui
def test_download_worker_get_ffmpeg_path(monkeypatch):
    from gui.main_window import DownloadWorker
    import sys
    worker = DownloadWorker()
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, '_MEIPASS', '/tmp/fake', raising=False)
    # Just check it returns None if not found
    assert worker._get_ffmpeg_path() is None

@pytest.mark.gui
def test_download_worker_fetch_info_error(qtbot, monkeypatch):
    from gui.main_window import DownloadWorker
    from core.downloader import DownloadError
    worker = DownloadWorker()
    worker.setup("http://url", "/tmp")
    worker.operation = "info"
    
    class FakeYt:
        def get_video_info(self, url):
            raise DownloadError("network error")
    
    worker.downloader = FakeYt()
    
    errors = []
    worker.error_occurred.connect(errors.append)
    worker._fetch_info()
    
    assert "network error" in errors[0]

@pytest.mark.gui
def test_download_worker_fetch_info_none(qtbot, monkeypatch):
    from gui.main_window import DownloadWorker
    worker = DownloadWorker()
    worker.setup("http://url", "/tmp")
    worker.operation = "info"
    
    class FakeYt:
        def get_video_info(self, url):
            return None
            
    worker.downloader = FakeYt()
    errors = []
    worker.error_occurred.connect(errors.append)
    worker._fetch_info()
    assert "Could not fetch video information" in errors[0]

@pytest.mark.gui
def test_download_worker_download_success(qtbot):
    from gui.main_window import DownloadWorker
    worker = DownloadWorker()
    worker.setup("http://url", "/tmp")
    worker.operation = "download"
    
    class FakeYt:
        is_cancelled = False
        def download(self, *a, **kw):
            return True
            
    worker.downloader = FakeYt()
    
    results = []
    worker.download_complete.connect(lambda s, m: results.append(s))
    worker._download()
    
    assert results == [True]

@pytest.mark.gui
def test_download_worker_download_error(qtbot):
    from gui.main_window import DownloadWorker
    from core.downloader import DownloadError
    worker = DownloadWorker()
    worker.setup("http://url", "/tmp")
    worker.operation = "download"
    
    class FakeYt:
        is_cancelled = False
        def download(self, *a, **kw):
            raise DownloadError("dl error")
            
    worker.downloader = FakeYt()
    
    results = []
    worker.download_complete.connect(lambda s, m: results.append(s))
    worker._download()
    
    assert results == [False]

@pytest.mark.gui
def test_browse_output(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr("gui.main_window.QFileDialog.getExistingDirectory", lambda *a, **kw: "/fake/dir")
    window._browse_output()
    assert window.output_input.text() == "/fake/dir"

@pytest.mark.gui
def test_browse_cookies_file(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr("gui.main_window.QFileDialog.getOpenFileName", lambda *a, **kw: ("/fake/cookies.txt", ""))
    window._browse_cookies_file()
    assert window.cookies_file_input.text() == "/fake/cookies.txt"

@pytest.mark.gui
def test_on_info_fetched(qtbot):
    from core.downloader import VideoInfo, VideoType
    window = MainWindow()
    qtbot.addWidget(window)
    
    info = VideoInfo(
        url="http://url",
        title="My Title",
        duration=60,
        thumbnail="",
        uploader="Uploader",
        video_type=VideoType.VIDEO,
        formats=[]
    )
    window._on_info_fetched(info)
    assert window.title_label.text() == "Title: My Title"
    assert window.download_btn.isEnabled() is True
    
@pytest.mark.gui
def test_cancel_download(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)
    
    class FakeWorker:
        def __init__(self):
            self.cancelled = False
        def cancel(self):
            self.cancelled = True
        def isRunning(self):
            return True
        def wait(self):
            return True
    
    worker = FakeWorker()
    window.download_worker = worker
    window._cancel_download()
    
    assert worker.cancelled is True
    assert window.status_bar.currentMessage() == "Cancelling..."

@pytest.mark.gui
def test_start_download_no_info(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)
    window.url_input.setText("http://url")
    window.current_video_info = None
    
    errors = []
    monkeypatch.setattr("gui.main_window.QMessageBox.warning", lambda *a: errors.append(a[2]))
    
    window._start_download()
    assert "Please analyze the URL first" in errors[0]

@pytest.mark.gui
def test_start_download_creates_worker(qtbot, monkeypatch):
    from core.downloader import VideoInfo, VideoType
    window = MainWindow()
    qtbot.addWidget(window)
    
    window.url_input.setText("http://url")
    window.output_input.setText("/tmp")
    window.current_video_info = VideoInfo("http://url", "Title", 1, "", "", VideoType.VIDEO, [])
    
    # We monkeypatch the worker's start to avoid real thread run
    started = []
    monkeypatch.setattr("gui.main_window.DownloadWorker.start", lambda self: started.append(True))
    
    window._start_download()
    
    assert started == [True]
    assert window.download_btn.isEnabled() is False
    assert window.cancel_btn.isEnabled() is True

@pytest.mark.gui
def test_download_queue_processing(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)
    window.url_input.setText("http://url")
    
    window._add_to_queue()
    assert window.queue_list.count() == 1
    
    # Mock download execution
    started = []
    monkeypatch.setattr(window, "_execute_download", lambda url, opts: started.append(url))
    
    window._download_queue()
    assert started == ["http://url"]
    
@pytest.mark.gui
def test_show_error_and_success(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)
    
    msgs = []
    monkeypatch.setattr("gui.main_window.QMessageBox.critical", lambda *a: msgs.append("error"))
    monkeypatch.setattr("gui.main_window.QMessageBox.information", lambda *a: msgs.append("success"))
    
    window._show_error("some error")
    window._show_success("some success")
    
    assert msgs == ["error", "success"]
