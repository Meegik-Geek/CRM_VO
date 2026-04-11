from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, 
    QFormLayout, QGroupBox, QScrollArea, QHBoxLayout, QDialog, QComboBox, QButtonGroup, QRadioButton
)
from PyQt5.QtGui import QCursor, QIntValidator
from PyQt5.QtCore import Qt, QTimer
from pages.admin.student.reports.reports_druk_student import DocumentPrinter
from db.connect_db import setup_database, close_database
from datetime import datetime
from utils.notifications import show_success, show_error

class ButtonManager:
    """Керує видимістю кнопок друку у розкладці."""
    def __init__(self, parent):
        self.parent = parent
        self.create_buttons()

    def create_buttons(self):
        """Створення кнопок друку для різних звітів з відповідними обробниками."""
        self.buttons = {
            "reported_student_denne_page": self.create_button("Повідомлення студентів (денна)", self.parent.reported_student_denne_page),
            "reported_student_zaoch_page": self.create_button("Повідомлення студентів (заочна)", self.parent.reported_student_zaoch_page),
            "reported_student_day_scor_page": self.create_button("Повідомлення студентів (денна скорочена)", self.parent.reported_student_day_scor_page),
            "vitag_nakaz_denne_page": self.create_button("Витяг до наказу (денна)", self.parent.vitag_nakaz_denne_page),
            "vitag_nakaz_zaoch_page": self.create_button("Витяг до наказу (заочна)", self.parent.vitag_nakaz_zaoch_page),
            "vitag_nakaz_day_scor_page": self.create_button("Витяг до наказу (денна скорочена)", self.parent.vitag_nakaz_day_scor_page),
            "list_grup_page": self.create_button("Списки груп", self.parent.list_grup_page),
            "list_grup_roz_page": self.create_button("Списки груп (розширені)", self.parent.list_grup_roz_page),
            "export_date_student_page": self.create_button("Експорт даних студентів (всі)", self.parent.export_date_student_page),
        }

    def create_button(self, text, handler):
        """Допоміжний метод для створення і налаштування кнопки."""
        button = QPushButton(text, self.parent)
        button.setObjectName("printButton")
        button.setFixedHeight(50)
        button.setFixedWidth(350)
        button.setCursor(QCursor(Qt.PointingHandCursor))
        button.setVisible(False)
        button.clicked.connect(handler)
        return button

    def show_buttons(self, *keys):
        """Показати вказані кнопки за їх ключами та приховати інші."""
        for key, button in self.buttons.items():
            button.setVisible(key in keys)

