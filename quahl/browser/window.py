from uuid import UUID
from typing import TYPE_CHECKING
from functools import partial

from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtCore import Signal, Slot, QEvent, QUrl, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QToolBar, QProgressBar,
)
from PySide6.QtWebEngineCore import QWebEnginePage

from .helpers import connect_once, discard_args
from .profile import BrowserProfile
from .urleditwidget import UrlEdit
from .webpage import WebPage
from .webview import WebView
from .notificationoverlay import NotificationOverlay
from .resources import Icons, NEW_WINDOW_PAGE_HTML


if TYPE_CHECKING:
    from .app import BrowserApp


class BrowserWindow(QMainWindow):

    _action_history_back: QAction
    _action_history_forward: QAction
    _action_show_downloads: QAction
    _action_stop_reload: QAction
    _url_edit: UrlEdit
    _url_edit_action: QAction
    _browser_app: "BrowserApp"
    _layout: QVBoxLayout
    _profile: BrowserProfile
    _uuid: UUID | None = None
    _webpage: WebPage
    _webview: WebView
    _navigation_bar: QToolBar
    _progress_bar: QProgressBar
    _notification_overlay: NotificationOverlay
    about_to_close = Signal(UUID)
    ready = Signal(UUID)

    def __init__(
            self,
            browser_app: "BrowserApp",
            profile: BrowserProfile,
            is_popup: bool = False,
            uuid: UUID | None = None,
            initial_url: QUrl | None = None):
        super().__init__()
        self._browser_app = browser_app
        self._profile = profile
        self._is_popup = is_popup
        self._uuid = uuid
        self._init_actions()
        self._build_layout()
        self._build_navigation_bar()
        self._build_menu_bar()
        self._build_progress_bar()
        self._connect_web_actions()
        self._connect_progress_bar()
        self._connect_downloads()
        self._configure_ui_elements()
        self.update_icon(self._browser_app.default_icon)
        self.set_url(QUrl("quahl://new"))
        # @TODO: Clear last item from history (don't want to be able to go "back" to unloaded state)
        if is_popup:
            self._configure_as_popup()
        if initial_url:
            self.ready.connect(discard_args(partial(self.set_url_clear, initial_url)))

        self._notification_overlay = NotificationOverlay(self)

    def notify(self, icon: QIcon, message: str):
        self._notification_overlay.notify(icon, message)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._notification_overlay._reposition()

    @Slot()
    def _on_first_loaded(self):
        # @BUG: Really weird bug, where the WebPage's loading hangs at 0%
        # if we try to load/setUrl too soon. Around 65ms I start getting
        # inconsistent on/off failures to load, from around 80ms it seems to
        # consistently load. Maybe some background process for the QWebEngine
        # or Chromium stack isn't ready yet (because even when you add a
        # blocking sleep() in-between the delay needed is the same). Might
        # need further debugging and constructing minimal examples to isolate
        # the issue, but 100ms delay seems fairly safe and not super noticable
        # for users at present?
        # Clearly, setHtml works before, so it might be more the network side
        # of things...?
        QTimer.singleShot(100, self, partial(self.ready.emit, self.uuid))

    def _init_actions(self):
        """Initialise the `BrowserWindow`'s QActions."""
        self._action_quit = QAction()
        self._action_quit.setIcon(QIcon.fromTheme("application-exit"))
        self._action_quit.setIconText("Quit")
        self._action_quit.setIconVisibleInMenu(False)
        self._action_quit.setMenuRole(QAction.QuitRole)
        self._action_quit.setShortcut(QKeySequence.Quit)
        self._action_quit.setText("&Quit Quahl")
        self._action_quit.setToolTip("Quit the application")
        self._action_quit.setEnabled(True)
        self._action_quit.triggered.connect(self.browser_app.quit)

        self._action_new = QAction()
        self._action_new.setIcon(QIcon.fromTheme("window-new"))
        self._action_new.setIconText("New")
        self._action_new.setIconVisibleInMenu(False)
        self._action_new.setShortcut(QKeySequence.New)
        self._action_new.setText("&New Window")
        self._action_new.setToolTip("Open a new window")
        self._action_new.setEnabled(True)
        self._action_new.triggered.connect(
            partial(self.browser_app.create_window, show=True, from_window=self)
        )

        self._action_close = QAction()
        self._action_close.setIcon(QIcon.fromTheme("window-close"))
        self._action_close.setIconText("Close")
        self._action_close.setIconVisibleInMenu(False)
        self._action_close.setShortcut(QKeySequence.Close)
        self._action_close.setText("Close &Window")
        self._action_close.setToolTip("Close the current window")
        self._action_close.setEnabled(True)
        self._action_close.triggered.connect(self.close)

        self._action_close_all = QAction()
        self._action_close_all.setIcon(QIcon.fromTheme("window-close"))
        self._action_close_all.setIconText("Close All")
        self._action_close_all.setIconVisibleInMenu(False)
        self._action_close_all.setText("Close All Windows")
        self._action_close_all.setToolTip("Close all windows")
        self._action_close_all.setEnabled(True)
        self._action_close_all.triggered.connect(self.browser_app.close_all_windows)

        self._action_show_downloads = QAction(self)
        self._action_show_downloads.setIcon(Icons.Downloads)
        self._action_show_downloads.setIconText("Downloads")
        self._action_show_downloads.setIconVisibleInMenu(False)
        self._action_show_downloads.setShortcut("Ctrl+Alt+L")
        self._action_show_downloads.setText("Show &Downloads")
        self._action_show_downloads.setToolTip("Open the download manager")
        self._action_show_downloads.setEnabled(True)
        self._action_show_downloads.triggered.connect(self.browser_app.show_downloads)

        self._action_history_back = QAction(self)
        self._action_history_back.setIcon(Icons.Back)
        self._action_history_back.setIconText("Back")
        self._action_history_back.setIconVisibleInMenu(False)
        self._action_history_back.setShortcut(QKeySequence.Back)
        self._action_history_back.setText("&Back")
        self._action_history_back.setToolTip("Go back in history")
        self._action_history_back.setEnabled(False)
        self._action_history_back.triggered.connect(self.history_back)

        self._action_history_forward = QAction(self)
        self._action_history_forward.setIcon(Icons.Forward)
        self._action_history_forward.setIconText("Forward")
        self._action_history_forward.setIconVisibleInMenu(False)
        self._action_history_forward.setShortcut(QKeySequence.Forward)
        self._action_history_forward.setText("&Forward")
        self._action_history_forward.setToolTip("Go forward in history")
        self._action_history_forward.setEnabled(False)
        self._action_history_forward.triggered.connect(self.history_forward)

        self._action_stop_reload = QAction(self)
        self._action_stop_reload.setIcon(Icons.Reload)
        self._action_stop_reload.setIconText("Reload")
        self._action_stop_reload.setIconVisibleInMenu(False)
        self._action_stop_reload.setShortcut(QKeySequence.Refresh)
        self._action_stop_reload.setText("&Reload")
        self._action_stop_reload.setToolTip("Reload the current view")
        self._action_stop_reload.triggered.connect(self.stop_reload)
        self._action_stop_reload.setEnabled(False)

    def _build_layout(self):
        """Build the `BrowserWindow`'s Qt layout."""
        # Central Widget
        central_widget = QWidget(self)
        self._layout = QVBoxLayout(central_widget)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._webview = WebView(self)
        self._webpage = WebPage(self._profile, self._webview)
        connect_once(self._webpage.loadFinished, discard_args(self._on_first_loaded))
        self._webview.setPage(self._webpage)
        self._webview.urlChanged.connect(self.update_url_edit)
        self._webview.titleChanged.connect(self.update_title)
        self._webview.iconChanged.connect(self.update_icon)
        self._layout.addWidget(self._webview)
        self.setCentralWidget(central_widget)

    def _build_menu_bar(self):
        """Build the `BrowserWindow`'s menu bar."""
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self._action_new)
        file_menu.addAction(self._action_close)
        file_menu.addAction(self._action_close_all)
        file_menu.addSeparator()
        file_menu.addAction(self._action_quit)

        nav_menu = self.menuBar().addMenu("&Navigation")
        nav_menu.addAction(self._action_history_back)
        nav_menu.addAction(self._action_history_forward)
        nav_menu.addAction(self._action_stop_reload)
        nav_menu.addSeparator()

        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self._action_show_downloads)
        view_menu.addSeparator()

    def _build_navigation_bar(self):
        """Build the `BrowserWindow`'s navigation bar."""
        toolbar = QToolBar("Navigation")
        toolbar.setMovable(False)
        toolbar.toggleViewAction().setEnabled(False)

        toolbar.addAction(self._action_history_back)
        toolbar.addAction(self._action_history_forward)
        toolbar.addAction(self._action_stop_reload)

        self._url_edit = UrlEdit(self)
        self._url_edit.url_entered.connect(self.load_from_url_edit)
        self._url_edit_action = toolbar.addWidget(self._url_edit)

        toolbar.addAction(self._action_show_downloads)

        self._navigation_bar = toolbar
        self.addToolBar(self._navigation_bar)
        self.setUnifiedTitleAndToolBarOnMac(True)

    def _build_progress_bar(self):
        progress_bar = QProgressBar(self)
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        progress_bar.setTextVisible(False)
        progress_bar.setMaximumHeight(3)
        progress_bar.setStyleSheet(
            "QProgressBar { border: none; background-color: rgba(0, 0, 0, 0%); }\n"
            "QProgressBar::chunk { background: #2f80ed; }"
        )
        self._layout.addWidget(progress_bar)
        self._progress_bar = progress_bar

    def _connect_progress_bar(self):
        self._webpage.loadProgress.connect(self._progress_bar.setValue)
        self._webpage.loadFinished.connect(self._progress_bar.reset)

    def _configure_ui_elements(self):
        self.menuBar().setVisible(self._profile.settings.menu_bar_show)
        self._navigation_bar.setVisible(self._profile.settings.navigation_bar_show)
        self._action_history_back.setVisible(self._profile.settings.navigation_back_show)
        self._action_history_forward.setVisible(self._profile.settings.navigation_forward_show)
        self._action_stop_reload.setVisible(self._profile.settings.navigation_stop_reload_show)
        self._action_show_downloads.setVisible(self._profile.settings.navigation_downloads_show)
        self._url_edit_action.setEnabled(self._profile.settings.navigation_url_editable)
        self._url_edit_action.setVisible(self._profile.settings.navigation_url_show)

    def _configure_as_popup(self):
        # Override only definite changes compared to normal UI, leave rest as per
        # profile/settings for normal browser window.
        self._action_history_back.setVisible(False)
        self._action_history_forward.setVisible(False)
        self._action_stop_reload.setVisible(False)
        self._action_show_downloads.setVisible(False)
        self._url_edit_action.setEnabled(False)

    def _connect_web_actions(self):
        """Connect to change signals for Back, Forward, Stop and Reload WebActions."""
        back_action = self._webpage.action(QWebEnginePage.Back)
        back_action.changed.connect(self._web_action_back_changed)
        forward_action = self._webpage.action(QWebEnginePage.Forward)
        forward_action.changed.connect(self._web_action_forward_changed)
        stop_action = self._webpage.action(QWebEnginePage.Stop)
        stop_action.changed.connect(self._web_action_stop_reload_changed)
        reload_action = self._webpage.action(QWebEnginePage.Reload)
        reload_action.changed.connect(self._web_action_stop_reload_changed)
        # self._webview.devtools_requested.connect(self._launch_devtools)

    def _connect_downloads(self):
        self._profile.downloadRequested.connect(
            self._browser_app.download_manager_model.handle_download_request
        )
        self._profile.downloadRequested.connect(
            discard_args(self._browser_app.show_downloads)
        )

    @property
    def browser_app(self) -> "BrowserApp":
        """Return the managing `BrowserApp` instance."""
        return self._browser_app

    @property
    def dev_tool_window(self) -> bool:
        """Return whether this is a dev tool window or not."""
        return self._dev_tool_window

    @property
    def layout(self) -> QVBoxLayout:
        """Return the `BrowserWindow`'s main QVBoxLayout."""
        return self.layout()

    @property
    def profile(self) -> BrowserProfile:
        """Return the `BrowserWindow`'s profile."""
        return self._profile

    @property
    def url_edit(self) -> UrlEdit:
        """Return the window's URL line edit widget."""
        return self._url_edit

    @property
    def uuid(self) -> UUID | None:
        """Return the `BrowserWindow`'s UUID (if it has one)."""
        return self._uuid

    @property
    def webpage(self) -> WebPage:
        """Return the `BrowserWindow`'s `WebPage`."""
        return self._webpage

    @property
    def webview(self) -> WebView:
        """Return the `BrowserWindow`'s `WebView`."""
        return self._webview

    def web_action_enabled(self, action: QWebEnginePage.WebAction) -> bool:
        """Check whether the specified `WebAction` is enabled."""
        return self._webpage.action(action).isEnabled()

    @Slot()
    def _web_action_back_changed(self):
        self._action_history_back.setEnabled(self.web_action_enabled(QWebEnginePage.Back))

    @Slot()
    def _web_action_forward_changed(self):
        self._action_history_forward.setEnabled(self.web_action_enabled(QWebEnginePage.Forward))

    @Slot()
    def _web_action_stop_reload_changed(self):
        if self.web_action_enabled(QWebEnginePage.Stop):
            self._action_stop_reload.setIcon(Icons.Stop)
            self._action_stop_reload.setIconText("Stop")
            self._action_stop_reload.setShortcut(QKeySequence.Cancel)
            self._action_stop_reload.setText("&Stop loading")
            self._action_stop_reload.setToolTip("Stop loading the current view")
            self._action_stop_reload.setEnabled(True)
            return
        self._action_stop_reload.setIcon(Icons.Reload)
        self._action_stop_reload.setIconText("Reload")
        self._action_stop_reload.setShortcut(QKeySequence.Refresh)
        self._action_stop_reload.setText("&Reload")
        self._action_stop_reload.setToolTip("Reload the current view")
        if self.web_action_enabled(QWebEnginePage.Reload):
            self._action_stop_reload.setEnabled(True)
            return
        self._action_stop_reload.setEnabled(False)

    @Slot()
    def history_back(self):
        self._webpage.triggerAction(QWebEnginePage.Back)

    @Slot()
    def history_forward(self):
        self._webpage.triggerAction(QWebEnginePage.Forward)

    @Slot()
    def stop_reload(self):
        if self.web_action_enabled(QWebEnginePage.Stop):
            self._webpage.triggerAction(QWebEnginePage.Stop)
            return
        self._webpage.triggerAction(QWebEnginePage.Reload)

    @Slot()
    def update_url_edit(self, override: str | None = None):
        if isinstance(override, str):
            self._url_edit.setText(override)
            return
        url = self.webview.url().url()
        if url == "quahl://new":
            url = ""
        self._url_edit.setText(url)

    @Slot()
    def update_title(self, title: str):
        self.setWindowTitle(title)

    @Slot()
    def update_icon(self, icon: QIcon):
        url_str = self._webpage.url().toDisplayString()
        if url_str.startswith("view-source:"):
            icon = Icons.CodeHost
        elif url_str.startswith("devtools://"):
            icon = Icons.CliHost
        if icon.isNull():
            icon = self._browser_app.default_icon
        self.setWindowIcon(icon)

    @Slot(QUrl)
    def load_from_url_edit(self, url: QUrl):
        # Reject if empty
        if url.isEmpty():
            return
        self.set_url(url)

    def closeEvent(self, event: QEvent):
        event.accept()
        self.about_to_close.emit(self._uuid)
        self.deleteLater()

    def set_url(self, url: QUrl):
        if url.isEmpty() or url.url() == "quahl://new":
            self.webview.setHtml(NEW_WINDOW_PAGE_HTML, "quahl://new")
            return
        self.webview.setUrl(url)
        self.webview.setFocus()

    def set_url_clear(self, url: QUrl):
        """Convenience method that sets the URL *and* clears the history."""
        self.set_url(url)
        connect_once(self._webpage.loadFinished, discard_args(self._webpage.history().clear))
