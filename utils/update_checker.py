import os
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from db.connect_db import get_setting

class UpdateCheckerThread(QThread):
    # Сигнали:
    # 1. Глобальне оновлення (є на GitHub, але ще нема локально) -> Показує інфо-сповіщення
    # 2. Локальне оновлення (є в локальній БД дозвіл) -> Показує кнопку "Перезавантажити Оновити"
    global_update_available = pyqtSignal(str) 
    admin_update_available = pyqtSignal(str, str, str) # version, method, path

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            # Читаємо локальну версію з version.txt
            local_version_file = "version.txt"
            my_version = "1.0.0-0"
            if os.path.exists(local_version_file):
                with open(local_version_file, "r") as f:
                    my_version = f.read().strip()
            
            # Читаємо з БД дозволену адміном версію
            admin_version = get_setting('admin_approved_version', my_version)
            method = get_setting('update_delivery_method', 'NONE')
            url_path = get_setting('update_path', '')

            # Якщо адмінська версія новіша за нашу -> сповіщаємо про обов'язкове оновлення!
            if self._compare_versions(admin_version, my_version) > 0:
                self.admin_update_available.emit(admin_version, method, url_path)
                return  # Більше нічого не треба, це пріоритет.

            # Якщо ні, перевіримо GitHub
            github_repo = os.getenv('GITHUB_REPO', '')
            if github_repo:
                try:
                    resp = requests.get(f"https://api.github.com/repos/{github_repo}/releases/latest", timeout=3)
                    if resp.status_code == 200:
                        data = resp.json()
                        github_version = data.get("tag_name", "").replace('v', '') + "-0"
                        if self._compare_versions(github_version, my_version) > 0:
                            # Сповіщаємо, що просто є нова в інтернеті
                            self.global_update_available.emit(github_version)
                except Exception as e:
                    print("Не вдалося перевірити GitHub:", e)

        except Exception as e:
            print("Помилка в UpdateCheckerThread:", e)

    def _compare_versions(self, v1, v2):
        """Повертає 1 якщо v1 > v2, -1 якщо v1 < v2, 0 якщо рівні. Версія у форматі X.Y.Z-L"""
        try:
            base1, patch1 = v1.split('-') if '-' in v1 else (v1, "0")
            base2, patch2 = v2.split('-') if '-' in v2 else (v2, "0")
            
            parts1 = [int(x) for x in base1.split('.')]
            parts2 = [int(x) for x in base2.split('.')]
            
            for p1, p2 in zip(parts1, parts2):
                if p1 > p2: return 1
                if p1 < p2: return -1
                
            if int(patch1) > int(patch2): return 1
            if int(patch1) < int(patch2): return -1
            
            return 0
        except:
            return 0
