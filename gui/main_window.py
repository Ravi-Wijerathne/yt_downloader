"""
Main Window GUI
PyQt6-based graphical user interface for YouTube Downloader
"""

import os
import sys
from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar,
    QTextEdit, QFileDialog, QGroupBox, QRadioButton, QButtonGroup,
    QMessageBox, QFrame, QSplitter, QStatusBar, QCheckBox,
    QListWidget, QListWidgetItem, QTabWidget, QSpacerItem, QSizePolicy,
    QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QClipboard, QAction, QPalette, QColor

from core.downloader import YouTubeDownloader, DownloadType, DownloadError, VideoInfo
from core.formats import FormatHandler
from core.progress import ProgressHook, ProgressInfo, DownloadStatus, DownloadQueue


class DownloadWorker(QThread):
    """Worker thread for downloading videos"""
    
    progress_update = pyqtSignal(object)  # ProgressInfo
    download_complete = pyqtSignal(bool, str)  # success, message
    info_fetched = pyqtSignal(object)  # VideoInfo
    error_occurred = pyqtSignal(str)  # error message
    log_message = pyqtSignal(str)  # log message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.downloader: Optional[YouTubeDownloader] = None
        self.url: str = ""
        self.output_path: str = ""
        self.quality: str = "best"
        self.output_format: str = "mp4"
        self.audio_only: bool = False
        self.use_cookies_from_browser: bool = False
        self.cookies_file: Optional[str] = None
        self.operation: str = "download"  # "download" or "info"
        
    def setup(
        self,
        url: str,
        output_path: str,
        quality: str = "best",
        output_format: str = "mp4",
        audio_only: bool = False,
        use_cookies_from_browser: bool = False,
        cookies_file: Optional[str] = None,
        operation: str = "download"
    ):
        """Setup download parameters"""
        self.url = url
        self.output_path = output_path
        self.quality = quality
        self.output_format = output_format
        self.audio_only = audio_only
        self.use_cookies_from_browser = use_cookies_from_browser
        self.cookies_file = cookies_file
        self.operation = operation
        
    def run(self):
        """Execute the download operation"""
        self.downloader = YouTubeDownloader(
            output_path=self.output_path,
            use_cookies_from_browser=self.use_cookies_from_browser,
            cookies_file=self.cookies_file
        )
        
        if self.operation == "info":
            self._fetch_info()
        else:
            self._download()
            
    def _fetch_info(self):
        """Fetch video information"""
        try:
            self.log_message.emit(f"Fetching info for: {self.url}")
            info = self.downloader.get_video_info(self.url)
            if info:
                self.info_fetched.emit(info)
                self.log_message.emit(f"Found: {info.title}")
            else:
                self.error_occurred.emit("Could not fetch video information")
        except DownloadError as e:
            self.error_occurred.emit(str(e))
        except Exception as e:
            self.error_occurred.emit(f"Error: {str(e)}")
            
    def _download(self):
        """Execute download"""
        try:
            # Create progress hook
            progress_hook = ProgressHook(self._on_progress)
            
            self.log_message.emit(f"Starting download: {self.url}")
            self.log_message.emit(f"Quality: {self.quality}, Format: {self.output_format}")
            self.log_message.emit(f"Output: {self.output_path}")
            if self.cookies_file:
                self.log_message.emit("Using cookies file")
            elif self.use_cookies_from_browser:
                self.log_message.emit("Using browser cookies (Chrome/Edge)")
            
            download_type = DownloadType.AUDIO if self.audio_only else DownloadType.VIDEO
            
            success = self.downloader.download(
                url=self.url,
                download_type=download_type,
                quality=self.quality,
                output_format=self.output_format,
                progress_hook=progress_hook,
                audio_only=self.audio_only
            )
            
            if success:
                self.log_message.emit("Download completed successfully!")
                self.download_complete.emit(True, "Download completed successfully!")
            else:
                self.download_complete.emit(False, "Download was cancelled")
                
        except DownloadError as e:
            self.log_message.emit(f"Error: {str(e)}")
            self.error_occurred.emit(str(e))
            self.download_complete.emit(False, str(e))
        except Exception as e:
            self.log_message.emit(f"Unexpected error: {str(e)}")
            self.error_occurred.emit(f"Unexpected error: {str(e)}")
            self.download_complete.emit(False, str(e))
            
    def _on_progress(self, progress: ProgressInfo):
        """Handle progress updates"""
        self.progress_update.emit(progress)
        
    def cancel(self):
        """Cancel the current operation"""
        if self.downloader:
            self.downloader.cancel()


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.format_handler = FormatHandler()
        self.download_worker: Optional[DownloadWorker] = None
        self.current_video_info: Optional[VideoInfo] = None
        self.download_queue = DownloadQueue()
        
        # Default output path
        self.output_path = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # Setup UI
        self._setup_window()
        self._create_widgets()
        self._setup_layout()
        self._connect_signals()
        self._apply_styles()
        
    def _setup_window(self):
        """Configure main window properties"""
        self.setWindowTitle("YouTube Downloader")
        self.setMinimumSize(800, 700)
        self.resize(900, 750)
        
        # Center window
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def _create_widgets(self):
        """Create all UI widgets"""
        # URL Input Section
        self.url_label = QLabel("YouTube URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube video or playlist URL here...")
        
        self.paste_btn = QPushButton("📋 Paste")
        self.paste_btn.setFixedWidth(80)
        self.clear_btn = QPushButton("✖ Clear")
        self.clear_btn.setFixedWidth(80)
        self.analyze_btn = QPushButton("🔍 Analyze")
        self.analyze_btn.setFixedWidth(100)
        
        # Video Info Display
        self.info_label = QLabel("Video Information:")
        self.title_label = QLabel("Title: -")
        self.title_label.setWordWrap(True)
        self.duration_label = QLabel("Duration: -")
        self.uploader_label = QLabel("Uploader: -")
        self.type_label = QLabel("Type: -")
        
        # Download Type Selection
        self.video_radio = QRadioButton("📹 Video")
        self.video_radio.setChecked(True)
        self.audio_radio = QRadioButton("🎵 Audio Only")
        
        self.type_group = QButtonGroup()
        self.type_group.addButton(self.video_radio, 1)
        self.type_group.addButton(self.audio_radio, 2)
        
        # Quality Selection
        self.quality_label = QLabel("Quality:")
        self.quality_combo = QComboBox()
        self._populate_quality_combo()
        
        # Format Selection
        self.format_label = QLabel("Format:")
        self.format_combo = QComboBox()
        self._populate_format_combo()

        # Cookies
        self.cookies_checkbox = QCheckBox("Use browser cookies (Chrome/Edge)")
        self.cookies_file_checkbox = QCheckBox("Use cookies.txt file")
        self.cookies_file_input = QLineEdit()
        self.cookies_file_input.setReadOnly(True)
        self.cookies_file_input.setPlaceholderText("Select cookies.txt file...")
        self.cookies_file_btn = QPushButton("📄 Browse")
        self.cookies_file_btn.setFixedWidth(100)
        self.cookies_file_input.setEnabled(False)
        self.cookies_file_btn.setEnabled(False)
        
        # Output Location
        self.output_label = QLabel("Save to:")
        self.output_input = QLineEdit()
        self.output_input.setText(self.output_path)
        self.output_input.setReadOnly(True)
        self.browse_btn = QPushButton("📁 Browse")
        self.browse_btn.setFixedWidth(100)
        
        # Download Queue
        self.queue_list = QListWidget()
        self.queue_list.setMaximumHeight(100)
        self.add_queue_btn = QPushButton("➕ Add to Queue")
        self.clear_queue_btn = QPushButton("🗑️ Clear Queue")
        
        # Action Buttons
        self.download_btn = QPushButton("⬇️ Download")
        self.download_btn.setFixedHeight(45)
        self.download_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.setFixedHeight(45)
        self.cancel_btn.setEnabled(False)
        
        self.download_queue_btn = QPushButton("⬇️ Download Queue")
        self.download_queue_btn.setFixedHeight(40)
        self.download_queue_btn.setEnabled(False)
        
        # Progress Section
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        
        self.speed_label = QLabel("Speed: -")
        self.eta_label = QLabel("ETA: -")
        self.size_label = QLabel("Size: -")
        
        # Log Output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        self.log_output.setPlaceholderText("Download logs will appear here...")
        
        # Disclaimer
        self.disclaimer_label = QLabel(
            "⚠️ Disclaimer: This tool is for personal use only. "
            "Please respect copyright laws and YouTube's Terms of Service."
        )
        self.disclaimer_label.setWordWrap(True)
        self.disclaimer_label.setStyleSheet("color: #888; font-size: 11px;")
        
    def _setup_layout(self):
        """Setup the window layout"""
        # Create scroll area for main content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.setCentralWidget(scroll_area)
        
        # Create content widget
        central_widget = QWidget()
        scroll_area.setWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # URL Input Group
        url_group = QGroupBox("🔗 Video URL")
        url_layout = QVBoxLayout(url_group)
        
        url_row = QHBoxLayout()
        url_row.addWidget(self.url_input)
        url_row.addWidget(self.paste_btn)
        url_row.addWidget(self.clear_btn)
        url_row.addWidget(self.analyze_btn)
        url_layout.addLayout(url_row)
        
        main_layout.addWidget(url_group)
        
        # Video Info Group
        info_group = QGroupBox("📺 Video Information")
        info_layout = QVBoxLayout(info_group)
        info_layout.addWidget(self.title_label)
        
        info_row = QHBoxLayout()
        info_row.addWidget(self.duration_label)
        info_row.addWidget(self.uploader_label)
        info_row.addWidget(self.type_label)
        info_row.addStretch()
        info_layout.addLayout(info_row)
        
        main_layout.addWidget(info_group)
        
        # Options Group
        options_group = QGroupBox("⚙️ Download Options")
        options_layout = QGridLayout(options_group)
        options_layout.setContentsMargins(15, 20, 15, 15)
        options_layout.setVerticalSpacing(12)
        options_layout.setHorizontalSpacing(10)
        options_layout.setColumnMinimumWidth(0, 70)
        options_layout.setColumnStretch(1, 1)
        
        # Download type row
        type_layout = QHBoxLayout()
        type_layout.setSpacing(20)
        type_layout.addWidget(self.video_radio)
        type_layout.addWidget(self.audio_radio)
        type_layout.addStretch()
        options_layout.addLayout(type_layout, 0, 0, 1, 2)
        
        # Quality row
        self.quality_label.setMinimumWidth(60)
        self.quality_combo.setMinimumHeight(32)
        options_layout.addWidget(self.quality_label, 1, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        options_layout.addWidget(self.quality_combo, 1, 1)
        
        # Format row
        self.format_label.setMinimumWidth(60)
        self.format_combo.setMinimumHeight(32)
        options_layout.addWidget(self.format_label, 2, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        options_layout.addWidget(self.format_combo, 2, 1)
        
        # Output location row
        output_layout = QHBoxLayout()
        output_layout.setSpacing(10)
        self.output_input.setMinimumHeight(32)
        output_layout.addWidget(self.output_input)
        output_layout.addWidget(self.browse_btn)
        options_layout.addWidget(self.cookies_checkbox, 3, 0, 1, 2)
        options_layout.addWidget(self.cookies_file_checkbox, 4, 0, 1, 2)
        cookies_file_layout = QHBoxLayout()
        cookies_file_layout.setSpacing(10)
        self.cookies_file_input.setMinimumHeight(32)
        cookies_file_layout.addWidget(self.cookies_file_input)
        cookies_file_layout.addWidget(self.cookies_file_btn)
        options_layout.addLayout(cookies_file_layout, 5, 1)
        options_layout.addWidget(self.output_label, 6, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        options_layout.addLayout(output_layout, 6, 1)
        
        main_layout.addWidget(options_group)
        
        # Queue Group
        queue_group = QGroupBox("📋 Download Queue")
        queue_layout = QVBoxLayout(queue_group)
        queue_layout.addWidget(self.queue_list)
        
        queue_btn_layout = QHBoxLayout()
        queue_btn_layout.addWidget(self.add_queue_btn)
        queue_btn_layout.addWidget(self.clear_queue_btn)
        queue_btn_layout.addStretch()
        queue_btn_layout.addWidget(self.download_queue_btn)
        queue_layout.addLayout(queue_btn_layout)
        
        main_layout.addWidget(queue_group)
        
        # Action Buttons
        action_layout = QHBoxLayout()
        action_layout.addWidget(self.download_btn)
        action_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(action_layout)
        
        # Progress Group
        progress_group = QGroupBox("📊 Progress")
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.addWidget(self.progress_bar)
        
        stats_layout = QHBoxLayout()
        stats_layout.addWidget(self.speed_label)
        stats_layout.addWidget(self.eta_label)
        stats_layout.addWidget(self.size_label)
        stats_layout.addStretch()
        progress_layout.addLayout(stats_layout)
        
        main_layout.addWidget(progress_group)
        
        # Log Group
        log_group = QGroupBox("📝 Logs")
        log_layout = QVBoxLayout(log_group)
        log_layout.addWidget(self.log_output)
        main_layout.addWidget(log_group)
        
        # Disclaimer
        main_layout.addWidget(self.disclaimer_label)
        
    def _connect_signals(self):
        """Connect widget signals to slots"""
        # Button clicks
        self.paste_btn.clicked.connect(self._paste_url)
        self.clear_btn.clicked.connect(self._clear_url)
        self.analyze_btn.clicked.connect(self._analyze_url)
        self.browse_btn.clicked.connect(self._browse_output)
        self.cookies_file_btn.clicked.connect(self._browse_cookies_file)
        self.download_btn.clicked.connect(self._start_download)
        self.cancel_btn.clicked.connect(self._cancel_download)
        self.add_queue_btn.clicked.connect(self._add_to_queue)
        self.clear_queue_btn.clicked.connect(self._clear_queue)
        self.download_queue_btn.clicked.connect(self._download_queue)
        
        # Radio button changes
        self.video_radio.toggled.connect(self._on_type_changed)
        self.audio_radio.toggled.connect(self._on_type_changed)
        self.cookies_file_checkbox.toggled.connect(self._on_cookies_file_toggled)
        
        # URL input changes
        self.url_input.textChanged.connect(self._on_url_changed)
        self.url_input.returnPressed.connect(self._analyze_url)
        
    def _apply_styles(self):
        """Apply custom styles to the application"""
        style = """
            QMainWindow {
                background-color: #1e1e1e;
            }
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #1e1e1e;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666;
            }
            QScrollBar:horizontal {
                background-color: #2d2d2d;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #555;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                width: 0px;
                height: 0px;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                padding-top: 25px;
                background-color: #2d2d2d;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 12px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                background-color: #3d3d3d;
                color: #e0e0e0;
                font-size: 13px;
            }
            QLineEdit:disabled {
                background-color: #2b2b2b;
                color: #b0b0b0;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            QPushButton {
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
                background-color: #0078d4;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
            QComboBox {
                padding: 8px;
                padding-right: 30px;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                background-color: #3d3d3d;
                color: #ffffff;
                font-size: 12px;
                min-width: 150px;
            }
            QComboBox:hover {
                border: 1px solid #0078d4;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #555;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #ffffff;
            }
            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                color: #ffffff;
                selection-background-color: #0078d4;
                border: 1px solid #555;
                padding: 4px;
            }
            QProgressBar {
                border: none;
                border-radius: 5px;
                background-color: #3d3d3d;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 5px;
            }
            QTextEdit {
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
            QRadioButton {
                color: #e0e0e0;
                font-size: 12px;
            }
            QCheckBox {
                color: #e0e0e0;
                font-size: 12px;
            }
            QCheckBox:disabled {
                color: #9a9a9a;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QRadioButton::indicator {
                border: 1px solid #9a9a9a;
                border-radius: 8px;
                background-color: #2a2a2a;
            }
            QRadioButton::indicator:checked {
                border: 1px solid #0078d4;
                background-color: #0078d4;
            }
            QRadioButton::indicator:disabled {
                border: 1px solid #666;
                background-color: #242424;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #9a9a9a;
                border-radius: 3px;
                background-color: #2a2a2a;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #0078d4;
                background-color: #0078d4;
            }
            QCheckBox::indicator:disabled {
                border: 1px solid #666;
                background-color: #242424;
            }
            QListWidget {
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                background-color: #3d3d3d;
                color: #e0e0e0;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
            }
        """
        self.setStyleSheet(style)
        
    def _populate_quality_combo(self):
        """Populate quality dropdown"""
        self.quality_combo.clear()
        for code, name in FormatHandler.get_quality_options():
            self.quality_combo.addItem(name, code)
            
    def _populate_format_combo(self, audio_only: bool = False):
        """Populate format dropdown"""
        self.format_combo.clear()
        for code, name in FormatHandler.get_output_formats(audio_only):
            self.format_combo.addItem(name, code)
            
    def _paste_url(self):
        """Paste URL from clipboard"""
        clipboard = QClipboard()
        text = clipboard.text()
        if text:
            self.url_input.setText(text.strip())
            self._log(f"Pasted URL from clipboard")
            
    def _clear_url(self):
        """Clear URL input"""
        self.url_input.clear()
        self._reset_video_info()
        self.download_btn.setEnabled(False)
        
    def _on_url_changed(self, text: str):
        """Handle URL input change"""
        has_url = bool(text.strip())
        self.analyze_btn.setEnabled(has_url)
        
    def _on_type_changed(self):
        """Handle download type change"""
        audio_only = self.audio_radio.isChecked()
        self._populate_format_combo(audio_only)
        
        if audio_only:
            self.quality_combo.setEnabled(False)
            self.quality_combo.setCurrentIndex(0)
        else:
            self.quality_combo.setEnabled(True)
            
    def _browse_output(self):
        """Open folder browser dialog"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Download Folder",
            self.output_path,
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.output_path = folder
            self.output_input.setText(folder)
            self._log(f"Output folder set to: {folder}")

    def _browse_cookies_file(self):
        """Open cookies file browser dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select cookies.txt file",
            os.path.expanduser("~"),
            "Cookies (*.txt);;All Files (*)"
        )
        if file_path:
            self.cookies_file_input.setText(file_path)
            self.cookies_file_checkbox.setChecked(True)
            self._log("Cookies file selected")

    def _on_cookies_file_toggled(self, checked: bool):
        """Enable/disable cookies file controls"""
        self.cookies_file_input.setEnabled(checked)
        self.cookies_file_btn.setEnabled(checked)
            
    def _analyze_url(self):
        """Analyze the YouTube URL"""
        url = self.url_input.text().strip()
        if not url:
            self._show_error("Please enter a YouTube URL")
            return
            
        if not self._is_valid_youtube_url(url):
            self._show_error("Invalid YouTube URL")
            return
            
        self._set_ui_state(analyzing=True)
        self._log("Analyzing URL...")
        
        # Create and start worker
        self.download_worker = DownloadWorker(self)
        self.download_worker.setup(
            url=url,
            output_path=self.output_path,
            operation="info"
        )
        self.download_worker.info_fetched.connect(self._on_info_fetched)
        self.download_worker.error_occurred.connect(self._on_error)
        self.download_worker.log_message.connect(self._log)
        self.download_worker.finished.connect(lambda: self._set_ui_state(analyzing=False))
        self.download_worker.start()
        
    def _on_info_fetched(self, info: VideoInfo):
        """Handle video info fetched"""
        self.current_video_info = info
        
        # Update UI with video info
        self.title_label.setText(f"Title: {info.title}")
        
        duration_str = self._format_duration(info.duration)
        self.duration_label.setText(f"Duration: {duration_str}")
        self.uploader_label.setText(f"Uploader: {info.uploader}")
        self.type_label.setText(f"Type: {info.video_type.value.capitalize()}")
        
        self.download_btn.setEnabled(True)
        self.status_bar.showMessage(f"Ready to download: {info.title}")
        
    def _start_download(self):
        """Start the download"""
        url = self.url_input.text().strip()
        if not url:
            self._show_error("Please enter a URL")
            return
            
        quality = self.quality_combo.currentData()
        output_format = self.format_combo.currentData()
        audio_only = self.audio_radio.isChecked()
        cookies_file = self.cookies_file_input.text().strip() if self.cookies_file_checkbox.isChecked() else None
        if self.cookies_file_checkbox.isChecked() and not cookies_file:
            self._show_error("Please select a cookies.txt file or disable cookies file option")
            return
        
        self._set_ui_state(downloading=True)
        self._log("Starting download...")
        
        # Create and start worker
        self.download_worker = DownloadWorker(self)
        self.download_worker.setup(
            url=url,
            output_path=self.output_path,
            quality=quality,
            output_format=output_format,
            audio_only=audio_only,
            use_cookies_from_browser=self.cookies_checkbox.isChecked(),
            cookies_file=cookies_file,
            operation="download"
        )
        self.download_worker.progress_update.connect(self._on_progress_update)
        self.download_worker.download_complete.connect(self._on_download_complete)
        self.download_worker.error_occurred.connect(self._on_error)
        self.download_worker.log_message.connect(self._log)
        self.download_worker.start()
        
    def _cancel_download(self):
        """Cancel the current download"""
        if self.download_worker:
            self.download_worker.cancel()
            self._log("Cancelling download...")
            self.status_bar.showMessage("Cancelling...")
            
    def _on_progress_update(self, progress: ProgressInfo):
        """Handle progress update"""
        self.progress_bar.setValue(int(progress.percent))
        self.speed_label.setText(f"Speed: {progress.speed_str}")
        self.eta_label.setText(f"ETA: {progress.eta_str}")
        self.size_label.setText(f"Size: {progress.size_str}")
        self.status_bar.showMessage(f"Downloading: {progress.percent:.1f}%")
        
    def _on_download_complete(self, success: bool, message: str):
        """Handle download completion"""
        self._set_ui_state(downloading=False)
        
        if success:
            self.progress_bar.setValue(100)
            self._show_info("Download Complete", message)
            self.status_bar.showMessage("Download completed!")
        else:
            self.progress_bar.setValue(0)
            self.status_bar.showMessage("Download failed or cancelled")
            
    def _on_error(self, error: str):
        """Handle error"""
        self._set_ui_state(downloading=False, analyzing=False)
        self._show_error(error)
        self._log(f"Error: {error}")
        self.status_bar.showMessage("Error occurred")
        
    def _add_to_queue(self):
        """Add current URL to download queue"""
        url = self.url_input.text().strip()
        if not url:
            self._show_error("Please enter a URL")
            return
            
        # Add to queue list
        title = self.current_video_info.title if self.current_video_info else url[:50]
        item = QListWidgetItem(f"📹 {title}")
        item.setData(Qt.ItemDataRole.UserRole, {
            'url': url,
            'quality': self.quality_combo.currentData(),
            'format': self.format_combo.currentData(),
            'audio_only': self.audio_radio.isChecked()
        })
        self.queue_list.addItem(item)
        
        self.download_queue.add(url)
        self.download_queue_btn.setEnabled(True)
        self._log(f"Added to queue: {title}")
        
        # Clear for next URL
        self._clear_url()
        
    def _clear_queue(self):
        """Clear the download queue"""
        self.queue_list.clear()
        self.download_queue.clear()
        self.download_queue_btn.setEnabled(False)
        self._log("Queue cleared")
        
    def _download_queue(self):
        """Download all items in queue"""
        if self.download_queue.is_empty:
            self._show_error("Queue is empty")
            return
            
        self._log("Starting queue download...")
        # TODO: Implement queue download logic
        self._show_info("Queue Download", "Queue download feature coming soon!")
        
    def _set_ui_state(self, downloading: bool = False, analyzing: bool = False):
        """Set UI state based on current operation"""
        busy = downloading or analyzing
        
        self.url_input.setEnabled(not busy)
        self.paste_btn.setEnabled(not busy)
        self.clear_btn.setEnabled(not busy)
        self.analyze_btn.setEnabled(not busy and bool(self.url_input.text()))
        self.quality_combo.setEnabled(not busy and not self.audio_radio.isChecked())
        self.format_combo.setEnabled(not busy)
        self.browse_btn.setEnabled(not busy)
        self.video_radio.setEnabled(not busy)
        self.audio_radio.setEnabled(not busy)
        self.cookies_checkbox.setEnabled(not busy)
        self.cookies_file_checkbox.setEnabled(not busy)
        self.cookies_file_input.setEnabled(not busy and self.cookies_file_checkbox.isChecked())
        self.cookies_file_btn.setEnabled(not busy and self.cookies_file_checkbox.isChecked())
        self.add_queue_btn.setEnabled(not busy)
        self.download_queue_btn.setEnabled(not busy and not self.download_queue.is_empty)
        
        self.download_btn.setEnabled(not busy and self.current_video_info is not None)
        self.cancel_btn.setEnabled(downloading)
        
        if analyzing:
            self.status_bar.showMessage("Analyzing URL...")
        elif downloading:
            self.status_bar.showMessage("Downloading...")
            
    def _reset_video_info(self):
        """Reset video info display"""
        self.current_video_info = None
        self.title_label.setText("Title: -")
        self.duration_label.setText("Duration: -")
        self.uploader_label.setText("Uploader: -")
        self.type_label.setText("Type: -")
        self.progress_bar.setValue(0)
        self.speed_label.setText("Speed: -")
        self.eta_label.setText("ETA: -")
        self.size_label.setText("Size: -")
        
    def _log(self, message: str):
        """Add message to log output"""
        self.log_output.append(f"> {message}")
        # Auto-scroll to bottom
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def _show_error(self, message: str):
        """Show error message dialog"""
        QMessageBox.critical(self, "Error", message)
        
    def _show_info(self, title: str, message: str):
        """Show info message dialog"""
        QMessageBox.information(self, title, message)
        
    @staticmethod
    def _is_valid_youtube_url(url: str) -> bool:
        """Check if URL is a valid YouTube URL"""
        youtube_patterns = [
            'youtube.com/watch',
            'youtube.com/shorts',
            'youtube.com/playlist',
            'youtu.be/',
            'youtube.com/embed',
            'youtube.com/v/'
        ]
        url_lower = url.lower()
        return any(pattern in url_lower for pattern in youtube_patterns)
    
    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Format duration in HH:MM:SS"""
        if seconds <= 0:
            return "Live/Unknown"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.download_worker and self.download_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Download in Progress",
                "A download is in progress. Do you want to cancel and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.download_worker.cancel()
                self.download_worker.wait(2000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
