from pathlib import Path
import platform
import subprocess
import math
from functools import wraps
from typing import Callable, Any

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import Signal, Slot, QRect


class ClickableQWidget(QWidget):

    clicked: Signal = Signal(QWidget)
    __mouse_pressed: bool = False

    def mousePressEvent(self, event: QMouseEvent):
        super().mousePressEvent(event)
        self._mouse_pressed = True

    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)
        click_pos = event.position()
        # Attn: Click poss on release might be outside the widget boundaries!
        if (self._mouse_pressed
                and click_pos.x() > 0 and click_pos.y() > 0
                and click_pos.y() < self.height()
                and click_pos.x() < self.width()):
            self.clicked.emit(self)
        self._mouse_pressed = False


def connect_once(signal: Signal, slot: Slot):
    @wraps(slot)
    def wrapper(*args, **kwargs):
        signal.disconnect(wrapper)
        return slot(*args, **kwargs)
    signal.connect(wrapper)
    return wrapper


def discard_args(f: Callable[..., Any]):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f()
    return wrapper


def qrect_to_tuple(qrect: QRect) -> tuple[int, int, int, int]:
    """Turns a `QRect` into a `tuple` of the form *(x, y, width, height)*."""
    return (qrect.x(), qrect.y(), qrect.width(), qrect.height())


def squish_string(
        s: str,
        max_len: int,
        leave_left: int | None = None,
        leave_right: int | None = None,
        ellipsis: str = "…") -> str:
    """Squish string *s* to be *max_len*.

    IMPORTANT: Only central squishing currently implemented. Does not run with leave_left or
    leave_right yet!

    The squished string will minimally leave *leave_left* and *leave_right* characters in tact.
    If either of *leave_left* or *leave_right* is `None`, the result will be tilted toward the
    non-`None` side. If both are `None`, it will be (approximately) centered.

    *ellipsis* specifies a string to be inserted at the site of squishing.

    Raises `ValueError` if the sums of *leave_left*, *leave_right* and `len(ellipsis)` make
    squishing impossible.

    Returns the string as is if it is shorter or equal to *max_len*.
    """
    el_len = len(ellipsis)
    if leave_left or leave_right:
        min_len = (leave_left or 0) + (leave_right or 0) + el_len
        if min_len > max_len:
            ValueError(
                "Cannot squish with sum of leave_left, "
                "leave_right and len(ellipsis) exceeding max_len"
            )
    s_len = len(s)
    if s_len <= max_len:
        return s
    if not leave_left and not leave_right:
        # Squish as centrally as possible
        if s_len % 2 == 0:
            left_len = right_len = int(s_len / 2)
        else:
            left_len = math.floor(s_len / 2)
            right_len = math.ceil(s_len / 2)
        if el_len % 2 == 0:
            remove_left = remove_right = int(el_len / 2)
        else:
            remove_left = math.floor(el_len / 2)
            remove_right = math.ceil(el_len / 2)
        overflow = s_len - max_len
        if overflow % 2 == 0:
            remove_left += int(overflow / 2)
            remove_right += int(overflow / 2)
        else:
            remove_left += math.floor(overflow / 2)
            remove_right += math.ceil(overflow / 2)
        s_left = s[0:(left_len - remove_left)]
        s_right = s[(right_len + remove_right):]
        return f"{s_left}{ellipsis}{s_right}"
    raise NotImplementedError


def show_in_file_manager(path: Path) -> bool:
    if not path.exists():
        return False
    is_file = True if path.is_file() else False
    if platform.system() == "Windows":
        # Launch explorer.exe
        if is_file:
            path = str(path)
            if '"' in path or "^" in path:
                return False  # Not safe, and not allowed in Windows paths either
            subprocess.run(f'explorer /select,"{path}"')
        else:
            subprocess.run(["explorer", f"{path}\\"])
        return True
    if platform.system() == "Darwin":
        if is_file:
            subprocess.run(["open", "-R", str(path)])
        else:
            subprocess.run(["open", str(path)])
    else:
        try:
            if is_file:
                result = subprocess.run([
                    "dbus-send",
                    "--print-reply",
                    "--dest=org.freedesktop.FileManager1",
                    "/org/freedesktop/FileManager1",
                    "org.freedesktop.FileManager1.ShowFolders",
                    f"array:string:'file://{path.absolute()}'",
                    "string:''"
                ])
            else:
                result = subprocess.run([
                    "dbus-send",
                    "--print-reply",
                    "--dest=org.freedesktop.FileManager1",
                    "/org/freedesktop/FileManager1",
                    "org.freedesktop.FileManager1.ShowItems",
                    f"array:string:'file://{path.absolute()}'",
                    "string:''"
                ])
            if result.returncode:
                raise FileNotFoundError(
                    "Failed to execute method call for 'org.freedesktop.FileManager1' via dbus"
                )
            return True
        except FileNotFoundError:
            pass
        try:
            if path.is_file:
                subprocess.Popen(
                    ["nautilus", "-s", str(path)],
                    start_new_session=True,
                    stdout=subprocess.DEVNULL
                )
            else:
                subprocess.Popen(
                    ["nautilus", str(path)],
                    start_new_session=True,
                    stdout=subprocess.DEVNULL
                )
            return True
        except FileNotFoundError:
            pass
        try:
            if path.is_file:
                path = path.absolute().parent  # gio can't point to files
            result = subprocess.run(["gio", "open", f"file://{path}/"])
            if result.returncode:
                raise FileNotFoundError(
                    "Failed to open folder with 'gio'"
                )
            return True
        except FileNotFoundError:
            pass
        try:
            if path.is_file:
                path = path.absolute().parent  # xdg-open can't point to files
            subprocess.Popen(
                ["xdg-open", f"file://{path}"],
                start_new_session=True,  # may not detach itself based on local binaries
                stdout=subprocess.DEVNULL,
            )
            return True
        except FileNotFoundError:
            pass
    return False
