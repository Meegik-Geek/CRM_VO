import os
import subprocess
from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QDialog, QLineEdit, QApplication
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QCursor, QIcon
from pages.denne.denne_page import InputDenPage
from pages.zaoch.zaoch_page import InputZaochPage
from pages.admin.admin_page import InputAdminPage
from db.connect_db import get_setting
from utils.logger import log_error, log_info
from utils.notifications import show_error, show_success

class HomePage(QMainWindow):
    
    def __init__(self):
        super(HomePage, self).__init__()
        self.theme = "light"  # Початкова тема
        self.size = "medium"  # Початковий розмір
        self.size_levels = ["medium", "large"]  # Рівні розміру
        self.is_large_size = False  # Стан розміру
        self.init_ui()
        self.load_settings()
        self.load_styles()

    def init_ui(self):
        self.setWindowTitle("CRM Вступ.Офіс")
        self.setFixedSize(600, 450)
        # Центрування вікна
        frame_geometry = self.frameGeometry()
        screen_center = QApplication.desktop().screenGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

        # Центральний віджет
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(25)

        # Заголовок
        try:
            college_name = get_setting('college_short_name', 'CRM Вступ.Офіс')
            log_info(f"Завантажено скорочену назву закладу: {college_name}")
        except Exception as e:
            college_name = "CRM Вступ.Офіс (Помилка БД)"
            log_error("Не вдалося завантажити назву закладу з БД", e)
            show_error(self, "Помилка підключення до бази даних. Перевірте налаштування .env")

        # Банер оновлення
        self.update_banner = QWidget(self)
        self.update_banner.setObjectName("updateBanner")
        banner_layout = QVBoxLayout(self.update_banner)
        self.update_banner_label = QLabel("", self)
        self.update_banner_label.setWordWrap(True)
        self.update_banner_label.setAlignment(Qt.AlignCenter)
        self.update_banner_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        
        self.update_banner_btn = QPushButton("Перезавантажити та Оновити", self)
        self.update_banner_btn.setObjectName("logButton")
        self.update_banner_btn.setFixedSize(250, 40)
        self.update_banner_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.update_banner_btn.clicked.connect(self.run_updater)
        self.update_banner_btn.hide()
        
        banner_layout.addWidget(self.update_banner_label)
        banner_layout.addWidget(self.update_banner_btn, alignment=Qt.AlignCenter)
        self.update_banner.hide()
        layout.addWidget(self.update_banner)

        self.title_label = QLabel(college_name, self)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # Кнопки навігації
        self.full_time_button = QPushButton("Денна", self)
        self.full_time_button.setObjectName("navButton")
        self.part_time_button = QPushButton("Заочна", self)
        self.part_time_button.setObjectName("greenButton")
        self.setup_buttons()
        layout.addWidget(self.full_time_button, alignment=Qt.AlignCenter)
        layout.addWidget(self.part_time_button, alignment=Qt.AlignCenter)

        # Верхні кнопки
        self.login_button = QPushButton("Вхід", self)
        self.toggle_size_button = QPushButton(self)
        self.toggle_theme_button = QPushButton(self)
        
        # Поточна версія
        self.version_label = QLabel(self)
        self.version_label.setObjectName("versionLabel")
        self.version_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        self.load_version()
        
        self.setup_top_buttons()

    def setup_buttons(self):
        for button in [self.full_time_button, self.part_time_button]:
            button.setFixedWidth(300)
            button.setCursor(QCursor(Qt.PointingHandCursor))
        self.full_time_button.clicked.connect(self.on_full_time_clicked)
        self.part_time_button.clicked.connect(self.on_part_time_clicked)
        
        # Запуск перевірки оновлень
        try:
            from utils.update_checker import UpdateCheckerThread
            self.update_thread = UpdateCheckerThread()
            self.update_thread.global_update_available.connect(self.show_global_update)
            self.update_thread.admin_update_available.connect(self.show_admin_update)
            self.update_thread.start()
        except:
            pass

    def show_global_update(self, version):
        self.update_banner_label.setText(f"Є нова версія програми ({version}). Зверніться до локального адміністратора.")
        self.update_banner_btn.hide()
        self.update_banner.show()

    def show_admin_update(self, version, method, path):
        self.update_banner_label.setText(f"Доступне обов'язкове оновлення (v{version})!")
        self.update_banner_btn.show()
        self.update_banner.show()
        
        # Зберігаємо параметри для апдейтера
        self.update_method = method
        self.update_path = path

    def run_updater(self):
        if hasattr(self, 'update_method') and hasattr(self, 'update_path'):
            import sys
            import subprocess
            updater_path = "updater.exe" if os.path.exists("updater.exe") else sys.executable
            
            args = [updater_path]
            if updater_path == sys.executable:
                args.append("updater.py")
                
            args.extend([self.update_method, self.update_path])
            subprocess.Popen(args)
            QApplication.quit()

    def show_login_dialog(self):
        login_dialog = LoginDialog(self)
        if login_dialog.exec_() == QDialog.Accepted:
            self.input_admin_page = InputAdminPage()
            self.input_admin_page.show()

    def load_version(self):
        try:
            version_path = "version.txt"
            if os.path.exists(version_path):
                with open(version_path, "r", encoding="utf-8") as f:
                    version = f.read().strip()
                self.version_label.setText(f"v{version}")
            else:
                self.version_label.setText("v1.0.0")
        except Exception as e:
            print(f"Помилка завантаження версії: {e}")
            self.version_label.setText("v1.0.0")

    def setup_top_buttons(self):
        # Кнопка логіна
        self.login_button.setObjectName("logButton")
        self.login_button.setFixedSize(80, 30)
        self.login_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.login_button.clicked.connect(self.show_login_dialog)

        # Кнопка перемикання розміру
        self.toggle_size_button.setObjectName("iconButton")
        self.toggle_size_button.setFixedSize(30, 30)
        self.toggle_size_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.toggle_size_button.setToolTip("Переключити розмір шрифту")
        self.update_size_button_icon()
        self.toggle_size_button.clicked.connect(self.toggle_size)

        # Кнопка перемикання теми
        self.toggle_theme_button.setObjectName("iconButton")
        self.toggle_theme_button.setFixedSize(30, 30)
        self.toggle_theme_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.toggle_theme_button.setToolTip("Переключити тему")
        self.update_theme_button_icon()
        self.toggle_theme_button.clicked.connect(self.toggle_theme)

        def update_positions():
            window_width = self.width()
            window_height = self.height()
            
            # Позиціонування верхніх кнопок
            spacing = 10
            button_width = 30
            login_width = self.login_button.width()
            total_width = login_width + 2 * button_width + 2 * spacing
            start_x = window_width - total_width - 20
            y = 20
            self.login_button.move(start_x, y)
            self.toggle_size_button.move(start_x + login_width + spacing, y)
            self.toggle_theme_button.move(start_x + login_width + 2 * spacing + button_width, y)
            
            # Позиціонування версії (знизу справа)
            self.version_label.adjustSize()
            self.version_label.move(window_width - self.version_label.width() - 10, window_height - self.version_label.height() - 5)

        original_resize_event = self.resizeEvent
        def resize_event(event):
            original_resize_event(event)
            update_positions()
        self.resizeEvent = resize_event
        update_positions()

    def update_size_button_icon(self):
        icon_path = "resource/eye.png" if not self.is_large_size else "resource/eye_off.png"
        if os.path.exists(icon_path):
            self.toggle_size_button.setIcon(QIcon(icon_path))
        else:
            self.toggle_size_button.setText("E" if not self.is_large_size else "X")
            print(f"Попередження: іконка не знайдена: {icon_path}")

    def update_theme_button_icon(self):
        icon_path = "resource/moon.png" if self.theme == "light" else "resource/sun.png"
        if os.path.exists(icon_path):
            self.toggle_theme_button.setIcon(QIcon(icon_path))
        else:
            self.toggle_theme_button.setText("M" if self.theme == "light" else "S")
            print(f"Попередження: іконка не знайдена: {icon_path}")

    def toggle_size(self):
        self.is_large_size = not self.is_large_size
        self.size = "large" if self.is_large_size else "medium"
        self.update_size_button_icon()
        self.load_styles()
        self.save_settings()

    def toggle_theme(self):
        self.theme = "grey" if self.theme == "light" else "light"
        self.update_theme_button_icon()
        self.load_styles()
        self.save_settings()

    def load_styles(self):
        styles = ""
        try:
            with open("resource/styles/base.qss", "r", encoding="utf-8") as f:
                styles += f.read()
            with open(f"resource/styles/{self.theme}_theme.qss", "r", encoding="utf-8") as f:
                styles += f.read()
            with open(f"resource/styles/{self.size}_size.qss", "r", encoding="utf-8") as f:
                styles += f.read()
        except FileNotFoundError as e:
            print(f"Попередження: файл стилів не знайдено: {e}")
            styles = "QMainWindow { background-color: #FFFFFF; }"
        QApplication.instance().setStyleSheet(styles)

    def save_settings(self):
        settings = QSettings("MyApp", "Settings")
        settings.setValue("theme", self.theme)
        settings.setValue("size", self.size)

    def load_settings(self):
        settings = QSettings("MyApp", "Settings")
        self.theme = settings.value("theme", "light")
        self.size = settings.value("size", "medium")
        self.is_large_size = self.size == "large"
        self.update_size_button_icon()
        self.update_theme_button_icon()

    def on_full_time_clicked(self):
        self.input_den_page = InputDenPage()
        self.input_den_page.show()
        

    def on_part_time_clicked(self):
        self.input_zaoch_page = InputZaochPage()
        self.input_zaoch_page.show()
        

    def show_login_dialog(self):
        login_dialog = LoginDialog(self)
        if login_dialog.exec_() == QDialog.Accepted:
            self.input_admin_page = InputAdminPage()
            self.input_admin_page.show()
            

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Вхід")
        self.setFixedSize(300, 150)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.username_input = QLineEdit(self)
        self.username_input.setObjectName("usernameInput")
        self.username_input.setPlaceholderText("Логін")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit(self)
        self.password_input.setObjectName("passwordInput")
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.error_label = QLabel("", self)
        self.error_label.setObjectName("errorLabel")
        layout.addWidget(self.error_label)

        self.login_button = QPushButton("Вхід", self)
        self.login_button.setObjectName("loginButton")
        self.login_button.setFixedSize(150, 30)
        self.login_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.login_button.clicked.connect(self.authenticate_user)
        layout.addWidget(self.login_button, alignment=Qt.AlignCenter)

    def authenticate_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if username == "admin" and password == "password":
            self.accept()
        else:
            self.error_label.setText("Невірний логін або пароль")
            self.username_input.clear()
            self.password_input.clear()

