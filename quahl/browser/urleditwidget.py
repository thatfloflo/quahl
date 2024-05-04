from PySide6.QtCore import QObject, Signal, Slot, QTimer, QUrl
from PySide6.QtGui import QFocusEvent
from PySide6.QtWidgets import QLineEdit


class UrlEdit(QLineEdit):

    url_entered: Signal = Signal(QUrl)
    _user_editing_in_progress: bool = False

    def __init__(self, contents: str | None = None, parent: QObject | None = None):
        if contents is None:
            super().__init__(parent)
        else:
            super().__init__(contents, parent)
        self.setClearButtonEnabled(True)
        self.setStyleSheet("""
            QLineEdit {
                border-radius: 5px;
                padding: 4px;
                margin: 4px;
            }
            QLineEdit:focus {
                margin: 1px;
                border: 3px solid palette(highlight);
            }
        """)
        self.returnPressed.connect(self._handle_return_pressed)
        self.textChanged.connect(self._handle_text_changed)
        self.textEdited.connect(self._handle_text_edited)

    def focusInEvent(self, event: QFocusEvent):
        if not self._user_editing_in_progress:
            QTimer.singleShot(0, self, self.selectAll)
        super().focusInEvent(event)

    def focusOutEvent(self, event: QFocusEvent):
        if not self._user_editing_in_progress:
            self._reset_view()
        super().focusOutEvent(event)

    @Slot()
    def _handle_text_edited(self):
        self._user_editing_in_progress = True

    @Slot()
    def _handle_return_pressed(self):
        url = QUrl.fromUserInput(self.text())
        self.url_entered.emit(url)
        self._reset_view()

    @Slot()
    def _handle_text_changed(self):
        if not self.hasFocus():
            # Text was changed programmatically
            self._reset_view()

    def _reset_view(self):
        self._user_editing_in_progress = False
        self.setCursorPosition(0)
        