from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, 
    QFormLayout, QGroupBox, QScrollArea, QHBoxLayout, QDialog
)
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt, QTimer
from implement.druk_zaoch import DocumentPrinter

class ButtonManager:
    """Керує видимістю кнопок друку в лейауті."""
    def __init__(self, parent):
        self.parent = parent
        self.create_buttons()

    def create_buttons(self):
        """Створює кнопки друку для різних завдань та призначає їхні обробники."""
        self.buttons = {
            "first_page": self.create_button("Перша сторінка анкети вступника", self.parent.print_first_page),
            "second_page": self.create_button("Друга сторінка анкети вступника", self.parent.print_second_page),
            "osobova_sprava": self.create_button("Друк опису особової справи", self.parent.print_osobova_sprava),
            "titulka": self.create_button("Друк титулки особової справи", self.parent.print_titulka),
            "pilga": self.create_button("Друк пільги вступника", self.parent.print_pilga),
            "result_first_page": self.create_button("Перша сторінка аркушу вступних випробувань", self.parent.print_result_first_page),
            "result_second_page": self.create_button("Друга сторінка аркушу вступних випробувань", self.parent.print_result_second_page),
            "vstupna_zayava": self.create_button("Друк заяви на вступні випробування", self.parent.print_vstupna_zayava)
        }

    def create_button(self, text, handler):
        """Допоміжна функція для створення та налаштування кнопки."""
        button = QPushButton(text, self.parent)
        button.setObjectName("printButton")
        button.setCursor(QCursor(Qt.PointingHandCursor))
        button.setVisible(False)
        button.clicked.connect(handler)
        return button

    def show_buttons(self, *keys):
        """Показує вказані кнопки за їхніми ключами та приховує інші."""
        for key, button in self.buttons.items():
            button.setVisible(key in keys)

