from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, 
    QFormLayout, QGroupBox, QScrollArea, QHBoxLayout, QDialog, QComboBox, QButtonGroup, QRadioButton
)
from PyQt5.QtGui import QCursor, QIntValidator
from PyQt5.QtCore import Qt
from pages.admin.student.reports.reports_druk_student import DocumentPrinter
from db.connect_db import setup_database, close_database
from datetime import datetime
from utils.notifications import show_success, show_error

class ButtonManager:
    """Керує видимістю кнопок друку та описів."""
    def __init__(self, parent):
        self.parent = parent
        self.descriptions = {
            "reported_student_denne_page": "Офіційне повідомлення для студента про зарахування до закладу освіти. Містить інформацію про наказ, дату прибуття та умови навчання.",
            "reported_student_zaoch_page": "Офіційне повідомлення для студента про зарахування до закладу освіти (заочна форма). Містить інформацію про наказ та дату прибуття.",
            "reported_student_day_scor_page": "Офіційне повідомлення для студента про зарахування (денна скорочена). Містить інформацію про наказ та умови навчання.",
            "vitag_nakaz_denne_page": "Витяг із наказу про зарахування студента. Використовується для особової справи та підтвердження статусу студента.",
            "vitag_nakaz_zaoch_page": "Витяг із наказу про зарахування студента (заочна форма). Містить реквізити наказу та рішення ПК.",
            "vitag_nakaz_day_scor_page": "Витяг із наказу про зарахування студента (денна скорочена). Необхідний для особової справи.",
            "list_grup_page": "Простий список студентів, розподілених за номерами навчальних груп. Використовується для первинного формування груп.",
            "list_grup_roz_page": "Детальний список студентів групи з додатковими даними (контакти, пільги тощо). Необхідний для кураторів.",
            "export_date_student_page": "Повний експорт бази даних усіх зарахованих студентів у формат Excel для ведення внутрішньої звітності.",
        }
        self.create_buttons()

    def create_buttons(self):
        """Створення кнопок друку."""
        self.buttons = {
            "reported_student_denne_page": self.create_button("Друк повідомлення (денна)", self.parent.reported_student_denne_page),
            "reported_student_zaoch_page": self.create_button("Друк повідомлення (заочна)", self.parent.reported_student_zaoch_page),
            "reported_student_day_scor_page": self.create_button("Друк повідомлення (скорочена)", self.parent.reported_student_day_scor_page),
            "vitag_nakaz_denne_page": self.create_button("Друк витягу до наказу (денна)", self.parent.vitag_nakaz_denne_page),
            "vitag_nakaz_zaoch_page": self.create_button("Друк витягу до наказу (заочна)", self.parent.vitag_nakaz_zaoch_page),
            "vitag_nakaz_day_scor_page": self.create_button("Друк витягу до наказу (скорочена)", self.parent.vitag_nakaz_day_scor_page),
            "list_grup_page": self.create_button("Друк списків груп", self.parent.list_grup_page),
            "list_grup_roz_page": self.create_button("Друк розширених списків груп", self.parent.list_grup_roz_page),
            "export_date_student_page": self.create_button("Експорт даних студентів (всі)", self.parent.export_date_student_page),
        }

    def create_button(self, text, handler):
        button = QPushButton(text, self.parent)
        button.setObjectName("printButton")
        button.setFixedHeight(50)
        button.setFixedWidth(450)
        button.setCursor(QCursor(Qt.PointingHandCursor))
        button.setVisible(False)
        button.clicked.connect(handler)
        return button

    def show_buttons(self, key):
        """Показати вказану кнопку та опис."""
        self.parent.general_desc_label.setVisible(False)
        desc = self.descriptions.get(key, "")
        self.parent.report_desc_label.setText(desc)
        self.parent.report_desc_label.setVisible(True)
        
        for k, button in self.buttons.items():
            button.setVisible(k == key)

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
        layout = QVBoxLayout(self)
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
                    group_layout = QVBoxLayout()
                    button_group = QButtonGroup(self)
                    self.fields[field_name] = button_group
                    button_group.buttonClicked.connect(self.validate_fields)

                    for i, option in enumerate(field["options"]):
                        radio_button = QRadioButton(option)
                        if option == field.get("default"):
                            radio_button.setChecked(True)
                        button_group.addButton(radio_button, i)
                        group_layout.addWidget(radio_button)

                    group_box.setLayout(group_layout)
                    layout.addWidget(group_box)

        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Зберегти", self)
        self.save_btn.setObjectName("printButton")
        self.save_btn.setFixedSize(110, 40)
        self.save_btn.clicked.connect(lambda: self.print_handler(self))
        buttons_layout.addWidget(self.save_btn)
        layout.addLayout(buttons_layout)
        self.validate_fields()

    def load_specialnosti(self, name, field_name):
        if not self.conn: return
        try:
            cursor = self.conn.cursor()
            query = f"SELECT name_specialnosti FROM public.specialities_{name}" if name != "day_scor" else "SELECT DISTINCT name_specialnosti FROM personal_case_day_scor"
            cursor.execute(query)
            for (name_specialnosti,) in cursor.fetchall():
                self.fields[field_name].addItem(name_specialnosti)
        except Exception: pass

    def get_field_values(self):
        values = {}
        for name, field in self.fields.items():
            if isinstance(field, QComboBox): values[name] = field.currentText()
            elif isinstance(field, QLineEdit): values[name] = field.text()
            elif isinstance(field, QButtonGroup): values[name] = field.checkedButton().text() if field.checkedButton() else None
        return values

    def validate_fields(self):
        if not hasattr(self, 'save_btn'): return
        all_filled = True
        for field in self.fields.values():
            if isinstance(field, QComboBox) and (field.currentIndex() == -1 or not field.currentText().strip()): all_filled = False
            elif isinstance(field, QLineEdit) and not field.text().strip(): all_filled = False
            elif isinstance(field, QButtonGroup) and not field.checkedButton(): all_filled = False
        self.save_btn.setEnabled(all_filled)

    def closeEvent(self, event):
        try:
            if self.conn: close_database(self.conn)
        except: pass
        super().closeEvent(event)

