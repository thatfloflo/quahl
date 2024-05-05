from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QToolBar, QProgressBar, QScrollArea
)
from PySide6.QtCore import Qt, Slot, Signal, QFileInfo
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import QFileIconProvider, QSizePolicy, QMainWindow
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEngineProfile

from .resources import Icons, OutlineIcons
from .helpers import show_in_file_manager, squish_string, OS


class DownloadCard(QFrame):

    _download: QWebEngineDownloadRequest | None
    _filename: str = ""
    _progress: int = 0
    _loading_started: bool = False
    _loading_finished: bool = False
    _layout = QHBoxLayout
    _filename_label: QLabel
    _status_widget: QWidget
    _status_label: QLabel
    _progress_bar: QProgressBar
    _file_icon: QLabel
    _toolbar: QToolBar
    show_file_action: QAction
    abort_action: QAction
    remove_action: QAction
    removal_requested: Signal = Signal(QWidget)
    download_aborted: Signal = Signal()

    def __init__(self, download: QWebEngineDownloadRequest, parent: QWidget | None):
        super().__init__(parent)

        self._download = download
        self._filename = download.downloadFileName()
        self._progress = 0

        if OS.detected == OS.WINDOWS:
            self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        else:
            self.setStyleSheet("""
                DownloadCard {
                    background-color: palette(base);
                    border-radius: 5px;
                }
                QLabel#FilenameLabel {
                    font-size: 11pt;
                }
                QLabel#StatusLabel {
                    font-size: 9pt;
                }
                QToolBar {
                    border: 0;
                    margin: 0;
                    padding: 0;
                    background: palette(base);
                }
                QToolButton {
                    margin: 1px;
                    padding: 1px;
                    background-color: palette(base);
                    border: 1px solid palette(base);
                    border-radius: 3px;
                }
                QToolButton:hover {
                    border-color: palette(midlight);
                }
                QToolButton:pressed {
                    border-color: palette(dark);
                    background-color: palette(midlight);
                    border-style: inset;
                }
            """)
        self.setMinimumHeight(64)
        self._build_layout()
        self._update_icon()

        download.totalBytesChanged.connect(self._update_download_progress)
        download.receivedBytesChanged.connect(self._update_download_progress)
        download.stateChanged.connect(self._update_download_progress)
        download.isFinishedChanged.connect(self._update_download_progress)
        self._update_download_progress()

        download.destroyed.connect(self._download_request_destroyed)

    def _update_icon(self):
        if self._download:
            file_info = QFileInfo(self._download.downloadFileName())
            provider = QFileIconProvider()
            icon: QIcon = provider.icon(file_info)
            self._file_icon.setPixmap(icon.pixmap(32))
            return
        self._file_icon.setPixmap(Icons.File.pixmap(32))

    @Slot()
    def _download_request_destroyed(self):
        self._download = None

    @Slot()
    def _update_download_progress(self):
        if not self._download:
            return
        state = self._download.state()
        if state == QWebEngineDownloadRequest.DownloadCompleted:
            self.set_loading_finished()
            return
        if state == QWebEngineDownloadRequest.DownloadCancelled:
            self.set_download_cancelled()
            return
        if state == QWebEngineDownloadRequest.DownloadInterrupted:
            reason = self._download.interruptReasonString()
            self.set_download_interrupted(reason)
            return
        if state == QWebEngineDownloadRequest.DownloadRequested:
            # do nothing - leave initial "getting ready..." state
            return
        # state must be DownloadInProgress
        if not self._loading_started:
            self._loading_started = True
            self.set_loading_started()
        total = self._download.totalBytes()
        received = self._download.receivedBytes()
        completed = (received / total) * 100 if total > 0 else 100
        self.set_progress(completed)

    def _build_layout(self):
        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 5)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        self._file_icon = QLabel(self)
        self._file_icon.setAlignment(Qt.AlignCenter)
        self._file_icon.setPixmap(Icons.File.pixmap(32))
        self._layout.addWidget(self._file_icon, alignment=Qt.AlignLeft)

        label_layout = QVBoxLayout()
        label_layout.setSpacing(0)
        self._layout.addLayout(label_layout)

        self._filename_label = QLabel(self)
        self._filename_label.setObjectName("FilenameLabel")
        # self._filename_label.setStyleSheet("font-size: 10pt;")
        self._filename_label.setText(squish_string(self._filename, 35))
        self._filename_label.setToolTip(self._filename)
        label_layout.addWidget(self._filename_label)

        self._status_label = QLabel(self)
        self._status_label.setObjectName("StatusLabel")
        # self._status_label.setStyleSheet("font-size: 8pt;")
        self._status_label.setText("Getting ready...")
        label_layout.addWidget(self._status_label)

        self._progress_bar = QProgressBar(self)
        self._progress_bar.setValue(self._progress)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setMaximumHeight(10)
        label_layout.addWidget(self._progress_bar)
        self._progress_bar.setVisible(False)

        self._layout.addStretch()

        self._toolbar = QToolBar(self)
        self._layout.addWidget(self._toolbar, alignment=Qt.AlignRight)

        self.show_file_action = QAction(OutlineIcons.FolderOpen, "Show in folder", self)
        self.show_file_action.triggered.connect(self.show_file)
        self.show_file_action.setVisible(False)
        self.show_file_action.setEnabled(False)
        self.show_file_action.setPriority(QAction.LowPriority)
        self._toolbar.addAction(self.show_file_action)
        self.remove_action = QAction(OutlineIcons.Remove, "Remove", self)
        self.remove_action.triggered.connect(self._emit_removal_requested)
        self.remove_action.setPriority(QAction.HighPriority)
        self.remove_action.setVisible(False)
        self.remove_action.setEnabled(False)
        self._toolbar.addAction(self.remove_action)
        self.abort_action = QAction(OutlineIcons.Stop, "Cancel Download", self)
        self.abort_action.triggered.connect(self._cancel_download)
        self.abort_action.setVisible(True)
        self.abort_action.setEnabled(True)
        self._toolbar.addAction(self.abort_action)

    def _cancel_download(self):
        if not self._download:
            return
        self._download.cancel()
        self.set_download_cancelled()
        self.download_aborted.emit()

    def _emit_removal_requested(self):
        self.removal_requested.emit(self)

    @Slot()
    def show_file(self):
        if self._download:
            path = Path(self._download.downloadDirectory()) / self._download.downloadFileName()
            if path.exists():
                show_in_file_manager(path)
                return
        self.show_file_action.setEnabled(False)

    @Slot()
    def set_download_cancelled(self):
        self._status_label.setText("<em>Cancelled</em>")
        self._progress_bar.setVisible(False)
        self._status_label.setVisible(True)
        self.abort_action.setVisible(False)
        self.abort_action.setEnabled(False)
        self.remove_action.setVisible(True)
        self.remove_action.setEnabled(True)

    @Slot()
    def set_download_interrupted(self, reason: str):
        self._status_label.setText(f"<em>Download interrupted:</em> {reason}")
        self._progress_bar.setVisible(False)
        self._status_label.setVisible(True)
        self.abort_action.setVisible(False)
        self.abort_action.setEnabled(False)
        self.remove_action.setVisible(True)
        self.remove_action.setEnabled(True)

    @Slot(int)
    def set_progress(self, progress: int):
        self._progress = progress
        self._progress_bar.setValue(progress)
        if self._progress > 0:
            self._loading_started = True
        if self._loading_started and not self._loading_finished:
            self._status_label.setVisible(False)
            self._progress_bar.setVisible(True)
        else:
            self._status_label.setVisible(True)
            self._progress_bar.setVisible(False)

    @Slot()
    def set_loading_started(self):
        self._loading_started = True
        self._loading_finished = False
        self.abort_action.setVisible(True)
        self.abort_action.setEnabled(True)
        self.remove_action.setVisible(False)
        self.remove_action.setEnabled(False)
        self.set_progress(0)
        self._update_icon()

    @Slot()
    def set_loading_finished(self):
        self._loading_started = True
        self._loading_finished = True
        self._status_label.setText("Finished")
        self.abort_action.setVisible(False)
        self.abort_action.setEnabled(False)
        self.remove_action.setVisible(True)
        self.remove_action.setEnabled(True)
        self.set_progress(100)
        if self._download:
            path = Path(self._download.downloadDirectory()) / self._download.downloadFileName()
            if path.exists():
                self.show_file_action.setEnabled(True)
                self.show_file_action.setVisible(True)

    def closeEvent(self, event):
        event.ignore()
        self.hide()


