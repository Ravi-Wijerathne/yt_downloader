import pytest

from core.downloader import DownloadError
from gui.main_window import DownloadWorker


class StubDownloader:
    def __init__(self, *_args, **_kwargs):
        self.cancelled = False
        self.should_fail = False

    def get_video_info(self, _url):
        if self.should_fail:
            raise DownloadError("failed")
        return type("Info", (), {"title": "Title"})()

    def download(self, **_kwargs):
        if self.should_fail:
            raise DownloadError("download failed")
        return True

    def cancel(self):
        self.cancelled = True


@pytest.mark.gui
def test_worker_setup_assigns_values():
    worker = DownloadWorker()

    worker.setup(
        url="https://youtube.com/watch?v=abc",
        output_path="C:/tmp",
        quality="720p",
        output_format="mp4",
        audio_only=True,
        operation="download",
    )

    assert worker.url.endswith("abc")
    assert worker.quality == "720p"
    assert worker.output_format == "mp4"
    assert worker.audio_only is True


@pytest.mark.gui
def test_worker_fetch_info_success(monkeypatch):
    logs = []
    fetched = []

    worker = DownloadWorker()
    worker.setup("https://youtube.com/watch?v=abc", "C:/tmp", operation="info")

    monkeypatch.setattr("gui.main_window.YouTubeDownloader", lambda **_kwargs: StubDownloader())

    worker.log_message.connect(logs.append)
    worker.info_fetched.connect(fetched.append)

    worker.run()

    assert fetched
    assert any("Found:" in msg for msg in logs)


@pytest.mark.gui
def test_worker_download_success_emits_complete(monkeypatch):
    completed = []

    worker = DownloadWorker()
    worker.setup("https://youtube.com/watch?v=abc", "C:/tmp", operation="download")

    monkeypatch.setattr("gui.main_window.YouTubeDownloader", lambda **_kwargs: StubDownloader())

    worker.download_complete.connect(lambda ok, msg: completed.append((ok, msg)))

    worker.run()

    assert completed
    assert completed[0][0] is True


@pytest.mark.gui
def test_worker_cancel_calls_downloader(monkeypatch):
    downloader = StubDownloader()

    worker = DownloadWorker()
    worker.downloader = downloader

    worker.cancel()

    assert downloader.cancelled is True
