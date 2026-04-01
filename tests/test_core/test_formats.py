import pytest

from core.formats import FormatHandler


@pytest.mark.unit
def test_parse_formats_returns_objects(sample_video_formats):
    handler = FormatHandler()

    parsed = handler.parse_formats(sample_video_formats)

    assert len(parsed) == 3
    assert parsed[0].format_id == "137"
    assert parsed[0].resolution == "1920x1080"
    assert parsed[0].is_video is True
    assert parsed[2].is_audio is True
    assert parsed[2].is_video is False


@pytest.mark.unit
def test_get_video_formats_filters_audio_only(sample_video_formats):
    handler = FormatHandler()

    video_formats = handler.get_video_formats(sample_video_formats)

    assert len(video_formats) == 2
    assert all(item.is_video for item in video_formats)


@pytest.mark.unit
def test_get_audio_formats_filters_video_streams(sample_video_formats):
    handler = FormatHandler()

    audio_formats = handler.get_audio_formats(sample_video_formats)

    assert len(audio_formats) == 1
    assert audio_formats[0].format_id == "251"


@pytest.mark.unit
def test_get_available_qualities_includes_best_and_available(sample_video_formats):
    handler = FormatHandler()

    qualities = handler.get_available_qualities(sample_video_formats)

    assert qualities[0] == ("best", "Best Available")
    codes = [q[0] for q in qualities]
    assert "1080p" in codes
    assert "720p" in codes


@pytest.mark.unit
def test_get_best_format_for_quality_prefers_target_and_ext(sample_video_formats):
    handler = FormatHandler()

    best_720 = handler.get_best_format_for_quality(sample_video_formats, "720p", "mp4")

    assert best_720 == "22"


@pytest.mark.unit
def test_get_best_format_for_quality_returns_none_for_best(sample_video_formats):
    handler = FormatHandler()

    result = handler.get_best_format_for_quality(sample_video_formats, "best", "mp4")

    assert result is None


@pytest.mark.unit
def test_format_size_boundaries():
    assert FormatHandler.format_size(500) == "500.0 B"
    assert FormatHandler.format_size(1024) == "1.0 KB"
    assert FormatHandler.format_size(1024 * 1024) == "1.0 MB"
    assert FormatHandler.format_size(1024 * 1024 * 1024) == "1.0 GB"


@pytest.mark.unit
def test_format_description_contains_codec_and_ext(sample_video_formats):
    handler = FormatHandler()

    description = handler._build_format_description(sample_video_formats[0])

    assert "1080p" in description
    assert "H.264" in description
    assert ".mp4" in description


@pytest.mark.unit
def test_output_formats_switch_for_audio_mode():
    video_formats = FormatHandler.get_output_formats(audio_only=False)
    audio_formats = FormatHandler.get_output_formats(audio_only=True)

    assert ("mp4", "MP4 Video") in video_formats
    assert ("mp3", "MP3 Audio") in audio_formats


@pytest.mark.unit
def test_quality_options_contains_expected_entries():
    qualities = FormatHandler.get_quality_options()

    assert qualities[0] == ("best", "Best Available")
    assert ("720p", "HD (720p)") in qualities
