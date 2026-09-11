from types import SimpleNamespace

import pytest

from core.downloader import DownloadError, DownloadType, VideoType, YouTubeDownloader


class FakeYtDlpError(Exception):
    pass


class FakeYoutubeDL:
    should_raise = None
    info_response = None
    last_options = None
    downloaded_urls = None

    def __init__(self, options):
        self.options = options
        FakeYoutubeDL.last_options = options

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, url, download=False):
        if FakeYoutubeDL.should_raise:
            raise FakeYoutubeDL.should_raise
        return FakeYoutubeDL.info_response

    def download(self, urls):
        FakeYoutubeDL.downloaded_urls = urls
        if FakeYoutubeDL.should_raise:
            raise FakeYoutubeDL.should_raise


@pytest.fixture
def downloader(monkeypatch, tmp_path):
    import core.downloader as module

    FakeYoutubeDL.should_raise = None
    FakeYoutubeDL.info_response = None
    FakeYoutubeDL.last_options = None
    FakeYoutubeDL.downloaded_urls = None

    monkeypatch.setattr(module.yt_dlp, "YoutubeDL", FakeYoutubeDL)
    monkeypatch.setattr(module.yt_dlp, "utils", SimpleNamespace(DownloadError=FakeYtDlpError))
    monkeypatch.setattr(module, "shutil", SimpleNamespace(which=lambda _: None))

    return YouTubeDownloader(output_path=str(tmp_path))


@pytest.mark.unit
def test_detect_video_type_variants(downloader):
    assert downloader.detect_video_type("https://youtube.com/watch?v=abc") == VideoType.VIDEO
    assert downloader.detect_video_type("https://youtube.com/shorts/abc") == VideoType.SHORT
    assert downloader.detect_video_type("https://youtube.com/playlist?list=abc") == VideoType.PLAYLIST
    assert downloader.detect_video_type("https://facebook.com/watch?v=123") == VideoType.VIDEO
    assert downloader.detect_video_type("https://fb.watch/123") == VideoType.VIDEO
    assert downloader.detect_video_type("https://example.com") == VideoType.UNKNOWN


@pytest.mark.unit
def test_get_video_info_maps_fields(downloader, sample_video_info_dict):
    FakeYoutubeDL.info_response = sample_video_info_dict

    info = downloader.get_video_info("https://youtube.com/watch?v=abc")

    assert info.title == "Sample Video"
    assert info.duration == 120
    assert info.video_type == VideoType.VIDEO
    assert len(info.formats) == 3


@pytest.mark.unit
def test_get_video_info_raises_download_error_message(downloader):
    FakeYoutubeDL.should_raise = FakeYtDlpError("network failed")

    with pytest.raises(DownloadError, match="Failed to get video info"):
        downloader.get_video_info("https://youtube.com/watch?v=abc")


@pytest.mark.unit
def test_build_format_string_variants(downloader):
    best = downloader._build_format_string("best", "mp4")
    p720 = downloader._build_format_string("720p", "mp4")
    fallback = downloader._build_format_string("custom", "mp4")

    assert "bestvideo" in best
    assert "height<=720" in p720
    assert fallback == "bestvideo+bestaudio/best"


@pytest.mark.unit
def test_build_audio_format_string(downloader):
    fmt = downloader._build_audio_format_string()

    assert "bestaudio" in fmt
    assert "protocol=https" in fmt


@pytest.mark.unit
def test_download_video_sets_expected_options(downloader):
    success = downloader.download(
        url="https://youtube.com/watch?v=abc",
        download_type=DownloadType.VIDEO,
        quality="720p",
        output_format="mp4",
    )

    assert success is True
    assert FakeYoutubeDL.downloaded_urls == ["https://youtube.com/watch?v=abc"]
    assert FakeYoutubeDL.last_options["merge_output_format"] == "mp4"
    assert "postprocessors" in FakeYoutubeDL.last_options