class PrintDialog(QDialog):
    """Базовий клас для діалогів із полем вводу номера справи та кнопками друку/перегляду."""
    def __init__(self, parent, title, print_handler, extra_fields=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(300, 150)
        self.print_handler = print_handler
        self.fields = {}
        self.init_ui(extra_fields)

    def init_ui(self, extra_fields):
        """Ініціалізує компоненти інтерфейсу діалогу."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 20)

        self.fields['Номер справи'] = QLineEdit(self)
        self.fields['Номер справи'].setObjectName("inputField")
        self.fields['Номер справи'].textChanged.connect(self.validate_fields)
        layout.addWidget(QLabel("Номер справи:"))
        layout.addWidget(self.fields['Номер справи'])

        if extra_fields:
            for field_name in extra_fields:
                self.fields[field_name] = QLineEdit(self)
                self.fields[field_name].setObjectName("inputField")
                self.fields[field_name].textChanged.connect(self.validate_fields)
                layout.addWidget(QLabel(f"{field_name}:"))
                layout.addWidget(self.fields[field_name])

        # Кнопки для перегляду та друку
        buttons_layout = QHBoxLayout()
        # preview_button = QPushButton("Перегляд", self)
        # preview_button.setObjectName("previewButton")
        # preview_button.setCursor(QCursor(Qt.PointingHandCursor))
        # buttons_layout.addWidget(preview_button)

        self.print_btn = QPushButton("Друк", self)
        self.print_btn.setObjectName("printButton")
        self.print_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.print_btn.clicked.connect(lambda: self.print_handler(self))
        buttons_layout.addWidget(self.print_btn)

        layout.addLayout(buttons_layout)
        self.validate_fields()

    def get_field_values(self):
        """Отримує значення всіх полів у діалозі."""
        return {name: field.text() for name, field in self.fields.items()}

    def validate_fields(self):
        """Перевірка заповненості всіх полів для активації кнопки."""
        if not hasattr(self, 'print_btn'):
            return
        all_filled = all(field.text().strip() for field in self.fields.values())
        self.print_btn.setEnabled(all_filled)

class DrukDocumentZaoch(QWidget):
    """Головний віджет для інтерфейсу друку документів із кнопками та діалогами."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Форма для друку документів вступників (заочної форми)")
        self.document_printer = DocumentPrinter()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        layout.addWidget(QLabel("Форма для друку документів (заочної форми)", self))
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.create_main_button("Анкета вступника", self.show_anketa_buttons))
        button_layout.addWidget(self.create_main_button("Опис особової справи", self.show_osobova_sprava_button))
        button_layout.addWidget(self.create_main_button("Титулка особової справи", self.show_titulka_button))
        button_layout.addWidget(self.create_main_button("Пільги вступника", self.show_pilga_button))
        button_layout.addWidget(self.create_main_button("Аркуш результатів", self.show_result_buttons))
        button_layout.addWidget(self.create_main_button("Заява на вступні випробування", self.show_vstupna_zayava_button))
        layout.addLayout(button_layout)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        form_layout = QFormLayout(container)

        document_data_group = QGroupBox("Друку документів вступника (заочної форми)")
        document_data_group.setObjectName("groupBox")
        self.button_layout = QVBoxLayout()
        self.button_layout.setSpacing(40)
        self.button_layout.addStretch(1)

        # Додаємо кнопки, керовані ButtonManager
        self.button_manager = ButtonManager(self)
        for button in self.button_manager.buttons.values():
            self.button_layout.addWidget(button, alignment=Qt.AlignCenter)

        self.button_layout.addStretch(1)
        document_data_group.setLayout(self.button_layout)
        form_layout.addRow(document_data_group)
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)
        self.setLayout(layout)

    def create_main_button(self, text, handler):
        button = QPushButton(text, self)
        button.setObjectName("mainButton")
        button.setCursor(QCursor(Qt.PointingHandCursor))
        button.clicked.connect(handler)
        return button

    # Обробники дій кнопок
    def show_anketa_buttons(self):
        self.button_manager.show_buttons("first_page", "second_page")

    def show_osobova_sprava_button(self):
        self.button_manager.show_buttons("osobova_sprava")

    def show_titulka_button(self):
        self.button_manager.show_buttons("titulka")

    def show_pilga_button(self):
        self.button_manager.show_buttons("pilga")

    def show_result_buttons(self):
        self.button_manager.show_buttons("result_first_page", "result_second_page")
    def show_vstupna_zayava_button(self):
        self.button_manager.show_buttons("vstupna_zayava")
    # Методи друку з діалогами
    def print_first_page(self):
        dialog = PrintDialog(self, "Друк першої сторінки анкети", self.handle_first_page_print)
        dialog.exec_()

    def print_second_page(self):
        dialog = PrintDialog(self, "Друк другої сторінки анкети", self.handle_second_page_print)
        dialog.exec_()

    def print_osobova_sprava(self):
        dialog = PrintDialog(self, "Друк опису особової справи", self.handle_osobova_sprava_print)
        dialog.exec_()

    def print_titulka(self):
        dialog = PrintDialog(self, "Друк титулки особової справи", self.handle_titulka_print)
        dialog.exec_()

    def print_pilga(self):
        dialog = PrintDialog(self, "Друк пільги вступника", self.handle_pilga_print, extra_fields=["Код пільги"])
        dialog.exec_()

    def print_result_first_page(self):
        dialog = PrintDialog(self, "Перша сторінка аркушу вступних випробувань", self.handle_result_first_page_print)
        dialog.exec_()

    def print_result_second_page(self):
        dialog = PrintDialog(self, "Друга сторінка аркушу вступних випробувань", self.handle_result_second_page_print)
        dialog.exec_()
    def print_vstupna_zayava(self):
        dialog = PrintDialog(self, "Друк заяви на вступні випробування", self.handle_vstupna_zayava_print)
        dialog.exec_()
    # Методи обробки друку
    def handle_first_page_print(self, dialog):
        sprava_number = dialog.get_field_values()['Номер справи']
        self.document_printer.print_first_page(sprava_number, dialog)

    def handle_second_page_print(self, dialog):
        sprava_number = dialog.get_field_values()['Номер справи']
        self.document_printer.print_second_page(sprava_number, dialog)

    def handle_osobova_sprava_print(self, dialog):
        sprava_number = dialog.get_field_values()['Номер справи']
        self.document_printer.print_osobova_sprava(sprava_number, dialog)

    def handle_titulka_print(self, dialog):
        sprava_number = dialog.get_field_values()['Номер справи']
        self.document_printer.print_titulka(sprava_number, dialog)

    def handle_pilga_print(self, dialog):
        fields = dialog.get_field_values()
        sprava_number, kod_pilgi = fields['Номер справи'], fields['Код пільги']
        self.document_printer.print_pilga(sprava_number, kod_pilgi, dialog)

    def handle_result_first_page_print(self, dialog):
        sprava_number = dialog.get_field_values()['Номер справи']
        self.document_printer.print_result_first_page(sprava_number, dialog)

    def handle_result_second_page_print(self, dialog):
        sprava_number = dialog.get_field_values()['Номер справи']
        self.document_printer.print_result_second_page(sprava_number, dialog)
    def handle_vstupna_zayava_print(self, dialog):
        sprava_number = dialog.get_field_values()['Номер справи']
        self.document_printer.print_vstupna_zayava(sprava_number, dialog)