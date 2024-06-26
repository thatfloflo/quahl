from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineCertificateError
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QObject, Slot

from .profile import BrowserProfile
from .certificateerrordialog import CertificateErrorDialog
from .resources import Icons


class WebPage(QWebEnginePage):

    def __init__(self, profile: BrowserProfile, parent: QObject):
        super().__init__(profile, parent)
        self._profile = profile
        self.renderProcessPidChanged.connect(self.on_render_process_pid_change)
        self.renderProcessTerminated.connect(self.on_render_process_terminated)
        self.certificateError.connect(self._handle_certificate_error)
        self.loadFinished.connect(self._handle_load_finished)

    @Slot(QWebEngineCertificateError)
    def _handle_certificate_error(self, error: QWebEngineCertificateError):
        if not error.isOverridable():
            error.rejectCertificate()
            return
        error.defer()
        print("SSL ERROR:", error.description())
        dialog = CertificateErrorDialog(error, self.parent())
        decision = dialog.exec()
        print("Received decision:", decision)
        if decision:
            error.acceptCertificate()
        else:
            error.rejectCertificate()

    @Slot(int)
    def on_render_process_pid_change(self, pid: int):
        # print("Render process PID changed to", pid)
        ...

    @Slot(QWebEnginePage.RenderProcessTerminationStatus, int)
    def on_render_process_terminated(
            self,
            termination_status: QWebEnginePage.RenderProcessTerminationStatus,
            exit_code: int):
        reason = "unknown"
        if termination_status == QWebEnginePage.NormalTerminationStatus:
            reason = "normal"
        elif termination_status == QWebEnginePage.AbnormalTerminationStatus:
            reason = "abnormal"
        elif termination_status == QWebEnginePage.CrashedTerminationStatus:
            reason = "crashed"
        elif termination_status == QWebEnginePage.KilledTerminationStatus:
            reason = "killed"
        url_message = ""
        parent = self.parent()
        if isinstance(parent, QWebEngineView):
            url_message = f", url: {parent.url().toString()}"
        short_msg = (
            f"Renderer crashed! Status: {reason}, exit code: {exit_code}. "
            "Attempting to reload page..."
        )
        message = (
            "Renderer process terminated abnomrally. "
            f"Status: {reason}, exit code: {exit_code}{url_message}. "
            "Reloading page..."
        )
        if isinstance(parent, QWebEngineView):
            window = parent.window()
            if hasattr(window, "notify") and callable(window.notify):
                window.notify(Icons.Crash, short_msg)
        print("ERROR:", message)
        self.triggerAction(QWebEnginePage.Reload)

    @Slot(bool)
    def _handle_load_finished(self, ok: bool):
        if ok:
            self._profile.suggestion_model.add_url(self.url())
