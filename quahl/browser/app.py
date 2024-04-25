from uuid import UUID, uuid4

from PySide6.QtCore import QObject, Signal, Slot, QPoint, QUrl

from .helpers import connect_once, discard_args
from .profile import BrowserProfile
from .window import BrowserWindow
from .resources import Icons
from .downloadmanager import DownloadManager


class BrowserApp(QObject):
    """The main Quahl Browser App which manages browser profiles and windows."""

    window_removed: Signal = Signal(UUID)
    window_created: Signal = Signal(UUID)
    all_windows_removed: Signal = Signal()

    _windows: dict[UUID, BrowserWindow] = {}
    _download_manager: DownloadManager
    _profile: BrowserProfile

    default_icon = Icons.Browser

    def __init__(self, parent: QObject | None = None, profile: BrowserProfile | None = None):
        super().__init__(parent)
        self._profile = profile if profile else BrowserProfile()
        connect_once(self.window_created, discard_args(self._profile.trigger_startup_actions))
        self.all_windows_removed.connect(self._profile.trigger_shutdown_actions)
        self._download_manager = DownloadManager(self._profile)

    @property
    def profile(self) -> BrowserProfile:
        """Get the `BrowserApp` instance's profile."""
        return self._profile

    @property
    def windows(self) -> dict[UUID, BrowserWindow]:
        """Get a dictionary of all current main windows."""
        return self._windows

    @property
    def download_manager(self) -> DownloadManager:
        """Return the `DownloadManager` instance associated with this `BrowserApp` instance."""
        return self._download_manager

    def create_window(
            self,
            profile: BrowserProfile | None = None,
            show: bool = False,
            background: bool = False,
            from_window: BrowserWindow | None = None,
            initial_url: QUrl | None = None,
            is_popup: bool = False) -> BrowserWindow:
        """Create a new main window.

        The window can be given an optional *profile* different to the browser's
        default profile (e.g. if intended as an incognito window). If no
        *profile* is specified, the profile associated with the `BrowserApp`
        instance is used.
        """
        profile = profile if profile else self._profile
        while (uuid := uuid4()) in self._windows:
            pass
        window = BrowserWindow(self, profile, is_popup=is_popup, uuid=uuid, initial_url=initial_url)
        window.about_to_close.connect(self._remove_window)
        self._windows[uuid] = window
        self.window_created.emit(uuid)
        if self._profile.settings.inherit_window_size and from_window:
            window.resize(from_window.size())
            if from_window.isMaximized():
                window.showMaximized()
        else:
            window.resize(*self._profile.settings.default_window_size)
        if from_window and not from_window.isMaximized():
            # Get the window created before this one, then
            # stagger new non-maximized window relative to that
            prev = self._windows[list(self._windows)[-2]] if len(self._windows) > 1 else from_window
            window.move(prev.pos() + QPoint(*self._profile.settings.window_stagger))
            # Move to top left corner if we get perilously close to the bottom right corner
            scr_w, scr_h = window.screen().availableGeometry().size().toTuple()
            win_x, win_y = window.pos().toTuple()
            min_dist = 100
            if win_x + min_dist > scr_w or win_y + min_dist > scr_h:
                window.move(0, 0)
        if show:
            window.show()
        else:
            window.hide()
        if background:
            window.lower()
        return window

    def _check_windows_remaining(self) -> int:
        c = len(self._windows)
        if c <= 0:
            self.all_windows_removed.emit()
        return c

    @Slot(UUID)
    def _remove_window(self, uuid: UUID | None = None) -> int:
        """Remove a window from the browser app's window registry."""
        # Remove by UUID if possible
        if uuid in self._windows:
            del self._windows[uuid]
            self.window_removed.emit(uuid)
            return self._check_windows_remaining()
        # Attempt removal by indirectly gaining UUID
        window = self.sender()
        if window.uuid in self._windows:
            del self._windows[uuid]
            self.window_removed.emit(uuid)
            return self._check_windows_remaining()
        # Attempt removal by direct reference to the BrowserWindow
        for key, value in self._windows.items():
            if value is window:
                del self._windows[key]
                self.window_removed.emit(key)
                return self._check_windows_remaining()

    @Slot()
    def show_downloads(self):
        """Show the download manager window."""
        self._download_manager.show()
        if self._download_manager.isMinimized():
            self._download_manager.showNormal()
        self._download_manager.activateWindow()