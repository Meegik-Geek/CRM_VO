from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QLineEdit, QHeaderView, QDialog, QCheckBox, QScrollArea, QLabel
)
from PyQt5.QtCore import Qt
from db.connect_db import setup_database, close_database
from utils.notifications import show_success, show_error, ask_confirmation
import json
import hashlib

class PermissionsDialog(QDialog):
    """Вікно для вибору прав доступу (чекбокси для меню)"""
    def __init__(self, parent, current_permissions):
        super().__init__(parent)
        self.setWindowTitle("Налаштування прав доступу")
        self.setMinimumSize(400, 500)
        self.permissions = current_permissions
        self.checkboxes = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.scroll_layout = QVBoxLayout(content)

        # Список всіх пунктів меню з AdminPage
        self.menu_items = [
            "Головна",
            "Список вступників (денна)", "Список особових справ (денна)", "Список особових справ (денна) скорочена",
            "Список пільг вступників (денна)", "Список спеціальностей (денна)", "Список секретарів (денна)",
            "Список вступних випробувань (денна)", "Список вступних випробувань (денна) скорочена",
            "Список вступників (заочна)", "Список особових справ (заочна)", "Список пільг вступників (заочна)",
            "Список спеціальностей (заочна)", "Список секретарів (заочна)", "Список вступних випробувань (заочна)",
            "Список галузі знань", "Список пільг загальні", "Введення балів випробувань",
            "Звіти вступної кампанії", "Журнали вступної кампанії", "Протоколи/Допуски вступної кампанії",
            "Графіки", "Створення типу фінансування та груп", "Витяги, звіти студентів",
            "Налаштування системи", "Системні оновлення"
        ]

        for item in self.menu_items:
            cb = QCheckBox(item)
            cb.setChecked(self.permissions.get(item, False))
            self.scroll_layout.addWidget(cb)
            self.checkboxes[item] = cb

        scroll.setWidget(content)
        layout.addWidget(scroll)

        btn_save = QPushButton("Зберегти права")
        btn_save.setObjectName("greenButton")
        btn_save.clicked.connect(self.accept)
        layout.addWidget(btn_save)

    def get_permissions(self):
        return {item: cb.isChecked() for item, cb in self.checkboxes.items()}

class UsersPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_users()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        
        self.title = QLabel("Керування користувачами системи")
        self.title.setObjectName("titleLabel")
        self.layout.addWidget(self.title)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Відповідальна особа", "Логін", "Пароль", "Дія"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

    def load_users(self):
        """Завантажує відповідальних осіб з налаштувань та їхні облікові записи"""
        conn = setup_database()
        if not conn: return
        try:
            cursor = conn.cursor()
            
            # Ключі в таблиці settings для відповідальних осіб
            resp_keys = ["resp_secretary", "deputy_secretary", "legal_counsel", "edebo_admin"]
            resp_persons = []
            
            for key in resp_keys:
                cursor.execute("SELECT value FROM settings WHERE key = %s", (key,))
                res = cursor.fetchone()
                if res and res[0]:
                    resp_persons.append(res[0])

            # Завантажуємо існуючих користувачів з БД
            cursor.execute("SELECT person_name, login, permissions FROM system_users")
            existing_users = {row[0]: {"login": row[1], "perms": row[2]} for row in cursor.fetchall()}

            self.table.setRowCount(len(resp_persons))
            for i, name in enumerate(resp_persons):
                self.table.setItem(i, 0, QTableWidgetItem(name))
                
                # Знаходимо користувача за ім'ям особи (або за логіном, якщо він уже є)
                user_info = {"login": "", "perms": {}}
                for p_name, info in existing_users.items():
                    if p_name == name:
                        user_info = info
                        break
                
                login_edit = QLineEdit(user_info["login"])
                login_edit.setPlaceholderText("Логін")
                self.table.setCellWidget(i, 1, login_edit)

                pass_edit = QLineEdit()
                pass_edit.setPlaceholderText("Новий пароль")
                pass_edit.setEchoMode(QLineEdit.Password)
                self.table.setCellWidget(i, 2, pass_edit)

                btn_action = QPushButton("Надати доступ")
                btn_action.setObjectName("navButton")
                # Використовуємо замикання для збереження значень
                btn_action.clicked.connect(lambda ch, n=name, l=login_edit, p=pass_edit, pr=user_info["perms"]: 
                                         self.setup_access(n, l, p, pr))
                self.table.setCellWidget(i, 3, btn_action)

        except Exception as e:
            print(f"Помилка завантаження користувачів: {e}")
        finally:
            close_database(conn)

    def setup_access(self, name, login_edit, pass_edit, current_perms):
        login = login_edit.text().strip()
        password = pass_edit.text().strip()

        if not login:
            show_error(self, "Логін не може бути порожнім!")
            return

        dialog = PermissionsDialog(self, current_perms)
        if dialog.exec_() == QDialog.Accepted:
            new_perms = dialog.get_permissions()
            self.save_user(name, login, password, new_perms)

    def save_user(self, name, login, password, permissions):
        conn = setup_database()
        if not conn: return
        try:
            cursor = conn.cursor()
            
            if password:
                # Хешуємо пароль
                pwd_hash = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute("""
                    INSERT INTO system_users (person_name, login, password_hash, permissions)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (login) DO UPDATE SET 
                        password_hash = EXCLUDED.password_hash,
                        permissions = EXCLUDED.permissions,
                        person_name = EXCLUDED.person_name
                """, (name, login, pwd_hash, json.dumps(permissions)))
            else:
                # Оновлюємо без пароля (якщо він не введений)
                cursor.execute("""
                    INSERT INTO system_users (person_name, login, password_hash, permissions)
                    VALUES (%s, %s, 'nopass', %s)
                    ON CONFLICT (login) DO UPDATE SET 
                        permissions = EXCLUDED.permissions,
                        person_name = EXCLUDED.person_name
                """, (name, login, json.dumps(permissions)))

            conn.commit()
            show_success(self, f"Доступ для {name} успішно налаштовано!")
            self.load_users() # Оновлюємо таблицю
        except Exception as e:
            show_error(self, f"Помилка збереження: {e}")
        finally:
            close_database(conn)
