import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QLabel, 
    QLineEdit, QRadioButton, QButtonGroup, QGroupBox, QFormLayout,
    QProgressBar, QTextEdit, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap
import psycopg2
from psycopg2 import sql

# Спроба імпортувати утиліти, якщо вони вже існують
try:
    from utils.notifications import show_error, show_success
except ImportError:
    # Фоллбек якщо інсталятор запускається окремо
    from PyQt5.QtWidgets import QMessageBox
    def show_error(parent, msg): QMessageBox.critical(parent, "Помилка", msg)
    def show_success(parent, msg): QMessageBox.information(parent, "Успіх", msg)

class InstallWorker(QThread):
    """Потік для виконання тривалих операцій інсталяції."""
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        try:
            self.log.emit("Початок інсталяції...")
            
            # 1. Створення .env файлу
            self.progress.emit(10)
            self.log.emit("Створення конфігураційного файлу .env...")
            env_content = (
                f"DB_NAME={self.config['db_name']}\n"
                f"DB_USER={self.config['db_user']}\n"
                f"DB_PASSWORD={self.config['db_pass']}\n"
                f"DB_HOST={self.config['db_host']}\n"
                f"DB_PORT={self.config['db_port']}\n"
            )
            with open(".env", "w", encoding="utf-8") as f:
                f.write(env_content)
            
            # 2. Перевірка/Створення бази даних
            self.progress.emit(30)
            self.log.emit(f"Підключення до PostgreSQL на {self.config['db_host']}...")
            
            # Спроба підключитися до postgres для створення цільової бази
            conn = psycopg2.connect(
                host=self.config['db_host'],
                port=self.config['db_port'],
                user=self.config['db_user'],
                password=self.config['db_pass'],
                dbname='postgres'
            )
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [self.config['db_name']])
                if not cur.fetchone():
                    self.log.emit(f"Створення бази даних {self.config['db_name']}...")
                    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.config['db_name'])))
            conn.close()

            # 3. Розгортання схеми
            self.progress.emit(60)
            self.log.emit("Розгортання схеми бази даних (init_db.sql)...")
            target_conn = psycopg2.connect(
                host=self.config['db_host'],
                port=self.config['db_port'],
                user=self.config['db_user'],
                password=self.config['db_pass'],
                dbname=self.config['db_name']
            )
            with target_conn.cursor() as cur:
                with open("db/init_db.sql", "r", encoding="utf-8") as f:
                    cur.execute(f.read())
                
                # Записуємо базові налаштування закладу
                self.log.emit("Збереження реквізитів закладу...")
                cur.execute(
                    "UPDATE institution_info SET full_name = %s WHERE id = 1",
                    (self.config.get('inst_name', 'Мій заклад'),)
                )
            target_conn.commit()
            target_conn.close()

            # 4. Створення сховища оновлень для сервера
            if self.config.get("is_server"):
                self.progress.emit(80)
                self.log.emit("Налаштування мережевої папки для системних оновлень...")
                try:
                    updater_path = r"C:\CRM_VO_Updater"
                    if not os.path.exists(updater_path):
                        os.makedirs(updater_path)
                    
                    import subprocess
                    check_share = subprocess.run(["net", "share", "CRM_VO_Updater"], capture_output=True, text=True)
                    if "CRM_VO_Updater" not in check_share.stdout:
                        subprocess.run(
                            ["net", "share", f"CRM_VO_Updater={updater_path}", "/GRANT:Everyone,FULL"], 
                            check=True, 
                            capture_output=True
                        )
                        self.log.emit(f"Папку {updater_path} успішно розшарено як 'CRM_VO_Updater'!")
                    else:
                        self.log.emit("Мережева папка 'CRM_VO_Updater' вже налаштована.")
                except Exception as share_e:
                    self.log.emit(f"Попередження (Оновлення): не вдалося налаштувати доступ - {share_e}")

            self.progress.emit(100)
            self.finished.emit(True, "Інсталяцію успішно завершено!")
            
        except Exception as e:
            self.finished.emit(False, str(e))

class IntroPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Ласкаво просимо до Вступ 2026")
        layout = QVBoxLayout(self)
        label = QLabel(
            "Цей майстер допоможе вам налаштувати систему для першого запуску.\n\n"
            "Виберіть тип інсталяції:\n"
            "1. СЕРВЕР - якщо база даних буде зберігатися на цьому комп'ютері.\n"
            "2. КЛІЄНТ - якщо ви підключаєтесь до існуючого сервера в мережі."
        )
        label.setWordWrap(True)
        layout.addWidget(label)

        self.group = QButtonGroup(self)
        self.radio_server = QRadioButton("Сервер (Повна інсталяція)")
        self.radio_client = QRadioButton("Клієнт (Тільки підключення)")
        self.radio_server.setChecked(True)
        
        self.group.addButton(self.radio_server)
        self.group.addButton(self.radio_client)
        
        layout.addWidget(self.radio_server)
        layout.addWidget(self.radio_client)
        
        self.registerField("is_server", self.radio_server)

class DbConfigPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Налаштування бази даних")
        self.setSubTitle("Введіть параметри підключення до PostgreSQL")
        
        layout = QFormLayout(self)
        
        self.host_edit = QLineEdit("localhost")
        self.port_edit = QLineEdit("5432")
        self.name_edit = QLineEdit("vstup")
        self.user_edit = QLineEdit("postgres")
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.Password)
        
        layout.addRow("Адреса хоста:", self.host_edit)
        layout.addRow("Порт:", self.port_edit)
        layout.addRow("Назва бази:", self.name_edit)
        layout.addRow("Користувач:", self.user_edit)
        layout.addRow("Пароль:", self.pass_edit)
        
        self.registerField("db_host*", self.host_edit)
        self.registerField("db_port*", self.port_edit)
        self.registerField("db_name*", self.name_edit)
        self.registerField("db_user*", self.user_edit)
        self.registerField("db_pass*", self.pass_edit)

    def initializePage(self):
        if self.field("is_server"):
            self.host_edit.setText("localhost")
            self.host_edit.setEnabled(False)
        else:
            self.host_edit.setEnabled(True)

class InstitutionPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Дані закладу")
        layout = QFormLayout(self)
        
        self.inst_name = QLineEdit()
        layout.addRow("Повна назва закладу:", self.inst_name)
        self.registerField("inst_name*", self.inst_name)

class ProgressPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Виконання інсталяції")
        layout = QVBoxLayout(self)
        
        self.bar = QProgressBar()
        layout.addWidget(self.bar)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)
        
        self.is_complete = False

    def initializePage(self):
        config = {
            "is_server": self.field("is_server"),
            "db_host": self.field("db_host"),
            "db_port": self.field("db_port"),
            "db_name": self.field("db_name"),
            "db_user": self.field("db_user"),
            "db_pass": self.field("db_pass"),
            "inst_name": self.field("inst_name")
        }
        
        self.worker = InstallWorker(config)
        self.worker.progress.connect(self.bar.setValue)
        self.worker.log.connect(self.log_view.append)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, success, message):
        if success:
            self.log_view.append("\n" + message)
            self.is_complete = True
            self.completeChanged.emit()
        else:
            self.log_view.append(f"\nПОМИЛКА: {message}")
            show_error(self, f"Виникла помилка: {message}")

    def isComplete(self):
        return self.is_complete

class InstallerWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вступ 2026 - Майстер налаштування")
        self.setWizardStyle(QWizard.ModernStyle)
        self.resize(600, 450)
        
        self.addPage(IntroPage())
        self.addPage(DbConfigPage())
        self.addPage(InstitutionPage())
        self.addPage(ProgressPage())
        
        self.setButtonText(QWizard.FinishButton, "Завершити")
        self.setButtonText(QWizard.CancelButton, "Скасувати")
        self.setButtonText(QWizard.NextButton, "Далі >")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    wizard = InstallerWizard()
    wizard.show()
    sys.exit(app.exec_())
