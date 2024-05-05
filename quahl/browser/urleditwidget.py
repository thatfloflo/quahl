from PySide6.QtCore import Qt, QObject, Signal, Slot, QTimer, QUrl
from PySide6.QtGui import QFocusEvent, QGuiApplication
from PySide6.QtWidgets import QLineEdit, QCompleter

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
        style_hints = QGuiApplication.styleHints()
        style_hints.colorSchemeChanged.connect(self._handle_color_scheme_changed)
        self.returnPressed.connect(self._handle_return_pressed)
        self.textChanged.connect(self._handle_text_changed)
        self.textEdited.connect(self._handle_text_edited)

        url_list = [
            "https://www.google.com",
            "https://www.florian.me.uk/",
            "https://github.com/thatfloflo/quahl/",
        ]
        self._completer = QCompleter(url_list, self)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchContains)
        self.setCompleter(self._completer)

    @Slot()
    def _handle_color_scheme_changed(self):
        self.setStyleSheet(self.styleSheet())

    @Slot()
    def _handle_palette_change2(self):
        print("Pallette change 2 handler!")


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

    # def changeEvent(self, event: QEvent):
    #     if event.type() == QEvent.ApplicationPaletteChange:
    #         print("AppPalChange on UrlLineEdit")
    #         self.setStyleSheet(self.styleSheet())
    #     super().changeEvent(event)
        