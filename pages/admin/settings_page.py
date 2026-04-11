from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QFormLayout, QGroupBox, QFileDialog, QTimeEdit
)
from PyQt5.QtCore import Qt, QTime
from db.repository import SettingsRepository, InstitutionRepository
from db.backup_manager import schedule_backup
from utils.notifications import show_error, show_success
from utils.logger import log_error, log_info

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_repo = SettingsRepository()
        self.inst_repo = InstitutionRepository()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Налаштування системи", self)
        title.setObjectName("adminTitleLabel")
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
        self.backup_freq.addItems(["off", "3h", "daily", "weekly"])
        
        self.backup_time = QTimeEdit()
        self.backup_time.setDisplayFormat("HH:mm")

        backup_layout.addRow("Шлях до бекапів:", path_layout)
        backup_layout.addRow("Частота:", self.backup_freq)
        backup_layout.addRow("Час (для щодня/тиждень):", self.backup_time)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)

        # Кнопка збереження
        self.save_btn = QPushButton("Зберегти всі налаштування", self)
        self.save_btn.setObjectName("navButton")
        self.save_btn.setFixedWidth(300)
        self.save_btn.clicked.connect(self.save_all)
        layout.addWidget(self.save_btn, alignment=Qt.AlignCenter)

    def select_backup_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Виберіть папку для бекапів")
        if directory:
            self.backup_path.setText(directory)

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
            self.backup_freq.setCurrentText(all_s.get("backup_frequency", "daily"))
            
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
            self.settings_repo.set_setting("backup_frequency", self.backup_freq.currentText())
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
