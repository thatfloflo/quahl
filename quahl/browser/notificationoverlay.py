from PySide6.QtCore import Qt, Slot, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect, QHBoxLayout, QVBoxLayout, QWidget, QFrame, QLabel,
    QSizePolicy, QToolBar
)
from PySide6.QtGui import QAction, QIcon, QResizeEvent, QGuiApplication

from .resources import Icons, OutlineIcons
from .helpers import ClickableQWidget


class NotificationCard(QFrame):

    removal_requested: Signal = Signal(QWidget, bool)
    clicked: Signal = Signal(QWidget)
    about_to_delete: Signal = Signal(QWidget)
    _deletion_scheduled: bool = False
    _mouse_pressed: bool = False
    _mouse_pressed_on_toolbar: bool = False

    def __init__(self, icon: QIcon, message: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumSize(395, 60)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("""
            NotificationCard {
                background-color: palette(base);
                border-radius: 5px;
                border: 1px solid palette(midlight);
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
        style_hints = QGuiApplication.styleHints()
        style_hints.colorSchemeChanged.connect(self._handle_color_scheme_changed)

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 5)
        self._layout.setSpacing(5)
        self.setLayout(self._layout)

        self._click_zone = ClickableQWidget(self)
        self._click_zone.clicked.connect(self._emit_clicked)
        cz_layout = QHBoxLayout()
        cz_layout.setContentsMargins(5, 0, 5, 0)
        self._click_zone.setLayout(cz_layout)
        self._layout.addWidget(self._click_zone)

        self._icon = QLabel(self)
        self._icon.setAlignment(Qt.AlignCenter)
        self._icon.setPixmap(icon.pixmap(32))
        cz_layout.addWidget(self._icon)

        self._label = QLabel(self)
        self._label.setText(message)
        self._label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self._label.setWordWrap(True)
        cz_layout.addWidget(self._label)

        self._toolbar = QToolBar()
        self._layout.addWidget(self._toolbar, alignment=Qt.AlignRight)

        self.remove_action = QAction(OutlineIcons.Remove, "Remove", self)
        self.remove_action.setPriority(QAction.HighPriority)
        self.remove_action.triggered.connect(self._emit_prompt_removal_request)
        self._toolbar.addAction(self.remove_action)
        self.hide()

    def activate(self):
        self._fade_in()
        QTimer.singleShot(10_000, self, self._emit_removal_requested)

    def deactivate(self):
        self._fade_out()

    def delete(self, prompt=False):
        self._deletion_scheduled = True
        if not prompt and self.isVisible():
            self._fade_out()
        else:
            self._after_fade_out()

    def _fade_in(self):
        self._tmp_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._tmp_effect)
        self._tmp_anim = QPropertyAnimation(self._tmp_effect, b"opacity")
        self._tmp_anim.setDuration(500)
        self._tmp_anim.setStartValue(0)
        self._tmp_anim.setEndValue(1)
        self._tmp_anim.setEasingCurve(QEasingCurve.InBack)
        self._tmp_anim.start(QPropertyAnimation.DeleteWhenStopped)
        self.show()

    def _fade_out(self):
        self._tmp_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._tmp_effect)
        self._tmp_anim = QPropertyAnimation(self._tmp_effect, b"opacity")
        self._tmp_anim.setDuration(500)
        self._tmp_anim.setStartValue(1)
        self._tmp_anim.setEndValue(0)
        self._tmp_anim.setEasingCurve(QEasingCurve.InBack)
        self._tmp_anim.start(QPropertyAnimation.DeleteWhenStopped)
        self._tmp_anim.finished.connect(self._after_fade_out)

    def _after_fade_out(self):
        self.hide()
        if self._deletion_scheduled:
            self.deleteLater()

    def deleteLater(self):
        self.about_to_delete.emit(self)
        super().deleteLater()

    def _emit_clicked(self):
        self.clicked.emit(self)

    def _emit_prompt_removal_request(self):
        self.removal_requested.emit(self, True)

    def _emit_removal_requested(self):
        self.removal_requested.emit(self, False)

    @Slot()
    def _handle_color_scheme_changed(self):
        self.setStyleSheet(self.styleSheet())


class NotificationOverlay(QWidget):

    _active_cards: list[QWidget] = []

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(5, 5, 5, 5)
        self._layout.setSpacing(5)
        test = QLabel(self)
        self._layout.addWidget(test)
        self.setLayout(self._layout)
        self.setMinimumWidth(400)
        self.setFixedHeight(0)
        self._reposition()

    def _run_demo(self):
        demo_card1 = NotificationCard(Icons.Information, "Demo notification 1...", self)
        demo_card2 = NotificationCard(Icons.Browser, "Second demo notification...", self)
        demo_card3 = NotificationCard(Icons.Question, "3rd demo notifiication...", self)
        demo_card4 = NotificationCard(Icons.Warning, "Fourth and final demo notification!", self)
        demo_card4.hide()
        self.add_card(demo_card1)
        QTimer.singleShot(1_000, self, lambda: self.add_card(demo_card2))
        QTimer.singleShot(2_000, self, lambda: self.add_card(demo_card3))
        QTimer.singleShot(3_000, self, lambda: self.add_card(demo_card4))

    def _reposition(self):
        parent = self.parent()
        if not isinstance(parent, QWidget):
            return
        pgeom = parent.geometry()
        y = pgeom.height() - self.height() - 20
        x = pgeom.width() - 400 - 20
        self.move(x, y)

    def _update_heigt(self):
        if not self._active_cards:
            self.setFixedHeight(0)
        else:
            self.setFixedHeight(len(self._active_cards) * 80)
        self._reposition()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self._reposition()

    def notify(self, icon: QIcon, message: str):
        card = NotificationCard(icon, message, self)
        self.add_card(card)

    @Slot(QWidget)
    def add_card(self, card: QWidget):
        if card in self._active_cards:
            return
        if isinstance(card, NotificationCard):
            card.removal_requested.connect(self.remove_card)
            card.clicked.connect(self.remove_card)
            card.about_to_delete.connect(self._widget_about_to_delete)
            card.activate()
        self._layout.addWidget(card)
        self._active_cards.append(card)
        if len(self._active_cards) > 3:
            oldest_card = self._active_cards[0]
            self.remove_card(oldest_card)
        self._update_heigt()

    @Slot()
    @Slot(QWidget)
    def remove_card(self, card: QWidget | None = None, prompt: bool = False):
        if not card:
            card = self.sender()
        if not isinstance(card, QWidget):
            return
        if isinstance(card, NotificationCard):
            card.delete(prompt=prompt)
        else:
            self._layout.removeWidget(card)
            self._widget_about_to_delete(card)
            card.deleteLater()

    @Slot(QWidget)
    def _widget_about_to_delete(self, card: QWidget):
        self._layout.removeWidget(card)
        card_index = self._active_cards.index(card)
        del self._active_cards[card_index]
        self._update_heigt()
