class MockYtDlpError(Exception):
    pass


class MockYoutubeDL:
    """Reusable mock for yt-dlp context manager behavior in tests."""

    last_options = None
    should_raise = None
    info_response = None
    downloaded_urls = None

    def __init__(self, options):
        self.options = options
        MockYoutubeDL.last_options = options

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, _url, download=False):
        if MockYoutubeDL.should_raise:
            raise MockYoutubeDL.should_raise
        return MockYoutubeDL.info_response

    def download(self, urls):
        MockYoutubeDL.downloaded_urls = urls
        if MockYoutubeDL.should_raise:
            raise MockYoutubeDL.should_raise
