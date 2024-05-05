from pathlib import Path
import enum
import sys
from typing import Iterable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QToolBar, QProgressBar, QScrollArea,
    QMenu
)
from PySide6.QtCore import Qt, Slot, Signal, QFileInfo, QObject
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import QFileIconProvider, QSizePolicy, QMainWindow
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEngineProfile

from .resources import Icons, OutlineIcons
from .helpers import show_in_file_manager, squish_string


class DownloadState(enum.IntEnum):

    REQUESTED = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    CANCELLED = 3
    INTERRUPTED = 4
    PAUSED = 5

    def __str__(self) -> str:
        if self == self.REQUESTED:
            return "Getting ready…"
        if self == self.IN_PROGRESS:
            return "In progress"
        if self == self.COMPLETED:
            return "Finished"
        if self == self.CANCELLED:
            return "Cancelled"
        if self == self.INTERRUPTED:
            return "Interrupted"
        if self == self.PAUSED:
            return "Paused"

    def is_failure(self) -> bool:
        if self in (self.CANCELLED, self.INTERRUPTED):
            return True
        return False

    def is_alive(self) -> bool:
        if self in (self.REQUESTED, self.IN_PROGRESS, self.PAUSED):
            return True


class DownloadManagerItem(QObject):

    progress_changed: Signal = Signal(QObject)
    state_changed: Signal = Signal(QObject)
    path_changed: Signal = Signal(QObject)
    icon_changed: Signal = Signal(QObject)

    _download: QWebEngineDownloadRequest | None = None
    _id: int
    _filename: Path
    _path: Path
    _progress_percent: int
    _received_bytes: int
    _total_bytes: int
    _state: DownloadState
    _loading_started: bool
    _loading_finished: bool
    icon: QIcon = Icons.File

    def __init__(self, download: QWebEngineDownloadRequest, parent: QObject | None = None):
        super().__init__(parent)

        self._filename = Path()
        self._path = Path()
        self._state = DownloadState.REQUESTED
        self._progress_percent = 0
        self._received_bytes = 0
        self._total_bytes = 0
        self._loading_started = False
        self._loading_finished = False
        self._download = download
        self._id = download.id()
        self._update_path()

        download.downloadDirectoryChanged.connect(self._update_path)
        download.downloadFileNameChanged.connect(self._update_path)
        download.totalBytesChanged.connect(self._update_progress)
        download.receivedBytesChanged.connect(self._update_progress)
        download.stateChanged.connect(self._update_progress)
        download.isPausedChanged.connect(self._update_progress)
        self._update_progress()

        download.destroyed.connect(self._request_destroyed)

    @property
    def id(self) -> int:
        return self._id

    @property
    def download_request(self) -> QWebEngineDownloadRequest | None:
        return self._download

    @property
    def filename(self) -> Path:
        return self._filename

    @property
    def path(self) -> Path:
        return self._path

    @property
    def progress_percent(self) -> int:
        return self._progress_percent

    @property
    def progress_bytes(self) -> tuple[int, int]:
        return (self._received_bytes, self._total_bytes)

    @property
    def state(self) -> DownloadState:
        return self._state

    @Slot()
    def cancel(self):
        if self._download:
            self._download.cancel()
            self._update_download_state()

    @Slot()
    def pause(self):
        if self._download:
            self._download.pause()

    @Slot()
    def resume(self):
        if self._download:
            self._download.resume()
            self._update_download_state()

    @Slot()
    def _request_destroyed(self):
        self._download = None

    @Slot()
    def _update_path(self):
        if self._download:
            filename = Path(self._download.downloadFileName())
            path = Path(self._download.downloadDirectory()) / filename
            if (self._filename, self._path) != (filename, path):
                self._filename = filename
                self._path = path
                self.path_changed.emit(self)
                self._update_icon()

    @Slot()
    def _update_progress(self):
        if not self._download:
            return
        old_state = self._state
        self._update_download_state()
        if self._state == DownloadState.COMPLETED:
            self._set_loading_finished()
        elif self._state == DownloadState.CANCELLED:
            self._set_cancelled()
        elif self._state == DownloadState.INTERRUPTED:
            self._set_interrupted()
        elif self._state == DownloadState.REQUESTED:
            pass  # Do nothing - remain in "getting ready..." state?
        else:  # self._state must be DownloadState.IN_PROGRESS or DownloadState.PAUSED:
            if not self._loading_started:
                self._set_loading_started()
            total_bytes = self._download.totalBytes()
            received_bytes = self._download.receivedBytes()
            self._set_progress(received_bytes, total_bytes)
        if self._state != old_state:
            self.state_changed.emit(self)

    def _update_download_state(self):
        if self._download:
            polled = DownloadState(self._download.state().value)
            if polled.is_alive() and self._download.isPaused():
                self._state = DownloadState.PAUSED
            else:
                self._state = polled
        elif self.state.is_alive():
            # A destroyed download certainly shouldn't be in an alive state!
            print("ERROR: DownloadManagerItem.state is a live state but the "
                  "DownloadRequest has been destroyed already.", file=sys.stderr)
            if self.path.exists():
                self._state = DownloadState.COMPLETED
            else:
                self._state = DownloadState.INTERRUPTED

    def _update_icon(self):
        if self._download:
            file_info = QFileInfo(self._path)
            provider = QFileIconProvider()
            icon = provider.icon(file_info)
            if icon.isNull():
                icon = Icons.File
            if self.icon is not icon:
                self.icon = icon
                self.icon_changed.emit(self)

    def _set_progress(self, received_bytes: int, total_bytes: int):
        change_detected: bool = False
        if (self._received_bytes, self._total_bytes) != (received_bytes, total_bytes):
            self._total_bytes = received_bytes
            self._received_bytes = total_bytes
            change_detected = True
        progress_percent = 100  # Used if total_bytes == 0, because 0/0 => 100%
        if total_bytes > 0:
            progress_percent = (received_bytes / total_bytes) * 100
        if self._progress_percent != progress_percent:
            self._progress_percent = progress_percent
            change_detected = True
        if change_detected:
            self.progress_changed.emit(self)

    def _set_loading_started(self):
        if self._loading_started and not self._loading_finished:
            return
        self._loading_started = True
        self._loading_finished = False
        self._set_progress(0, self._total_bytes)
        self._update_icon()

    def _set_loading_finished(self):
        if self._loading_started and self._loading_finished:
            return
        self._loading_started = True
        self._loading_finished = True
        self._set_progress(self._total_bytes, self._total_bytes)
        self._update_icon()

    def _set_cancelled(self):
        pass

    def _set_interrupted(self):
        pass


