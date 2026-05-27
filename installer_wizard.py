import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QLabel, 
    QLineEdit, QRadioButton, QButtonGroup, QGroupBox, QFormLayout,
    QProgressBar, QTextEdit
)

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QIcon
import psycopg2
from psycopg2 import sql


try:
    from utils.notifications import show_error_msg, show_info
except ImportError:
    # Фоллбек якщо інсталятор запускається окремо
    from PyQt5.QtWidgets import QMessageBox
    def show_error_msg(parent, title, msg): QMessageBox.critical(parent, title, msg)
    def show_info(parent, title, msg): QMessageBox.information(parent, title, msg)

class InstallWorker(QThread):
    """Потік для виконання тривалих операцій інсталяції."""
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        def safe_str(e):
            """Надійно перетворює виключення в рядок, уникаючи UnicodeDecodeError."""
            try:
                return str(e)
            except:
                try:
                    return repr(e)
                except:
                    return "Невідома помилка підключення (помилка декодування тексту)"

        try:
            self.log.emit("Початок інсталяції...")
            self.progress.emit(10)
            self.log.emit("Створення конфігураційного файлу .env...")
            env_content = (
                f"DB_NAME={self.config['db_name']}\n"
                f"DB_USER={self.config['db_user']}\n"
                f"DB_PASSWORD={self.config['db_pass']}\n"
                f"DB_HOST={self.config['db_host']}\n"
                f"DB_PORT={self.config['db_port']}\n"
                f"ADMIN_LOGIN={self.config.get('admin_login', 'admin')}\n"
                f"ADMIN_PASSWORD={self.config.get('admin_pass', '')}\n"
                f"GITHUB_REPO=Meegik-Geek/CRM_VO\n"
            )
            with open(".env", "w", encoding="utf-8") as f:
                f.write(env_content)

            
            # 2. Перевірка/Створення бази даних
            self.progress.emit(30)
            
            if self.config.get("is_server"):
                self.log.emit("Налаштування бази даних на локальному сервері...")
                
                # Дочекаємося запуску служби
                import time
                max_retries = 5
                conn = None
                last_error_msg = ""
                
                for i in range(max_retries):
                    try:
                        conn = psycopg2.connect(
                            host=self.config['db_host'],
                            port=self.config['db_port'],
                            user=self.config['db_user'],
                            password=self.config['db_pass'],
                            dbname='postgres',
                            connect_timeout=5
                        )
                        break
                    except (psycopg2.Error, UnicodeDecodeError, Exception) as e:
                        # Якщо це помилка декодування - це майже напевно локалізоване повідомлення про пароль
                        if isinstance(e, UnicodeDecodeError):
                            last_error_msg = "Помилка авторизації: невірний пароль для користувача 'postgres' (локалізоване повідомлення системи)."
                        else:
                            last_error_msg = safe_str(e)
                            
                        if i == max_retries - 1:
                            if "password authentication failed" in last_error_msg.lower() or "authorization" in last_error_msg.lower():
                                raise Exception("Невірний пароль для користувача 'postgres'. Будь ласка, вкажіть пароль, який ви задали під час встановлення PostgreSQL.")
                            
                            # Якщо ми так і не розшифрували, але була помилка Unicode
                            if "UnicodeDecodeError" in last_error_msg or not last_error_msg:
                                raise Exception("Не вдалося підключитися до PostgreSQL. Найімовірніше: невірний пароль користувача 'postgres'.")
                                
                            raise Exception(last_error_msg)
                        
                        self.log.emit(f"Очікування запуску PostgreSQL ({i+1}/{max_retries})...")
                        time.sleep(5)

                if not conn:
                    raise Exception(last_error_msg or "Не вдалося встановити підключення до PostgreSQL")

                conn.autocommit = True
                data_dir = ""
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [self.config['db_name']])
                    if not cur.fetchone():
                        self.log.emit(f"Створення бази даних {self.config['db_name']}...")
                        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.config['db_name'])))
                    
                    # Отримуємо шлях до папки даних
                    cur.execute("SHOW data_directory;")
                    data_dir = cur.fetchone()[0]
                conn.close()

                # Налаштовуємо віддалений доступ
                if data_dir:
                    self.configure_postgres_remote(data_dir)

                # 3. Розгортання схеми (Тільки для сервера!)
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
                    sql_content = ""
                    encodings = ['utf-8', 'cp1251', 'latin-1']
                    for enc in encodings:
                        try:
                            with open("db/init_db.sql", "r", encoding=enc) as f:
                                sql_content = f.read()
                            break 
                        except UnicodeDecodeError:
                            continue
                    
                    if not sql_content:
                        raise Exception("Не вдалося прочитати файл db/init_db.sql")
                    
                    cur.execute(sql_content)
                target_conn.commit()
                target_conn.close()
            else:
                self.log.emit(f"Перевірка підключення до сервера {self.config['db_host']}...")
                test_conn = psycopg2.connect(
                    host=self.config['db_host'],
                    port=self.config['db_port'],
                    user=self.config['db_user'],
                    password=self.config['db_pass'],
                    dbname=self.config['db_name']
                )
                test_conn.close()
                self.log.emit("✅ Підключення до сервера успішне!")


            # 4. Створення сховища оновлень для сервера
            if self.config.get("is_server"):
                self.progress.emit(80)
                self.log.emit("Налаштування мережевої папки для системних оновлень...")
                try:
                    updater_path = r"C:\CRM_VO_Updater"
                    if not os.path.exists(updater_path):
                        os.makedirs(updater_path)
                    
                    import subprocess
                    check_share = subprocess.run(["net", "share", "CRM_VO_Updater"], capture_output=True)
                    stdout = check_share.stdout.decode('cp1251', errors='replace')
                    if "CRM_VO_Updater" not in stdout:
                        subprocess.run(["icacls", updater_path, "/grant", "Everyone:(OI)(CI)F", "/T"], capture_output=True)
                        subprocess.run(
                            ["net", "share", f"CRM_VO_Updater={updater_path}", "/GRANT:Everyone,FULL"], 
                            capture_output=True
                        )
                        self.log.emit(f"Папку {updater_path} успішно розшарено з повним доступом!")
                    else:
                        self.log.emit("Мережева папка 'CRM_VO_Updater' вже налаштована.")
                    
                    import socket
                    hostname = socket.gethostname()
                    unc_path = f"\\\\{hostname}\\CRM_VO_Updater"
                    
                    target_conn = psycopg2.connect(
                        host=self.config['db_host'],
                        port=self.config['db_port'],
                        user=self.config['db_user'],
                        password=self.config['db_pass'],
                        dbname=self.config['db_name']
                    )
                    with target_conn.cursor() as cur:
                        cur.execute("UPDATE settings SET value = %s WHERE key = 'update_path'", (unc_path,))
                        cur.execute("UPDATE settings SET value = 'LOCAL' WHERE key = 'update_delivery_method'")
                    target_conn.commit()
                    target_conn.close()
                    self.log.emit(f"Шлях оновлень встановлено: {unc_path}")
                except Exception as share_e:
                    self.log.emit(f"Попередження (Оновлення): не вдалося налаштувати доступ - {safe_str(share_e)}")

            self.progress.emit(100)
            self.finished.emit(True, "Інсталяцію успішно завершено!")
            
        except Exception as e:
            error_text = safe_str(e)
            # Якщо навіть safe_str повернув UnicodeDecodeError в тексті - замінюємо на людську мову
            if "utf-8' codec can't decode" in error_text:
                error_text = "Невірний пароль для бази даних або помилка підключення до PostgreSQL."
            
            self.log.emit(f"❌ ПОМИЛКА: {error_text}")
            self.finished.emit(False, error_text)

    def configure_postgres_remote(self, data_dir):
        """Налаштовує віддалений доступ до PostgreSQL."""
        try:
            self.log.emit("Налаштування віддаленого доступу до бази даних...")
            
            # 1. Windows Firewall
            port = self.config['db_port']
            fw_cmd = f'powershell -Command "New-NetFirewallRule -DisplayName \'PostgreSQL CRM\' -Direction Inbound -LocalPort {port} -Protocol TCP -Action Allow"'
            subprocess.run(fw_cmd, shell=True, capture_output=True)
            self.log.emit(f"✅ Порт {port} відкрито в Брандмауері.")

            # 2. postgresql.conf
            pg_conf_path = os.path.join(data_dir, "postgresql.conf")
            if os.path.exists(pg_conf_path):
                with open(pg_conf_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                if "listen_addresses = '*'" not in content:
                    # Шукаємо закоментований або існуючий рядок і замінюємо
                    import re
                    if re.search(r"^#?listen_addresses\s*=", content, re.MULTILINE):
                        content = re.sub(r"^#?listen_addresses\s*=.*", "listen_addresses = '*'", content, flags=re.MULTILINE)
                    else:
                        content += "\nlisten_addresses = '*'\n"
                    
                    with open(pg_conf_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    self.log.emit("✅ Увімкнено прослуховування всіх адрес у postgresql.conf")

            # 3. pg_hba.conf
            hba_path = os.path.join(data_dir, "pg_hba.conf")
            if os.path.exists(hba_path):
                with open(hba_path, "r", encoding="utf-8", errors="ignore") as f:
                    hba_content = f.read()
                
                rule = "\nhost    all             all             0.0.0.0/0               scram-sha-256\n"
                if "0.0.0.0/0" not in hba_content:
                    with open(hba_path, "a", encoding="utf-8") as f:
                        f.write(rule)
                    self.log.emit("✅ Додано правило доступу 0.0.0.0/0 (scram-sha-256) у pg_hba.conf")

            # 4. Перезапуск служби
            self.log.emit("Перезапуск служби PostgreSQL для застосування налаштувань...")
            # Намагаємось знайти ім'я служби через sc
            find_service = subprocess.run('sc query type= service state= all | findstr /i "postgresql"', shell=True, capture_output=True, text=True)
            service_name = ""
            for line in find_service.stdout.splitlines():
                if "SERVICE_NAME" in line:
                    service_name = line.split(":")[1].strip()
                    break
            
            if service_name:
                subprocess.run(f"net stop {service_name}", shell=True, capture_output=True)
                subprocess.run(f"net start {service_name}", shell=True, capture_output=True)
                self.log.emit(f"✅ Службу {service_name} перезапущено.")
            else:
                self.log.emit("⚠️ Не вдалося знайти ім'я служби для автоматичного перезапуску. Будь ласка, перезапустіть PostgreSQL вручну.")

        except Exception as e:
            self.log.emit(f"⚠️ Попередження (Remote Config): {str(e)}")

class AdminSetupPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Обліковий запис адміністратора")
        self.setSubTitle("Створіть логін та пароль для супер-адміністратора системи")
        layout = QFormLayout(self)
        
        self.admin_login = QLineEdit("admin")
        self.admin_pass = QLineEdit()
        self.admin_pass.setEchoMode(QLineEdit.Password)
        self.admin_pass_confirm = QLineEdit()
        self.admin_pass_confirm.setEchoMode(QLineEdit.Password)
        
        layout.addRow("Логін адміністратора:", self.admin_login)
        layout.addRow("Пароль:", self.admin_pass)
        layout.addRow("Підтвердіть пароль:", self.admin_pass_confirm)
        
        self.registerField("admin_login*", self.admin_login)
        self.registerField("admin_pass", self.admin_pass)
        self.registerField("admin_pass_confirm", self.admin_pass_confirm)
        
        # Важливо: підключаємо сигнали для миттєвого оновлення кнопки "Далі"
        self.admin_pass.textChanged.connect(self.completeChanged)
        self.admin_pass_confirm.textChanged.connect(self.completeChanged)
        self.admin_login.textChanged.connect(self.completeChanged)


    def isComplete(self):
        return (len(self.field("admin_pass")) >= 4 and 
                self.field("admin_pass") == self.field("admin_pass_confirm"))

class IntroPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Ласкаво просимо до CRM Вступ.Офіс")
        layout = QVBoxLayout(self)
        label = QLabel(
            "Цей майстер допоможе вам налаштувати систему для першого запуску.\n\n"
            "Буде виконано:\n"
            "• Налаштування підключення до бази даних PostgreSQL\n"
            "• Створення необхідних таблиць та структур\n"
            "• Налаштування облікового запису адміністратора"
        )
        label.setWordWrap(True)
        layout.addWidget(label)

        group_box = QGroupBox("Тип інсталяції")
        group_layout = QVBoxLayout(group_box)
        
        self.radio_server = QRadioButton("СЕРВЕР (База даних на цьому ПК)")
        self.radio_client = QRadioButton("КЛІЄНТ (Підключення до іншого ПК)")
        self.radio_server.setChecked(True)
        
        group_layout.addWidget(self.radio_server)
        group_layout.addWidget(self.radio_client)
        layout.addWidget(group_box)
        
        self.registerField("is_server", self.radio_server)

class DbConfigPage(QWizardPage):

    def __init__(self):
        super().__init__()
        self.setTitle("Параметри бази даних")
        self.setSubTitle("Вкажіть дані для доступу до сервера PostgreSQL")
        
        layout = QFormLayout(self)
        
        self.host_edit = QLineEdit("localhost")
        self.port_edit = QLineEdit("5432")
        self.name_edit = QLineEdit("vstup")
        self.user_edit = QLineEdit("postgres")
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.Password)
        
        layout.addRow("Адреса сервера (IP):", self.host_edit)
        layout.addRow("Порт:", self.port_edit)
        layout.addRow("Назва бази даних:", self.name_edit)
        layout.addRow("Користувач (DB User):", self.user_edit)
        layout.addRow("Пароль (DB Pass):", self.pass_edit)
        
        self.registerField("db_host", self.host_edit)
        self.registerField("db_port", self.port_edit)
        self.registerField("db_name", self.name_edit)
        self.registerField("db_user", self.user_edit)
        self.registerField("db_pass*", self.pass_edit)
        
        # Оновлення кнопки при зміні будь-якого поля
        for edit in [self.host_edit, self.port_edit, self.name_edit, self.user_edit, self.pass_edit]:
            edit.textChanged.connect(self.completeChanged)

    def isComplete(self):
        # Сторінка готова, якщо заповнені основні поля (пароль може бути порожнім)
        return (bool(self.field("db_host")) and 
                bool(self.field("db_port")) and 
                bool(self.field("db_name")) and 
                bool(self.field("db_user")))



    def initializePage(self):
        if self.field("is_server"):
            self.host_edit.setText("localhost")
            self.host_edit.setEnabled(False)
        else:
            self.host_edit.setEnabled(True)
        
        # Примусово кажемо майстру перевірити готовність сторінки
        self.completeChanged.emit()



class ProgressPage(QWizardPage):

    def __init__(self):
        super().__init__()
        self.setTitle("Процес інсталяції")
        layout = QVBoxLayout(self)
        
        self.bar = QProgressBar()
        layout.addWidget(self.bar)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 9))
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
            "admin_login": self.field("admin_login"),
            "admin_pass": self.field("admin_pass")
        }

        
        self.worker = InstallWorker(config)
        self.worker.progress.connect(self.bar.setValue)
        self.worker.log.connect(self.log_view.append)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, success, message):
        if success:
            self.log_view.append("\n" + "✅ " + message)
            self.is_complete = True
            self.completeChanged.emit()
        else:
            self.log_view.append(f"\n❌ ПОМИЛКА: {message}")
            show_error_msg(self, "Помилка інсталяції", f"Виникла помилка: {message}")


    def isComplete(self):
        return self.is_complete

class InstallerWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CRM Вступ.Офіс - Налаштування системи")
        self.setWizardStyle(QWizard.ModernStyle)
        self.resize(700, 500)
        
        # Налаштування кнопок (Українізація)
        self.setButtonText(QWizard.NextButton, "Далі >")
        self.setButtonText(QWizard.BackButton, "< Назад")
        self.setButtonText(QWizard.FinishButton, "Завершити")
        self.setButtonText(QWizard.CancelButton, "Скасувати")
        
        self.addPage(IntroPage())
        self.addPage(DbConfigPage())
        self.addPage(AdminSetupPage())
        self.addPage(ProgressPage())

        if os.path.exists("resource/logo.ico"):
            self.setWindowIcon(QIcon("resource/logo.ico"))
        elif os.path.exists("resource/logo.png"):
            self.setWindowIcon(QIcon("resource/logo.png"))

        if os.path.exists("resource/logo.png"):
            self.setPixmap(QWizard.LogoPixmap, QPixmap("resource/logo.png"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    wizard = InstallerWizard()
    wizard.show()
    sys.exit(app.exec_())
