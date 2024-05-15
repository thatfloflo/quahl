from pathlib import Path
import platform
import subprocess
import math
import enum
import sys
from functools import wraps
from typing import Callable, Any, Self

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import Signal, Slot, QRect


class OS(enum.IntFlag):
    """Enum for basic operating system information."""

    UNKNOWN = enum.auto()
    WINDOWS = enum.auto()
    LINUX = enum.auto()
    MACOS = enum.auto()

    BIT_WIDTH_32 = enum.auto()
    BIT_WIDTH_64 = enum.auto()

    @classmethod
    def __detect_os(cls):
        sname = platform.system()
        if sname == "Windows":
            cls._detected_os = cls.WINDOWS
        elif sname == "Linux":
            cls._detected_os = cls.LINUX
        elif sname == "Darwin":
            cls._detected_os = cls.MACOS
        else:
            cls._detected_os = cls.UNKNOWN

    @classmethod
    def __detect_bit_width(cls):
        if sys.maxsize > 2**32:
            cls._detected_bit_width = cls.BIT_WIDTH_64
        else:
            cls._detected_bit_width = cls.BIT_WIDTH_32

    @classmethod
    def detected(cls) -> Self:
        """Returns the host's detected operating system and bit width.

        The host's operating system is detected based on the value returned
        by the built-in :code:`platform.system()` call. Bit width is determined
        by testing whether :code:`sys.maxsize` exceeds 2^32.

        Use bitwise-and :code:`&` or the :code:`in` operator to test an `OS`
        enum value with the returned value.
        For example::

            if OS.detected() & OS.MACOS:
                print("You're the apple of my eye!")
            elif OS.detected() & OS.WINDOWS:
                print("Who drew the curtains?")

        This is the same as::

            if OS.MACOS in OS.detected():
                print("You're the apple of my eye!")
            elif OS.WINDOWS in OS.detected():
                print("Who drew the curtains?")
        """
        if not hasattr(cls, "_detected_os"):
            cls.__detect_os()
        if not hasattr(cls, "_detected_bit_width"):
            cls.__detect_bit_width()
        return cls._detected_os | cls._detected_bit_width


class ClickableQWidget(QWidget):
    """Utility `QWidget`-wrapper which emits a `clicked` signal on mouse clicks.

    This widget can be inherited by other widgets, or used as a wrapper widget,
    to become sensitive to mouse click events. If a mouse click is detected on
    the (wrapped) widget, the `ClickableQWidget.clicked` signal is emitted.
    """

    #: Signal emitted when a mous click is detected anywhere on the wrapped widget.
    clicked: Signal = Signal(QWidget)
    __mouse_pressed: bool = False

    def mousePressEvent(self, event: QMouseEvent):
        """Listener for mouse press events.

        Internally records when a mouse press event is recorded anywhere on the
        (wrapped) widget.
        """
        super().mousePressEvent(event)
        self._mouse_pressed = True

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Listener for mouse release events.

        Intercepts mouse release events and then checkes whether the mouse was
        released within the bounds of the (wrapped) widget, and also whether
        the original click occured within the bounds of the (wrapped) widget.

        If both conditions have been met, it emits the `clicked` signal,
        otherwise it resets the click-tracking state of the (wrapped) widget
        without emitting the `clicked` signal.
        """
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
    if OS.detected() == OS.WINDOWS:
        # Launch explorer.exe
        if is_file:
            path = str(path)
            if '"' in path or "^" in path:
                return False  # Not safe, and not allowed in Windows paths either
            subprocess.run(f'explorer /select,"{path}"')
        else:
            subprocess.run(["explorer", f"{path}\\"])
        return True
    if OS.detected() == OS.MACOS:
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
