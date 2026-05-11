import os
import sys
import shutil
import subprocess
import requests
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, 
    QProgressBar, QHBoxLayout, QGroupBox, QApplication,
    QTextEdit, QScrollArea
)
from utils.notifications import show_info, show_warning_msg, show_error_msg, ask_confirmation
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QCursor
from db.connect_db import get_setting, setup_database
from utils.logger import log_error, log_info


class GitHubInfoThread(QThread):
    result = pyqtSignal(dict)

    def __init__(self, repo):
        super().__init__()
        self.repo = repo

    def run(self):
        try:
            resp = requests.get(
                f"https://api.github.com/repos/{self.repo}/releases/latest",
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                url = None
                for asset in data.get('assets', []):
                    if asset['name'].endswith('.zip'):
                        url = asset['browser_download_url']
                        break
                if not url:
                    url = data.get('zipball_url', '')
                self.result.emit({
                    'ok': True,
                    'tag': data.get('tag_name', '').replace('v', ''),
                    'body': data.get('body', 'Опис відсутній.'),
                    'url': url
                })
            else:
                self.result.emit({'ok': False, 'error': f'HTTP {resp.status_code}'})
        except Exception as e:
            self.result.emit({'ok': False, 'error': str(e)})

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, url, dest_path):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            response = requests.get(self.url, stream=True, timeout=10)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            block_size = 1024
            downloaded = 0
            
            with open(self.dest_path, 'wb') as file:
                for data in response.iter_content(block_size):
                    file.write(data)
                    downloaded += len(data)
                    if total_size > 0:
                        prog = int((downloaded / total_size) * 100)
                        self.progress.emit(prog)
            
            self.progress.emit(100)
            self.finished.emit(True, "Завантаження завершено.")
        except Exception as e:
            self.finished.emit(False, str(e))

class UpdatesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.check_latest_global_version()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.addStretch()

        # 0. ІНФОРМАЦІЯ
        info_group = QGroupBox("Інформація")
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(8)

        # Поточна версія
        local_ver = '1.0.0-0'
        try:
            if os.path.exists('version.txt'):
                with open('version.txt', 'r') as f:
                    local_ver = f.read().strip()
                if '-' not in local_ver:
                    local_ver += "-0"
        except Exception:
            pass

        self.info_local_lbl = QLabel(f"Поточна версія програми: <b>v{local_ver}</b>")
        self.info_local_lbl.setTextFormat(Qt.RichText)
        info_layout.addWidget(self.info_local_lbl)

        self.info_github_lbl = QLabel("Перевірка GitHub...")
        info_layout.addWidget(self.info_github_lbl)

        # Блок нового релізу (захований за замовчуванням)
        self.info_release_widget = QWidget()
        release_layout = QVBoxLayout(self.info_release_widget)
        release_layout.setContentsMargins(0, 0, 0, 0)
        release_layout.setSpacing(10)

        self.info_release_title = QLabel()
        self.info_release_title.setTextFormat(Qt.RichText)
        release_layout.addWidget(self.info_release_title)

        # Тільки опис у вигляді панелі
        self.description_group = QGroupBox("Опис оновлення")
        desc_layout = QVBoxLayout(self.description_group)
        self.info_release_body = QLabel()
        self.info_release_body.setWordWrap(True)
        self.info_release_body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        desc_layout.addWidget(self.info_release_body)
        release_layout.addWidget(self.description_group)

        self.btn_info_update = QPushButton("Оновити та перезавантажити")
        self.btn_info_update.setObjectName("greenButton")
        self.btn_info_update.setMinimumHeight(36)
        self.btn_info_update.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_info_update.setToolTip("Програма закриється! Збережіть внесені дані!")
        self.btn_info_update.clicked.connect(self._run_info_updater)
        release_layout.addWidget(self.btn_info_update, alignment=Qt.AlignLeft)

        self.info_release_widget.hide()
        info_layout.addWidget(self.info_release_widget)
        layout.addWidget(info_group)

        # 1. СТАТУС ВЕРСІЙ В БД
        status_group = QGroupBox("Поточний стан сервера")
        status_layout = QVBoxLayout(status_group)
        
        self.db_version_lbl = QLabel(f"Затверджена версія (роздається клієнтам): <b>{get_setting('admin_approved_version', '1.0.0-0')}  </b>")
        self.db_version_lbl.setTextFormat(Qt.RichText)
        self.db_method_lbl = QLabel(f"Метод доставки: <b>{get_setting('update_delivery_method', 'NONE')}</b>")
        self.db_method_lbl.setTextFormat(Qt.RichText)
        self.db_path_lbl = QLabel(f"Шлях: <b>{get_setting('update_path', 'Немає')}</b>")
        self.db_path_lbl.setTextFormat(Qt.RichText)
        
        status_layout.addWidget(self.db_version_lbl)
        status_layout.addWidget(self.db_method_lbl)
        status_layout.addWidget(self.db_path_lbl)

        self.btn_check_access = QPushButton("Перевірити доступ до шляху")
        self.btn_check_access.setObjectName("greenButton")
        self.btn_check_access.setMinimumHeight(30)
        self.btn_check_access.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_check_access.clicked.connect(self.check_access)
        status_layout.addWidget(self.btn_check_access, alignment=Qt.AlignLeft)
        
        layout.addWidget(status_group)

        # 2. ОНОВЛЕННЯ З GITHUB
        github_group = QGroupBox("Оновлення з Інтернету (GitHub)")
        github_layout = QVBoxLayout(github_group)
        
        self.github_status_lbl = QLabel("Перевірка версій на GitHub...")
        github_layout.addWidget(self.github_status_lbl)
        
        btn_layout_1 = QHBoxLayout()
        self.btn_download_local = QPushButton("Завантажити і роздати локально (Варіант А)")
        self.btn_download_local.setObjectName("greenButton")
        self.btn_download_local.setMinimumHeight(40)
        self.btn_download_local.clicked.connect(self.deploy_local_from_github)
        
        self.btn_set_internet = QPushButton("Роздати вказівку качати з Інтернету (Варіант Б)")
        self.btn_set_internet.setObjectName("greenButton")
        self.btn_set_internet.setMinimumHeight(40)
        self.btn_set_internet.clicked.connect(self.deploy_internet_from_github)
        
        btn_layout_1.addWidget(self.btn_download_local)
        btn_layout_1.addWidget(self.btn_set_internet)
        github_layout.addLayout(btn_layout_1)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        github_layout.addWidget(self.progress_bar)
        
        layout.addWidget(github_group)

        # 3. ВЛАСНІ КАСТОМНІ ПАТЧІ
        custom_group = QGroupBox("Власний локальний патч")
        custom_layout = QVBoxLayout(custom_group)
        
        custom_layout.addWidget(QLabel("Використовується, якщо ви власноруч модифікували файли і хочете розповсюдити на всі ПК.\nЦе автоматично збільшить номер патчу (напр. з -0 на -1)."))
        
        self.btn_custom_patch = QPushButton("Вибрати архів (update.zip) та розповсюдити")
        self.btn_custom_patch.setObjectName("greenButton")
        self.btn_custom_patch.setMinimumHeight(40)
        self.btn_custom_patch.clicked.connect(self.deploy_custom_patch)
        custom_layout.addWidget(self.btn_custom_patch)
        
        layout.addWidget(custom_group)
        layout.addStretch()

        self.latest_github_version = None
        self.latest_github_url = None

    def check_latest_global_version(self):
        github_repo = os.getenv('GITHUB_REPO', '')
        if not github_repo:
            self.github_status_lbl.setText("Помилка: GITHUB_REPO не вказано в .env")
            self.info_github_lbl.setText("Статус GitHub: GITHUB_REPO не налаштовано")
            self.info_github_lbl.setStyleSheet("color: #e74c3c;")
            return

        # Запуск потоку для розділу Інформація
        self._info_thread = GitHubInfoThread(github_repo)
        self._info_thread.result.connect(self._on_info_received)
        self._info_thread.start()

        # Запуск потоку для розділу GitHub
        try:
            resp = requests.get(f"https://api.github.com/repos/{github_repo}/releases/latest", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                tag = data.get("tag_name", "1.0.0").replace('v', '')
                self.latest_github_version = tag + "-0"
                for asset in data.get('assets', []):
                    if asset['name'].endswith('.zip'):
                        self.latest_github_url = asset['browser_download_url']
                        break
                if not self.latest_github_url:
                    self.latest_github_url = data.get('zipball_url')
                self.github_status_lbl.setText(f"Остання версія на GitHub: <b>{tag}</b>")
            else:
                self.github_status_lbl.setText(f"Не вдалося перевірити GitHub (Status: {resp.status_code})")
        except Exception as e:
            self.github_status_lbl.setText(f"Помилка з'єднання: <b>Немає з'єднання з сервісом</b>")

    def _on_info_received(self, data):
        if not data.get('ok'):
            err = data.get('error', '')
            self.info_github_lbl.setTextFormat(Qt.RichText)
            self.info_github_lbl.setText(f"Статус GitHub: <b>Помилка з'єднання</b>")
            return

        self.info_github_lbl.setTextFormat(Qt.RichText)
        self.info_github_lbl.setText("Статус GitHub: <b>Підключено</b>")
        self.info_github_lbl.setStyleSheet("")

        tag = data['tag']
        gh_ver = tag + "-0"
        self._info_update_url = data['url']
        self._info_update_version = gh_ver

        # Порівнюємо з локальною версією
        local_ver = '1.0.0-0'
        try:
            if os.path.exists('version.txt'):
                with open('version.txt', 'r') as f:
                    local_ver = f.read().strip()
            if '-' not in local_ver:
                local_ver = local_ver + '-0'
        except Exception:
            pass

        def ver_tuple(v):
            base, p = v.split('-') if '-' in v else (v, '0')
            return tuple(int(x) for x in base.split('.')) + (int(p),)

        if ver_tuple(gh_ver) > ver_tuple(local_ver):
            self.info_release_title.setText(f"Знайдено нову версію: <b>v{tag}</b>")
            self.info_release_body.setText(data['body'])
            self.info_release_widget.show()
        else:
            lbl = QLabel("<b>У вас встановлена остання версія.</b>")
            lbl.setTextFormat(Qt.RichText)
            self.info_release_widget.parent().layout().addWidget(lbl)

    def _run_info_updater(self):
        if not hasattr(self, '_info_update_url') or not self._info_update_url:
            show_warning_msg(self, "Посилання на архів не знайдено.")
            return
        reply = ask_confirmation(
            self, 
            "Програма закриється, виконається оновлення та автоматично перезапускається.\nЗбережіть внесені дані!\n\nРозпочати?",
            "Підтвердження"
        )
        if not reply:
            return

        updater = "updater.exe" if os.path.exists("updater.exe") else sys.executable
        args = [updater]
        if updater == sys.executable:
            args.append("updater.py")
        args.extend(["INTERNET", self._info_update_url, self._info_update_version])
        subprocess.Popen(args)
        QApplication.quit()

    def check_access(self):
        method = get_setting('update_delivery_method', 'NONE')
        path = get_setting('update_path', '')
        
        if method == 'NONE':
            show_info(self, "Метод оновлення не встановлено.")
            return
        
        if method == 'INTERNET':
            try:
                resp = requests.head(path, timeout=5)
                if resp.status_code == 200:
                    show_info(self, "Посилання в Інтернеті доступне (HTTP 200).")
                else:
                    show_warning_msg(self, f"Сервер повернув помилку: {resp.status_code}")
            except Exception as e:
                show_error_msg(self, f"Не вдалося перевірити посилання:\n{e}")

        
        else: # LOCAL
            if not path:
                show_warning_msg(self, "Шлях до локального оновлення не вказано.", "Помилка")
                return
            
            if os.path.exists(path):
                show_info(self, f"Файл знайдено за шляхом:\n{path}\n\nКлієнти зможуть його скачати.")
            else:
                dir_path = os.path.dirname(path)
                if os.path.exists(dir_path):
                     show_warning_msg(self, f"Папка доступна, але ФАЙЛ 'update.zip' НЕ ЗНАЙДЕНО за шляхом:\n{path}")
                else:
                     show_error_msg(self, f"ШЛЯХ НЕДОСТУПНИЙ:\n{path}\n\nПеревірте налаштування мережевого доступу (SMB)!")


    def update_db_settings(self, version, method, path):
        try:
            conn = setup_database()
            cursor = conn.cursor()
            cursor.execute("UPDATE settings SET value = %s WHERE key = 'admin_approved_version'", (version,))
            cursor.execute("UPDATE settings SET value = %s WHERE key = 'update_delivery_method'", (method,))
            cursor.execute("UPDATE settings SET value = %s WHERE key = 'update_path'", (path,))
            conn.commit()
            conn.close()
            
            self.db_version_lbl.setText(f"Затверджена версія (роздається клієнтам): <b> {version}</b>")
            self.db_method_lbl.setText(f"Метод доставки: <b>{method}</b>")
            self.db_path_lbl.setText(f"Шлях: <b>{path}</b>")
            show_info(self, "Налаштування оновлень в БД збережено. Клієнти отримають сповіщення.")
        except Exception as e:
            show_error_msg(self, str(e), "Помилка БД")


    def _get_server_unc_path(self):
        import socket
        hostname = socket.gethostname()
        db_host = os.getenv('DB_HOST', 'localhost')
        
        # Якщо ми на сервері (localhost), використовуємо ім'я комп'ютера для мережевого шляху
        if db_host == 'localhost' or db_host == '127.0.0.1':
            return rf"\\{hostname}\CRM_VO_Updater\update.zip"
            
        return rf"\\{db_host}\CRM_VO_Updater\update.zip"

    def deploy_local_from_github(self):
        if not self.latest_github_url:
            show_warning_msg(self, "Не знайдено посилання на GitHub. Спочатку дочекайтеся перевірки.")
            return


        temp_dest = "temp_update.zip"
        self.btn_download_local.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
        self.thread = DownloadThread(self.latest_github_url, temp_dest)
        self.thread.progress.connect(self.progress_bar.setValue)
        self.thread.finished.connect(self._on_github_download_finished)
        self.thread.start()

    def _on_github_download_finished(self, success, msg):
        self.btn_download_local.setEnabled(True)
        self.progress_bar.hide()
        if not success:
            show_error_msg(self, f"Не вдалося завантажити: {msg}")
            return

            
        try:
            import socket
            hostname = socket.gethostname()
            db_host = os.getenv('DB_HOST', 'localhost')
            
            # Шлях для бази (завжди мережевий)
            if db_host == 'localhost' or db_host == '127.0.0.1':
                db_path = rf"\\{hostname}\CRM_VO_Updater\update.zip"
                local_dir = r"C:\CRM_VO_Updater"
            else:
                db_path = rf"\\{db_host}\CRM_VO_Updater\update.zip"
                local_dir = rf"\\{db_host}\CRM_VO_Updater"

            target_path = os.path.join(local_dir, "update.zip")
            
            if not os.path.exists(local_dir):
                os.makedirs(local_dir, exist_ok=True)
                
            shutil.move("temp_update.zip", target_path)
            self.update_db_settings(self.latest_github_version, "LOCAL", db_path)
        except Exception as e:
            show_error_msg(self, f"Не вдалося скопіювати файл на сервер:\n{e}", "Помилка файлової системи")

    def deploy_internet_from_github(self):
        if not self.latest_github_url:
            show_warning_msg(self, "Не знайдено посилання на GitHub.")
            return
        
        reply = ask_confirmation(self, "Ви хочете щоб всі локальні комп'ютери скачували оновлення з Інтернету?")
        if reply:
            self.update_db_settings(self.latest_github_version, "INTERNET", self.latest_github_url)


    def deploy_custom_patch(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Виберіть архів оновлення", "", "ZIP Files (*.zip)")
        if not file_path: return
        
        # Беремо базу з локального файлу, щоб патч відповідав поточному коду
        base_version = "1.0.0"
        try:
            if os.path.exists('version.txt'):
                with open('version.txt', 'r') as f:
                    base_version = f.read().strip().split('-')[0]
        except: pass

        current_db_version = get_setting('admin_approved_version', base_version + "-0")
        db_base, db_patch = current_db_version.split('-') if '-' in current_db_version else (current_db_version, "0")
        
        # Якщо база в БД така ж як наша поточна, інкрементуємо патч
        if db_base == base_version:
            new_patch = int(db_patch) + 1
        else:
            new_patch = 1
            
        new_version = f"{base_version}-{new_patch}"
        
        reply = ask_confirmation(self, f"Буде випущено локальний патч версії {new_version}.\nПочати копіювання на сервер?", "Розповсюдження патчу")
        if not reply: return
        
        try:
            import socket
            hostname = socket.gethostname()
            db_host = os.getenv('DB_HOST', 'localhost')
            
            # Шлях для бази (завжди мережевий)
            if db_host == 'localhost' or db_host == '127.0.0.1':
                db_path = rf"\\{hostname}\CRM_VO_Updater\update.zip"
                local_dir = r"C:\CRM_VO_Updater"
            else:
                db_path = rf"\\{db_host}\CRM_VO_Updater\update.zip"
                local_dir = rf"\\{db_host}\CRM_VO_Updater"

            target_path = os.path.join(local_dir, "update.zip")
            
            if not os.path.exists(local_dir):
                os.makedirs(local_dir, exist_ok=True)
                
            shutil.copy2(file_path, target_path)
            self.update_db_settings(new_version, "LOCAL", db_path)
        except Exception as e:
            show_error_msg(self, f"Не вдалося скопіювати файл на сервер:\n{e}", "Помилка файлової системи")
