import sys
import os
import glob
from cx_Freeze import setup, Executable
import site

# Set base for Windows GUI application (hides console window)
base = "Win32GUI" if sys.platform == "win32" else None

# Define build options for cx_Freeze
build_exe_options = {
    "packages": [
        "PyQt5",
        "psycopg2",
        "pandas",
        "docxtpl",
        "tkinter",
        "openpyxl",
        "jinja2",  # Required by docxtpl
        "numpy",   # Required by pandas
    ],
    "include_files": [
        ("resource", "resource"),          # Resource folder
        ("templates", "templates"),        # Templates folder
        ("pages", "pages"),                # Pages folder
        ("reports", "reports"),            # Reports folder
        ("db", "db"),                      # DB folder
        ("implement", "implement"),        # Implement folder
        ("version.txt", "version.txt"),    # Version file
        ("updater.exe", "updater.exe"),
        ("host.txt", "host.txt"),          # Host configuration
    ],
    "include_msvcr": True,                 # Include Microsoft Visual C++ runtime
    "excludes": [
        "PyQt5.QtQml",                    # Exclude unused PyQt5 modules
        "PyQt5.QtQuick",
        "PyQt5.QtWebEngineWidgets",
        "PyQt5.QtWebEngineCore",
        "tkinter.ttk",                    # Optional: reduce tkinter size
    ],
    "optimize": 2,                        # Optimize bytecode
    "silent": True,                       # Suppress warnings during build
}

# Handle psycopg2 DLLs and dependencies
site_packages_paths = site.getsitepackages()

libs_path = None
for path in site_packages_paths:
    possible_path = os.path.join(path, "psycopg2.libs")
    if os.path.exists(possible_path):
        libs_path = possible_path
        break

if libs_path:
    print(f"Знайдено psycopg2.libs за шляхом: {libs_path}")
    dll_files = glob.glob(os.path.join(libs_path, "*.dll"))

    for f in dll_files:
        if not os.path.exists(f):
            print(f"Увага: Файл {f} не знайдено.")
            continue

        basename = os.path.basename(f).lower()
        build_exe_options["include_files"].append((f, basename))

        # Якщо це libpq з хешем — додати копію як libpq.dll
        if basename.startswith("libpq") and basename.endswith(".dll") and basename != "libpq.dll":
            build_exe_options["include_files"].append((f, "libpq.dll"))
            print(f"Додано копію {basename} як libpq.dll")
else:
    print("⚠️ Увага: Папка psycopg2.libs не знайдена. Перевір встановлення psycopg2.")

# Verify existence of include_files
print("\nСписок включених файлів і папок:")
for src, dest in build_exe_options["include_files"]:
    if isinstance(src, str) and not os.path.exists(src):
        print(f"⚠️ Увага: Файл або папка {src} не знайдено. Це може спричинити помилки.")
    else:
        print(f"✅ {src} → {dest}")
# Setup configuration
setup(
    name="MyApp",
    version="1.0",
    description="Вступна система",
    author="Your Name",  # Optional: add your name or organization
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            script="main.py",
            base=base,
            target_name="main.exe",
            icon="resource/logo.ico" if os.path.exists("resource/logo.ico") else None,
        )
    ],
)