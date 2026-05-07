import sys
import os
import subprocess
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon
from pages.home_page import HomePage
from db.connect_db import setup_database, close_database
from utils.notifications import ask_confirmation, show_error_msg

# Завантаження налаштувань (вже завантажені в connect_db, але про всяк випадок)
from dotenv import load_dotenv
load_dotenv()


def check_database_connection():
    # Якщо нема .env - це перша інсталяція
    if not os.path.exists(".env"):
        reply = ask_confirmation(
            None, 
            "Конфігураційний файл не знайдено. Запустити майстер налаштування?",
            "Перший запуск"
        )
        if reply:
            run_installer()
        sys.exit(0)


    try:
        connection = setup_database()
        if not connection:
            raise Exception("Не вдалося підключитися до бази даних.")
        close_database(connection)
    except Exception as e:
        reply = ask_confirmation(
            None, 
            f"Не вдається підключитись до бази:\n{e}\n\nЗапустити майстер налаштування для перевірки параметрів?",
            "Помилка бази даних"
        )
        if reply:
            run_installer()
        sys.exit(1)


def run_installer():
    """Запускає процес інсталяції"""
    try:
        # Можемо запустити як окремий скрипт або імпортувати
        # Запускаємо окремим процесом для чистоти
        subprocess.run([sys.executable, "installer_wizard.py"])
    except Exception as e:
        QMessageBox.critical(None, "Критична помилка", f"Не вдалося запустити інсталятор: {e}")

def main():
    app = QApplication(sys.argv)
    check_database_connection()

    # Налаштування іконки
    try:
        app.setWindowIcon(QIcon("resource/logo.svg"))
    except Exception:
        print("Попередження: іконка не знайдена.")

    window = HomePage()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()



# python setup.py clean --all
# python setup.py build
