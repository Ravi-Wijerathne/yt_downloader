"""
YouTube Downloader Core Engine
Handles all yt-dlp operations for downloading videos and audio
"""

import os
import sys
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
    
    def __init__(self, output_path: str = None, ffmpeg_path: str = None):
        """
        Initialize the downloader
        
        Args:
            output_path: Directory to save downloaded files
            ffmpeg_path: Path to FFmpeg binary (optional)
        """
        self.output_path = output_path or os.path.join(os.path.expanduser("~"), "Downloads")
        self.ffmpeg_path = ffmpeg_path
        self.current_process: Optional[yt_dlp.YoutubeDL] = None
        self.is_cancelled = False
        
    def _get_ffmpeg_location(self) -> Optional[str]:
        """Get FFmpeg location, checking bundled version first"""
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
            return bundled_ffmpeg
            
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
        
        ffmpeg_location = self._get_ffmpeg_location()
        if ffmpeg_location:
            options['ffmpeg_location'] = ffmpeg_location
            
        if progress_hook:
            options['progress_hooks'] = [progress_hook]
            
        return options
    
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
            options['format'] = 'bestaudio/best'
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
            
            if 'private video' in error_msg:
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
            
    def _build_format_string(self, quality: str, output_format: str) -> str:
        """
        Build yt-dlp format string based on quality preference
        
        Args:
            quality: Quality string (144p, 240p, 360p, 480p, 720p, 1080p, 1440p, 2160p, best)
            output_format: Output format (mp4, mkv, webm)
            
        Returns:
            yt-dlp format string
        """
        quality_map = {
            '144p': '160',
            '240p': '133',
            '360p': '134',
            '480p': '135',
            '720p': '136',
            '1080p': '137',
            '1440p': '271',
            '2160p': '313',
            '4320p': '272',  # 8K
        }
        
        if quality == 'best':
            return f'bestvideo[ext={output_format}]+bestaudio/bestvideo+bestaudio/best'
        elif quality in quality_map:
            height = quality.replace('p', '')
            return f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
        else:
            return 'bestvideo+bestaudio/best'
    
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
            options['format'] = 'bestaudio/best'
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