class PrintDialog(QDialog):
    """Діалогове вікно для введення параметрів друку."""
    def __init__(self, parent, title, print_handler, extra_fields=None):
        super().__init__(parent)
        self.setObjectName("printDialog")
        self.setWindowTitle(title)
        self.setModal(True)
        self.print_handler = print_handler
        self.fields = {}
        self.conn = setup_database()
        self.init_ui(extra_fields)

    def init_ui(self, extra_fields):
        """Ініціалізація компонентів інтерфейсу діалогу."""
        layout = QVBoxLayout(self)
        layout.setObjectName("dialogLayout")
        layout.setContentsMargins(10, 10, 10, 20)

        if extra_fields:
            for field in extra_fields:
                field_type = field.get('type')
                field_label = field.get('label', '')
                field_name = field.get('name', '')

                label_widget = QLabel(field_label)
                label_widget.setObjectName("fieldLabel")
                if field_type == 'text':
                    self.fields[field_name] = QLineEdit(self)
                    self.fields[field_name].setObjectName("inputField")
                    self.fields[field_name].setPlaceholderText(field.get('placeholder', ''))
                    self.fields[field_name].textChanged.connect(self.validate_fields)
                    layout.addWidget(label_widget)
                    layout.addWidget(self.fields[field_name])

                elif field_type == 'number':
                    self.fields[field_name] = QLineEdit(self)
                    self.fields[field_name].setObjectName("inputField")
                    self.fields[field_name].setValidator(QIntValidator(1, 9999, self))
                    self.fields[field_name].textChanged.connect(self.validate_fields)
                    layout.addWidget(label_widget)
                    layout.addWidget(self.fields[field_name])

                elif field_type == 'combo':
                    self.fields[field_name] = QComboBox(self)
                    self.fields[field_name].setObjectName("comboBox")
                    self.fields[field_name].currentIndexChanged.connect(self.validate_fields)
                    layout.addWidget(label_widget)
                    layout.addWidget(self.fields[field_name])
                    if field_name == 'specialty_name':
                        self.load_specialnosti("day", field_name)
                    elif field_name == 'specialty_name_zaoch':
                        self.load_specialnosti("evening", field_name)
                    elif field_name == 'specialty_name_day_scor':
                        self.load_specialnosti("day_scor", field_name)
                elif field_type == "radio_group":
                    group_box = QGroupBox(field_label)
                    group_box.setObjectName("groupBox")
                    group_layout = QVBoxLayout()
                    button_group = QButtonGroup(self)
                    self.fields[field_name] = button_group
                    button_group.buttonClicked.connect(self.validate_fields)

                    for i, option in enumerate(field["options"]):
                        radio_button = QRadioButton(option)
                        radio_button.setObjectName("radioButton")
                        if option == field.get("default"):
                            radio_button.setChecked(True)
                        button_group.addButton(radio_button, i)
                        group_layout.addWidget(radio_button)

                    group_box.setLayout(group_layout)
                    layout.addWidget(group_box)

        buttons_layout = QHBoxLayout()
        buttons_layout.setObjectName("buttonLayout")
        self.save_btn = QPushButton("Зберегти", self)
        self.save_btn.setObjectName("printButton")
        self.save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_btn.setFixedSize(110, 40)
        self.save_btn.clicked.connect(lambda: self.print_handler(self))
        buttons_layout.addWidget(self.save_btn)
        layout.addLayout(buttons_layout)
        self.validate_fields()

    def load_specialnosti(self, name, field_name):
        """Завантаження спеціальностей з бази даних для заповнення випадаючого списку."""
        if not self.conn:
            self.parent.show_error_message("Помилка: з'єднання з базою даних не встановлено.")
            return
        try:
            cursor = self.conn.cursor()
            if name == "day_scor":
                query = "SELECT DISTINCT name_specialnosti FROM personal_case_day_scor"
            else:
                query = f"SELECT name_specialnosti FROM public.specialities_{name}"
            cursor.execute(query)
            specialnosti = cursor.fetchall()
            for (name_specialnosti,) in specialnosti:
                self.fields[field_name].addItem(name_specialnosti)
        except Exception as e:
            self.parent.show_error_message(f"Помилка завантаження спеціальностей: {str(e)}")

    def get_field_values(self):
        """Отримання значень з усіх полів у діалозі."""
        values = {}
        for name, field in self.fields.items():
            if isinstance(field, QComboBox):
                values[name] = field.currentText()
            elif isinstance(field, QLineEdit):
                values[name] = field.text()
            elif isinstance(field, QButtonGroup):
                checked_button = field.checkedButton()
                values[name] = checked_button.text() if checked_button else None
        return values

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
            elif isinstance(field, QLineEdit):
                if not field.text().strip():
                    all_filled = False
                    break
            elif isinstance(field, QButtonGroup):
                if not field.checkedButton():
                    all_filled = False
                    break
        self.save_btn.setEnabled(all_filled)

    def show_error_message(self, message):
        """Відображає повідомлення про помилку через Toast."""
        show_error(self, message)

    def closeEvent(self, event):
        """Закриття з'єднання з базою даних при закритті вікна."""
        try:
            if self.conn:
                close_database(self.conn)
        except Exception as e:
            self.parent.show_error_message(f"Помилка при закритті бази даних: {str(e)}")
        super().closeEvent(event)


