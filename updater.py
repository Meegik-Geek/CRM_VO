import os
import sys
import time
import shutil
import zipfile
import subprocess
import urllib.request

def download_file(url, dest):
    print(f"Завантаження оновлення з {url}...")
    try:
        urllib.request.urlretrieve(url, dest)
        print("Завантаження завершено.")
        return True
    except Exception as e:
        print(f"Помилка завантаження: {e}")
        return False

def extract_and_copy(zip_path, target_dir):
    temp_extract_dir = "temp_update_extracted"
    if os.path.exists(temp_extract_dir):
        shutil.rmtree(temp_extract_dir)
        
    os.makedirs(temp_extract_dir)
    print(f"Розпакування архіву {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)
    except Exception as e:
        print(f"Помилка розпакування: {e}")
        return False

    # Зазвичай GitHub архів містить одну кореневу папку (репозиторій-гілка)
    # Знайдемо вміст
    source_dir = temp_extract_dir
    items = os.listdir(source_dir)
    if len(items) == 1 and os.path.isdir(os.path.join(source_dir, items[0])):
        source_dir = os.path.join(source_dir, items[0])

    print("Копіювання файлів...")
    for root, dirs, files in os.walk(source_dir):
        rel_path = os.path.relpath(root, source_dir)
        target_root = os.path.join(target_dir, rel_path) if rel_path != "." else target_dir

        if not os.path.exists(target_root):
            os.makedirs(target_root)

        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(target_root, file)
            try:
                shutil.copy2(src_file, dst_file)
            except Exception as e:
                print(f"Помилка копіювання {src_file} -> {dst_file}: {e}")

    # Прибираємо за собою
    shutil.rmtree("temp_update_extracted", ignore_errors=True)
    if os.path.exists("temp_downloaded_update.zip"):
        os.remove("temp_downloaded_update.zip")
    
    return True

def main():
    if len(sys.argv) < 3:
        print("Використання: updater.exe [LOCAL|INTERNET] [PATH_OR_URL]")
        time.sleep(5)
        return

    method = sys.argv[1]
    path = sys.argv[2]
    current_folder = os.getcwd()

    print("Очікування завершення основної програми (5 секунд)...")
    time.sleep(5)

    zip_path = path

    if method == "INTERNET":
        zip_path = "temp_downloaded_update.zip"
        success = download_file(path, zip_path)
        if not success:
            print("Оновлення скасовано через помилку завантаження.")
            time.sleep(5)
            return

    elif method == "LOCAL":
        if not os.path.exists(zip_path):
            print(f"Файл {zip_path} не знайдено!")
            time.sleep(5)
            return

    # Розпаковуємо та копіюємо
    success = extract_and_copy(zip_path, current_folder)

    if success:
        print("Оновлення успішно застосовано!")
    else:
        print("Оновлення завершилось з помилкою.")

    print("Запуск програми...")
    main_exe = os.path.join(current_folder, "main.exe")
    main_py = os.path.join(current_folder, "main.py")
    
    if os.path.exists(main_exe):
        subprocess.Popen([main_exe])
    elif os.path.exists(main_py):
        subprocess.Popen([sys.executable, main_py])
    else:
        print("Виконуваний файл не знайдено!")
        time.sleep(5)

if __name__ == "__main__":
    main()
