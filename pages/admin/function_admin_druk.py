from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, 
    QFormLayout, QGroupBox, QScrollArea, QHBoxLayout, QDialog, QComboBox
)
from PyQt5.QtGui import QCursor, QIntValidator
from PyQt5.QtCore import Qt, QTimer, QPoint
from db.connect_db import setup_database, close_database
from datetime import datetime
from utils.notifications import show_success, show_error

class ButtonManager:
    """Керує видимістю кнопок друку у розкладці."""
    def __init__(self, parent):
        self.parent = parent
        self.buttons = {}

    def add_buttons(self, button_configs):
        """Додає кнопки згідно з конфігурацією."""
        for key, config in button_configs.items():
            self.buttons[key] = self.create_button(config['text'], config['handler'])
            self.parent.button_layout.addWidget(self.buttons[key], alignment=Qt.AlignCenter)
    
    def create_button(self, text, handler):
        """Створення кнопки."""
        button = QPushButton(text, self.parent)
        button.setFixedHeight(50)
        button.setFixedWidth(350)
        button.setCursor(QCursor(Qt.PointingHandCursor))
        button.setVisible(False)
        button.setStyleSheet("font-size: 14px;")
        button.clicked.connect(handler)
        return button

    def show_buttons(self, *keys):
        """Показати вказані кнопки за їх ключами та приховати інші."""
        for key, button in self.buttons.items():
            button.setVisible(key in keys)


class PrintDialog(QDialog):
    """Універсальний діалог для параметрів друку."""
    def __init__(self, parent, title, print_handler, extra_fields=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(250, 150)
        self.print_handler = print_handler
        self.fields = {}
        self.conn = setup_database()
        self.init_ui(extra_fields)

    def init_ui(self, extra_fields):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 20)

        if extra_fields:
            for field in extra_fields:
                field_type = field.get('type')
                field_label = field.get('label', '')
                field_name = field.get('name', '')

                if field_type == 'text':
                    self.fields[field_name] = QLineEdit(self)
                    self.fields[field_name].setPlaceholderText(field.get('placeholder', ''))
                    self.fields[field_name].textChanged.connect(self.validate_fields)
                    layout.addWidget(QLabel(field_label))
                    layout.addWidget(self.fields[field_name])

                elif field_type == 'number':
                    self.fields[field_name] = QLineEdit(self)
                    self.fields[field_name].setValidator(QIntValidator(1, 9999, self))
                    self.fields[field_name].textChanged.connect(self.validate_fields)
                    layout.addWidget(QLabel(field_label))
                    layout.addWidget(self.fields[field_name])

                elif field_type == 'combo':
                    self.fields[field_name] = QComboBox(self)
                    self.fields[field_name].currentIndexChanged.connect(self.validate_fields)
                    layout.addWidget(QLabel(field_label))
                    layout.addWidget(self.fields[field_name])
                    if field_name == 'Назва спеціальності':
                        self.load_specialnosti()

        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Зберегти", self)
        self.save_btn.setObjectName("printButton")
        self.save_btn.setFixedSize(110, 40)
        self.save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_btn.clicked.connect(lambda: self.print_handler(self))
        buttons_layout.addWidget(self.save_btn)
        layout.addLayout(buttons_layout)
        self.validate_fields()

    def load_specialnosti(self):
        """Завантаження спеціальностей у випадаючий список."""
        try:
            cursor = self.conn.cursor()
            query = "SELECT name_specialnosti FROM public.specialities_day"
            cursor.execute(query)
            for (name,) in cursor.fetchall():
                self.fields['Назва спеціальності'].addItem(name)
        except Exception as e:
            print(f"Помилка завантаження спеціальностей: {e}")

    def get_field_values(self):
        """Отримання значень із полів."""
        return {name: field.currentText() if isinstance(field, QComboBox) else field.text()
                for name, field in self.fields.items()}

    def validate_fields(self):
        """Перевірка заповненості всіх полів для активації кнопки."""
        if not hasattr(self, 'save_btn'):
            return
        all_filled = True
        for name, field in self.fields.items():
            if isinstance(field, QComboBox):
                if field.currentIndex() == -1 or not field.currentText().strip():
                    all_filled = False
                    break
            else:
                if not field.text().strip():
                    all_filled = False
                    break
        self.save_btn.setEnabled(all_filled)

    def show_error_message(self, message):
        """Відображає повідомлення про помилку через Toast."""
        show_error(self, message)

    def closeEvent(self, event):
        if self.conn:
            close_database(self.conn)
        super().closeEvent(event)




class BasePrintWidget(QWidget):
    """Універсальний клас для створення виджетів друку."""
    def __init__(self, title, button_configs, document_printer):
        super().__init__()
        self.setWindowTitle(title)
        self.document_printer = document_printer
        self.init_ui(button_configs)

    def init_ui(self, button_configs):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.windowTitle(), self))

        # Основний менеджер кнопок
        self.button_manager = ButtonManager(self)
        self.button_layout = QVBoxLayout()
        self.button_manager.add_buttons(button_configs)

        layout.addLayout(self.button_layout)
        self.setLayout(layout)

    def show_error_message(self, message):
        show_error(self, message)

    def show_success_message(self, message):
        show_success(self, message)
