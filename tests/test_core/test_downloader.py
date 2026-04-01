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
