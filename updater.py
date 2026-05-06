import os
import sys
import time
import shutil
import zipfile
import subprocess
import urllib.request
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, 
    QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QSettings
from PyQt5.QtGui import QColor, QFont

class UpdateWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, method, path, target_dir, version=None):
        super().__init__()
        self.method = method
        self.path = path
        self.target_dir = target_dir
        self.version = version

    def run(self):
        try:
            self.status.emit("Очікування завершення основної програми...")
            time.sleep(3)

            zip_path = self.path
            if self.method == "INTERNET":
                self.status.emit("Завантаження оновлення з GitHub...")
                zip_path = "temp_downloaded_update.zip"
                
                def reporthook(count, block_size, total_size):
                    if total_size > 0:
                        prog = int(count * block_size * 100 / total_size)
                        self.progress.emit(min(prog, 50))

                urllib.request.urlretrieve(self.path, zip_path, reporthook)
            else:
                self.progress.emit(30)

            self.status.emit("Розпакування архіву...")
            temp_extract_dir = "temp_update_extracted"
            if os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)
            os.makedirs(temp_extract_dir)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
            self.progress.emit(60)

            self.status.emit("Копіювання нових файлів...")
            source_dir = temp_extract_dir
            items = os.listdir(source_dir)
            if len(items) == 1 and os.path.isdir(os.path.join(source_dir, items[0])):
                source_dir = os.path.join(source_dir, items[0])

            files_to_copy = []
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file.lower() != "desktop.ini":
                        files_to_copy.append((root, file))

            total_files = len(files_to_copy)
            for i, (root, file) in enumerate(files_to_copy):
                rel_path = os.path.relpath(root, source_dir)
                target_root = os.path.join(self.target_dir, rel_path) if rel_path != "." else self.target_dir
                
                if not os.path.exists(target_root):
                    os.makedirs(target_root)
                
                src_file = os.path.join(root, file)
                dst_file = os.path.join(target_root, file)
                
                try:
                    shutil.copy2(src_file, dst_file)
                except Exception:
                    pass
                
                prog = 60 + int((i + 1) * 40 / total_files)
                self.progress.emit(prog)

            shutil.rmtree(temp_extract_dir, ignore_errors=True)
            if os.path.exists("temp_downloaded_update.zip"):
                os.remove("temp_downloaded_update.zip")

            # Оновлення файлу version.txt
            if self.version:
                try:
                    with open(os.path.join(self.target_dir, "version.txt"), "w", encoding="utf-8") as f:
                        f.write(self.version)
                except Exception:
                    pass

            # ЗАПУСК МІГРАЦІЙ БАЗИ ДАНИХ
            self.status.emit("Оновлення структури бази даних...")
            try:
                # Визначаємо як запустити скрипт міграції
                db_manager_path = os.path.join(self.target_dir, "utils", "db_manager.py")
                if os.path.exists(db_manager_path):
                    # Використовуємо той самий інтерпретатор, що і для апдейтера
                    subprocess.run([sys.executable, db_manager_path], check=False, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            except Exception as e:
                print(f"Помилка при запуску міграцій: {e}")

            self.status.emit("Оновлення завершено!")
            time.sleep(1)
            self.finished.emit(True, "Успіх")
        except Exception as e:
            self.finished.emit(False, str(e))

class UpdateUI(QWidget):
    def __init__(self, method, path):
        super().__init__()
        self.method = method
        self.path = path
        
        # Читання теми з налаштувань
        settings = QSettings("MyApp", "Settings")
        self.theme = settings.value("theme", "light")
        
        self.init_ui()
        self.start_update()

    def init_ui(self):
        # Визначення кольорів залежно від теми
        if self.theme == "light":
            bg_color = "#fdfdfd"
            text_color = "#333333"
            sub_text_color = "#7f8c8d"
            progress_bg = "#ecf0f1"
            progress_chunk = "#2ecc71"
            border_radius = "15px"
            shadow_color = QColor(0, 0, 0, 80)
        else: # grey/dark theme
            bg_color = "#2c3e50"
            text_color = "#ffffff"
            sub_text_color = "#bdc3c7"
            progress_bg = "#34495e"
            progress_chunk = "#2ecc71"
            border_radius = "15px"
            shadow_color = QColor(0, 0, 0, 150)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(400, 200)

        # Центрування
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # Контейнер
        self.container = QFrame(self)
        self.container.setGeometry(10, 10, 380, 180)
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: {border_radius};
            }}
        """)

        # Тінь
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(shadow_color)
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(30, 30, 30, 30)

        self.title_label = QLabel("Оновлення CRM Вступ.Офіс")
        self.title_label.setStyleSheet(f"color: {text_color}; font-size: 18px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        self.status_label = QLabel("Підготовка...")
        self.status_label.setStyleSheet(f"color: {sub_text_color}; font-size: 13px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {progress_bg};
                color: white;
                border-style: none;
                border-radius: 5px;
                text-align: center;
                height: 10px;
            }}
            QProgressBar::chunk {{
                background-color: {progress_chunk};
                border-radius: 5px;
            }}
        """)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

    def start_update(self):
        # Отримуємо версію з аргументів командного рядка (якщо є)
        version = sys.argv[3] if len(sys.argv) >= 4 else None
        self.worker = UpdateWorker(self.method, self.path, os.getcwd(), version)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self.status_label.setText)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, success, message):
        if not success:
            self.status_label.setText(f"Помилка: {message}")
            self.status_label.setStyleSheet("color: #e74c3c;")
            time.sleep(3)
        
        # Запуск програми
        main_exe = os.path.join(os.getcwd(), "main.exe")
        main_py = os.path.join(os.getcwd(), "main.py")
        
        if os.path.exists(main_exe):
            subprocess.Popen([main_exe])
        elif os.path.exists(main_py):
            subprocess.Popen([sys.executable, main_py])
        
        QApplication.quit()

def main():
    if len(sys.argv) < 3:
        return

    app = QApplication(sys.argv)
    
    # Встановлення шрифту
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    method = sys.argv[1]
    path = sys.argv[2]
    
    ui = UpdateUI(method, path)
    ui.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
