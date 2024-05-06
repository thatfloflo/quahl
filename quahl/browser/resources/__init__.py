from importlib import resources
from typing import Final
from copy import copy

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon, QGuiApplication

NEW_WINDOW_PAGE_HTML: Final[str] = resources.read_text(__package__, "new_window_page.html")


class InvertableIcon(QIcon):

    _light: QIcon
    _dark: QIcon
    _active_color_scheme: Qt.ColorScheme

    def __init__(self, light_icon: QIcon, dark_icon: QIcon):
        super().__init__()
        self._light = light_icon
        self._dark = dark_icon
        style_hints = QGuiApplication.styleHints()
        style_hints.colorSchemeChanged.connect(self._handle_color_scheme_changed)
        self._active_color_scheme = style_hints.colorScheme()
        self.update_active_icon()

    def get_light_variant(self) -> QIcon:
        return self._light

    def get_dark_variant(self) -> QIcon:
        return self._dark

    def set_light_variant(self, icon: QIcon):
        self._light = icon
        self.update_active_icon()

    def set_dark_variant(self, icon: QIcon):
        self._dark = icon
        self.update_active_icon()

    def update_active_icon(self):
        if self._active_color_scheme == Qt.Dark:
            self.swap(copy(self._dark))
        else:
            self.swap(copy(self._light))

    @Slot()
    def _handle_color_scheme_changed(self):
        style_hints = QGuiApplication.styleHints()
        self._active_color_scheme = style_hints.colorScheme()
        self.update_active_icon()


def load_icon(icon_name: str) -> QIcon:
    icon = QIcon()
    with resources.path(__package__, f"icon_{icon_name}_colour.svg") as path:
        icon.addFile(str(path))
    with resources.path(__package__, f"icon_{icon_name}_grey.svg") as path:
        icon.addFile(str(path), mode=QIcon.Disabled)
    return icon


def load_icon_outline(icon_name: str) -> QIcon:
    light = QIcon()
    dark = QIcon()
    with resources.path(__package__, f"icon_{icon_name}_outline.svg") as path:
        light.addFile(str(path))
    with resources.path(__package__, f"icon_{icon_name}_outline_d.svg") as path:
        dark.addFile(str(path))
    with resources.path(__package__, f"icon_{icon_name}_outline50.svg") as path:
        light.addFile(str(path), mode=QIcon.Disabled)
    with resources.path(__package__, f"icon_{icon_name}_outline50_d.svg") as path:
        dark.addFile(str(path), mode=QIcon.Disabled)
    icon = InvertableIcon(light, dark)
    return icon


class Icons:

    Back: QIcon = load_icon("arrow-lg-left")
    Browser: QIcon = load_icon("quahl")
    Certificate: QIcon = load_icon("scroll")
    CertificateWarning: QIcon = load_icon("scroll-exclamation")
    Clear: QIcon = load_icon("x")
    Cli: QIcon = load_icon("cli")
    CliHost: QIcon = load_icon("cli-laptop")
    Code: QIcon = load_icon("code")
    CodeHost: QIcon = load_icon("code-laptop")
    Controls: QIcon = load_icon("sliders")
    Copy: QIcon = load_icon("copy")
    CopyFile: QIcon = load_icon("copy-file")
    CopyLink: QIcon = load_icon("copy-link")
    Crash: QIcon = load_icon("car-crash")
    Cut: QIcon = load_icon("scissors-open")
    Delete: QIcon = load_icon("trash")
    Download: QIcon = load_icon("arrow-end-down")
    Downloads: QIcon = load_icon("arrow-solid-bracket-end-down")
    Edit: QIcon = load_icon("edit")
    Error: QIcon = load_icon("x-circle")
    File: QIcon = load_icon("file")
    Folder: QIcon = load_icon("folder")
    FolderOpen: QIcon = load_icon("folder-open")
    Forward: QIcon = load_icon("arrow-lg-right")
    Information: QIcon = load_icon("info-circle")
    Link: QIcon = load_icon("link")
    Loop: QIcon = load_icon("repeat")
    MediaPause: QIcon = load_icon("pause-circle")
    MediaPlay: QIcon = load_icon("play-circle")
    MediaStop: QIcon = load_icon("stop-circle")
    OpenExtern: QIcon = load_icon("arrow-external-diag")
    OpenIntern: QIcon = load_icon("arrow-level-diag")
    Paste: QIcon = load_icon("paste")
    Question: QIcon = load_icon("question-circle")
    Redo: QIcon = load_icon("arrow-u-turn-right")
    Reload: QIcon = load_icon("arrows-round")
    Remove: QIcon = load_icon("x")
    Repeat: QIcon = load_icon("repeat")
    Save: QIcon = load_icon("save")
    Stop: QIcon = load_icon("stop-hand")
    Undo: QIcon = load_icon("arrow-u-turn-left")
    Unlink: QIcon = load_icon("unlink")
    Warning: QIcon = load_icon("exclamation-triangle")


class OutlineIcons:

    Back: QIcon = load_icon_outline("arrow-lg-left")
    Browser: QIcon = load_icon_outline("quahl")
    Certificate: QIcon = load_icon_outline("scroll")
    CertificateWarning: QIcon = load_icon_outline("scroll-exclamation")
    Clear: QIcon = load_icon_outline("x")
    Cli: QIcon = load_icon_outline("cli")
    CliHost: QIcon = load_icon_outline("cli-laptop")
    Code: QIcon = load_icon_outline("code")
    CodeHost: QIcon = load_icon_outline("code-laptop")
    Controls: QIcon = load_icon_outline("sliders")
    Copy: QIcon = load_icon_outline("copy")
    CopyFile: QIcon = load_icon_outline("copy-file")
    CopyLink: QIcon = load_icon_outline("copy-link")
    Crash: QIcon = load_icon_outline("car-crash")
    Cut: QIcon = load_icon_outline("scissors-open")
    Delete: QIcon = load_icon_outline("trash")
    Download: QIcon = load_icon_outline("arrow-end-down")
    Downloads: QIcon = load_icon_outline("arrow-solid-bracket-end-down")
    Edit: QIcon = load_icon_outline("edit")
    Error: QIcon = load_icon_outline("x-circle")
    File: QIcon = load_icon_outline("file")
    Folder: QIcon = load_icon_outline("folder")
    FolderOpen: QIcon = load_icon_outline("folder-open")
    Forward: QIcon = load_icon_outline("arrow-lg-right")
    Information: QIcon = load_icon_outline("info-circle")
    Link: QIcon = load_icon_outline("link")
    Loop: QIcon = load_icon_outline("repeat")
    MediaPause: QIcon = load_icon_outline("pause-circle")
    MediaPlay: QIcon = load_icon_outline("play-circle")
    MediaStop: QIcon = load_icon_outline("stop-circle")
    OpenExtern: QIcon = load_icon_outline("arrow-external-diag")
    OpenIntern: QIcon = load_icon_outline("arrow-level-diag")
    Paste: QIcon = load_icon_outline("paste")
    Question: QIcon = load_icon_outline("question-circle")
    Redo: QIcon = load_icon_outline("arrow-u-turn-right")
    Reload: QIcon = load_icon_outline("arrows-round")
    Remove: QIcon = load_icon_outline("x")
    Repeat: QIcon = load_icon_outline("repeat")
    Save: QIcon = load_icon_outline("save")
    Stop: QIcon = load_icon_outline("stop-hand")
    Undo: QIcon = load_icon_outline("arrow-u-turn-left")
    Unlink: QIcon = load_icon_outline("unlink")
    Warning: QIcon = load_icon_outline("exclamation-triangle")
