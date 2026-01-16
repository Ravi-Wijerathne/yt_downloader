"""
Format Handler Module
Manages video/audio formats, qualities, and conversions
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class QualityPreset(Enum):
    """Quality preset options"""
    BEST = "best"
    HIGH = "high"       # 1080p+
    MEDIUM = "medium"   # 720p
    LOW = "low"         # 480p
    LOWEST = "lowest"   # 360p


@dataclass
class FormatOption:
    """Represents a single format option"""
    format_id: str
    extension: str
    resolution: Optional[str]
    fps: Optional[int]
    filesize: Optional[int]
    vcodec: Optional[str]
    acodec: Optional[str]
    quality: str
    is_video: bool
    is_audio: bool
    description: str


class FormatHandler:
    """
    Handles format selection and quality management
    """
    
    # Video quality options (resolution in pixels)
    VIDEO_QUALITIES = [
        ('4320p', '8K Ultra HD', 4320),
        ('2160p', '4K Ultra HD', 2160),
        ('1440p', '2K QHD', 1440),
        ('1080p', 'Full HD', 1080),
        ('720p', 'HD', 720),
        ('480p', 'SD', 480),
        ('360p', 'Low', 360),
        ('240p', 'Very Low', 240),
        ('144p', 'Minimum', 144),
    ]
    
    # Video container formats
    VIDEO_FORMATS = ['mp4', 'mkv', 'webm', 'avi', 'mov']
    
    # Audio formats
    AUDIO_FORMATS = ['mp3', 'aac', 'm4a', 'wav', 'flac', 'opus']
    
    # Audio quality bitrates
    AUDIO_QUALITIES = [
        ('320', 'High (320 kbps)'),
        ('256', 'Medium-High (256 kbps)'),
        ('192', 'Medium (192 kbps)'),
        ('128', 'Standard (128 kbps)'),
        ('96', 'Low (96 kbps)'),
    ]
    
    def __init__(self):
        self.available_formats: List[Dict[str, Any]] = []
        
    def parse_formats(self, formats: List[Dict[str, Any]]) -> List[FormatOption]:
        """
        Parse raw yt-dlp formats into FormatOption objects
        
        Args:
            formats: List of format dicts from yt-dlp
            
        Returns:
            List of FormatOption objects
        """
        self.available_formats = formats
        parsed = []
        
        for fmt in formats:
            format_id = fmt.get('format_id', '')
            ext = fmt.get('ext', '')
            height = fmt.get('height')
            width = fmt.get('width')
            fps = fmt.get('fps')
            filesize = fmt.get('filesize') or fmt.get('filesize_approx')
            vcodec = fmt.get('vcodec', 'none')
            acodec = fmt.get('acodec', 'none')
            
            # Determine if video or audio
            is_video = vcodec != 'none' and vcodec is not None
            is_audio = acodec != 'none' and acodec is not None
            
            # Build resolution string
            if height and width:
                resolution = f"{width}x{height}"
            elif height:
                resolution = f"{height}p"
            else:
                resolution = None
                
            # Build quality description
            quality = self._get_quality_label(height) if height else "Audio"
            
            # Build description
            description = self._build_format_description(fmt)
            
            parsed.append(FormatOption(
                format_id=format_id,
                extension=ext,
                resolution=resolution,
                fps=fps,
                filesize=filesize,
                vcodec=vcodec if is_video else None,
                acodec=acodec if is_audio else None,
                quality=quality,
                is_video=is_video,
                is_audio=is_audio,
                description=description
            ))
            
        return parsed
    
    def get_video_formats(self, formats: List[Dict[str, Any]]) -> List[FormatOption]:
        """Get only video formats"""
        parsed = self.parse_formats(formats)
        return [f for f in parsed if f.is_video]
    
    def get_audio_formats(self, formats: List[Dict[str, Any]]) -> List[FormatOption]:
        """Get only audio formats"""
        parsed = self.parse_formats(formats)
        return [f for f in parsed if f.is_audio and not f.is_video]
    
    def get_available_qualities(self, formats: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
        """
        Get list of available quality options based on formats
        
        Args:
            formats: List of format dicts from yt-dlp
            
        Returns:
            List of (quality_code, display_name) tuples
        """
        available_heights = set()
        
        for fmt in formats:
            height = fmt.get('height')
            if height:
                available_heights.add(height)
                
        qualities = [('best', 'Best Available')]
        
        for quality_code, display_name, height in self.VIDEO_QUALITIES:
            if height in available_heights or any(h >= height for h in available_heights):
                qualities.append((quality_code, f"{display_name} ({quality_code})"))
                
        return qualities
    
    def get_best_format_for_quality(
        self, 
        formats: List[Dict[str, Any]], 
        target_quality: str,
        prefer_format: str = 'mp4'
    ) -> Optional[str]:
        """
        Get the best format ID for a target quality
        
        Args:
            formats: List of format dicts
            target_quality: Quality string (e.g., "1080p")
            prefer_format: Preferred container format
            
        Returns:
            Format ID string or None
        """
        if target_quality == 'best':
            return None  # Let yt-dlp choose
            
        target_height = int(target_quality.replace('p', ''))
        
        # Find formats with matching or lower height
        candidates = []
        for fmt in formats:
            height = fmt.get('height')
            if height and height <= target_height:
                vcodec = fmt.get('vcodec', 'none')
                if vcodec != 'none':
                    candidates.append(fmt)
                    
        if not candidates:
            return None
            
        # Sort by height (descending), then prefer mp4
        candidates.sort(
            key=lambda x: (
                x.get('height', 0),
                1 if x.get('ext') == prefer_format else 0
            ),
            reverse=True
        )
        
        return candidates[0].get('format_id')
    
    def _get_quality_label(self, height: int) -> str:
        """Get quality label for a height value"""
        for quality_code, display_name, h in self.VIDEO_QUALITIES:
            if height >= h:
                return quality_code
        return 'Low'
    
    def _build_format_description(self, fmt: Dict[str, Any]) -> str:
        """Build a human-readable format description"""
        parts = []
        
        # Resolution
        height = fmt.get('height')
        if height:
            parts.append(f"{height}p")
            
        # FPS
        fps = fmt.get('fps')
        if fps and fps > 30:
            parts.append(f"{fps}fps")
            
        # Codec
        vcodec = fmt.get('vcodec', 'none')
        if vcodec != 'none':
            # Simplify codec name
            if 'avc' in vcodec.lower() or 'h264' in vcodec.lower():
                parts.append('H.264')
            elif 'hevc' in vcodec.lower() or 'h265' in vcodec.lower():
                parts.append('H.265')
            elif 'vp9' in vcodec.lower():
                parts.append('VP9')
            elif 'av1' in vcodec.lower() or 'av01' in vcodec.lower():
                parts.append('AV1')
                
        # Audio codec
        acodec = fmt.get('acodec', 'none')
        if acodec != 'none' and vcodec == 'none':
            abr = fmt.get('abr')
            if abr:
                parts.append(f"{int(abr)}kbps")
                
        # File size
        filesize = fmt.get('filesize') or fmt.get('filesize_approx')
        if filesize:
            parts.append(self.format_size(filesize))
            
        # Extension
        ext = fmt.get('ext', '')
        if ext:
            parts.append(f".{ext}")
            
        return ' | '.join(parts) if parts else 'Unknown'
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format file size in human-readable format"""
        if size_bytes is None:
            return "Unknown"
            
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    @staticmethod
    def get_output_formats(audio_only: bool = False) -> List[Tuple[str, str]]:
        """
        Get list of output format options
        
        Args:
            audio_only: If True, return only audio formats
            
        Returns:
            List of (format_code, display_name) tuples
        """
        if audio_only:
            return [
                ('mp3', 'MP3 Audio'),
                ('m4a', 'M4A Audio (AAC)'),
                ('aac', 'AAC Audio'),
                ('wav', 'WAV Audio (Lossless)'),
                ('flac', 'FLAC Audio (Lossless)'),
                ('opus', 'Opus Audio'),
            ]
        else:
            return [
                ('mp4', 'MP4 Video'),
                ('mkv', 'MKV Video'),
                ('webm', 'WebM Video'),
                ('avi', 'AVI Video'),
                ('mov', 'MOV Video'),
            ]
    
    @staticmethod
    def get_quality_options() -> List[Tuple[str, str]]:
        """Get all quality options for dropdown"""
        return [
            ('best', 'Best Available'),
            ('2160p', '4K Ultra HD (2160p)'),
            ('1440p', '2K QHD (1440p)'),
            ('1080p', 'Full HD (1080p)'),
            ('720p', 'HD (720p)'),
            ('480p', 'SD (480p)'),
            ('360p', 'Low (360p)'),
            ('240p', 'Very Low (240p)'),
            ('144p', 'Minimum (144p)'),
        ]
