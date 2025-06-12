# terminal_widget.py
import sys
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton
from PyQt6.QtCore import QProcess, QEvent, Qt, QSize, pyqtSignal
from PyQt6.QtGui import QTextCursor, QIcon

# --- КОНФИГУРАЦИЯ ---
FONT_FAMILY = "Consolas"
INITIAL_FONT_SIZE = 11
SHELL_TO_RUN = "cmd.exe"
# Команда chcp 65001 переключает кодовую страницу на UTF-8
SHELL_ARGS = ["/k", "chcp 65001"]

def resource_path(relative_path):
    """Возвращает правильный путь к ресурсу, работает и в .exe, и при разработке."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

SETTINGS_ICON_PATH = resource_path(os.path.join("icons", "settings.png"))

class CommandLineEdit(QLineEdit):
    """Кастомное поле ввода с поддержкой истории команд."""
    def __init__(self, parent_terminal):
        super().__init__()
        self.parent_terminal = parent_terminal

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            self.parent_terminal.navigate_history(-1)
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            self.parent_terminal.navigate_history(1)
            event.accept()
        else:
            super().keyPressEvent(event)

class TerminalWidget(QWidget):
    """Виджет, инкапсулирующий один полноценный терминал."""
    settings_requested = pyqtSignal(QPushButton)

    def __init__(self):
        super().__init__()
        self.current_font_size = INITIAL_FONT_SIZE
        self.command_history = []
        self.history_index = 0
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(10)

        self.output_area = QTextEdit(readOnly=True)
        self.output_area.installEventFilter(self)
        
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        self.input_entry = CommandLineEdit(self)
        self.input_entry.returnPressed.connect(self.send_command)

        self.settings_button = QPushButton()
        self.settings_button.setObjectName("settings_button")
        self.settings_button.setIcon(QIcon(SETTINGS_ICON_PATH))
        self.settings_button.setIconSize(QSize(22, 22))
        self.settings_button.setFixedSize(42, 42)
        self.settings_button.clicked.connect(lambda: self.settings_requested.emit(self.settings_button))
        
        input_layout.addWidget(self.input_entry)
        input_layout.addWidget(self.settings_button)
        
        main_layout.addWidget(self.output_area)
        main_layout.addLayout(input_layout)

        font = self.output_area.font()
        font.setFamily(FONT_FAMILY)
        font.setPointSize(self.current_font_size)
        self.output_area.setFont(font)
        self.input_entry.setFont(font)

        self._setup_shell_process()
    
    def _setup_shell_process(self):
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.on_ready_read)
        self.process.start(SHELL_TO_RUN, SHELL_ARGS)
    
    def send_command(self):
        command = self.input_entry.text()
        processed_command = command.strip()

        if not processed_command:
            self.process.write(b'\n')
            self.input_entry.clear()
            return
            
        if not self.command_history or self.command_history[-1] != command:
            self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        if processed_command.lower().startswith("cd "):
            parts = processed_command.split(" ", 1)
            if len(parts) > 1 and not parts[1].strip().startswith("/d"):
                processed_command = f"cd /d {parts[1]}"
        elif processed_command.lower() == 'cd':
            processed_command = '\n'
        
        self.process.write((processed_command + '\n').encode('utf-8'))
        self.input_entry.clear()
        
    def on_ready_read(self):
        data = self.process.readAllStandardOutput().data().decode('utf-8', 'replace')
        self.append_text(data)

    def append_text(self, text):
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.output_area.ensureCursorVisible()
        
    def setFocusOnInput(self):
        self.input_entry.setFocus()
    
    def navigate_history(self, direction):
        if not self.command_history: return
        new_index = self.history_index + direction
        if 0 <= new_index < len(self.command_history):
            self.history_index = new_index
            self.input_entry.setText(self.command_history[self.history_index])
            self.input_entry.end(False)
        elif new_index >= len(self.command_history):
            self.history_index = len(self.command_history)
            self.input_entry.clear()

    def eventFilter(self, obj, event):
        if obj is self.output_area and event.type() == QEvent.Type.Wheel:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                delta = event.angleDelta().y()
                self.current_font_size += 1 if delta > 0 else -1
                self.current_font_size = max(6, min(self.current_font_size, 72))
                font = self.output_area.font()
                font.setPointSize(self.current_font_size)
                self.output_area.setFont(font)
                self.input_entry.setFont(font)
                return True
        return super().eventFilter(obj, event)