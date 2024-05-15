"""The Quahl Browser.

An embeddable and remote-controllable web browser component written in
Python and based on PySide6 (Qt) and its Chromium-based QWebEngine.

Quahl includes two packages: :mod:`quahl.browser`, which contains the code for
the web browser, and :mod:`quahl.ipc`, which contains the code for the
browser-end of Quahl's inter-process communication facilities.

Utilities for controlling an instance of the Quahl Browser via IPC are offered
via a separate Python package, :code:`quahl-controller`, which is much lighter
on dependencies.
"""

# import PySide6.QtCore

# print(f"PySide Version: {PySide6.__version__}")
# print(f"Qt Version: {PySide6.QtCore.__version__}")