class DownloadManagerWidget(QWidget):

    _download_ids: list[int] = []
    _layout: QVBoxLayout
    _header: QLabel
    _toolbar: QToolBar
    _card_list = QVBoxLayout
    _active_cards: dict[QWebEngineDownloadRequest, DownloadCard] = dict()

    def __init__(self, profile: QWebEngineProfile, parent: QWidget | None = None):
        super().__init__(parent)
        self._profile = profile
        self.setMinimumWidth(300)
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 5)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)
        self._header = QLabel(self)
        self._header.setMargin(3)
        self._header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self._header.setText("Downloads")
        self._layout.addWidget(self._header, alignment=Qt.AlignTop)

        self._card_list = QVBoxLayout()
        self._card_list.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        scroll.setContentsMargins(0, 0, 0, 0)
        scroll.setFrameStyle(QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(300)
        scroll.setMinimumHeight(200)
        # scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        wrapper = QWidget(scroll)
        scroll.setWidget(wrapper)
        self._layout.addWidget(scroll)
        wrapper.setLayout(self._card_list)
        self._card_list.setAlignment(Qt.AlignTop)

        # self._layout.addStretch()

        self._toolbar = QToolBar(self)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._toolbar.addWidget(spacer)
        self.open_folder_action = QAction(self)
        self.open_folder_action.setIcon(OutlineIcons.Folder)
        self.open_folder_action.setIconText("Open Downloads Folder")
        self.open_folder_action.setIconVisibleInMenu(False)
        self.open_folder_action.setText("Open Downloads Folder")
        self.open_folder_action.setToolTip("Open the Downloads folder")
        self.open_folder_action.triggered.connect(self.open_downloads_folder)
        self._toolbar.addAction(self.open_folder_action)
        self.clear_all_action = QAction(self)
        self.clear_all_action.setIcon(OutlineIcons.Delete)
        self.clear_all_action.setIconText("Clear All")
        self.clear_all_action.setIconVisibleInMenu(False)
        self.clear_all_action.setText("Clear Download History")
        self.clear_all_action.setToolTip("Clear the history of downloads")
        self.clear_all_action.triggered.connect(self.clear_all)
        self._toolbar.addAction(self.clear_all_action)
        self._layout.addWidget(self._toolbar, alignment=Qt.AlignBottom)

        self._toolbar.setStyleSheet("""
            QToolBar {
                border: 0;
                background: palette(window);
            }
            QToolButton {
                padding: 3px;
                border-radius: 3px;
                border: 1px solid palette(window);
            }
            QToolButton:hover {
                background: palette(midlight);
                border-style: outset;
            }
            QToolButton:pressed {
                background: palette(dark);
                border-style: inset;
            }
        """)

    @Slot()
    def clear_all(self):
        removal_list: list[DownloadCard] = []
        for i in range(0, self._card_list.count()):
            layout_item = self._card_list.itemAt(i)
            widget = layout_item.widget()
            if isinstance(widget, DownloadCard) and widget.remove_action.isEnabled():
                removal_list.append(widget)
        for card in removal_list:
            card.remove_action.trigger()

    @Slot()
    def open_downloads_folder(self):
        path = Path(self._profile.downloadPath())
        show_in_file_manager(path)

    @Slot(QWebEngineDownloadRequest)
    def download_requested(self, download: QWebEngineDownloadRequest):
        self.add_download(download)

    def add_download(self, download: QWebEngineDownloadRequest) -> DownloadCard:
        id = download.id()
        if id in self._download_ids:
            return  # sometimes we get sent the same ID twice...
        self._rename_file_if_duplicate(download)
        card = DownloadCard(download, self)
        self.add_card(card)
        download.accept()
        self._download_ids.append(id)
        return card

    def _rename_file_if_duplicate(self, download: QWebEngineDownloadRequest):
        suggested = original = Path(download.downloadDirectory()) / download.downloadFileName()
        if not original.exists():
            return
        counter = 2
        while suggested.exists():
            suggested = suggested.with_stem(f"{original.stem} ({counter})")
            counter += 1
        download.setDownloadFileName(suggested.name)

    @Slot(QWidget)
    def add_card(self, card: QWidget):
        if isinstance(card, DownloadCard):
            card.removal_requested.connect(self.remove_card)
        self._card_list.insertWidget(0, card)
        card.setFocus()

    @Slot()
    @Slot(QWidget)
    def remove_card(self, card: QWidget | None = None):
        if card is None:
            card = self.sender()
            if not isinstance(card, QWidget):
                return
        self._card_list.removeWidget(card)
        card.hide()
        if isinstance(card, DownloadCard):
            card.deleteLater()


class DownloadManagerWindow(QMainWindow):

    def __init__(self, profile: QWebEngineProfile, parent: QWidget | None = None):
        super().__init__(parent)

        self.setWindowTitle("Download Manager")
        self.setWindowIcon(Icons.Downloads)
        self.resize(380, 450)

        self._manager = DownloadManagerWidget(profile, parent)
        self.setCentralWidget(self._manager)

        self._file_menu = self.menuBar().addMenu("&File")
        self._action_close = QAction()
        self._action_close.setIcon(QIcon.fromTheme("window-close"))
        self._action_close.setIconText("Close")
        self._action_close.setIconVisibleInMenu(False)
        self._action_close.setShortcut(QKeySequence.Close)
        self._action_close.setText("Close Do&wnload Manager")
        self._action_close.setToolTip("Close the Download Manager window")
        self._action_close.setEnabled(True)
        self._action_close.triggered.connect(self.close)
        self._file_menu.addAction(self._action_close)
        self._file_menu.addSeparator()
        self._file_menu.addAction(self._manager.open_folder_action)
        self._file_menu.addAction(self._manager.clear_all_action)

    def clear_all(self):
        return self._manager.clear_all()
    
    def open_downloads_folder(self):
        return self._manager.open_downloads_folder()

    @Slot(QWebEngineDownloadRequest)
    def download_requested(self, download: QWebEngineDownloadRequest):
        self._manager.download_requested(download)

    def add_download(self, download: QWebEngineDownloadRequest) -> DownloadCard:
        return self._manager.add_download(download)

    def add_card(self, card: QWidget):
        return self._manager.add_card(card)

    def remove_card(self, card: QWidget | None = None):
        return self._manager.remove_card(card)