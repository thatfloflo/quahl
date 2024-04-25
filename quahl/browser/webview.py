from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QAction, QContextMenuEvent

from typing import Self, TYPE_CHECKING

from .resources import OutlineIcons

if TYPE_CHECKING:
    from .window import BrowserWindow


class WebView(QWebEngineView):

    devtools_requested: Signal = Signal(QWebEnginePage)
    _context_menu_actions_ready: Signal = Signal()
    _context_menu_actions: dict[QWebEnginePage.WebAction, QAction] = dict()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._context_menu_actions_ready.connect(self._style_context_menu_actions)

    def contextMenuEvent(self, event: QContextMenuEvent):
        if not self.page().profile().settings.allow_context_menu:
            return
        menu = self.createStandardContextMenu()
        if True or not self._context_menu_actions:
            self._grab_context_menu_actions()
        webactions = self._context_menu_actions
        menu_actions = menu.actions()
        if webactions[QWebEnginePage.OpenLinkInNewTab] in menu_actions:
            menu.removeAction(webactions[QWebEnginePage.OpenLinkInNewTab])
        if webactions[QWebEnginePage.InspectElement] not in menu_actions:
            if menu_actions and menu_actions[-1] is not webactions[QWebEnginePage.ViewSource]:
                menu.addSeparator()
            menu.addAction(webactions[QWebEnginePage.InspectElement])
            webactions[QWebEnginePage.InspectElement].triggered.connect(
                self._emit_devtools_requested
            )
        menu.popup(event.globalPos())

    @Slot()
    def _emit_devtools_requested(self):
        self.devtools_requested.emit(self.page())

    def _grab_context_menu_actions(self):
        webactions = [
            QWebEnginePage.Cut,
            QWebEnginePage.Copy,
            QWebEnginePage.Paste,
            QWebEnginePage.Undo,
            QWebEnginePage.Redo,
            QWebEnginePage.Back,
            QWebEnginePage.Forward,
            QWebEnginePage.Reload,
            QWebEnginePage.OpenLinkInThisWindow,
            QWebEnginePage.OpenLinkInNewWindow,
            QWebEnginePage.OpenLinkInNewTab,
            QWebEnginePage.OpenLinkInNewBackgroundTab,
            QWebEnginePage.CopyLinkToClipboard,
            QWebEnginePage.CopyImageToClipboard,
            QWebEnginePage.CopyImageUrlToClipboard,
            QWebEnginePage.CopyMediaUrlToClipboard,
            QWebEnginePage.ToggleMediaControls,
            QWebEnginePage.ToggleMediaLoop,
            QWebEnginePage.DownloadLinkToDisk,
            QWebEnginePage.DownloadImageToDisk,
            QWebEnginePage.DownloadMediaToDisk,
            QWebEnginePage.InspectElement,
            QWebEnginePage.SavePage,
            QWebEnginePage.ViewSource,
        ]
        page = self.page()
        for webaction in webactions:
            self._context_menu_actions[webaction] = page.action(webaction)
        self._context_menu_actions_ready.emit()

    @Slot()
    def _style_context_menu_actions(self):
        webactions = self._context_menu_actions
        webactions[QWebEnginePage.Cut].setIcon(OutlineIcons.Cut)
        webactions[QWebEnginePage.Copy].setIcon(OutlineIcons.Copy)
        webactions[QWebEnginePage.Paste].setIcon(OutlineIcons.Paste)
        webactions[QWebEnginePage.Undo].setIcon(OutlineIcons.Undo)
        webactions[QWebEnginePage.Redo].setIcon(OutlineIcons.Redo)
        webactions[QWebEnginePage.Back].setIcon(OutlineIcons.Back)
        webactions[QWebEnginePage.Forward].setIcon(OutlineIcons.Forward)
        webactions[QWebEnginePage.Reload].setIcon(OutlineIcons.Reload)
        webactions[QWebEnginePage.OpenLinkInThisWindow].setIcon(OutlineIcons.OpenIntern)
        webactions[QWebEnginePage.OpenLinkInNewWindow].setIcon(OutlineIcons.OpenExtern)
        webactions[QWebEnginePage.CopyLinkToClipboard].setIcon(OutlineIcons.CopyLink)
        webactions[QWebEnginePage.CopyImageToClipboard].setIcon(OutlineIcons.CopyFile)
        webactions[QWebEnginePage.CopyImageUrlToClipboard].setIcon(OutlineIcons.CopyLink)
        webactions[QWebEnginePage.CopyMediaUrlToClipboard].setIcon(OutlineIcons.CopyLink)
        webactions[QWebEnginePage.ToggleMediaControls].setIcon(OutlineIcons.Controls)
        webactions[QWebEnginePage.ToggleMediaLoop].setIcon(OutlineIcons.Loop)
        webactions[QWebEnginePage.DownloadLinkToDisk].setIcon(OutlineIcons.Save)
        webactions[QWebEnginePage.DownloadImageToDisk].setIcon(OutlineIcons.Save)
        webactions[QWebEnginePage.DownloadMediaToDisk].setIcon(OutlineIcons.Save)
        webactions[QWebEnginePage.InspectElement].setIcon(OutlineIcons.Inspect)
        webactions[QWebEnginePage.SavePage].setIcon(OutlineIcons.Save)
        webactions[QWebEnginePage.ViewSource].setIcon(OutlineIcons.Code)

    def createWindow(self, type: QWebEnginePage.WebWindowType) -> Self | None:
        main_window: "BrowserWindow" | None = self.window()
        if not main_window:
            return None

        if type == QWebEnginePage.WebBrowserTab:
            print("New Tab requested")
            return main_window.browser_app.create_window(
                show=True,
                from_window=self.window()
            ).webview

        if type == QWebEnginePage.WebBrowserBackgroundTab:
            print("New Background Tab requested")
            return main_window.browser_app.create_window(
                show=True,
                background=True,
                from_window=self.window()
            ).webview

        if type == QWebEnginePage.WebBrowserWindow:
            print("New Window requested")
            return main_window.browser_app.create_window(
                show=True,
                from_window=self.window()
            ).webview

        if type == QWebEnginePage.WebDialog:
            print("New Dialog requested")
            return main_window.browser_app.create_window(
                show=True,
                from_window=self.window(),
                is_popup=True
            ).webview

        return None
