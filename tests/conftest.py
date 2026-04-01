import os
import sys
from pathlib import Path

import pytest


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_video_formats():
    return [
        {
            "format_id": "137",
            "ext": "mp4",
            "height": 1080,
            "width": 1920,
            "fps": 30,
            "filesize": 50 * 1024 * 1024,
            "vcodec": "avc1.640028",
            "acodec": "none",
        },
        {
            "format_id": "22",
            "ext": "mp4",
            "height": 720,
            "width": 1280,
            "fps": 30,
            "filesize": 30 * 1024 * 1024,
            "vcodec": "avc1.4d401f",
            "acodec": "mp4a.40.2",
        },
        {
            "format_id": "251",
            "ext": "webm",
            "height": None,
            "width": None,
            "fps": None,
            "filesize": 5 * 1024 * 1024,
            "vcodec": "none",
            "acodec": "opus",
            "abr": 160,
        },
    ]


@pytest.fixture
def sample_video_info_dict(sample_video_formats):
    return {
        "title": "Sample Video",
        "duration": 120,
        "thumbnail": "https://example.com/thumb.jpg",
        "uploader": "Sample Uploader",
        "formats": sample_video_formats,
        "is_live": False,
        "age_limit": 0,
    }
