import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, QUrl

from .browser.app import BrowserApp
from .ipc import Server

if __name__ == "__main__":
    # Workaround for Windows not recognising window icons on task bar
    # See: https://stackoverflow.com/questions/1551605/
    if os.name == "nt":
        import ctypes
        custom_app_id = "quahl.quahl_browser.0.0.1"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(custom_app_id)
    QCoreApplication.setApplicationName("Quahl Browser")
    QCoreApplication.setApplicationVersion("0.0.1")
    QCoreApplication.setOrganizationName("Quahl")
    app = QApplication(["--webEngineArgs"])
    browser = BrowserApp()
    window = browser.create_window(show=True, initial_url=QUrl("http://www.google.com/"))
    server = Server()
    server.run()
    sys.exit(app.exec())
