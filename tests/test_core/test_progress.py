import pytest

from core.progress import DownloadQueue, DownloadStatus, ProgressHook, ProgressInfo


@pytest.mark.unit
def test_progress_info_formatters_handle_none_and_values():
    info = ProgressInfo(
        status=DownloadStatus.DOWNLOADING,
        downloaded_bytes=1024,
        total_bytes=2048,
        speed=4096,
        eta=65,
        percent=50.0,
        filename="file.mp4",
        elapsed=1.0,
    )

    assert info.speed_str == "4.0 KB/s"
    assert info.eta_str == "01:05"
    assert info.size_str == "1.0 KB / 2.0 KB"


@pytest.mark.unit
def test_progress_info_format_speed_ranges():
    assert ProgressInfo._format_speed(500) == "500 B/s"
    assert ProgressInfo._format_speed(1500).endswith("KB/s")
    assert ProgressInfo._format_speed(2 * 1024 * 1024).endswith("MB/s")


@pytest.mark.unit
def test_progress_hook_downloading_emits_callback(monkeypatch):
    emitted = []
    hook = ProgressHook(callback=emitted.append)

    monkeypatch.setattr("core.progress.time.time", lambda: 1000.0)

    hook(
        {
            "status": "downloading",
            "filename": "video.mp4",
            "downloaded_bytes": 50,
            "total_bytes": 100,
            "speed": 10,
            "eta": 5,
        }
    )

    assert len(emitted) == 1
    assert emitted[0].percent == 50.0
    assert emitted[0].filename == "video.mp4"


@pytest.mark.unit
def test_progress_hook_uses_percent_str_when_total_missing(monkeypatch):
    emitted = []
    hook = ProgressHook(callback=emitted.append)

    monkeypatch.setattr("core.progress.time.time", lambda: 1000.0)

    hook(
        {
            "status": "downloading",
            "downloaded_bytes": 10,
            "_percent_str": "42.5%",
        }
    )

    assert emitted[0].percent == 42.5


@pytest.mark.unit
def test_progress_hook_finished_and_error_states(monkeypatch):
    emitted = []
    hook = ProgressHook(callback=emitted.append)

    monkeypatch.setattr("core.progress.time.time", lambda: 1000.0)
    hook({"status": "downloading", "downloaded_bytes": 1, "total_bytes": 10})
    hook({"status": "finished", "filename": "done.mp4", "total_bytes": 10})
    hook({"status": "error"})

    assert emitted[-2].status == DownloadStatus.FINISHED
    assert emitted[-1].status == DownloadStatus.ERROR


@pytest.mark.unit
def test_progress_hook_rate_limit(monkeypatch):
    emitted = []
    hook = ProgressHook(callback=emitted.append)

    times = iter([1000.0, 1000.05, 1000.2])
    monkeypatch.setattr("core.progress.time.time", lambda: next(times))

    hook({"status": "downloading", "downloaded_bytes": 1, "total_bytes": 10})
    hook({"status": "downloading", "downloaded_bytes": 2, "total_bytes": 10})
    hook({"status": "downloading", "downloaded_bytes": 3, "total_bytes": 10})

    assert len(emitted) == 2


@pytest.mark.unit
def test_download_queue_lifecycle():
    queue = DownloadQueue()

    queue.add("https://youtu.be/a")
    queue.add("https://youtu.be/b")

    assert queue.total_items == 2
    assert queue.progress_text == "0/2"

    first = queue.get_next()
    assert first["url"] == "https://youtu.be/a"
    queue.mark_current_complete()

    second = queue.get_next()
    assert second["url"] == "https://youtu.be/b"
    queue.mark_current_error()

    assert queue.get_overall_progress() == 50.0
    assert queue.has_pending is False


@pytest.mark.unit
def test_download_queue_clear_resets_state():
    queue = DownloadQueue()
    queue.add("https://youtu.be/a")
    queue.clear()

    assert queue.is_empty is True
    assert queue.current_index == 0
    assert queue.total_items == 0
