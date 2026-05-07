from PyQt5.QtWidgets import (
    QMainWindow, QListWidget, QSizePolicy, QListWidgetItem, QVBoxLayout, QWidget, 
    QPushButton, QSplitter, QLabel, QApplication, QFileDialog, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QFont
import os
from db.backup_manager import restore_backup
from utils.logger import log_error, log_info
from utils.notifications import show_error, show_success, ask_confirmation

# Імпорт всіх необхідних класів сторінок
from pages.admin.denne.vstupnik_denna import ListVstupnikDen
from pages.admin.denne.sprava_denna import ListSpravaDen
from pages.admin.denne.sprava_denna_scor import ListSpravaDenScor
from pages.admin.denne.pilga_denna import ListPilgaDen
from pages.admin.denne.specialnosti_denna import ListSpecialnostiDen
from pages.admin.denne.secretari_denna import ListSecretariDen
from pages.admin.denne.entrance_examination_denna import ListExamDen
from pages.admin.denne.entrance_examination_denna_scor import ListExamDenScor
from pages.admin.denne.scores_admin import ListEntranceScores
from pages.admin.denne.galuz_znan import ListGaluzZnan
from pages.admin.denne.pilgi import ListPilgi
from pages.admin.reports.admin_zvit_camp import AdminZvitCamp
from pages.admin.reports.admin_journal_camp import AdminJournalCamp
from pages.admin.reports.admin_protocol_camp import AdminProtocolCamp
from pages.admin.zaoch.vstupnik_zaoch import ListVstupnikZao
from pages.admin.zaoch.sprava_zaoch import ListSpravaZao
from pages.admin.zaoch.pilga_zaoch import ListPilgaZao
from pages.admin.zaoch.specialnosti_zaoch import ListSpecialnostiZao
from pages.admin.zaoch.secretari_zaoch import ListSecretariZao
from pages.admin.zaoch.entrance_examination_zaoch import ListExamZao

from pages.admin.student.student_input_list import ListInputStudent
from pages.admin.student.reports.student_druk_denne import StudentDrukDen
from pages.admin.charts.charts_page import ChartsPage
from pages.admin.users_page import UsersPage
from pages.admin.settings_page import SettingsPage
from pages.admin.updates_page import UpdatesPage

class InputAdminPage(QMainWindow):
    def __init__(self):
        super(InputAdminPage, self).__init__()

        # Налаштування головного вікна
        self.setWindowTitle("CRM Вступ.Офіс - Адмін панель")
        self.setGeometry(0, 0, 1400, 800)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.showMaximized()

        # Створення основного віджета
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        # Використання QSplitter для горизонтального поділу
        splitter = QSplitter(Qt.Horizontal)

        # Ліва частина - Список вікон і шаблонів
        self.table_list = QListWidget()
        self.table_list.setObjectName("tableList")
        self.populate_menu_items()

        splitter.addWidget(self.table_list)

        # Права частина - Панель з кнопками
        self.right_panel = QWidget()
        self.right_panel.setObjectName("rightPanel")
        self.right_layout = QVBoxLayout(self.right_panel)

        splitter.addWidget(self.right_panel)
        splitter.setSizes([236, 800])

        # Основний layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
        main_widget.setLayout(main_layout)

        # Підключення вибору пунктів списку до дій
        self.table_list.itemClicked.connect(self.on_item_clicked)

        # Вибираємо пункт "Головна" за замовчуванням і підсвічуємо його
        self.table_list.setCurrentRow(0)
        self.on_item_clicked(self.table_list.item(0))

    def populate_menu_items(self):
        """Додає розділи меню для лівої панелі з урахуванням прав доступу"""
        menu_structure = [
            (None, ["Головна"]),
            ("Форми (денна)", [
                "Список вступників (денна)", "Список особових справ (денна)", 
                "Список особових справ (денна) скорочена", "Список пільг вступників (денна)", 
                "Список спеціальностей (денна)", "Список секретарів (денна)", 
                "Список вступних випробувань (денна)", "Список вступних випробувань (денна) скорочена"
            ]),
            ("Форми (заочна)", [
                "Список вступників (заочна)", "Список особових справ (заочна)", 
                "Список пільг вступників (заочна)", "Список спеціальностей (заочна)", 
                "Список секретарів (заочна)", "Список вступних випробувань (заочна)"
            ]),
            ("Форми (загальні)", [
                "Список галузі знань", "Список пільг загальні", "Введення балів випробувань"
            ]),
            ("Друк", [
                "Звіти вступної кампанії", "Журнали вступної кампанії", 
                "Протоколи/Допуски вступної кампанії"
            ]),
            ("Аналітика", ["Графіки"]),
            ("Студенти", [
                "Створення типу фінансування та груп", "Витяги, звіти студентів"
            ]),
            ("Система", ["Користувачі", "Налаштування системи", "Системні оновлення"])
        ]

        from pages.home_page import current_user_permissions

        def can_show(name):
            if name == "Головна": return True
            if current_user_permissions == "all": return True
            return isinstance(current_user_permissions, dict) and current_user_permissions.get(name)

        for section_title, items in menu_structure:
            # Фільтруємо пункти розділу
            visible_items = [item for item in items if can_show(item)]
            
            if visible_items:
                if section_title:
                    self.add_section(section_title, bold=True)
                for item in visible_items:
                    self.add_menu_item(item)

    def add_section(self, name, bold=False):
        """Додає роздільник з секцією в список."""
        section = QListWidgetItem(name)
        section.setFlags(section.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
        font = QFont()
        font.setBold(bold)
        section.setFont(font)
        section.setBackground(Qt.lightGray)
        section.setTextAlignment(Qt.AlignCenter)
        self.table_list.addItem(section)

    def add_menu_item(self, name):
        """Додає елемент меню до списку"""
        item = QListWidgetItem(name)
        item.setFont(QFont("Arial", 11))
        item.setTextAlignment(Qt.AlignLeft)
        self.table_list.addItem(item)

    def clear_right_layout(self):
        """Очищуємо вміст правого лейауту перед додаванням нового вмісту"""
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def on_item_clicked(self, item):
        """Обробник кліку на елемент списку"""
        # Ігноруємо кліки по заголовках-роздільниках (секціях)
        if not (item.flags() & Qt.ItemIsSelectable):
            return

        self.selected_item = item
        selected_text = item.text()
        self.clear_right_layout()

        if selected_text == "Головна":
            self.show_default_buttons()
        else:
            page_class = {
                "Список вступників (денна)": ListVstupnikDen,
                "Список особових справ (денна)": ListSpravaDen,
                "Список особових справ (денна) скорочена": ListSpravaDenScor,
                "Список пільг вступників (денна)": ListPilgaDen,
                "Список спеціальностей (денна)": ListSpecialnostiDen,
                "Список секретарів (денна)": ListSecretariDen,
                "Список вступних випробувань (денна)": ListExamDen,
                "Список вступних випробувань (денна) скорочена": ListExamDenScor,
                "Введення балів випробувань": ListEntranceScores,
                "Список галузі знань": ListGaluzZnan,
                "Список пільг загальні": ListPilgi,
                "Список вступників (заочна)": ListVstupnikZao,
                "Список особових справ (заочна)": ListSpravaZao,
                "Список пільг вступників (заочна)": ListPilgaZao,
                "Список спеціальностей (заочна)": ListSpecialnostiZao,
                "Список секретарів (заочна)": ListSecretariZao,
                "Список вступних випробувань (заочна)": ListExamZao,
                "Звіти вступної кампанії": AdminZvitCamp,
                "Журнали вступної кампанії": AdminJournalCamp,
                "Протоколи/Допуски вступної кампанії": AdminProtocolCamp,
                "Графіки": ChartsPage,
                "Користувачі": UsersPage,
                "Створення типу фінансування та груп": ListInputStudent,
                "Витяги, звіти студентів": StudentDrukDen,
                "Налаштування системи": SettingsPage,
                "Системні оновлення": UpdatesPage
            }.get(selected_text)

            if page_class:
                self.show_page(page_class, selected_text)
            else:
                print(f"Невідомий пункт меню: '{selected_text}'")

    def show_page(self, page_class, selected_text=None):
        """Динамічне створення і показ сторінки за класом"""
        try:
            page_instance = page_class()
            self.right_layout.addWidget(page_instance)
        except Exception as e:
            print(f"Помилка завантаження сторінки '{page_class}': {e}")

    def select_menu_item(self, index):
        """Вибір елемента меню за індексом"""
        if 0 <= index < self.table_list.count():
            item = self.table_list.item(index)
            self.table_list.setCurrentItem(item)
            self.on_item_clicked(item)
        else:
            print(f"Недійсний індекс: {index}")

    def select_menu_item_by_name(self, name):
        """Вибір елемента меню за назвою"""
        for i in range(self.table_list.count()):
            item = self.table_list.item(i)
            if item.text() == name:
                self.table_list.setCurrentItem(item)
                self.on_item_clicked(item)
                break

    def show_default_buttons(self):
        """Відображення кнопок на головній сторінці з урахуванням прав доступу"""
        from pages.home_page import current_user_permissions
        
        self.right_layout.addStretch(1) # Розпірка зверху

        label = QLabel("Адмін панель системи вступ", self)
        label.setObjectName("adminTitleLabel")
        self.right_layout.addWidget(label, alignment=Qt.AlignCenter)

        def has_access(name):
            if current_user_permissions == "all": return True
            if isinstance(current_user_permissions, dict) and current_user_permissions.get(name): return True
            return False

        # Кнопки з перевіркою прав
        buttons_config = [
            ("Список вступників (денна)", "navButton", lambda: self.select_menu_item_by_name("Список вступників (денна)")),
            ("Список вступників (заочна)", "navButton", lambda: self.select_menu_item_by_name("Список вступників (заочна)")),
            ("Звіти вступної кампанії", "navButton", lambda: self.select_menu_item_by_name("Звіти вступної кампанії")),
            ("Налаштування та бекапи", "navButton", lambda: self.on_item_clicked_by_name("Налаштування системи")),
        ]

        for text, style, callback in buttons_config:
            perm_name = text
            if text == "Налаштування та бекапи": perm_name = "Налаштування системи"
            
            if has_access(perm_name):
                btn = QPushButton(text, self)
                btn.setObjectName(style)
                btn.setFixedWidth(455)
                btn.setCursor(QCursor(Qt.PointingHandCursor))
                btn.clicked.connect(callback)
                self.right_layout.addWidget(btn, alignment=Qt.AlignCenter)

        # Спеціальна кнопка тільки для супер-адміна
        if current_user_permissions == "all":
            self.button6 = QPushButton("Відновити базу з файлу", self)
            self.button6.setObjectName("navButton")
            self.button6.setFixedWidth(455)
            self.button6.setCursor(QCursor(Qt.PointingHandCursor))
            self.button6.clicked.connect(self.handle_restore)
            self.right_layout.addWidget(self.button6, alignment=Qt.AlignCenter)

        # Кнопка Вихід - завжди є
        self.button4 = QPushButton("Вихід", self)
        self.button4.setObjectName("greenButton")
        self.button4.setFixedWidth(455)
        self.button4.setCursor(QCursor(Qt.PointingHandCursor))
        self.button4.clicked.connect(self.close)
        self.right_layout.addWidget(self.button4, alignment=Qt.AlignCenter)

        self.right_layout.setSpacing(25)
        self.right_layout.addStretch(1) # Розпірка знизу

    def on_item_clicked_by_name(self, name):
        """Знаходить пункт меню за ім'ям та імітує клік"""
        for i in range(self.table_list.count()):
            item = self.table_list.item(i)
            if item.text() == name:
                self.table_list.setCurrentItem(item)
                self.on_item_clicked(item)
                break

    def handle_restore(self):
        """Обробка відновлення бази даних"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Виберіть файл бекапу", "", "Backup Files (*.backup *.sql);;All Files (*)"
        )
        
        if not file_path:
            return

        # Запитуємо назву бази (за замовчуванням з .env)
        default_db = os.getenv("DB_NAME", "vstup")
        db_name, ok = QInputDialog.getText(
            self, "Назва бази даних", 
            "Введіть назву бази даних для відновлення:", 
            text=default_db
        )

        if ok and db_name:
            if ask_confirmation(
                self, 
                f"Ви впевнені, що хочете відновити базу '{db_name}' з файлу?\nВсі поточні дані будуть замінені!"
            ):
                self.setCursor(Qt.WaitCursor)
                try:
                    success, message = restore_backup(file_path, db_name)
                    if success:
                        log_info(f"Базу '{db_name}' успішно відновлено з {file_path}")
                        show_success(self, "Базу даних успішно відновлено!")
                    else:
                        log_error(f"Помилка відновлення бази {db_name}: {message}")
                        show_error(self, f"Не вдалося відновити базу:\n{message}")
                except Exception as e:
                    log_error("Виняток при відновленні бази", e)
                    show_error(self, f"Критична помилка: {str(e)}")
                finally:
                    self.unsetCursor()