from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QObject, Slot

from .profile import BrowserProfile
from .resources import Icons


class WebPage(QWebEnginePage):

    def __init__(self, profile: BrowserProfile, parent: QObject):
        super().__init__(profile, parent)
        self.renderProcessPidChanged.connect(self.on_render_process_pid_change)
        self.renderProcessTerminated.connect(self.on_render_process_terminated)

    @Slot(int)
    def on_render_process_pid_change(self, pid: int):
        print("Render process PID changed to", pid)

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
