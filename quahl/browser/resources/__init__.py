from importlib import resources
from typing import Final

from PySide6.QtGui import QIcon

NEW_WINDOW_PAGE_HTML: Final[str] = resources.read_text(__package__, "new_window_page.html")


def load_icon(icon_name: str) -> QIcon:
    icon = QIcon()
    with resources.path(__package__, f"icon_{icon_name}_colour.svg") as path:
        icon.addFile(str(path))
    with resources.path(__package__, f"icon_{icon_name}_grey.svg") as path:
        icon.addFile(str(path), mode=QIcon.Disabled)
    return icon


def load_icon_outline(icon_name: str) -> QIcon:
    icon = QIcon()
    with resources.path(__package__, f"icon_{icon_name}_outline.svg") as path:
        icon.addFile(str(path))
    with resources.path(__package__, f"icon_{icon_name}_outline50.svg") as path:
        icon.addFile(str(path), mode=QIcon.Disabled)
    return icon


class Icons:

    Back: QIcon = load_icon("arrow-lg-left")
    Browser: QIcon = load_icon("quahl")
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
    File: QIcon = load_icon("file")
    Folder: QIcon = load_icon("folder")
    FolderOpen: QIcon = load_icon("folder-open")
    Forward: QIcon = load_icon("arrow-lg-right")
    Link: QIcon = load_icon("link")
    Loop: QIcon = load_icon("repeat")
    OpenExtern: QIcon = load_icon("arrow-external-diag")
    OpenIntern: QIcon = load_icon("arrow-level-diag")
    Paste: QIcon = load_icon("paste")
    Redo: QIcon = load_icon("arrow-u-turn-right")
    Reload: QIcon = load_icon("arrows-round")
    Remove: QIcon = load_icon("x")
    Repeat: QIcon = load_icon("repeat")
    Save: QIcon = load_icon("save")
    Stop: QIcon = load_icon("stop-hand")
    Undo: QIcon = load_icon("arrow-u-turn-left")
    Unlink: QIcon = load_icon("unlink")


class OutlineIcons:

    Back: QIcon = load_icon_outline("arrow-lg-left")
    Browser: QIcon = load_icon_outline("quahl")
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
    File: QIcon = load_icon_outline("file")
    Folder: QIcon = load_icon_outline("folder")
    FolderOpen: QIcon = load_icon_outline("folder-open")
    Forward: QIcon = load_icon_outline("arrow-lg-right")
    Link: QIcon = load_icon_outline("link")
    Loop: QIcon = load_icon_outline("repeat")
    OpenExtern: QIcon = load_icon_outline("arrow-external-diag")
    OpenIntern: QIcon = load_icon_outline("arrow-level-diag")
    Paste: QIcon = load_icon_outline("paste")
    Redo: QIcon = load_icon_outline("arrow-u-turn-right")
    Reload: QIcon = load_icon_outline("arrows-round")
    Remove: QIcon = load_icon_outline("x")
    Repeat: QIcon = load_icon_outline("repeat")
    Save: QIcon = load_icon_outline("save")
    Stop: QIcon = load_icon_outline("stop-hand")
    Undo: QIcon = load_icon_outline("arrow-u-turn-left")
    Unlink: QIcon = load_icon_outline("unlink")
