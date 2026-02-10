"""
YouTube Downloader Core Engine
Handles all yt-dlp operations for downloading videos and audio
"""

import os
import sys
import shutil
import yt_dlp
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class DownloadType(Enum):
    """Enum for download types"""
    VIDEO = "video"
    AUDIO = "audio"


class VideoType(Enum):
    """Enum for detected video types"""
    VIDEO = "video"
    SHORT = "short"
    PLAYLIST = "playlist"
    UNKNOWN = "unknown"


@dataclass
class VideoInfo:
    """Data class for video information"""
    url: str
    title: str
    duration: int
    thumbnail: str
    uploader: str
    video_type: VideoType
    formats: List[Dict[str, Any]]
    is_live: bool = False
    age_limit: int = 0
    

class YouTubeDownloader:
    """
    Main downloader class that wraps yt-dlp functionality
    """
    
    def __init__(
        self,
        output_path: str = None,
        ffmpeg_path: str = None,
        use_cookies_from_browser: bool = False,
        cookies_file: Optional[str] = None
    ):
        """
        Initialize the downloader
        
        Args:
            output_path: Directory to save downloaded files
            ffmpeg_path: Path to FFmpeg binary (optional)
            use_cookies_from_browser: Use browser cookies for restricted content
            cookies_file: Path to cookies.txt file
        """
        self.output_path = output_path or os.path.join(os.path.expanduser("~"), "Downloads")
        self.ffmpeg_path = ffmpeg_path
        self.use_cookies_from_browser = use_cookies_from_browser
        self.cookies_file = cookies_file
        self.current_process: Optional[yt_dlp.YoutubeDL] = None
        self.is_cancelled = False
        
    def _get_ffmpeg_location(self) -> Optional[str]:
        """Get FFmpeg location, checking bundled version first, then common paths"""
        if self.ffmpeg_path and os.path.exists(self.ffmpeg_path):
            return self.ffmpeg_path
            
        # Check bundled ffmpeg folder
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_path = sys._MEIPASS
        else:
            # Running as script
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        bundled_ffmpeg = os.path.join(base_path, 'ffmpeg')
        if os.path.exists(bundled_ffmpeg):
            # Check if ffmpeg executable exists in the folder
            ffmpeg_exe = os.path.join(bundled_ffmpeg, 'ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg')
            if os.path.exists(ffmpeg_exe):
                return bundled_ffmpeg
        
        # Check common installation paths on Windows
        if sys.platform == 'win32':
            common_paths = [
                r'C:\ProgramData\chocolatey\bin',
                r'C:\ffmpeg\bin',
                os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Links'),
                os.path.expandvars(r'%USERPROFILE%\scoop\shims'),
                r'C:\Program Files\ffmpeg\bin',
                r'C:\Program Files (x86)\ffmpeg\bin',
            ]
            for path in common_paths:
                ffmpeg_exe = os.path.join(path, 'ffmpeg.exe')
                if os.path.exists(ffmpeg_exe):
                    return path
            
        return None  # Use system FFmpeg
        
    def _get_base_options(self, progress_hook: Callable = None) -> Dict[str, Any]:
        """Get base yt-dlp options"""
        options = {
            'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
            'noplaylist': False,
            'ignoreerrors': False,
            'no_warnings': False,
            'quiet': False,
            'no_color': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
        }

        # Enable JS runtimes for YouTube EJS challenge solving
        options['js_runtimes'] = self._get_js_runtimes()

        # Allow yt-dlp to download EJS scripts from GitHub as fallback
        options['remote_components'] = {'ejs:github'}

        if self.cookies_file and os.path.exists(self.cookies_file):
            options['cookiefile'] = self.cookies_file
        elif self.use_cookies_from_browser:
            browser = self._detect_browser_for_cookies()
            if browser:
                options['cookiesfrombrowser'] = (browser,)
        
        ffmpeg_location = self._get_ffmpeg_location()
        if ffmpeg_location:
            options['ffmpeg_location'] = ffmpeg_location
            
        if progress_hook:
            options['progress_hooks'] = [progress_hook]
            
        return options

    def _get_js_runtimes(self) -> Dict[str, Dict[str, str]]:
        """
        Detect available JavaScript runtimes for yt-dlp EJS challenge solving.
        Always includes deno (yt-dlp default). Adds node/bun if found on PATH.

        Returns:
            Dict of js runtime configs keyed by runtime name.
        """
        runtimes: Dict[str, Dict[str, str]] = {}

        # Always enable deno (yt-dlp default)
        deno_path = shutil.which('deno')
        runtimes['deno'] = {'path': deno_path} if deno_path else {}

        # Enable node if available (must be explicitly enabled)
        node_path = shutil.which('node')
        if node_path:
            runtimes['node'] = {'path': node_path}

        # Enable bun if available
        bun_path = shutil.which('bun')
        if bun_path:
            runtimes['bun'] = {'path': bun_path}

        return runtimes

    def _detect_browser_for_cookies(self) -> Optional[str]:
        """
        Detect a supported browser for cookies (Chrome/Edge).

        Returns:
            Browser name for yt-dlp cookiesfrombrowser or None.
        """
        browsers = [
            ('chrome', [
                os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe'),
                os.path.expandvars(r'%PROGRAMFILES%\Google\Chrome\Application\chrome.exe'),
                os.path.expandvars(r'%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe'),
            ]),
            ('edge', [
                os.path.expandvars(r'%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe'),
                os.path.expandvars(r'%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe'),
            ]),
        ]

        for browser, paths in browsers:
            for path in paths:
                if path and os.path.exists(path):
                    return browser

        if shutil.which('chrome'):
            return 'chrome'
        if shutil.which('msedge'):
            return 'edge'

        return None
    
    def detect_video_type(self, url: str) -> VideoType:
        """
        Detect if URL is a video, short, or playlist
        
        Args:
            url: YouTube URL
            
        Returns:
            VideoType enum value
        """
        url_lower = url.lower()
        
        if '/shorts/' in url_lower:
            return VideoType.SHORT
        elif 'list=' in url_lower:
            return VideoType.PLAYLIST
        elif 'youtube.com/watch' in url_lower or 'youtu.be/' in url_lower:
            return VideoType.VIDEO
        else:
            return VideoType.UNKNOWN
    
    def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """
        Extract video information without downloading
        
        Args:
            url: YouTube URL
            
        Returns:
            VideoInfo object or None if extraction fails
        """
        options = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
        }

        # Enable JS runtimes for YouTube EJS challenge solving
        options['js_runtimes'] = self._get_js_runtimes()
        options['remote_components'] = {'ejs:github'}

        if self.cookies_file and os.path.exists(self.cookies_file):
            options['cookiefile'] = self.cookies_file
        elif self.use_cookies_from_browser:
            browser = self._detect_browser_for_cookies()
            if browser:
                options['cookiesfrombrowser'] = (browser,)
        
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info is None:
                    return None
                    
                video_type = self.detect_video_type(url)
                
                return VideoInfo(
                    url=url,
                    title=info.get('title', 'Unknown'),
                    duration=info.get('duration', 0) or 0,
                    thumbnail=info.get('thumbnail', ''),
                    uploader=info.get('uploader', 'Unknown'),
                    video_type=video_type,
                    formats=info.get('formats', []),
                    is_live=info.get('is_live', False),
                    age_limit=info.get('age_limit', 0)
                )
                
        except yt_dlp.utils.DownloadError as e:
            raise DownloadError(f"Failed to get video info: {str(e)}")
        except Exception as e:
            raise DownloadError(f"Unexpected error: {str(e)}")
    
    def get_available_formats(self, url: str) -> List[Dict[str, Any]]:
        """
        Get all available formats for a video
        
        Args:
            url: YouTube URL
            
        Returns:
            List of format dictionaries
        """
        info = self.get_video_info(url)
        if info:
            return info.formats
        return []
    
    def download(
        self,
        url: str,
        download_type: DownloadType = DownloadType.VIDEO,
        quality: str = "best",
        output_format: str = "mp4",
        progress_hook: Callable = None,
        audio_only: bool = False
    ) -> bool:
        """
        Download a video or audio from YouTube
        
        Args:
            url: YouTube URL
            download_type: VIDEO or AUDIO
            quality: Quality string (e.g., "1080p", "720p", "best")
            output_format: Output format (mp4, mkv, mp3, etc.)
            progress_hook: Callback function for progress updates
            audio_only: If True, download audio only
            
        Returns:
            True if download successful, False otherwise
        """
        self.is_cancelled = False
        options = self._get_base_options(progress_hook)
        
        if audio_only or download_type == DownloadType.AUDIO:
            # Audio only download
            options['format'] = self._build_audio_format_string()
            options['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': output_format if output_format in ['mp3', 'aac', 'wav', 'flac', 'm4a'] else 'mp3',
                'preferredquality': '320',
            }]
            options['outtmpl'] = os.path.join(self.output_path, '%(title)s.%(ext)s')
        else:
            # Video download
            format_string = self._build_format_string(quality, output_format)
            options['format'] = format_string
            options['merge_output_format'] = output_format
            
            # Add metadata and embed thumbnail
            options['postprocessors'] = [
                {'key': 'FFmpegMetadata'},
            ]
            
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                self.current_process = ydl
                
                if self.is_cancelled:
                    return False
                    
                ydl.download([url])
                return True
                
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            
            # On 403 Forbidden, retry with a more permissive format string
            if '403' in error_msg and 'forbidden' in error_msg:
                return self._retry_with_fallback_format(
                    url, options, audio_only or download_type == DownloadType.AUDIO,
                    output_format
                )
            elif 'private video' in error_msg:
                raise DownloadError("This video is private and cannot be downloaded.")
            elif 'age' in error_msg and 'restricted' in error_msg:
                raise DownloadError("This video is age-restricted. Please try logging in.")
            elif 'not available' in error_msg or 'geo' in error_msg:
                raise DownloadError("This video is not available in your region.")
            elif 'removed' in error_msg or 'deleted' in error_msg:
                raise DownloadError("This video has been removed or deleted.")
            else:
                raise DownloadError(f"Download failed: {str(e)}")
                
        except Exception as e:
            if self.is_cancelled:
                return False
            raise DownloadError(f"Unexpected error: {str(e)}")
        finally:
            self.current_process = None

    def _retry_with_fallback_format(
        self,
        url: str,
        options: Dict[str, Any],
        is_audio: bool,
        output_format: str
    ) -> bool:
        """
        Retry download with a more permissive format on 403 errors.
        YouTube's SABR streaming can restrict certain format combinations.
        """
        if self.is_cancelled:
            return False

        if is_audio:
            fallback_format = 'bestaudio/best'
        else:
            fallback_format = 'best'

        options['format'] = fallback_format

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                self.current_process = ydl
                ydl.download([url])
                return True
        except yt_dlp.utils.DownloadError as e:
            raise DownloadError(f"Download failed: {str(e)}")
        except Exception as e:
            if self.is_cancelled:
                return False
            raise DownloadError(f"Unexpected error: {str(e)}")
        finally:
            self.current_process = None
            
    def _build_format_string(self, quality: str, output_format: str) -> str:
        """
        Build yt-dlp format string based on quality preference.
        Uses height-based selection instead of hardcoded format IDs to avoid
        403 errors from SABR-restricted streams.
        
        Args:
            quality: Quality string (144p, 240p, 360p, 480p, 720p, 1080p, 1440p, 2160p, best)
            output_format: Output format (mp4, mkv, webm)
            
        Returns:
            yt-dlp format string
        """
        if quality == 'best':
            # Prefer protocol=https to avoid SABR-restricted formats
            return (
                f'bestvideo[protocol=https]+bestaudio[protocol=https]'
                f'/bestvideo+bestaudio/best'
            )
        elif quality.endswith('p'):
            height = quality.replace('p', '')
            return (
                f'bestvideo[height<={height}][protocol=https]+bestaudio[protocol=https]'
                f'/bestvideo[height<={height}]+bestaudio'
                f'/best[height<={height}]'
            )
        else:
            return 'bestvideo+bestaudio/best'

    def _build_audio_format_string(self) -> str:
        """
        Build audio format string, preferring protocols and codecs that
        are less likely to be SABR-restricted (403 errors).

        Returns:
            yt-dlp format string
        """
        return (
            'bestaudio[ext=m4a][protocol=https]'
            '/bestaudio[acodec^=mp4a][protocol=https]'
            '/bestaudio[protocol=https]'
            '/bestaudio/best'
        )
    
    def cancel(self):
        """Cancel the current download"""
        self.is_cancelled = True
        if self.current_process:
            # yt-dlp doesn't have a direct cancel method
            # Setting the flag will prevent further downloads
            pass
            
    def download_playlist(
        self,
        url: str,
        download_type: DownloadType = DownloadType.VIDEO,
        quality: str = "best",
        output_format: str = "mp4",
        progress_hook: Callable = None,
        audio_only: bool = False,
        playlist_items: str = None
    ) -> bool:
        """
        Download a playlist from YouTube
        
        Args:
            url: YouTube playlist URL
            download_type: VIDEO or AUDIO
            quality: Quality string
            output_format: Output format
            progress_hook: Progress callback
            audio_only: Audio only flag
            playlist_items: Specific items to download (e.g., "1-5,7,9-10")
            
        Returns:
            True if successful
        """
        self.is_cancelled = False
        options = self._get_base_options(progress_hook)
        options['noplaylist'] = False
        
        if playlist_items:
            options['playlist_items'] = playlist_items
            
        # Create playlist subfolder
        options['outtmpl'] = os.path.join(
            self.output_path, 
            '%(playlist_title)s', 
            '%(playlist_index)s - %(title)s.%(ext)s'
        )
        
        if audio_only or download_type == DownloadType.AUDIO:
            options['format'] = self._build_audio_format_string()
            options['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': output_format if output_format in ['mp3', 'aac', 'wav', 'flac', 'm4a'] else 'mp3',
                'preferredquality': '320',
            }]
        else:
            format_string = self._build_format_string(quality, output_format)
            options['format'] = format_string
            options['merge_output_format'] = output_format
            
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                self.current_process = ydl
                ydl.download([url])
                return True
        except Exception as e:
            if self.is_cancelled:
                return False
            raise DownloadError(f"Playlist download failed: {str(e)}")
        finally:
            self.current_process = None


class DownloadError(Exception):
    """Custom exception for download errors"""
    pass
