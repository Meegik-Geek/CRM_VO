import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

def setup_db():
    db_name = os.getenv("DB_NAME", "vstup")
    db_user = os.getenv("DB_USER", "postgres")
    db_pass = os.getenv("DB_PASSWORD", "12345")
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = os.getenv("DB_PORT", "5432")

    print(f"Connecting to PostgreSQL as {db_user}...")
    try:
        # Create database if not exists
        conn = psycopg2.connect(
            dbname="postgres",
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'")
        if not cur.fetchone():
            print(f"Creating database '{db_name}'...")
            cur.execute(f"CREATE DATABASE {db_name}")
        else:
            print(f"Database '{db_name}' already exists.")
        
        cur.close()
        conn.close()

        # Connect to newly created database and run init_db.sql
        print(f"Initializing database '{db_name}' from init_db.sql...")
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        cur = conn.cursor()
        
        sql_path = os.path.join("db", "init_db.sql")
        if os.path.exists(sql_path):
            with open(sql_path, "r", encoding="utf-8") as f:
                sql = f.read()
                cur.execute(sql)
            conn.commit()
            print("Database initialized successfully!")
        else:
            print(f"Error: {sql_path} not found.")
        
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error during DB setup: {e}")

if __name__ == "__main__":
    setup_db()
