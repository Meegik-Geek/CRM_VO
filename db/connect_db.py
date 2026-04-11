import os
import psycopg2
from dotenv import load_dotenv

# Завантажуємо налаштування з .env
load_dotenv()

def read_db_config():
    return {
        'dbname': os.getenv('DB_NAME', 'vstup'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '12345'),
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': os.getenv('DB_PORT', '5432'),
        'connect_timeout': 5,
        'client_encoding': 'UTF8'
    }

def ensure_update_settings(conn):
    try:
        cursor = conn.cursor()
        settings = [
            ('global_latest_version', '1.0.0-0', 'Глобальна версія системи на GitHub'),
            ('admin_approved_version', '1.0.0-0', 'Версія, яку затвердив адміністратор'),
            ('update_delivery_method', 'NONE', 'Як роздавати: LOCAL, INTERNET, NONE'),
            ('update_path', '', 'Шлях для оновлення (UNC папка сервера або URL-посилання)')
        ]
        for key, default_val, desc in settings:
            cursor.execute("SELECT 1 FROM settings WHERE key = %s", (key,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO settings (key, value, description) VALUES (%s, %s, %s)",
                    (key, default_val, desc)
                )
        conn.commit()
    except Exception as e:
        print(f"Помилка ініціалізації налаштувань оновлень: {e}")

def setup_database():
    config = read_db_config()
    conn = psycopg2.connect(**config)
    ensure_update_settings(conn)
    return conn

def close_database(conn):
    if conn:
        conn.close()

def get_setting(key, default=None):
    """Отримує значення налаштування з таблиці settings або закладу."""
    conn = None
    try:
        conn = setup_database()
        cursor = conn.cursor()
        
        # Спершу шукаємо в settings
        cursor.execute("SELECT value FROM settings WHERE key = %s", (key,))
        result = cursor.fetchone()
        if result:
            return result[0]
            
        # Якщо шукаємо назви закладу, а їх нема в settings - беремо з institution_info
        if key == "college_name":
            cursor.execute("SELECT full_name FROM institution_info WHERE id = 1")
            res_inst = cursor.fetchone()
            if res_inst and res_inst[0]: return res_inst[0]

        if key == "college_short_name":
            cursor.execute("SELECT short_name FROM institution_info WHERE id = 1")
            res_inst = cursor.fetchone()
            if res_inst and res_inst[0]: return res_inst[0]
            
        if key == "college_address":
            cursor.execute("SELECT address FROM institution_info WHERE id = 1")
            res_inst = cursor.fetchone()
            if res_inst and res_inst[0]: return res_inst[0]

        if key == "director_name":
            cursor.execute("SELECT director_name FROM institution_info WHERE id = 1")
            res_inst = cursor.fetchone()
            if res_inst and res_inst[0]: return res_inst[0]
            
        return default
    except Exception as e:
        print(f"Помилка отримання налаштування {key}: {e}")
        return default
    finally:
        if conn:
            close_database(conn)