@pytest.mark.unit
def test_download_audio_sets_postprocessor(downloader):
    success = downloader.download(
        url="https://youtube.com/watch?v=abc",
        download_type=DownloadType.AUDIO,
        output_format="mp3",
        audio_only=True,
    )

    assert success is True
    processors = FakeYoutubeDL.last_options["postprocessors"]
    assert processors[0]["key"] == "FFmpegExtractAudio"
    assert processors[0]["preferredcodec"] == "mp3"


@pytest.mark.unit
def test_download_retry_on_403_forbidden(downloader):
    class RaiseThenSucceed(FakeYoutubeDL):
        calls = 0

        def download(self, urls):
            RaiseThenSucceed.calls += 1
            if RaiseThenSucceed.calls == 1:
                raise FakeYtDlpError("HTTP Error 403: Forbidden")
            return None

    import core.downloader as module

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(module.yt_dlp, "YoutubeDL", RaiseThenSucceed)
    monkeypatch.setattr(module.yt_dlp, "utils", SimpleNamespace(DownloadError=FakeYtDlpError))

    try:
        ok = downloader.download("https://youtube.com/watch?v=abc")
        assert ok is True
        assert RaiseThenSucceed.calls == 2
    finally:
        monkeypatch.undo()


@pytest.mark.unit
def test_download_maps_known_error_messages(downloader):
    FakeYoutubeDL.should_raise = FakeYtDlpError("private video")
    with pytest.raises(DownloadError, match="private"):
        downloader.download("https://youtube.com/watch?v=abc")

    FakeYoutubeDL.should_raise = FakeYtDlpError("age restricted")
    with pytest.raises(DownloadError, match="age-restricted"):
        downloader.download("https://youtube.com/watch?v=abc")

    FakeYoutubeDL.should_raise = FakeYtDlpError("not available in your geo")
    with pytest.raises(DownloadError, match="region"):
        downloader.download("https://youtube.com/watch?v=abc")

    FakeYoutubeDL.should_raise = FakeYtDlpError("removed")
    with pytest.raises(DownloadError, match="removed"):
        downloader.download("https://youtube.com/watch?v=abc")


@pytest.mark.unit
def test_cancel_sets_internal_flag(downloader):
    assert downloader.is_cancelled is False

    downloader.cancel()

    assert downloader.is_cancelled is True


@pytest.mark.unit
def test_download_playlist_sets_playlist_template(downloader):
    success = downloader.download_playlist(
        url="https://youtube.com/playlist?list=abc",
        download_type=DownloadType.VIDEO,
        quality="1080p",
        output_format="mp4",
        playlist_items="1-3",
    )

    assert success is True
    assert FakeYoutubeDL.last_options["noplaylist"] is False
    assert FakeYoutubeDL.last_options["playlist_items"] == "1-3"
    assert "%(playlist_title)s" in FakeYoutubeDL.last_options["outtmpl"]


@pytest.mark.unit
def test_get_base_options_sets_cookiefile_when_file_exists(monkeypatch, tmp_path):
    import core.downloader as module

    cookie = tmp_path / "cookies.txt"
    cookie.write_text("dummy", encoding="utf-8")

    monkeypatch.setattr(module, "shutil", SimpleNamespace(which=lambda _: None))

    yt = YouTubeDownloader(output_path=str(tmp_path), cookies_file=str(cookie))
    opts = yt._get_base_options()

    assert opts["cookiefile"] == str(cookie)


@pytest.mark.unit
def test_get_js_runtimes_detects_node_and_bun(monkeypatch, tmp_path):
    import core.downloader as module

    def fake_which(name):
        return {
            "deno": "C:/deno.exe",
            "node": "C:/node.exe",
            "bun": "C:/bun.exe",
        }.get(name)

    monkeypatch.setattr(module, "shutil", SimpleNamespace(which=fake_which))

    yt = YouTubeDownloader(output_path=str(tmp_path))
    runtimes = yt._get_js_runtimes()

    assert runtimes["deno"]["path"] == "C:/deno.exe"
    assert runtimes["node"]["path"] == "C:/node.exe"
    assert runtimes["bun"]["path"] == "C:/bun.exe"


