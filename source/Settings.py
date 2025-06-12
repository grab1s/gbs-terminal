# Settings.py
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt

class SettingsMenu(QFrame):
    option_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Popup)
        self.setObjectName("settingsMenu")
        self.setFixedWidth(180) # ширина для всего меню

        self.setStyleSheet("""
            #settingsMenu {
                background-color: #2d2d2d;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
            }
            /* Теперь это единственный стиль для кнопок в этом файле */
            QPushButton {
                background-color: transparent;
                color: #d4d4d4;
                padding: 10px;
                text-align: left;
                border: none;
                border-radius: 3px;
                font-family: Consolas;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #3e3e3e;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # кнопки
        self.themes_button = QPushButton("Themes")
        self.custom_themes_button = QPushButton("Custom Themes")
        self.misc_button = QPushButton("Misc")
        
        self.themes_button.clicked.connect(lambda: self.on_option_clicked("themes"))
        self.custom_themes_button.clicked.connect(lambda: self.on_option_clicked("custom_themes"))
        self.misc_button.clicked.connect(lambda: self.on_option_clicked("misc"))

        layout.addWidget(self.themes_button)
        layout.addWidget(self.custom_themes_button)
        layout.addWidget(self.misc_button)

    def on_option_clicked(self, option_name):
        self.option_selected.emit(option_name)
        self.hide()