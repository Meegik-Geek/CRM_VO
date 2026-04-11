import os
import subprocess
from datetime import datetime
from db.connect_db import setup_database, close_database, get_setting
import sys

def perform_backup():
    """Виконує резервне копіювання бази даних."""
    backup_path = get_setting("backup_path", "C:\\Vstup_Backups")
    
    # Створюємо папку, якщо вона не існує
    if not os.path.exists(backup_path):
        try:
            os.makedirs(backup_path)
        except Exception as e:
            print(f"Помилка створення папки для бекапів: {e}")
            return False

    # Параметри підключення з .env (які підхоплює setup_database)
    # Оскільки ми використовуємо pg_dump, нам потрібні змінні середовища для пароля
    db_name = os.getenv("DB_NAME", "vstup")
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(backup_path, f"vstup_backup_{timestamp}.sql")

    # Встановлюємо пароль для pg_dump через змінну середовища
    os.environ["PGPASSWORD"] = db_pass

    try:
        # Шукаємо pg_dump (можна додати пошук у програмних файлах, якщо немає в PATH)
        pg_dump_path = "pg_dump" 
        
        command = [
            pg_dump_path,
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-F", "c", # Сферичний формат (custom) для pg_restore
            "-b", # Включити великі об'єкти
            "-v", # Verbose
            "-f", filename,
            db_name
        ]

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"Бекап успішно створено: {filename}")
            # Оновлюємо дату останнього запуску в БД
            conn = setup_database()
            cursor = conn.cursor()
            cursor.execute("UPDATE settings SET value = %s WHERE key = 'backup_last_run'", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
            conn.commit()
            close_database(conn)
            return True
        else:
            print(f"Помилка pg_dump: {result.stderr}")
            return False

    except Exception as e:
        print(f"Виняток при виконанні бекапу: {e}")
        return False

def restore_backup(backup_file, db_name=None):
    """Відновлює базу даних з файлу бекапу."""
    if not db_name:
        db_name = os.getenv("DB_NAME", "vstup")
    
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")

    os.environ["PGPASSWORD"] = db_pass

    try:
        # Шукаємо pg_restore
        pg_restore_path = "pg_restore"
        
        command = [
            pg_restore_path,
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            "-v", # Verbose
            "--clean", # Очистити базу перед відновленням
            "--if-exists",
            backup_file
        ]

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            print("Базу даних успішно відновлено.")
            return True, "Успішно відновлено!"
        else:
            # Деякі "терпимі" помилки можуть бути в stderr, але якщо returncode 0 то ок.
            # Якщо returncode не 0, це проблема.
            print(f"Помилка pg_restore: {result.stderr}")
            return False, result.stderr

    except Exception as e:
        return False, str(e)

def schedule_backup():
    """Реєструє завдання в Windows Task Scheduler."""
    frequency = get_setting("backup_frequency", "daily")
    if frequency == "off":
        print("Автоматичний бекап вимкнено.")
        return

    backup_time = get_setting("backup_time", "00:00")
    
    # Шлях до поточного інтерпретатора та цього скрипта
    python_exe = sys.executable
    script_path = os.path.abspath(__file__)
    
    task_name = "Vstup2026_AutoBackup"
    
    # Команда для створення завдання через schtasks
    # Приклад: щодня в зазначений час
    if frequency == "daily":
        cmd = f'schtasks /create /tn "{task_name}" /tr "\\"\\"{python_exe}\\" \\"{script_path}\\" --run\\"" /sc daily /st {backup_time} /f'
    elif frequency == "weekly":
        cmd = f'schtasks /create /tn "{task_name}" /tr "\\"\\"{python_exe}\\" \\"{script_path}\\" --run\\"" /sc weekly /d MON /st {backup_time} /f'
    elif frequency == "3h":
        cmd = f'schtasks /create /tn "{task_name}" /tr "\\"\\"{python_exe}\\" \\"{script_path}\\" --run\\"" /sc hourly /mo 3 /f'
    else:
        print(f"Невідома частота: {frequency}")
        return

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Завдання '{task_name}' успішно заплановано ({frequency}).")
        else:
            print(f"Помилка schtasks: {result.stderr}")
    except Exception as e:
        print(f"Виняток при плануванні завдання: {e}")

if __name__ == "__main__":
    # Якщо скрипт запущено з аргументом --run, виконуємо бекап
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        perform_backup()
    else:
        # Для тестів або налаштування
        print("Запуск управління бекапами...")
        # perform_backup()
        # schedule_backup()