class DownloadManagerModel(QObject):

    items_inserted: Signal = Signal()
    items_removed: Signal = Signal()

    _downloads: dict[int, DownloadManagerItem]
    _handled_download_ids: list[int]

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._downloads = {}
        self._handled_download_ids = []

    @Slot(QWebEngineDownloadRequest)
    def handle_download_request(self, download: QWebEngineDownloadRequest):
        id = download.id()
        if id in self._handled_download_ids:
            return
        self._rename_if_exists(download)
        item = DownloadManagerItem(download, self)
        download.accept()
        self._handled_download_ids.append(id)
        self.insert_item(item)

    @Slot(DownloadManagerItem)
    def insert_item(self, item: DownloadManagerItem) -> bool:
        if item.id not in self._downloads:
            self._downloads[item.id] = item
            self.items_inserted.emit()
            return True
        return False

    @Slot(int)
    @Slot(DownloadManagerItem)
    def remove_item(self, item_or_id: DownloadManagerItem | int) -> bool:
        if isinstance(item_or_id, DownloadManagerItem):
            item_or_id = item_or_id.id
        if item_or_id in self._downloads:
            del self._downloads[item_or_id]
            self.items_removed.emit()
            return True
        return False

    @Slot()
    @Slot(bool)
    def remove_all(self, dead_only: bool = False):
        remove: list[int] = []
        for id in self._downloads:
            if dead_only and self._downloads[id].state.is_alive():
                continue
            remove.append(id)
        if remove:
            for id in remove:
                del self._downloads[id]
            self.items_removed.emit()

    def _rename_if_exists(self, download: QWebEngineDownloadRequest):
        suggested = original = Path(download.downloadDirectory()) / download.downloadFileName()
        if not original.exists():
            return
        counter = 2
        while suggested.exists():
            suggested = suggested.with_stem(f"{original.stem} ({counter})")
            counter += 1
        download.setDownloadFileName(suggested.name)

    def count(self, alive_only: bool = False) -> int:
        if alive_only:
            count = 0
            for download in self._downloads.values():
                if download.state.is_alive():
                    count += 1
            return count
        return len(self._downloads)

    def get_all(self, alive_only: bool = False) -> dict[int, DownloadManagerItem]:
        d: dict[int, DownloadManagerItem] = {}
        for id, item in self._downloads.items():
            if (not alive_only) or item.state.is_alive():
                d[id] = item
        return d

    def get_item(self, id: int) -> DownloadManagerItem | None:
        if id in self._downloads:
            return self._downloads[id]

    def get_new_items(
            self,
            known_ids: Iterable[int],
            alive_only: bool = False) -> dict[int, DownloadManagerItem]:
        d: dict[int, DownloadManagerItem] = {}
        new_ids = (id for id in self._downloads.keys() if id not in known_ids)
        for id in new_ids:
            if (not alive_only) or self._downloads[id].state.is_alive():
                d[id] = self._downloads[id]
        return d

    def get_removed_items(self, known_ids: Iterable[int]) -> list[int]:
        return [id for id in known_ids if id not in self._downloads]


