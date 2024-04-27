from PySide6.QtWebEngineCore import QWebEngineCertificateError
from PySide6.QtWidgets import (
    QDialog, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QFrame, QPushButton,
    QDialogButtonBox
)
from PySide6.QtCore import Qt, QSize, Slot

from .resources import Icons


class CertificateErrorDialog(QDialog):

    _unexpanded_size: QSize | None = None
    _expanded_size: QSize | None = None

    def __init__(self, error: QWebEngineCertificateError, parent: QWidget | None = None):
        super().__init__(parent)
        self._error = error
        self.setWindowTitle("Certificate Error")
        self.setWindowIcon(Icons.Warning)
        self.setFixedWidth(450)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._build_layout()

    def _build_layout(self):
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._top_layout = QHBoxLayout()
        self._top_layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addLayout(self._top_layout)

        self._icon_label = QLabel(self)
        self._icon_label.setPixmap(Icons.CertificateWarning.pixmap(48))
        self._icon_label.setFixedWidth(60)
        self._top_layout.addWidget(self._icon_label, alignment=Qt.AlignTop | Qt.AlignHCenter)

        self._message_layout = QVBoxLayout()
        self._message_layout.setSpacing(5)
        self._top_layout.addLayout(self._message_layout)

        self._header = QLabel(self)
        self._header.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self._header.setText("Certificate Error")
        self._header.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self._message_layout.addWidget(self._header)

        self._preamble = QLabel(self)
        self._preamble.setText(
            "You are trying to establish a secure connection to "
            f"<b>{self._error.url().host()}</b>, "
            "but there are issues with the site's security certificate."
        )
        self._preamble.setWordWrap(True)
        self._message_layout.addWidget(self._preamble)

        self._description = QLabel(self)
        self._description.setStyleSheet("font-weight: bold;")
        self._description.setText(self._error.description())
        self._description.setWordWrap(True)
        self._message_layout.addWidget(self._description)

        self._expand_button = QPushButton(self)
        self._expand_button.setText("Show more...")
        self._expand_button.setAutoDefault(False)
        self._expand_button.pressed.connect(self._toggle_details)
        self._message_layout.addWidget(self._expand_button, alignment=Qt.AlignRight)

        detail = self._build_expandable()
        self._message_layout.addWidget(detail)

        self._button_box = QDialogButtonBox(
            QDialogButtonBox.Abort |
            QDialogButtonBox.Ignore,
            self
        )
        abort_button = self._button_box.button(QDialogButtonBox.Abort)
        abort_button.setDefault(True)
        abort_button.setFocus()
        abort_button.pressed.connect(self.reject)
        ignore_button = self._button_box.button(QDialogButtonBox.Ignore)
        ignore_button.pressed.connect(self.accept)
        self._layout.addWidget(self._button_box)

    @Slot()
    def reject(self):
        super().reject()

    @Slot()
    def accept(self):
        super().accept()

    def _build_expandable(self):
        self._detail_expandable = QFrame(self)
        self._detail_expandable.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self._detail_expandable.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self._detail_expandable.setVisible(False)

        vlayout = QVBoxLayout()
        self._detail_expandable.setLayout(vlayout)

        self._detail_domain = QLabel(self)
        self._detail_domain.setText(f"<b>Domain:</b> {self._error.url().host()}")
        self._detail_domain.setWordWrap(True)
        vlayout.addWidget(self._detail_domain)

        self._detail_url = QLabel(self)
        self._detail_url.setText(f"<b>Request URL:</b> {self._error.url().toDisplayString()}")
        self._detail_url.setWordWrap(True)
        vlayout.addWidget(self._detail_url)

        self._detail_type = QLabel(self)
        self._detail_type.setText(
            f"<b>Error Type:</b> {self._name_of_error_type(self._error.type())}"
        )
        self._detail_type.setWordWrap(True)
        vlayout.addWidget(self._detail_type)

        self._detail_description = QLabel(self)
        self._detail_description.setText(f"<b>Error Description:</b> {self._error.description()}.")
        self._detail_description.setWordWrap(True)
        vlayout.addWidget(self._detail_description)

        return self._detail_expandable

    def _name_of_error_type(self, error_type: QWebEngineCertificateError.Type) -> str:
        if error_type == QWebEngineCertificateError.Type.CertificateAuthorityInvalid:
            return "ERR_CERT_AUTHORITY_INVALID"
        if error_type == QWebEngineCertificateError.Type.CertificateCommonNameInvalid:
            return "ERR_CERT_COMMON_NAME_INVALID"
        if error_type == QWebEngineCertificateError.Type.CertificateContainsErrors:
            return "ERR_CERT_CONTAINS_ERRORS"
        if error_type == QWebEngineCertificateError.Type.CertificateDateInvalid:
            return "ERR_CERT_DATE_INVALID"
        if error_type == QWebEngineCertificateError.Type.CertificateInvalid:
            return "ERR_CERT_INVALID"
        if error_type == QWebEngineCertificateError.Type.CertificateKnownInterceptionBlocked:
            return "ERR_CERT_KNOWN_INTERCEPTION_BLOCKED"
        if error_type == QWebEngineCertificateError.Type.CertificateNameConstraintViolation:
            return "ERR_CERT_NAME_CONSTRAINT_VIOLATION"
        if error_type == QWebEngineCertificateError.Type.CertificateNonUniqueName:
            return "ERR_CERT_NON_UNIQUE_NAME"
        if error_type == QWebEngineCertificateError.Type.CertificateDateInvalid:
            return "ERR_CERT_DATE_INVALID"
        if error_type == QWebEngineCertificateError.Type.CertificateNoRevocationMechanism:
            return "ERR_CERT_NO_REVOCATION_MECHANISM"
        if error_type == QWebEngineCertificateError.Type.CertificateRevoked:
            return "ERR_CERT_REVOKED"
        if error_type == QWebEngineCertificateError.Type.CertificateSymantecLegacy:
            return "ERR_CERT_SYMANTEC_LEGACY"
        if error_type == QWebEngineCertificateError.Type.CertificateTransparencyRequired:
            return "ERR_CERT_TRANSPARENCY_REQUIRED"
        if error_type == QWebEngineCertificateError.Type.CertificateUnableToCheckRevocation:
            return "ERR_CERT_UNABLE_TO_CHECK_REVOCATION"
        if error_type == QWebEngineCertificateError.Type.CertificateValidityTooLong:
            return "ERR_CERT_VALIDITY_TOO_LONG"
        if error_type == QWebEngineCertificateError.Type.CertificateWeakKey:
            return "ERR_CERT_WEAK_KEY"
        if error_type == QWebEngineCertificateError.Type.CertificateWeakSignatureAlgorithm:
            return "ERR_CERT_WEAK_SIGNATURE_ALGORITHM"
        if error_type == QWebEngineCertificateError.Type.SslObsoleteVersion:
            return "ERR_SSL_OBSOLETE_VERSION"
        if error_type == QWebEngineCertificateError.Type.SslPinnedKeyNotInCertificateChain:
            return "ERR_SSL_PINNED_KEY_NOT_IN_CERTIFICATE_CHAIN"
        return f"ERR_UNKNOWN_CODE_{error_type}"

    def _toggle_details(self):
        if self._detail_expandable.isVisible():
            self._expanded_size = self.size()
            self._detail_expandable.setVisible(False)
            self._expand_button.setText("Show more...")
            self.setFixedSize(self._unexpanded_size)
        else:
            self._unexpanded_size = self.size()
            self._detail_expandable.setVisible(True)
            self._expand_button.setText("Show less...")
            if self._expanded_size:
                self.setFixedSize(self._expanded_size)