@pytest.mark.unit
def test_get_ffmpeg_location_explicit_path(monkeypatch, tmp_path):
    import core.downloader as module
    yt = YouTubeDownloader(output_path=str(tmp_path), ffmpeg_path="C:/custom/ffmpeg.exe")
    monkeypatch.setattr(module.os.path, "exists", lambda p: True if p == "C:/custom/ffmpeg.exe" else False)
    assert yt._get_ffmpeg_location() == "C:/custom/ffmpeg.exe"

@pytest.mark.unit
def test_get_ffmpeg_location_system_path(monkeypatch, tmp_path):
    import core.downloader as module
    yt = YouTubeDownloader(output_path=str(tmp_path))
    monkeypatch.setattr(module.os.path, "exists", lambda _: False)
    monkeypatch.setattr(module.shutil, "which", lambda cmd: "C:/system/ffmpeg.exe" if cmd == "ffmpeg" else None)
    assert yt._get_ffmpeg_location() is None

@pytest.mark.unit
def test_detect_browser_for_cookies_chrome_paths(monkeypatch, tmp_path):
    import core.downloader as module
    yt = YouTubeDownloader(output_path=str(tmp_path), use_cookies_from_browser=True)
    monkeypatch.setattr(module.os.path, "exists", lambda p: True if "chrome.exe" in p else False)
    assert yt._detect_browser_for_cookies() == "chrome"

@pytest.mark.unit
def test_detect_browser_for_cookies_edge_paths(monkeypatch, tmp_path):
    import core.downloader as module
    yt = YouTubeDownloader(output_path=str(tmp_path), use_cookies_from_browser=True)
    monkeypatch.setattr(module.os.path, "exists", lambda p: True if "msedge.exe" in p else False)
    assert yt._detect_browser_for_cookies() == "edge"

@pytest.mark.unit
def test_detect_browser_for_cookies_shutil_fallback(monkeypatch, tmp_path):
    import core.downloader as module
    yt = YouTubeDownloader(output_path=str(tmp_path), use_cookies_from_browser=True)
    monkeypatch.setattr(module.os.path, "exists", lambda p: False)
    monkeypatch.setattr(module.shutil, "which", lambda cmd: "path" if cmd == "msedge" else None)
    assert yt._detect_browser_for_cookies() == "edge"

@pytest.mark.unit
def test_get_base_options_with_browser_cookies(monkeypatch, tmp_path):
    yt = YouTubeDownloader(output_path=str(tmp_path), use_cookies_from_browser=True)
    monkeypatch.setattr(yt, "_detect_browser_for_cookies", lambda: "chrome")
    opts = yt._get_base_options()
    assert opts["cookiesfrombrowser"] == ("chrome",)

@pytest.mark.unit
def test_get_base_options_with_ffmpeg_and_progress(monkeypatch, tmp_path):
    yt = YouTubeDownloader(output_path=str(tmp_path))
    monkeypatch.setattr(yt, "_get_ffmpeg_location", lambda: "C:/ffmpeg.exe")
    def my_hook(d): pass
    opts = yt._get_base_options(progress_hook=my_hook)
    assert opts["ffmpeg_location"] == "C:/ffmpeg.exe"
    assert opts["progress_hooks"] == [my_hook]

@pytest.mark.unit
def test_get_video_info_browser_cookies(monkeypatch, downloader):
    downloader.use_cookies_from_browser = True
    monkeypatch.setattr(downloader, "_detect_browser_for_cookies", lambda: "chrome")
    FakeYoutubeDL.info_response = None
    info = downloader.get_video_info("http://url")
    assert FakeYoutubeDL.last_options["cookiesfrombrowser"] == ("chrome",)
    assert info is None

@pytest.mark.unit
def test_get_video_info_unexpected_error(downloader):
    FakeYoutubeDL.should_raise = Exception("random failure")
    with pytest.raises(DownloadError, match="Unexpected error: random failure"):
        downloader.get_video_info("http://url")

@pytest.mark.unit
def test_get_available_formats(downloader, sample_video_info_dict):
    FakeYoutubeDL.info_response = sample_video_info_dict
    formats = downloader.get_available_formats("http://url")
    assert len(formats) == 3
    FakeYoutubeDL.info_response = None
    assert downloader.get_available_formats("http://url") == []

