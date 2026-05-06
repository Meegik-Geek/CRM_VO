import os
from db.connect_db import setup_database
from utils.logger import log_error, log_info

def apply_migrations():
    """
    Виконує оновлення структури бази даних.
    Ця функція викликається апдейтером після копіювання нових файлів.
    """
    log_info("Запуск міграцій бази даних...")
    conn = None
    try:
        conn = setup_database()
        cursor = conn.cursor()
        
        # 1. Міграція: (Виконано: Додавання gpa_score)
        
        # Тут можна буде додавати наступні міграції...
        # if not column_exists('another_table', 'new_col'): ...

        conn.commit()
        log_info("Міграції бази даних успішно завершені.")
        return True
    except Exception as e:
        log_error("Критична помилка під час міграції БД", e)
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Можна запустити вручну для тесту
    apply_migrations()
