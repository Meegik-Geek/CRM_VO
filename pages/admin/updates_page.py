import os
import shutil
import requests
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, 
    QMessageBox, QProgressBar, QHBoxLayout, QGroupBox, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from db.connect_db import get_setting, setup_database
from utils.logger import log_error, log_info

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

        # 1. СТАТУС ВЕРСІЙ В БД
        status_group = QGroupBox("Поточний стан сервера")
        status_layout = QVBoxLayout(status_group)
        
        self.db_version_lbl = QLabel(f"Затверджена версія (роздається клієнтам): {get_setting('admin_approved_version', '1.0.0-0')}")
        self.db_method_lbl = QLabel(f"Метод доставки: {get_setting('update_delivery_method', 'NONE')}")
        self.db_path_lbl = QLabel(f"Шлях: {get_setting('update_path', 'Немає')}")
        
        status_layout.addWidget(self.db_version_lbl)
        status_layout.addWidget(self.db_method_lbl)
        status_layout.addWidget(self.db_path_lbl)
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
            return
            
        try:
            resp = requests.get(f"https://api.github.com/repos/{github_repo}/releases/latest", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self.latest_github_version = data.get("tag_name", "1.0.0").replace('v', '') + "-0"
                
                # Знайти посилання на zip
                for asset in data.get('assets', []):
                    if asset['name'].endswith('.zip'):
                        self.latest_github_url = asset['browser_download_url']
                        break
                
                if not self.latest_github_url:
                    # Посилання на вихідний код
                    self.latest_github_url = data.get('zipball_url')
                
                self.github_status_lbl.setText(f"Остання версія на GitHub: {self.latest_github_version}")
            else:
                self.github_status_lbl.setText(f"Не вдалося перевірити GitHub (Status: {resp.status_code})")
        except Exception as e:
            self.github_status_lbl.setText(f"Помилка з'єднання: {e}")

    def update_db_settings(self, version, method, path):
        try:
            conn = setup_database()
            cursor = conn.cursor()
            cursor.execute("UPDATE settings SET value = %s WHERE key = 'admin_approved_version'", (version,))
            cursor.execute("UPDATE settings SET value = %s WHERE key = 'update_delivery_method'", (method,))
            cursor.execute("UPDATE settings SET value = %s WHERE key = 'update_path'", (path,))
            conn.commit()
            conn.close()
            
            self.db_version_lbl.setText(f"Затверджена версія (роздається клієнтам): {version}")
            self.db_method_lbl.setText(f"Метод доставки: {method}")
            self.db_path_lbl.setText(f"Шлях: {path}")
            QMessageBox.information(self, "Успіх", "Налаштування оновлень в БД збережено. Клієнти отримають сповіщення.")
        except Exception as e:
            QMessageBox.critical(self, "Помилка БД", str(e))

    def _get_server_unc_path(self):
        db_host = os.getenv('DB_HOST', 'localhost')
        if db_host == 'localhost' or db_host == '127.0.0.1':
            return r"C:\CRM_VO_Updater\update.zip"
        return rf"\\{db_host}\CRM_VO_Updater\update.zip"

    def deploy_local_from_github(self):
        if not self.latest_github_url:
            QMessageBox.warning(self, "Увага", "Не знайдено посилання на GitHub. Спочатку дочекайтеся перевірки.")
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
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити: {msg}")
            return
            
        try:
            target_path = self._get_server_unc_path()
            target_dir = os.path.dirname(target_path)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
                
            shutil.move("temp_update.zip", target_path)
            self.update_db_settings(self.latest_github_version, "LOCAL", target_path)
        except Exception as e:
            QMessageBox.critical(self, "Помилка файлової системи", f"Не вдалося скопіювати файл на сервер:\n{e}")

    def deploy_internet_from_github(self):
        if not self.latest_github_url:
            QMessageBox.warning(self, "Увага", "Не знайдено посилання на GitHub.")
            return
        
        reply = QMessageBox.question(self, "Підтвердження", "Ви хочете щоб всі локальні комп'ютери скачували оновлення з Інтернету?")
        if reply == QMessageBox.Yes:
            self.update_db_settings(self.latest_github_version, "INTERNET", self.latest_github_url)

    def deploy_custom_patch(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Виберіть архів оновлення", "", "ZIP Files (*.zip)")
        if not file_path: return
        
        current_version = get_setting('admin_approved_version', '1.0.0-0')
        base, patch = current_version.split('-') if '-' in current_version else (current_version, "0")
        new_patch = int(patch) + 1
        new_version = f"{base}-{new_patch}"
        
        reply = QMessageBox.question(self, "Розповсюдження патчу", f"Це підвищить версію локального патчу до {new_version}.\nПочати копіювання на сервер?")
        if reply != QMessageBox.Yes: return
        
        try:
            target_path = self._get_server_unc_path()
            target_dir = os.path.dirname(target_path)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
                
            shutil.copy2(file_path, target_path)
            self.update_db_settings(new_version, "LOCAL", target_path)
        except Exception as e:
            QMessageBox.critical(self, "Помилка файлової системи", f"Не вдалося скопіювати файл на сервер:\n{e}")
