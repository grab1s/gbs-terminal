# main_window.py
import os, sys, psutil
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget, QPushButton, QFrame, QLabel, QHBoxLayout, QSystemTrayIcon, QMenu, QToolButton
from PyQt6.QtCore import Qt, QPoint, QEvent, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QIcon, QAction
from terminal_widget import TerminalWidget
from Settings import SettingsMenu

# --- КОНФИГУРАЦИЯ ---
APP_NAME = "gbsTerminal"
WINDOW_BORDER_RADIUS = 15
COLOR_BG = "#242424"; COLOR_TITLE_BAR = "#1e1e1e"; COLOR_BUTTON_HOVER = "#3e3e3e"; COLOR_INPUT_BG = "#2d2d2d"

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

WINDOW_ICON_PATH = resource_path(os.path.join("icons", "logo.ico"))
TRAY_ICON_PATH = resource_path(os.path.join("icons", "tray.jpg"))

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(WINDOW_ICON_PATH))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle(APP_NAME)
        self.resize(900, 600)
        self.setMinimumSize(500, 400)
        
        self.drag_pos = None

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.background_frame = QFrame(self)
        self.background_frame.setObjectName("background_frame")
        self.main_layout.addWidget(self.background_frame)
        
        frame_layout = QVBoxLayout(self.background_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)
        
        self._create_title_bar(frame_layout)
        
        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabWidget")
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        
        self.add_tab_button = QToolButton()
        self.add_tab_button.setObjectName("add_tab_button")
        self.add_tab_button.setText("+")
        self.add_tab_button.clicked.connect(self.add_new_tab)
        
        self.tabs.setCornerWidget(self.add_tab_button, Qt.Corner.TopRightCorner)
        
        frame_layout.addWidget(self.tabs)
        
        self.settings_menu = SettingsMenu(self)
        self.settings_menu.hide()
        self.settings_menu.option_selected.connect(self.handle_settings_option)
        
        self._setup_tray_icon()
        self.setStyleSheet(self._get_stylesheet())
        
        self.add_new_tab()
        
        self.setWindowOpacity(0.0)
        self.animation = QPropertyAnimation(self, b"windowOpacity", duration=300, startValue=0.0, endValue=1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.show()
        self.animation.start()

        QApplication.instance().installEventFilter(self)

    def _create_title_bar(self, parent_layout):
        self.title_bar = QFrame()
        self.title_bar.setObjectName("title_bar")
        self.title_bar.setFixedHeight(40)
        self.title_bar.mousePressEvent = self.title_bar_press
        self.title_bar.mouseMoveEvent = self.title_bar_move
        self.title_bar.mouseReleaseEvent = self.title_bar_release
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(20, 0, 0, 0)
        title_layout.setSpacing(0)

        self.title_label = QLabel(APP_NAME)
        title_layout.addWidget(self.title_label)
        
        self.minimize_button = QPushButton("—", clicked=self.hide)
        self.maximize_button = QPushButton("🗖", clicked=self.toggle_maximize)
        self.close_button = QPushButton("✕", clicked=self.close)
        self.close_button.setObjectName("close_button")
        
        title_layout.addWidget(self.minimize_button)
        title_layout.addWidget(self.maximize_button)
        title_layout.addWidget(self.close_button)
        parent_layout.addWidget(self.title_bar)

    def add_new_tab(self):
        if self.tabs.count() >= 7: return
        terminal_widget = TerminalWidget()
        terminal_widget.settings_requested.connect(self.toggle_settings_menu)
        index = self.tabs.addTab(terminal_widget, f"Терминал {self.tabs.count() + 1}")
        self.tabs.setCurrentIndex(index)
        terminal_widget.setFocusOnInput()

    def close_tab(self, index):
        if self.tabs.count() > 1:
            widget = self.tabs.widget(index)
            self.kill_proc_tree(widget.process.processId())
            self.tabs.removeTab(index)
        else:
            self.close()

    def toggle_settings_menu(self, button_widget):
        if self.settings_menu.isVisible():
            self.settings_menu.hide()
        else:
            self.settings_menu.adjustSize()
            button_pos = button_widget.mapToGlobal(QPoint(0, 0))
            menu_y = button_pos.y() - self.settings_menu.height() - 5
            menu_x = button_pos.x() + button_widget.width() - self.settings_menu.width()
            self.settings_menu.move(menu_x, menu_y)
            self.settings_menu.show()
    
    def handle_settings_option(self, option):
        print(f"Выбрана опция: {option}")

    def _get_stylesheet(self):
        return f"""
            #background_frame {{ background-color: {COLOR_BG}; border: 1px solid #000; border-radius: {WINDOW_BORDER_RADIUS}px; }}
            #background_frame[maximized="true"] {{ border-radius: 0px; }}
            #title_bar {{ background-color: {COLOR_TITLE_BAR}; border-top-left-radius: {WINDOW_BORDER_RADIUS}px; border-top-right-radius: {WINDOW_BORDER_RADIUS}px; }}
            #background_frame[maximized="true"] #title_bar {{ border-radius: 0px; }}
            QLabel {{ color: #d4d4d4; font-family: Consolas; font-size: 10pt; font-weight: bold; }}
            #title_bar QPushButton {{
                background-color: transparent; color: #d4d4d4; border: none; font-size: 14pt; font-family: "Segoe UI Symbol";
                min-width: 45px; max-width: 45px; min-height: 39px;
            }}
            #title_bar QPushButton:hover {{ background-color: {COLOR_BUTTON_HOVER}; }}
            #close_button:hover {{
                background-color: #c82b2b;
                border-top-right-radius: {WINDOW_BORDER_RADIUS - 1}px;
            }}
            #background_frame[maximized="true"] #close_button:hover {{ border-radius: 0px; }}
            
            #mainTabWidget::pane {{ border: none; }}
            QTabBar {{ qproperty-drawBase: 0; background-color: {COLOR_BG}; }}
            QTabBar::tab {{ background: #2d2d2d; color: #d4d4d4; padding: 8px 15px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px;}}
            QTabBar::tab:selected {{ background: {COLOR_BG}; }}
            
            #mainTabWidget QToolButton {{ 
                background-color: #2d2d2d; border-radius: 4px; color: #d4d4d4; border: none;
                font-size: 16pt; padding: 0 4px; margin: 4px 5px 0 0;
                min-width: 28px; max-width: 28px; min-height: 28px;
            }}
            #mainTabWidget QToolButton:hover {{ background-color: {COLOR_BUTTON_HOVER}; }}

            QTextEdit {{ background-color: {COLOR_BG}; color: #d4d4d4; font-family: Consolas; border: none; }}
            QLineEdit {{ background-color: {COLOR_INPUT_BG}; color: #d4d4d4; font-family: Consolas; border: none; padding: 12px; border-radius: 4px; }}
            #settings_button {{ background-color: {COLOR_INPUT_BG}; border: none; border-radius: 4px; }}
            #settings_button:hover {{ background-color: {COLOR_BUTTON_HOVER}; }}
        """
        
    def title_bar_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton: self.drag_pos = event.globalPosition().toPoint(); event.accept()
    def title_bar_move(self, event):
        if self.drag_pos: delta = event.globalPosition().toPoint() - self.drag_pos; self.move(self.pos() + delta); self.drag_pos = event.globalPosition().toPoint(); event.accept()
    def title_bar_release(self, event):
        self.drag_pos = None; event.accept()
    
    def toggle_maximize(self):
        if self.isMaximized():
            self.background_frame.setProperty("maximized", False); self.showNormal(); self.maximize_button.setText("🗖")
        else:
            self.background_frame.setProperty("maximized", True); self.showMaximized(); self.maximize_button.setText("🗗")
        self.background_frame.style().unpolish(self.background_frame); self.background_frame.style().polish(self.background_frame)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F11: self.toggle_maximize()
        super().keyPressEvent(event)
        
    def _setup_tray_icon(self):
        try: icon = QIcon(TRAY_ICON_PATH)
        except Exception as e: print(f"Иконка не найдена: {e}"); icon = QIcon()
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip(f"{APP_NAME} is running")
        menu = QMenu(); menu.addAction(QAction("Open", self, triggered=self.show)); menu.addAction(QAction("Hide", self, triggered=self.hide))
        menu.addSeparator(); menu.addAction(QAction("Quit", self, triggered=self.close)); self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
    
    def kill_proc_tree(self, pid, including_parent=True):
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                child.kill()
            if including_parent:
                parent.kill()
        except psutil.NoSuchProcess:
            pass # Процесс уже мог быть убит
            
    def closeEvent(self, event):
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if hasattr(widget, 'process') and widget.process.processId() is not None:
                self.kill_proc_tree(widget.process.processId())
        self.tray_icon.hide()
        event.accept()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if self.settings_menu.isVisible() and not self.settings_menu.geometry().contains(event.globalPosition().toPoint()):
                self.settings_menu.hide()
        return super().eventFilter(obj, event)