class StudentDrukDen(QWidget):
    """Основний віджет для інтерфейсу друку документів студентів."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Форма для друку витягів, звітів студентів")
        self.document_printer = DocumentPrinter(self.show_success_message, self.show_error_message)
        self.button_manager = ButtonManager(self)
        self.init_ui()

    def init_ui(self):
        """Налаштування інтерфейсу користувача."""
        layout = QVBoxLayout(self)
        layout.setObjectName("mainLayout")
        title_label = QLabel("Форма для друку витягів, звітів студентів", self)
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)

        main_buttons = [
            ("Повідомлення студентів (денна)", "reported_student_denne_page"),
            ("Повідомлення студентів (заочна)", "reported_student_zaoch_page"),
            ("Повідомлення студентів (денна скорочена)", "reported_student_day_scor_page"),
            ("Витяг до наказу (денна)", "vitag_nakaz_denne_page"),
            ("Витяг до наказу (заочна)", "vitag_nakaz_zaoch_page"),
            ("Витяг до наказу (денна скорочена)", "vitag_nakaz_day_scor_page"),
            ("Списки груп", "list_grup_page"),
            ("Списки груп (розширені)", "list_grup_roz_page"),
            ("Експорт даних студентів (всі)", "export_date_student_page"),
        ]

        self.create_main_buttons(layout, main_buttons)
        self.create_scroll_area(layout)

    def create_main_buttons(self, layout, main_buttons):
        """Створення кнопок для головних звітів."""
        buttons_per_row = 3
        current_row_layout = QHBoxLayout()
        current_row_layout.setObjectName("buttonRowLayout")

        for i, (text, page_key) in enumerate(main_buttons, start=1):
            button = self.create_main_button(text, page_key)
            current_row_layout.addWidget(button)

            if i % buttons_per_row == 0:
                layout.addLayout(current_row_layout)
                current_row_layout = QHBoxLayout()
                current_row_layout.setObjectName("buttonRowLayout")

        if current_row_layout.count() > 0:
            layout.addLayout(current_row_layout)

    def create_main_button(self, text, page_key):
        """Створення кнопки для головних функцій."""
        button = QPushButton(text, self)
        button.setObjectName("mainButton")
        button.setFixedHeight(40)
        button.setCursor(QCursor(Qt.PointingHandCursor))
        button.clicked.connect(lambda: self.button_manager.show_buttons(page_key))
        return button

    def create_scroll_area(self, layout):
        """Створення області з додатковими кнопками."""
        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("scrollArea")
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        form_layout = QFormLayout(container)
        form_layout.setObjectName("formLayout")

        document_data_group = QGroupBox("Друку витягів, звітів студентів")
        document_data_group.setObjectName("groupBox")
        self.button_layout = QVBoxLayout()
        self.button_layout.setObjectName("buttonLayout")
        self.button_layout.setSpacing(40)
        self.button_layout.addStretch(1)

        for button in self.button_manager.buttons.values():
            self.button_layout.addWidget(button, alignment=Qt.AlignCenter)
        self.button_layout.addStretch(1)

        document_data_group.setLayout(self.button_layout)
        form_layout.addRow(document_data_group)
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)

    def show_print_dialog(self, title, handler, fields_config):
        """Універсальний метод для показу діалогового вікна."""
        dialog = PrintDialog(self, title, handler, extra_fields=fields_config)
        dialog.exec()

    def validate_and_convert_dates(self, start, end):
        try:
            start_date = datetime.strptime(start, '%d.%m.%Y').date()
            end_date = datetime.strptime(end, '%d.%m.%Y').date()
            if start_date > end_date:
                raise ValueError("Початкова дата не може бути пізніше кінцевої дати.")
            return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
        except ValueError as e:
            self.show_error_message(f"Помилка введення дат: {str(e)}")
            return None, None

    def handle_report_print(self, dialog, print_method, required_fields, validate_dates=False):
        """Універсальний обробник для друку з опціональною валідацією дат."""
        fields = dialog.get_field_values()

        try:
            if validate_dates:
                start_date, end_date = self.validate_and_convert_dates(
                    fields.pop('period_start', ''), fields.pop('period_end', '')
                )
                if not start_date or not end_date:
                    return
                fields['period_start'] = start_date
                fields['period_end'] = end_date

            for field in required_fields:
                value = fields.get(field, "").strip()
                if not value:
                    raise ValueError(f"Поле '{field}' є обов'язковим для заповнення.")

            filtered_fields = {key: value.strip() for key, value in fields.items() if key in required_fields}
            print_method(**filtered_fields, dialog=dialog)

        except ValueError as e:
            self.show_error_message(str(e))
        except Exception as e:
            self.show_error_message(f"Помилка обробки: {str(e)}")

    def reported_student_denne_page(self):
        fields_config = self.get_common_fields("specialty_name")
        self.show_print_dialog(
            "Друк повідомлення студентів (денна)",
            lambda dialog: self.handle_report_print(
                dialog,
                self.document_printer.print_reported_student_denne,
                required_fields=["specialty_name", "finance_type", "order_number", "order_date", 
                                "arrival_date", "period_start", "period_end"],
                validate_dates=True
            ),
            fields_config
        )

    def reported_student_zaoch_page(self):
        fields_config = self.get_common_fields("specialty_name_zaoch")
        self.show_print_dialog(
            "Друк повідомлення студентів (заочна)",
            lambda dialog: self.handle_report_print(
                dialog,
                self.document_printer.print_reported_student_zaoch,
                required_fields=["specialty_name_zaoch", "finance_type", "order_number", "order_date", 
                                "arrival_date", "period_start", "period_end"],
                validate_dates=True
            ),
            fields_config
        )

    def reported_student_day_scor_page(self):
        fields_config = self.get_common_fields("specialty_name_day_scor")
        self.show_print_dialog(
            "Друк повідомлення студентів (денна скорочена)",
            lambda dialog: self.handle_report_print(
                dialog,
                self.document_printer.print_reported_student_day_scor,
                required_fields=["specialty_name_day_scor", "finance_type", "order_number", "order_date", 
                                "arrival_date", "period_start", "period_end"],
                validate_dates=True
            ),
            fields_config
        )

    def vitag_nakaz_denne_page(self):
        fields_config = [
            {"type": "combo", "label": "Назва спеціальності", "name": "specialty_name"},
            {"type": "radio_group", "label": "Тип фінансування", "name": "finance_type",
                "options": ["Державна форма", "Платна форма"], "default": "Державна форма"},
            {"type": "text", "label": "Номер наказу", "name": "order_number", "placeholder": "Введіть номер наказу"},
            {"type": "text", "label": "Дата наказу", "name": "order_date", "placeholder": "дд місяць рік"},
            {"type": "text", "label": "Номер протоколу (рішення приймальної комісії)", "name": "protokol_number", "placeholder": "Введіть номер протоколу"},
            {"type": "text", "label": "Дата протоколу", "name": "protokol_date", "placeholder": "дд місяць рік"},
            {"type": "text", "label": "Дата зарахування (зарахувати з)", "name": "zarah_date", "placeholder": "дд місяць рік"},
            {"type": "text", "label": "Початок періоду подачі заяв", "name": "period_start", "placeholder": "DD.MM.YYYY"},
            {"type": "text", "label": "Кінець періоду подачі заяв", "name": "period_end", "placeholder": "DD.MM.YYYY"},
        ]
        self.show_print_dialog(
            "Друк витягу з наказу (денна)",
            lambda dialog: self.handle_report_print(
                dialog,
                self.document_printer.print_vitag_nakaz_denne,
                required_fields=[
                    "specialty_name", "finance_type", "order_number", "order_date",
                    "protokol_number", "protokol_date", "zarah_date", "period_start", "period_end"
                ],
                validate_dates=True
            ),
            fields_config
        )

    def vitag_nakaz_zaoch_page(self):
        fields_config = [
            {"type": "combo", "label": "Назва спеціальності", "name": "specialty_name_zaoch"},
            {"type": "radio_group", "label": "Тип фінансування", "name": "finance_type",
                "options": ["Державна форма", "Платна форма"], "default": "Державна форма"},
            {"type": "text", "label": "Номер наказу", "name": "order_number", "placeholder": "Введіть номер наказу"},
            {"type": "text", "label": "Дата наказу", "name": "order_date", "placeholder": "дд місяць рік"},
            {"type": "text", "label": "Номер протоколу (рішення приймальної комісії)", "name": "protokol_number", "placeholder": "Введіть номер протоколу"},
            {"type": "text", "label": "Дата протоколу", "name": "protokol_date", "placeholder": "дд місяць рік"},
            {"type": "text", "label": "Дата зарахування (зарахувати з)", "name": "zarah_date", "placeholder": "дд місяць рік"},
            {"type": "text", "label": "Початок періоду подачі заяв", "name": "period_start", "placeholder": "DD.MM.YYYY"},
            {"type": "text", "label": "Кінець періоду подачі заяв", "name": "period_end", "placeholder": "DD.MM.YYYY"},
        ]
        self.show_print_dialog(
            "Друк витягу з наказу (заочна)",
            lambda dialog: self.handle_report_print(
                dialog,
                self.document_printer.print_vitag_nakaz_zaoch,
                required_fields=[
                    "specialty_name_zaoch", "finance_type", "order_number", "order_date",
                    "protokol_number", "protokol_date", "zarah_date", "period_start", "period_end"
                ],
                validate_dates=True
            ),
            fields_config
        )

    def vitag_nakaz_day_scor_page(self):
        fields_config = [
            {"type": "combo", "label": "Назва спеціальності", "name": "specialty_name_day_scor"},
            {"type": "radio_group", "label": "Тип фінансування", "name": "finance_type",
                "options": ["Державна форма", "Платна форма"], "default": "Державна форма"},
            {"type": "text", "label": "Номер наказу", "name": "order_number", "placeholder": "Введіть номер наказу"},
            {"type": "text", "label": "Дата наказу", "name": "order_date", "placeholder": "дд місяць рік"},
            {"type": "text", "label": "Номер протоколу (рішення приймальної комісії)", "name": "protokol_number", "placeholder": "Введіть номер протоколу"},
            {"type": "text", "label": "Дата протоколу", "name": "protokol_date", "placeholder": "дд місяць рік"},
            {"type": "text", "label": "Дата зарахування (зарахувати з)", "name": "zarah_date", "placeholder": "дд місяць рік"},
            {"type": "text", "label": "Початок періоду подачі заяв", "name": "period_start", "placeholder": "DD.MM.YYYY"},
            {"type": "text", "label": "Кінець періоду подачі заяв", "name": "period_end", "placeholder": "DD.MM.YYYY"},
        ]
        self.show_print_dialog(
            "Друк витягу з наказу (денна скорочена)",
            lambda dialog: self.handle_report_print(
                dialog,
                self.document_printer.print_vitag_nakaz_day_scor,
                required_fields=[
                    "specialty_name_day_scor", "finance_type", "order_number", "order_date",
                    "protokol_number", "protokol_date", "zarah_date", "period_start", "period_end"
                ],
                validate_dates=True
            ),
            fields_config
        )

    def list_grup_page(self):
        fields_config = [{"type": "text", "label": "Номер групи", "name": "number_group", "placeholder": "000 «Д» або 000 «З»"}]
        self.show_print_dialog(
            "Друк списків груп",
            lambda dialog: self.handle_report_print(
                dialog,
                self.document_printer.print_list_grup,
                required_fields=["number_group"],
                validate_dates=False
            ),
            fields_config
        )

    def list_grup_roz_page(self):
        fields_config = [{"type": "text", "label": "Номер групи", "name": "number_group", "placeholder": "000 «Д» або 000 «З»"}]
        self.show_print_dialog(
            "Друк розширених списків груп",
            lambda dialog: self.handle_report_print(
                dialog,
                self.document_printer.print_list_grup_roz,
                required_fields=["number_group"],
                validate_dates=False
            ),
            fields_config
        )

    def get_common_fields(self, specialty_field_name="specialty_name"):
        """Повертає загальні поля для звітів."""
        return [
            {"type": "combo", "label": "Назва спеціальності", "name": specialty_field_name},
            {"type": "radio_group", "label": "Тип фінансування", "name": "finance_type",
             "options": ["Державна форма", "Платна форма"], "default": "Державна форма"},
            {"type": "text", "label": "Номер наказу", "name": "order_number", "placeholder": "Введіть номер наказу"},
            {"type": "text", "label": "Дата наказу", "name": "order_date", "placeholder": "дд місяць рік"},
            {"type": "text", "label": "Дата прибуття", "name": "arrival_date", "placeholder": "дд місяць рік"},
            {"type": "text", "label": "Початок періоду", "name": "period_start", "placeholder": "DD.MM.YYYY"},
            {"type": "text", "label": "Кінець періоду", "name": "period_end", "placeholder": "DD.MM.YYYY"},
        ]

    def export_date_student_page(self):
        self.document_printer.print_export_date_vstupnik()

    def show_error_message(self, message):
        """Показати повідомлення про помилку."""
        show_error(self, message)

    def show_success_message(self, message):
        """Показати повідомлення про успіх."""
        show_success(self, message)