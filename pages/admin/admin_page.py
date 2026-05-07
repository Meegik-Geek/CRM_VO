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
        """Додає розділи меню для лівої панелі"""
        self.add_menu_item("Головна")
        self.add_section("Форми (денна)", bold=True)
        self.add_menu_item("Список вступників (денна)")
        self.add_menu_item("Список особових справ (денна)")
        self.add_menu_item("Список особових справ (денна) скорочена")
        self.add_menu_item("Список пільг вступників (денна)")
        self.add_menu_item("Список спеціальностей (денна)")
        self.add_menu_item("Список секретарів (денна)")
        self.add_menu_item("Список вступних випробувань (денна)")
        self.add_menu_item("Список вступних випробувань (денна) скорочена")
        self.add_section("Форми (заочна)", bold=True)
        self.add_menu_item("Список вступників (заочна)")
        self.add_menu_item("Список особових справ (заочна)")
        self.add_menu_item("Список пільг вступників (заочна)")
        self.add_menu_item("Список спеціальностей (заочна)")
        self.add_menu_item("Список секретарів (заочна)")
        self.add_menu_item("Список вступних випробувань (заочна)")
        self.add_section("Форми (загальні)", bold=True)
        self.add_menu_item("Список галузі знань")
        self.add_menu_item("Список пільг загальні")
        self.add_menu_item("Введення балів випробувань")
        self.add_section("Друк", bold=True)
        self.add_menu_item("Звіти вступної кампанії")
        self.add_menu_item("Журнали вступної кампанії")
        self.add_menu_item("Протоколи/Допуски вступної кампанії")
        self.add_section("Аналітика", bold=True)
        self.add_menu_item("Графіки")
        self.add_section("Студенти", bold=True)
        self.add_menu_item("Створення типу фінансування та груп")
        self.add_menu_item("Витяги, звіти студентів")
        self.add_section("Система", bold=True)
        self.add_menu_item("Налаштування системи")
        self.add_menu_item("Системні оновлення")

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

    def show_default_buttons(self):
        """Відображення кнопок за замовчуванням"""
        label = QLabel("Адмін панель системи вступ", self)
        label.setObjectName("adminTitleLabel")
        self.right_layout.addWidget(label)

        self.button1 = QPushButton("Список вступників (денна)", self)
        self.button2 = QPushButton("Список вступників (заочна)", self)
        self.button3 = QPushButton("Звіти вступної кампанії", self)
        self.button5 = QPushButton("Налаштування та бекапи", self)
        self.button6 = QPushButton("Відновити базу з файлу", self)
        self.button4 = QPushButton("Вихід", self)

        self.button1.setObjectName("navButton")
        self.button2.setObjectName("navButton")
        self.button3.setObjectName("navButton")
        self.button5.setObjectName("navButton")
        self.button6.setObjectName("navButton")
        self.button4.setObjectName("greenButton")

        for button in (self.button1, self.button2, self.button3, self.button5, self.button6, self.button4):
            button.setFixedWidth(455)
            button.setCursor(QCursor(Qt.PointingHandCursor))

        self.right_layout.addWidget(self.button1)
        self.right_layout.addWidget(self.button2)
        self.right_layout.addWidget(self.button3)
        self.right_layout.addWidget(self.button5)
        self.right_layout.addWidget(self.button6)
        self.right_layout.addWidget(self.button4)
        self.right_layout.setSpacing(25)

        self.button1.clicked.connect(lambda: self.select_menu_item(2))
        self.button2.clicked.connect(lambda: self.select_menu_item(11))
        self.button3.clicked.connect(lambda: self.select_menu_item(18))
        self.button5.clicked.connect(lambda: self.select_menu_item(21)) # Налаштування системи
        self.button6.clicked.connect(self.handle_restore)
        self.button4.clicked.connect(self.close)

        self.right_layout.setAlignment(Qt.AlignCenter)

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