class DownloadCard(QFrame):

    action_cancel: QAction
    action_pause_resume: QAction
    action_remove: QAction
    action_show_file: QAction

    _model: DownloadManagerModel
    _download_id: int

    _file_icon: QLabel
    _filename_label: QLabel
    _status_label: QLabel
    _layout: QHBoxLayout
    _progress_bar: QProgressBar
    _toolbar: QToolBar

    def __init__(self, model, download: DownloadManagerItem, parent: QWidget | None):
        super().__init__(parent)

        self._model = model
        self._download_id = download.id

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

        download.progress_changed.connect(self._handle_progress_changed)
        download.state_changed.connect(self._handle_state_changed)
        download.path_changed.connect(self._handle_path_changed)
        download.icon_changed.connect(self._handle_icon_changed)
        self._handle_progress_changed(download)
        self._handle_state_changed(download)
        self._handle_path_changed(download)
        self._handle_icon_changed(download)

    @property
    def model(self) -> DownloadManagerModel:
        return self._model

    @property
    def download_id(self) -> int:
        return self._download_id

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
        self._filename_label.setText("")
        self._filename_label.setToolTip("")
        self._filename_label.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Preferred
        )
        label_layout.addWidget(self._filename_label)

        self._status_label = QLabel(self)
        self._status_label.setObjectName("StatusLabel")
        self._status_label.setText("")
        self._status_label.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Preferred
        )
        label_layout.addWidget(self._status_label)

        self._progress_bar = QProgressBar(self)
        self._progress_bar.setValue(0)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Preferred
        )
        label_layout.addWidget(self._progress_bar)
        self._progress_bar.setVisible(False)

        self._toolbar = QToolBar(self)
        self._layout.addWidget(self._toolbar, alignment=Qt.AlignRight)

        self.action_show_file = QAction(OutlineIcons.FolderOpen, "Show in folder", self)
        self.action_show_file.triggered.connect(self.show_file)
        self.action_show_file.setVisible(False)
        self.action_show_file.setEnabled(False)
        self.action_show_file.setPriority(QAction.LowPriority)
        self._toolbar.addAction(self.action_show_file)
        self.action_remove = QAction(OutlineIcons.Remove, "Remove", self)
        self.action_remove.triggered.connect(self._request_removal)
        self.action_remove.setPriority(QAction.HighPriority)
        self.action_remove.setVisible(False)
        self.action_remove.setEnabled(False)
        self.action_pause_resume = QAction(OutlineIcons.MediaPause, "Pause Download", self)
        self.action_pause_resume.triggered.connect(self._request_toggle_pause)
        self.action_pause_resume.setVisible(False)
        self.action_pause_resume.setEnabled(False)
        self._toolbar.addAction(self.action_pause_resume)
        self._toolbar.addAction(self.action_remove)
        self.action_cancel = QAction(OutlineIcons.MediaStop, "Cancel Download", self)
        self.action_cancel.triggered.connect(self._request_cancellation)
        self.action_cancel.setVisible(False)
        self.action_cancel.setEnabled(False)
        self._toolbar.addAction(self.action_cancel)

    @Slot()
    def show_file(self):
        download = self._model.get_item(self._download_id)
        if download and download.path.exists():
            show_in_file_manager(download.path)
            return
        self.action_show_file.setEnabled(False)

    def _request_removal(self):
        download = self._model.get_item(self._download_id)
        if not download.state.is_alive():
            self._model.remove_item(self._download_id)
            return
        self.action_remove.setEnabled(False)

    def _request_cancellation(self):
        download = self._model.get_item(self._download_id)
        if download:
            download.cancel()

    def _request_toggle_pause(self):
        download = self._model.get_item(self._download_id)
        if download:
            if download.state == DownloadState.PAUSED:
                download.resume()
            else:
                download.pause()

    @Slot(QObject)
    def _handle_progress_changed(self, download: DownloadManagerItem):
        self._progress_bar.setValue(download.progress_percent)

    @Slot(QObject)
    def _handle_state_changed(self, download: DownloadManagerItem):
        state = download.state
        self._status_label.setText(str(state))
        if state == DownloadState.REQUESTED:
            self.action_show_file.setEnabled(False)
            self.action_show_file.setVisible(False)
            self.action_remove.setEnabled(False)
            self.action_remove.setVisible(False)
            self.action_pause_resume.setEnabled(False)
            self.action_pause_resume.setVisible(True)
            self.action_cancel.setEnabled(True)
            self.action_cancel.setVisible(True)
            self._status_label.setVisible(True)
            self._progress_bar.setVisible(False)
            return
        if state == DownloadState.IN_PROGRESS:
            self.action_show_file.setEnabled(False)
            self.action_show_file.setVisible(False)
            self.action_remove.setEnabled(False)
            self.action_remove.setVisible(False)
            self.action_pause_resume.setIcon(OutlineIcons.MediaPause)
            self.action_pause_resume.setIconText("Pause Download")
            self.action_pause_resume.setText("Pause Download")
            self.action_pause_resume.setToolTip("Temporarily pause this download")
            self.action_pause_resume.setEnabled(True)
            self.action_pause_resume.setVisible(True)
            self.action_cancel.setEnabled(True)
            self.action_cancel.setVisible(True)
            self._status_label.setVisible(False)
            self._progress_bar.setVisible(True)
            return
        if state == DownloadState.PAUSED:
            self.action_show_file.setEnabled(False)
            self.action_show_file.setVisible(False)
            self.action_remove.setEnabled(False)
            self.action_remove.setVisible(False)
            self.action_pause_resume.setIcon(OutlineIcons.MediaPlay)
            self.action_pause_resume.setIconText("Resume Download")
            self.action_pause_resume.setText("Resume Download")
            self.action_pause_resume.setToolTip("Resume this download")
            self.action_pause_resume.setEnabled(True)
            self.action_pause_resume.setVisible(True)
            self.action_cancel.setEnabled(True)
            self.action_cancel.setVisible(True)
            self._status_label.setVisible(True)
            self._progress_bar.setVisible(False)
            return
        # Must be CANCELLED, INTERRUPTED or COMPLETED
        self.action_show_file.setEnabled(download.path.exists())
        self.action_show_file.setVisible(True)
        self.action_remove.setEnabled(True)
        self.action_remove.setVisible(True)
        self.action_pause_resume.setEnabled(False)
        self.action_pause_resume.setVisible(False)
        self.action_cancel.setEnabled(False)
        self.action_cancel.setVisible(False)
        self._status_label.setVisible(True)
        self._progress_bar.setVisible(False)

    @Slot(QObject)
    def _handle_path_changed(self, download: DownloadManagerItem):
        self._filename_label.setText(squish_string(str(download.filename), 35))
        self._filename_label.setToolTip(str(download.filename))

    @Slot(QObject)
    def _handle_icon_changed(self, download: DownloadManagerItem):
        self._file_icon.setPixmap(download.icon.pixmap(32))


