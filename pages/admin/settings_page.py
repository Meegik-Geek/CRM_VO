from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QFormLayout, QGroupBox, QFileDialog, QTimeEdit, QScrollArea
)
from PyQt5.QtCore import Qt, QTime, QUrl
from PyQt5.QtGui import QCursor, QDesktopServices
from db.repository import SettingsRepository, InstitutionRepository
from db.backup_manager import schedule_backup, perform_backup, restore_backup
from utils.notifications import show_error, show_success, show_info, show_error_msg, show_warning_msg, ask_confirmation
from utils.logger import log_error, log_info

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_repo = SettingsRepository()
        self.inst_repo = InstitutionRepository()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        # Головний лейаут сторінки
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Створюємо область прокрутки
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setObjectName("settingsScrollArea")
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # Контейнер для вмісту
        container = QWidget()
        container.setObjectName("settingsContainer")
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 20, 40, 20)

        title = QLabel("Налаштування системи", self)
        title.setObjectName("adminTitleLabel")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 1. Дані закладу
        inst_group = QGroupBox("Дані навчального закладу")
        inst_layout = QFormLayout()
        self.inst_full_name = QLineEdit()
        self.inst_short_name = QLineEdit()
        self.inst_address = QLineEdit()
        self.inst_director = QLineEdit()
        self.inst_phone = QLineEdit()
        
        inst_layout.addRow("Повна назва:", self.inst_full_name)
        inst_layout.addRow("Коротка назва:", self.inst_short_name)
        inst_layout.addRow("Адреса:", self.inst_address)
        inst_layout.addRow("Директор:", self.inst_director)
        inst_layout.addRow("Телефон:", self.inst_phone)
        
        inst_group.setLayout(inst_layout)
        layout.addWidget(inst_group)

        # 1.1 Відповідальні особи
        resp_group = QGroupBox("Відповідальні особи (для звітів)")
        resp_layout = QFormLayout()
        
        self.resp_secretary = QLineEdit()
        self.deputy_secretary = QLineEdit()
        self.legal_counsel = QLineEdit()
        self.edebo_admin = QLineEdit()
        
        resp_layout.addRow("Відповідальний секретар ПК:", self.resp_secretary)
        resp_layout.addRow("Заступник відпов. секретаря:", self.deputy_secretary)
        resp_layout.addRow("Юрисконсульт коледжу:", self.legal_counsel)
        resp_layout.addRow("Адміністратор ЄДЕБО:", self.edebo_admin)
        
        resp_group.setLayout(resp_layout)
        layout.addWidget(resp_group)

        # 2. Налаштування бекапів
        backup_group = QGroupBox("Автоматичне резервне копіювання")
        backup_layout = QFormLayout()
        
        self.backup_path = QLineEdit()
        self.btn_select_path = QPushButton("Огляд...")
        self.btn_select_path.clicked.connect(self.select_backup_path)
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.backup_path)
        path_layout.addWidget(self.btn_select_path)
        
        self.backup_freq = QComboBox()
        self.backup_freq.addItem("Вимкнено", "off")
        self.backup_freq.addItem("При запуску сервера", "on_startup")
        self.backup_freq.addItem("В конкретний час (щодня, якщо сервер запущено)", "at_time")
        self.backup_freq.currentIndexChanged.connect(self.toggle_time_visibility)
        
        self.backup_time = QTimeEdit()
        self.backup_time.setObjectName("inputField")
        self.backup_time.setDisplayFormat("HH:mm")
        self.backup_time.setMinimumHeight(35)
        self.backup_time.setStyleSheet("""
            QTimeEdit#inputField {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 14px;
                color: #495057;
            }
            QTimeEdit#inputField:focus {
                border-color: #80bdff;
                outline: 0;
            }
        """)

        self.backup_time_label = QLabel("Час запуску:")

        # Шлях до утиліт PG
        self.pg_tools_path = QLineEdit()
        self.pg_tools_path.setObjectName("inputField")
        self.btn_select_pg_path = QPushButton("Огляд...")
        self.btn_select_pg_path.clicked.connect(self.select_pg_tools_path)
        pg_path_layout = QHBoxLayout()
        pg_path_layout.addWidget(self.pg_tools_path)
        pg_path_layout.addWidget(self.btn_select_pg_path)

        backup_layout.addRow("Шлях до бекапів:", path_layout)
        backup_layout.addRow("Шлях до PostgreSQL (bin):", pg_path_layout)
        backup_layout.addRow("Частота:", self.backup_freq)
        backup_layout.addRow(self.backup_time_label, self.backup_time)

        self.btn_manual_backup = QPushButton("Створити бекап зараз")
        self.btn_manual_backup.setObjectName("greenButton")
        self.btn_manual_backup.setFixedWidth(200)
        self.btn_manual_backup.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_manual_backup.clicked.connect(self.manual_backup)
        
        self.btn_restore_backup = QPushButton("Відновити базу з файлу")
        self.btn_restore_backup.setObjectName("navButton")
        self.btn_restore_backup.setFixedWidth(200)
        self.btn_restore_backup.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_restore_backup.clicked.connect(self.manual_restore)

        self.btn_view_log = QPushButton("Переглянути лог бекапів")
        self.btn_view_log.setObjectName("navButton")
        self.btn_view_log.setFixedWidth(200)
        self.btn_view_log.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_view_log.clicked.connect(self.view_backup_log)
        
        buttons_h_layout = QHBoxLayout()
        buttons_h_layout.addWidget(self.btn_manual_backup)
        buttons_h_layout.addWidget(self.btn_restore_backup)
        buttons_h_layout.addWidget(self.btn_view_log)
        buttons_h_layout.addStretch()
        
        backup_layout.addRow("", buttons_h_layout)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)

        # Кнопка збереження (тепер всередині скролу)
        self.save_btn = QPushButton("Зберегти всі налаштування", self)
        self.save_btn.setObjectName("navButton")
        self.save_btn.setFixedWidth(400)
        self.save_btn.setFixedHeight(50)
        self.save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_btn.clicked.connect(self.save_all)
        layout.addWidget(self.save_btn, alignment=Qt.AlignCenter)
        
        layout.addStretch(1) # Додаємо розпірку знизу

        # Встановлюємо контейнер у скрол і скрол у головний лейаут
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def select_backup_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Виберіть папку для бекапів")
        if directory:
            self.backup_path.setText(directory)

    def select_pg_tools_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Оберіть папку 'bin' встановленого PostgreSQL")
        if directory:
            self.pg_tools_path.setText(directory)

    def toggle_time_visibility(self):
        """Ховає або показує вибір часу залежно від частоти."""
        is_time_needed = self.backup_freq.currentData() == "at_time"
        self.backup_time.setVisible(is_time_needed)
        self.backup_time_label.setVisible(is_time_needed)

    def manual_backup(self):
        """Виконує бекап вручну при натисканні кнопки."""
        try:
            from PyQt5.QtWidgets import QApplication
            QApplication.setOverrideCursor(Qt.WaitCursor)
            success = perform_backup()
            QApplication.restoreOverrideCursor()
            
            if success:
                show_success(self, "Резервну копію успішно створено!")
            else:
                show_error(self, "Не вдалося створити бекап. Перевірте шлях у налаштуваннях.")
        except Exception as e:
            from PyQt5.QtWidgets import QApplication
            QApplication.restoreOverrideCursor()
            log_error("Помилка ручного бекапу", e)
            show_error(self, f"Помилка: {str(e)}")

    def manual_restore(self):
        """Виконує відновлення бази з обраного файлу з українізованим підтвердженням."""
        reply = ask_confirmation(
            self,
            "Ви збираєтесь відновити базу даних з архіву.\n\n"
            "УСІ ПОТОЧНІ ДАНІ БУДУТЬ ЗАМІНЕНІ даними з обраного бекапу!\n"
            "Це неможливо скасувати. Ви впевнені?",
            "УВАГА: Відновлення бази даних"
        )
        
        if reply:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Оберіть файл бекапу", 
                self.backup_path.text(), 
                "Backup Files (*.sql *.backup *.zip);;All Files (*)"
            )
            
            if file_path:
                try:
                    from PyQt5.QtWidgets import QApplication
                    QApplication.setOverrideCursor(Qt.WaitCursor)
                    success, message = restore_backup(file_path)
                    QApplication.restoreOverrideCursor()
                    
                    if success:
                        show_info(self, "Базу даних успішно відновлено!")
                    else:
                        show_error_msg(self, f"Помилка відновлення:\n{message}")
                except Exception as e:
                    from PyQt5.QtWidgets import QApplication
                    QApplication.restoreOverrideCursor()
                    show_error_msg(self, f"Критична помилка: {str(e)}")
                    QApplication.restoreOverrideCursor()
                    
                    if success:
                        show_success(self, "Базу даних успішно відновлено!")
                    else:
                        show_error(self, f"Помилка відновлення:\n{message}")
                except Exception as e:
                    from PyQt5.QtWidgets import QApplication
                    QApplication.restoreOverrideCursor()
                    log_error("Помилка ручного відновлення", e)
                    show_error(self, f"Критична помилка: {str(e)}")

    def view_backup_log(self):
        """Відкриває файл логування бекапів у стандартному редакторі."""
        import os
        # Шлях до логу в корені проекту
        script_dir = os.path.dirname(os.path.abspath(__file__)) # pages/admin
        project_root = os.path.dirname(os.path.dirname(script_dir))
        log_path = os.path.join(project_root, "backup_log.txt")
        
        if os.path.exists(log_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(log_path))
        else:
            show_error(self, "Файл логів ще не створено (бекапи ще не запускалися).")

    def load_settings(self):
        try:
            # Завантаження даних закладу
            inst_info = self.inst_repo.get_info()
            if inst_info:
                # row: id, full_name, short_name, address, director_name, contact_phone, logo_path
                self.inst_full_name.setText(str(inst_info[1] or ""))
                self.inst_short_name.setText(str(inst_info[2] or ""))
                self.inst_address.setText(str(inst_info[3] or ""))
                self.inst_director.setText(str(inst_info[4] or ""))
                self.inst_phone.setText(str(inst_info[5] or ""))

            # Завантаження налаштувань бекапу та посадових осіб
            all_s = self.settings_repo.get_all_settings()
            
            self.resp_secretary.setText(all_s.get("resp_secretary", "Людмила ЧАЙКА"))
            self.deputy_secretary.setText(all_s.get("deputy_secretary", "Костянтин СИДОРУК"))
            self.legal_counsel.setText(all_s.get("legal_counsel", "Тетяна ДЕНІСОВА"))
            self.edebo_admin.setText(all_s.get("edebo_admin", "Наталія ХОРУНЖА"))

            self.backup_path.setText(all_s.get("backup_path", "C:\\Vstup_Backups"))
            self.pg_tools_path.setText(all_s.get("pg_tools_path", ""))
            
            freq_key = all_s.get("backup_frequency", "off")
            index = self.backup_freq.findData(freq_key)
            if index >= 0:
                self.backup_freq.setCurrentIndex(index)
            
            self.toggle_time_visibility()
            
            b_time_str = all_s.get("backup_time", "00:00")
            h, m = map(int, b_time_str.split(":"))
            self.backup_time.setTime(QTime(h, m))

        except Exception as e:
            log_error("Помилка завантаження налаштувань", e)

    def save_all(self):
        try:
            # 1. Зберігаємо дані закладу
            inst_data = {
                "full_name": self.inst_full_name.text(),
                "short_name": self.inst_short_name.text(),
                "address": self.inst_address.text(),
                "director_name": self.inst_director.text(),
                "contact_phone": self.inst_phone.text(),
                "logo_path": "" # Поки порожньо
            }
            res1 = self.inst_repo.update_info(inst_data)

            # 2. Зберігаємо системні налаштування
            self.settings_repo.set_setting("college_name", self.inst_full_name.text())
            self.settings_repo.set_setting("college_short_name", self.inst_short_name.text())
            self.settings_repo.set_setting("resp_secretary", self.resp_secretary.text())
            self.settings_repo.set_setting("deputy_secretary", self.deputy_secretary.text())
            self.settings_repo.set_setting("legal_counsel", self.legal_counsel.text())
            self.settings_repo.set_setting("edebo_admin", self.edebo_admin.text())

            self.settings_repo.set_setting("backup_path", self.backup_path.text())
            self.settings_repo.set_setting("pg_tools_path", self.pg_tools_path.text())
            self.settings_repo.set_setting("backup_frequency", self.backup_freq.currentData())
            self.settings_repo.set_setting("backup_time", self.backup_time.time().toString("HH:mm"))
            
            # 3. Оновлюємо розклад у Windows
            schedule_backup()

            if res1:
                log_info("Адмін: Налаштування закладу та бекапів збережено")
                show_success(self, "Налаштування збережено та розклад бекапів оновлено!")
            else:
                log_error("Адмін: Часткова помилка при збереженні (дані закладу)")
                show_error(self, "Часткова помилка при збереженні (дані закладу).")

        except Exception as e:
            log_error("Помилка збереження налаштувань", e)
            show_error(self, f"Помилка: {str(e)}")
