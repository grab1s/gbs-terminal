# main.py
import sys, os, ctypes
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow

if __name__ == '__main__':
    try: is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError: is_admin = os.getuid() == 0
    if not is_admin:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())