class StudentDrukDen(QWidget):
    """Основний віджет для інтерфейсу друку документів студентів."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Витяги, звіти студентів")
        self.document_printer = DocumentPrinter(self.show_success_message, self.show_error_message)
        self.button_manager = ButtonManager(self)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        title_label = QLabel("Витяги, звіти студентів", self)
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
        buttons_per_row = 3
        current_row_layout = QHBoxLayout()
        for i, (text, key) in enumerate(main_buttons, start=1):
            btn = QPushButton(text, self)
            btn.setObjectName("mainButton")
            btn.setFixedHeight(40)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(lambda checked, k=key: self.button_manager.show_buttons(k))
            current_row_layout.addWidget(btn)
            if i % buttons_per_row == 0:
                layout.addLayout(current_row_layout)
                current_row_layout = QHBoxLayout()
        if current_row_layout.count() > 0:
            layout.addLayout(current_row_layout)

    def create_scroll_area(self, layout):
        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("scrollArea")
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        form_layout = QFormLayout(container)

        group_box = QGroupBox("Друк студентських документів")
        group_box.setObjectName("groupBox")
        self.button_layout = QVBoxLayout(group_box)
        self.button_layout.setSpacing(20)
        self.button_layout.addStretch(1)

        # Загальний опис по центру
        self.general_desc_label = QLabel("Оберіть тип студентського документа, щоб переглянути його призначення та сформувати файл.", self)
        self.general_desc_label.setWordWrap(True)
        self.general_desc_label.setAlignment(Qt.AlignCenter)
        self.general_desc_label.setStyleSheet("color: #888; font-size: 16px; font-style: italic;")
        self.button_layout.addWidget(self.general_desc_label)

        # Специфічний опис (прихований спочатку)
        self.report_desc_label = QLabel("", self)
        self.report_desc_label.setWordWrap(True)
        self.report_desc_label.setAlignment(Qt.AlignCenter)
        self.report_desc_label.setFixedWidth(700)
        self.report_desc_label.setMinimumHeight(70)
        self.report_desc_label.setStyleSheet("font-size: 15px; color: #333; line-height: 1.5; margin-bottom: 10px; padding: 5px;")
        self.report_desc_label.setVisible(False)
        self.button_layout.addWidget(self.report_desc_label, alignment=Qt.AlignCenter)

        for button in self.button_manager.buttons.values():
            self.button_layout.addWidget(button, alignment=Qt.AlignCenter)
        
        self.button_layout.addStretch(1)
        form_layout.addRow(group_box)
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)

    def show_print_dialog(self, title, handler, fields_config):
        dialog = PrintDialog(self, title, handler, extra_fields=fields_config)
        dialog.exec()

    def handle_report_print(self, dialog, print_method, required_fields, validate_dates=False):
        fields = dialog.get_field_values()
        try:
            if validate_dates:
                start = fields.pop('period_start', '')
                end = fields.pop('period_end', '')
                s_date = datetime.strptime(start, '%d.%m.%Y').date()
                e_date = datetime.strptime(end, '%d.%m.%Y').date()
                if s_date > e_date: raise ValueError("Початкова дата пізніше кінцевої.")
                fields['period_start'], fields['period_end'] = s_date.strftime('%Y-%m-%d'), e_date.strftime('%Y-%m-%d')
            for f in required_fields:
                if not fields.get(f, "").strip(): raise ValueError(f"Поле '{f}' обов'язкове.")
            print_method(**{k: v.strip() for k, v in fields.items() if k in required_fields}, dialog=dialog)
        except Exception as e: self.show_error_message(str(e))

    def reported_student_denne_page(self):
        self.show_print_dialog("Друк повідомлення (денна)", lambda d: self.handle_report_print(d, self.document_printer.print_reported_student_denne, ["specialty_name", "finance_type", "order_number", "order_date", "arrival_date", "period_start", "period_end"], True), self.get_common_fields("specialty_name"))
    def reported_student_zaoch_page(self):
        self.show_print_dialog("Друк повідомлення (заочна)", lambda d: self.handle_report_print(d, self.document_printer.print_reported_student_zaoch, ["specialty_name_zaoch", "finance_type", "order_number", "order_date", "arrival_date", "period_start", "period_end"], True), self.get_common_fields("specialty_name_zaoch"))
    def reported_student_day_scor_page(self):
        self.show_print_dialog("Друк повідомлення (скорочена)", lambda d: self.handle_report_print(d, self.document_printer.print_reported_student_day_scor, ["specialty_name_day_scor", "finance_type", "order_number", "order_date", "arrival_date", "period_start", "period_end"], True), self.get_common_fields("specialty_name_day_scor"))
    def vitag_nakaz_denne_page(self):
        self.show_print_dialog("Друк витягу (денна)", lambda d: self.handle_report_print(d, self.document_printer.print_vitag_nakaz_denne, ["specialty_name", "finance_type", "order_number", "order_date", "protokol_number", "protokol_date", "zarah_date", "period_start", "period_end"], True), self.get_vitag_fields("specialty_name"))
    def vitag_nakaz_zaoch_page(self):
        self.show_print_dialog("Друк витягу (заочна)", lambda d: self.handle_report_print(d, self.document_printer.print_vitag_nakaz_zaoch, ["specialty_name_zaoch", "finance_type", "order_number", "order_date", "protokol_number", "protokol_date", "zarah_date", "period_start", "period_end"], True), self.get_vitag_fields("specialty_name_zaoch"))
    def vitag_nakaz_day_scor_page(self):
        self.show_print_dialog("Друк витягу (скорочена)", lambda d: self.handle_report_print(d, self.document_printer.print_vitag_nakaz_day_scor, ["specialty_name_day_scor", "finance_type", "order_number", "order_date", "protokol_number", "protokol_date", "zarah_date", "period_start", "period_end"], True), self.get_vitag_fields("specialty_name_day_scor"))
    def list_grup_page(self):
        self.show_print_dialog("Друк списків груп", lambda d: self.handle_report_print(d, self.document_printer.print_list_grup, ["number_group"]), [{"type": "text", "label": "Номер групи", "name": "number_group"}])
    def list_grup_roz_page(self):
        self.show_print_dialog("Друк розширених списків", lambda d: self.handle_report_print(d, self.document_printer.print_list_grup_roz, ["number_group"]), [{"type": "text", "label": "Номер групи", "name": "number_group"}])
    def export_date_student_page(self): self.document_printer.print_export_date_vstupnik()

    def get_common_fields(self, spec_name):
        return [{"type": "combo", "label": "Спеціальність", "name": spec_name}, {"type": "radio_group", "label": "Фінансування", "name": "finance_type", "options": ["Державна форма", "Платна форма"], "default": "Державна форма"}, {"type": "text", "label": "№ наказу", "name": "order_number"}, {"type": "text", "label": "Дата наказу", "name": "order_date"}, {"type": "text", "label": "Дата прибуття", "name": "arrival_date"}, {"type": "text", "label": "Початок", "name": "period_start"}, {"type": "text", "label": "Кінець", "name": "period_end"}]

    def get_vitag_fields(self, spec_name):
        return [{"type": "combo", "label": "Спеціальність", "name": spec_name}, {"type": "radio_group", "label": "Фінансування", "name": "finance_type", "options": ["Державна форма", "Платна форма"], "default": "Державна форма"}, {"type": "text", "label": "№ наказу", "name": "order_number"}, {"type": "text", "label": "Дата наказу", "name": "order_date"}, {"type": "text", "label": "№ протоколу", "name": "protokol_number"}, {"type": "text", "label": "Дата протоколу", "name": "protokol_date"}, {"type": "text", "label": "Дата зарахування", "name": "zarah_date"}, {"type": "text", "label": "Початок", "name": "period_start"}, {"type": "text", "label": "Кінець", "name": "period_end"}]

    def show_error_message(self, m): show_error(self, m)
    def show_success_message(self, m): show_success(self, m)