class DownloadManagerView(QWidget):

    action_open_folder: QAction
    action_clear_all: QAction
    view_updated: Signal = Signal()

    _profile: QWebEngineProfile
    _model: DownloadManagerModel
    _download_cards: dict[int, DownloadCard]

    _layout: QVBoxLayout
    _header: QLabel
    _card_list = QVBoxLayout
    _toolbar = QToolBar

    def __init__(
            self,
            model: DownloadManagerModel,
            profile: QWebEngineProfile,
            parent: QWidget | None = None):
        super().__init__(parent)
        self._download_cards = {}
        self._profile = profile
        self.setMinimumWidth(350)
        self._build_layout()

        self._model = model
        model.items_inserted.connect(self._handle_items_inserted)
        model.items_removed.connect(self._handle_items_removed)
        self._handle_items_inserted()

    def _build_layout(self):
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 5)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        self._header = QLabel(self)
        self._header.setMargin(3)
        self._header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self._header.setText("Downloads")
        self._layout.addWidget(self._header, alignment=Qt.AlignTop)

        scroll = QScrollArea(self)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        scroll.setContentsMargins(0, 0, 0, 0)
        scroll.setFrameStyle(QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(300)
        scroll.setMinimumHeight(200)
        scroll_wrapper = QWidget(scroll)
        scroll.setWidget(scroll_wrapper)
        self._layout.addWidget(scroll)

        self._card_list = QVBoxLayout()
        self._card_list.setContentsMargins(0, 0, 0, 0)
        self._card_list.setAlignment(Qt.AlignTop)
        scroll_wrapper.setLayout(self._card_list)

        self._toolbar = QToolBar(self)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._toolbar.addWidget(spacer)

        self.action_open_folder = QAction(self)
        self.action_open_folder.setIcon(OutlineIcons.Folder)
        self.action_open_folder.setIconText("Open Downloads Folder")
        self.action_open_folder.setIconVisibleInMenu(False)
        self.action_open_folder.setText("Open Downloads Folder")
        self.action_open_folder.setToolTip("Open the Downloads folder")
        self.action_open_folder.triggered.connect(self.open_downloads_folder)
        self._toolbar.addAction(self.action_open_folder)

        self.action_clear_all = QAction(self)
        self.action_clear_all.setIcon(OutlineIcons.Delete)
        self.action_clear_all.setIconText("Clear All")
        self.action_clear_all.setIconVisibleInMenu(False)
        self.action_clear_all.setText("Clear Download History")
        self.action_clear_all.setToolTip("Remove all completed downloads from the history")
        self.action_clear_all.triggered.connect(self.clear_all)
        self._toolbar.addAction(self.action_clear_all)
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

    @property
    def profile(self) -> QWebEngineProfile:
        return self._profile

    @property
    def model(self) -> DownloadManagerModel:
        return self._model

    @property
    def header(self) -> QLabel:
        return self._header

    @Slot()
    def open_downloads_folder(self):
        path = Path(self._profile.downloadPath())
        show_in_file_manager(path)

    @Slot()
    def clear_all(self):
        remove: list[DownloadCard] = []
        for card in self._download_cards.values():
            if card.action_remove.isEnabled():
                remove.append(card)
        for card in remove:
            card.action_remove.trigger()

    @Slot(DownloadCard)
    def _insert_card(self, card: DownloadCard):
        self._download_cards[card.download_id] = card
        self._card_list.insertWidget(0, card)
        card.setFocus()
        self.view_updated.emit()

    @Slot(DownloadCard)
    def _remove_card(self, card: DownloadCard):
        download_id = card.download_id
        self._card_list.removeWidget(card)
        card.deleteLater()
        del self._download_cards[download_id]
        self.view_updated.emit()

    @Slot()
    def _handle_items_inserted(self):
        known_ids = self._download_cards.keys()
        new_items = self._model.get_new_items(known_ids)
        for download in new_items.values():
            card = DownloadCard(self._model, download, self)
            self._insert_card(card)

    @Slot()
    def _handle_items_removed(self):
        current_ids = self._download_cards.keys()
        removed_ids = self._model.get_removed_items(current_ids)
        for download_id in removed_ids:
            self._remove_card(self._download_cards[download_id])


class DownloadManagerWindow(QMainWindow):

    action_close: QAction

    _model: DownloadManagerModel
    _profile: QWebEngineProfile

    _view: DownloadManagerView
    _file_menu: QMenu

    def __init__(
            self,
            model: DownloadManagerModel,
            profile: QWebEngineProfile,
            parent: QWidget | None = None):
        super().__init__(parent)

        self._model = model
        self._profile = profile
        self._build_layout()

    def _build_layout(self):
        self.setWindowTitle("Download Manager")
        self.setWindowIcon(Icons.Downloads)
        self.resize(400, 450)

        self._view = DownloadManagerView(self._model, self._profile, self)
        self.setCentralWidget(self._view)

        self._file_menu = self.menuBar().addMenu("&File")
        self._file_menu.addAction(self._view.action_open_folder)
        self._file_menu.addAction(self._view.action_clear_all)
        self._file_menu.addSeparator()
        self.action_close = QAction()
        self.action_close.setIcon(QIcon.fromTheme("window-close"))
        self.action_close.setIconText("Close")
        self.action_close.setIconVisibleInMenu(False)
        self.action_close.setShortcut(QKeySequence.Close)
        self.action_close.setText("Close Do&wnload Manager")
        self.action_close.setToolTip("Close the Download Manager window")
        self.action_close.setEnabled(True)
        self.action_close.triggered.connect(self.close)
        self._file_menu.addAction(self.action_close)

    @property
    def model(self) -> DownloadManagerModel:
        return self._model

    @property
    def profile(self) -> QWebEngineProfile:
        return self._profile
