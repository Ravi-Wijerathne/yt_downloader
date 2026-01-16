"""
Progress Hook Module
Handles download progress tracking and reporting
"""

from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import time


class DownloadStatus(Enum):
    """Download status states"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    FINISHED = "finished"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class ProgressInfo:
    """Progress information data class"""
    status: DownloadStatus
    downloaded_bytes: int
    total_bytes: Optional[int]
    speed: Optional[float]  # bytes per second
    eta: Optional[int]  # seconds
    percent: float
    filename: str
    elapsed: float
    
    @property
    def speed_str(self) -> str:
        """Get formatted speed string"""
        if self.speed is None:
            return "-- KB/s"
        return self._format_speed(self.speed)
    
    @property
    def eta_str(self) -> str:
        """Get formatted ETA string"""
        if self.eta is None:
            return "--:--"
        return self._format_time(self.eta)
    
    @property
    def size_str(self) -> str:
        """Get formatted size string"""
        downloaded = self._format_size(self.downloaded_bytes)
        if self.total_bytes:
            total = self._format_size(self.total_bytes)
            return f"{downloaded} / {total}"
        return downloaded
    
    @staticmethod
    def _format_speed(speed: float) -> str:
        """Format speed in human-readable format"""
        if speed < 1024:
            return f"{speed:.0f} B/s"
        elif speed < 1024 * 1024:
            return f"{speed / 1024:.1f} KB/s"
        else:
            return f"{speed / (1024 * 1024):.2f} MB/s"
    
    @staticmethod
    def _format_time(seconds: int) -> str:
        """Format time in MM:SS or HH:MM:SS"""
        if seconds < 0:
            return "--:--"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size in human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


class ProgressHook:
    """
    Progress hook for yt-dlp that tracks download progress
    and emits updates to a callback function
    """
    
    def __init__(self, callback: Callable[[ProgressInfo], None] = None):
        """
        Initialize progress hook
        
        Args:
            callback: Function to call with progress updates
        """
        self.callback = callback
        self.start_time: Optional[float] = None
        self.current_file: str = ""
        self._last_update: float = 0
        self._update_interval: float = 0.1  # Update every 100ms max
        
    def __call__(self, data: Dict[str, Any]):
        """
        Called by yt-dlp with progress updates
        
        Args:
            data: Progress data dictionary from yt-dlp
        """
        status = data.get('status', '')
        
        if status == 'downloading':
            self._handle_downloading(data)
        elif status == 'finished':
            self._handle_finished(data)
        elif status == 'error':
            self._handle_error(data)
            
    def _handle_downloading(self, data: Dict[str, Any]):
        """Handle downloading status update"""
        current_time = time.time()
        
        # Rate limit updates
        if current_time - self._last_update < self._update_interval:
            return
        self._last_update = current_time
        
        if self.start_time is None:
            self.start_time = current_time
            
        filename = data.get('filename', '')
        if filename:
            self.current_file = filename
            
        downloaded = data.get('downloaded_bytes', 0)
        total = data.get('total_bytes') or data.get('total_bytes_estimate')
        speed = data.get('speed')
        eta = data.get('eta')
        
        # Calculate percent
        if total and total > 0:
            percent = (downloaded / total) * 100
        else:
            # Try to get from yt-dlp's calculated percent
            percent_str = data.get('_percent_str', '0%')
            try:
                percent = float(percent_str.strip('%'))
            except:
                percent = 0.0
                
        elapsed = current_time - self.start_time
        
        progress = ProgressInfo(
            status=DownloadStatus.DOWNLOADING,
            downloaded_bytes=downloaded,
            total_bytes=total,
            speed=speed,
            eta=int(eta) if eta else None,
            percent=min(percent, 100.0),
            filename=self.current_file,
            elapsed=elapsed
        )
        
        if self.callback:
            self.callback(progress)
            
    def _handle_finished(self, data: Dict[str, Any]):
        """Handle finished status update"""
        filename = data.get('filename', self.current_file)
        total_bytes = data.get('total_bytes', 0)
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        progress = ProgressInfo(
            status=DownloadStatus.FINISHED,
            downloaded_bytes=total_bytes,
            total_bytes=total_bytes,
            speed=None,
            eta=0,
            percent=100.0,
            filename=filename,
            elapsed=elapsed
        )
        
        if self.callback:
            self.callback(progress)
            
        # Reset for next file
        self.start_time = None
        
    def _handle_error(self, data: Dict[str, Any]):
        """Handle error status"""
        progress = ProgressInfo(
            status=DownloadStatus.ERROR,
            downloaded_bytes=0,
            total_bytes=None,
            speed=None,
            eta=None,
            percent=0.0,
            filename=self.current_file,
            elapsed=0
        )
        
        if self.callback:
            self.callback(progress)
            
    def reset(self):
        """Reset the progress hook for a new download"""
        self.start_time = None
        self.current_file = ""
        self._last_update = 0


class DownloadQueue:
    """
    Manages a queue of downloads with progress tracking
    """
    
    def __init__(self):
        self.queue: list = []
        self.current_index: int = 0
        self.total_items: int = 0
        
    def add(self, url: str, options: Dict[str, Any] = None):
        """Add a URL to the download queue"""
        self.queue.append({
            'url': url,
            'options': options or {},
            'status': DownloadStatus.PENDING,
            'progress': 0.0
        })
        self.total_items = len(self.queue)
        
    def get_next(self) -> Optional[Dict[str, Any]]:
        """Get the next item in the queue"""
        if self.current_index < len(self.queue):
            item = self.queue[self.current_index]
            self.current_index += 1
            return item
        return None
    
    def mark_current_complete(self):
        """Mark current item as complete"""
        if self.current_index > 0:
            self.queue[self.current_index - 1]['status'] = DownloadStatus.FINISHED
            self.queue[self.current_index - 1]['progress'] = 100.0
            
    def mark_current_error(self):
        """Mark current item as error"""
        if self.current_index > 0:
            self.queue[self.current_index - 1]['status'] = DownloadStatus.ERROR
            
    def clear(self):
        """Clear the queue"""
        self.queue = []
        self.current_index = 0
        self.total_items = 0
        
    def get_overall_progress(self) -> float:
        """Get overall queue progress percentage"""
        if self.total_items == 0:
            return 0.0
        completed = sum(1 for item in self.queue if item['status'] == DownloadStatus.FINISHED)
        return (completed / self.total_items) * 100
    
    @property
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return len(self.queue) == 0
    
    @property
    def has_pending(self) -> bool:
        """Check if there are pending items"""
        return self.current_index < len(self.queue)
    
    @property
    def progress_text(self) -> str:
        """Get progress text like '2/5'"""
        return f"{self.current_index}/{self.total_items}"