@pytest.mark.unit
def test_download_cancelled_early(downloader):
    class CancelYDL(FakeYoutubeDL):
        def __enter__(self):
            downloader.cancel()
            return super().__enter__()
    
    import core.downloader as module
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(module.yt_dlp, "YoutubeDL", CancelYDL)
    monkeypatch.setattr(module.yt_dlp, "utils", SimpleNamespace(DownloadError=FakeYtDlpError))
    
    try:
        ok = downloader.download("http://url")
        assert ok is False
    finally:
        monkeypatch.undo()

@pytest.mark.unit
def test_download_unexpected_error(downloader):
    FakeYoutubeDL.should_raise = Exception("unexpected")
    with pytest.raises(DownloadError, match="Unexpected error: unexpected"):
        downloader.download("http://url")

@pytest.mark.unit
def test_download_unexpected_error_cancelled(downloader):
    class CancelThenRaiseYDL(FakeYoutubeDL):
        def download(self, urls):
            downloader.cancel()
            raise Exception("unexpected")
    
    import core.downloader as module
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(module.yt_dlp, "YoutubeDL", CancelThenRaiseYDL)
    monkeypatch.setattr(module.yt_dlp, "utils", SimpleNamespace(DownloadError=FakeYtDlpError))
    
    try:
        ok = downloader.download("http://url")
        assert ok is False
    finally:
        monkeypatch.undo()

@pytest.mark.unit
def test_retry_fallback_cancelled_early(downloader):
    downloader.is_cancelled = True
    assert downloader._retry_with_fallback_format("http://url", {}, True, "mp3") is False

@pytest.mark.unit
def test_retry_fallback_unexpected_error(downloader):
    FakeYoutubeDL.should_raise = Exception("unexpected fallback")
    with pytest.raises(DownloadError, match="Unexpected error: unexpected fallback"):
        downloader._retry_with_fallback_format("http://url", {}, False, "mp4")

@pytest.mark.unit
def test_retry_fallback_unexpected_error_cancelled(downloader):
    class CancelThenRaiseYDL(FakeYoutubeDL):
        def download(self, urls):
            downloader.cancel()
            raise Exception("unexpected")
    
    import core.downloader as module
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(module.yt_dlp, "YoutubeDL", CancelThenRaiseYDL)
    monkeypatch.setattr(module.yt_dlp, "utils", SimpleNamespace(DownloadError=FakeYtDlpError))
    
    try:
        ok = downloader._retry_with_fallback_format("http://url", {}, True, "mp3")
        assert ok is False
    finally:
        monkeypatch.undo()

@pytest.mark.unit
def test_download_playlist_no_items_and_audio(downloader):
    success = downloader.download_playlist(
        url="https://youtube.com/playlist?list=abc",
        download_type=DownloadType.AUDIO,
        audio_only=True,
    )
    assert success is True
    assert "playlist_items" not in FakeYoutubeDL.last_options
    processors = FakeYoutubeDL.last_options["postprocessors"]
    assert processors[0]["key"] == "FFmpegExtractAudio"

@pytest.mark.unit
def test_download_playlist_unexpected_error(downloader):
    FakeYoutubeDL.should_raise = Exception("playlist err")
    with pytest.raises(DownloadError, match="Playlist download failed: playlist err"):
        downloader.download_playlist("http://url")

@pytest.mark.unit
def test_download_playlist_unexpected_error_cancelled(downloader):
    class CancelThenRaiseYDL(FakeYoutubeDL):
        def download(self, urls):
            downloader.cancel()
            raise Exception("unexpected")
    
    import core.downloader as module
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(module.yt_dlp, "YoutubeDL", CancelThenRaiseYDL)
    monkeypatch.setattr(module.yt_dlp, "utils", SimpleNamespace(DownloadError=FakeYtDlpError))
    
    try:
        ok = downloader.download_playlist("http://url")
        assert ok is False
    finally:
        monkeypatch.undo()

