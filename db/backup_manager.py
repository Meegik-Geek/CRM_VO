import os
import subprocess
import sys
from datetime import datetime
import ctypes
# --- ДИНАМІЧНЕ ВИЗНАЧЕННЯ ШЛЯХІВ (МАЄ БУТИ ПЕРЕД ІМПОРТАМИ ПРОЕКТУ) ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Тепер можна імпортувати модулі проекту
from db.connect_db import setup_database, close_database, get_setting
import shutil
from dotenv import load_dotenv

# Завантажуємо .env з кореня проекту
load_dotenv(os.path.join(project_root, ".env"))

def log_to_file(message):
    """Записує повідомлення у лог-файл."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_path = os.path.join(project_root, "backup_log.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

def find_pg_tool(tool_name):
    """Шукає шлях до pg_dump або pg_restore."""
    # 1. Перевіряємо шлях з налаштувань
    user_pg_path = get_setting("pg_tools_path", "")
    if user_pg_path and os.path.exists(user_pg_path):
        full_path = os.path.join(user_pg_path, tool_name + ".exe")
        if os.path.exists(full_path):
            return full_path

    # 2. Перевіряємо чи він є в PATH
    tool_path = shutil.which(tool_name)
    if tool_path:
        return tool_path

    # 3. Шукаємо в стандартних папках PostgreSQL
    common_paths = [
        r"C:\Program Files\PostgreSQL\19\bin",
        r"C:\Program Files\PostgreSQL\18\bin",
        r"C:\Program Files\PostgreSQL\17\bin",
        r"C:\Program Files\PostgreSQL\16\bin",
        r"C:\Program Files\PostgreSQL\15\bin",
        r"C:\Program Files\PostgreSQL\14\bin",
        r"C:\Program Files\PostgreSQL\13\bin",
        r"C:\Program Files\PostgreSQL\12\bin",
        r"C:\Program Files\PostgreSQL\11\bin"
    ]
    
    for path in common_paths:
        full_path = os.path.join(path, tool_name + ".exe")
        if os.path.exists(full_path):
            return full_path
            
    return None

def perform_backup():
    """Виконує резервне копіювання бази даних."""
    backup_path = get_setting("backup_path", "C:\\Vstup_Backups")
    
        # Створюємо папку, якщо вона не існує
    if not os.path.exists(backup_path):
        try:
            os.makedirs(backup_path)
        except Exception as e:
            msg = f"Помилка створення папки для бекапів: {e}"
            print(msg)
            log_to_file(msg)
            return False

    # Перевірка прав на запис у папку
    try:
        test_file = os.path.join(backup_path, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        msg = fr"Помилка доступу до папки бекапів: {e}. Оберіть іншу папку (не на диску C:\ безпосередньо)."
        print(msg)
        log_to_file(msg)
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
        # Шукаємо pg_dump
        pg_dump_path = find_pg_tool("pg_dump")
        if not pg_dump_path:
            print("Помилка: pg_dump не знайдено. Встановіть PostgreSQL або додайте шлях до bin у PATH.")
            return False
        
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
            msg = f"Бекап успішно створено: {filename}"
            log_to_file(msg)
            # Оновлюємо дату останнього запуску в БД
            conn = setup_database()
            cursor = conn.cursor()
            cursor.execute("UPDATE settings SET value = %s WHERE key = 'backup_last_run'", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
            conn.commit()
            close_database(conn)
            return True
        else:
            msg = f"Помилка pg_dump: {result.stderr.strip()}"
            log_to_file(msg)
            return False

    except Exception as e:
        msg = f"Виняток при виконанні бекапу: {e}"
        log_to_file(msg)
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
        pg_restore_path = find_pg_tool("pg_restore")
        if not pg_restore_path:
            return False, "pg_restore не знайдено. Встановіть PostgreSQL."
        
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
            return True, "Успішно відновлено!"
        else:
            # Деякі "терпимі" помилки можуть бути в stderr, але якщо returncode 0 то ок.
            # Якщо returncode не 0, це проблема.
            log_to_file(f"Помилка pg_restore: {result.stderr}")
            return False, result.stderr

    except Exception as e:
        return False, str(e)
def get_short_path(long_path):
    """Конвертує шлях з кирилицею/пробілами у короткий формат Windows 8.3."""
    buf = ctypes.create_unicode_buffer(260)
    ctypes.windll.kernel32.GetShortPathNameW(str(long_path), buf, 260)
    return buf.value if buf.value else long_path
def schedule_backup():
    """Реєструє завдання в Windows Task Scheduler."""
    frequency = get_setting("backup_frequency", "daily")
    if frequency == "off":
        return

    backup_time = get_setting("backup_time", "00:00")

    python_exe  = sys.executable
    script_path = os.path.abspath(__file__)
    log_path    = os.path.join(project_root, "backup_log.txt")
    task_name   = "Vstup2026_AutoBackup"
    bat_path    = os.path.join(project_root, "run_backup.bat")

    # Короткі шляхи — без кирилиці та пробілів, працюють на будь-якому ПК
    s_python  = get_short_path(python_exe)
    s_script  = get_short_path(script_path)
    s_log     = get_short_path(log_path)
    s_bat     = get_short_path(bat_path)

    try:
        with open(bat_path, "w", encoding="ascii", errors="replace") as f:
            f.write('@echo off\n')
            # Без cd — Python сам визначає project_root через __file__
            f.write(f'"{s_python}" "{s_script}" --run >> "{s_log}" 2>&1\n')
        log_to_file(f"Bat створено: {bat_path}")
        log_to_file(f"Короткі шляхи: python={s_python} | script={s_script}")
    except Exception as e:
        log_to_file(f"Помилка створення bat: {e}")
        return

    if frequency == "on_startup":
        cmd = [
            "schtasks", "/create",
            "/tn", task_name,
            "/tr", f'"{s_bat}"',
            "/sc", "ONSTART",
            "/ru", os.getenv("USERNAME", ""),
            "/f"
        ]
    else:
        cmd = [
            "schtasks", "/create",
            "/tn", task_name,
            "/tr", f'"{s_bat}"',
            "/sc", "DAILY",
            "/st", backup_time,
            "/ru", os.getenv("USERNAME", ""),
            "/f"
        ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="cp1251")
        if result.returncode == 0:
            msg = f"Планувальник зареєстровано: {frequency} о {backup_time}"
            log_to_file(msg)
        else:
            msg = f"Помилка schtasks: {result.stderr.strip()}"
            log_to_file(msg)
    except Exception as e:
        log_to_file(f"Виняток планування: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        log_to_file("Скрипт запущено Планувальником (--run)")
        perform_backup()
