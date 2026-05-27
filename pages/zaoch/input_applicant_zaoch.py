from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox,
    QFormLayout, QGroupBox, QScrollArea, QHBoxLayout
)
from PyQt5.QtGui import QCursor, QIntValidator, QRegExpValidator
from PyQt5.QtCore import Qt, QTimer, QRegExp
from db.repository import ApplicantRepository
from utils.logger import log_error, log_info
from utils.notifications import show_error, show_success
from datetime import datetime
import re

class DateLineEdit(QLineEdit):
    def __init__(self, width=None, parent=None):
        if isinstance(width, QWidget):
            parent = width
            width = None
        super().__init__(parent)
        if width is not None:
            self.setFixedWidth(width)
        self.setPlaceholderText("ДД.ММ.РРРР")
        self.setStyleSheet("letter-spacing: 2px;")
        
    def focusInEvent(self, event):
        if not self.text() or self.text() == "__.__.____":
            self.setInputMask("99.99.9999;_")
            self.setCursorPosition(0)
        super().focusInEvent(event)
        
    def focusOutEvent(self, event):
        cleaned = self.text().replace(".", "").replace("_", "").strip()
        if not cleaned:
            self.setInputMask("")
            self.setPlaceholderText("ДД.ММ.РРРР")
        super().focusOutEvent(event)

    def setText(self, text):
        if text and text.strip():
            self.setInputMask("99.99.9999;_")
            super().setText(text)
        else:
            self.setInputMask("")
            super().setText("")

class PhoneLineEdit(QLineEdit):
    def __init__(self, width=None, parent=None):
        if isinstance(width, QWidget):
            parent = width
            width = None
        super().__init__(parent)
        if width is not None:
            self.setFixedWidth(width)
        self.setPlaceholderText("+380 (ХХ) ХХХ-ХХ-ХХ")
        self.setStyleSheet("letter-spacing: 2px;")
        
    def focusInEvent(self, event):
        if not self.text() or self.text() == "+380 (__) ___-__-__":
            self.setInputMask("+38\\0 (99) 999-99-99;_")
            self.setCursorPosition(6)
        super().focusInEvent(event)
        
    def focusOutEvent(self, event):
        cleaned = self.text().replace("+380", "").replace("(", "").replace(")", "").replace("-", "").replace("_", "").strip()
        if not cleaned:
            self.setInputMask("")
            self.setPlaceholderText("+380 (ХХ) ХХХ-ХХ-ХХ")
        super().focusOutEvent(event)

    def setText(self, text):
        if text and text.strip() and text != "+380 (__) ___-__-__":
            raw_digits = "".join(c for c in text if c.isdigit())
            if len(raw_digits) == 12 and raw_digits.startswith("380"):
                formatted = f"+380 ({raw_digits[3:5]}) {raw_digits[5:8]}-{raw_digits[8:10]}-{raw_digits[10:12]}"
                self.setInputMask("+38\\0 (99) 999-99-99;_")
                super().setText(formatted)
                return
            elif len(raw_digits) == 9:
                formatted = f"+380 ({raw_digits[0:2]}) {raw_digits[2:5]}-{raw_digits[5:7]}-{raw_digits[7:9]}"
                self.setInputMask("+38\\0 (99) 999-99-99;_")
                super().setText(formatted)
                return
            self.setInputMask("+38\\0 (99) 999-99-99;_")
            super().setText(text)
        else:
            self.setInputMask("")
            super().setText("")

class InputApplicantZaoch(QWidget):
    def __init__(self):
        super(InputApplicantZaoch, self).__init__()

        # Основний лейаут
        layout = QVBoxLayout(self); layout.setContentsMargins(10, 10, 10, 10); layout.setSpacing(10)


        # Заголовок
        label = QLabel("Форма для введення нового вступника (заочної форми)", self)
        layout.addWidget(label)

        # Пошук
        search_layout = QHBoxLayout(); search_layout.setContentsMargins(0, 0, 0, 0); search_layout.setSpacing(10)
        self.search_input = QLineEdit(self)
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Пошук за прізвищем, ім'ям або номером свідоцтва...")
        self.search_input.setMaxLength(100)
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Шукати", self)
        self.search_button.setObjectName("searchButton")
        self.search_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.search_button.clicked.connect(self.search_applicant)
        search_layout.addWidget(self.search_button)

        self.clear_button = QPushButton("Очистити форму", self)
        self.clear_button.setObjectName("clearButton")
        self.clear_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.clear_button.clicked.connect(self.clear_all_fields)
        search_layout.addWidget(self.clear_button)

        self.cancel_button = QPushButton("Скасувати пошук", self)
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.cancel_button.setEnabled(False)
        self.cancel_button
        self.cancel_button.clicked.connect(self.cancel_search)
        search_layout.addWidget(self.cancel_button)

        layout.addLayout(search_layout)

        # Прокручувана область
        scroll_area = QScrollArea(self); scroll_area.setFrameShape(QScrollArea.NoFrame); scroll_area.setViewportMargins(0, 0, 0, 0); scroll_area.setContentsMargins(0, 0, 0, 0)
        scroll_area.setWidgetResizable(True)
        container = QWidget(); container.setObjectName("formContainer")
        form_layout = QFormLayout(container); form_layout.setLabelAlignment(Qt.AlignLeft); form_layout.setFormAlignment(Qt.AlignLeft); form_layout.setLabelAlignment(Qt.AlignLeft); form_layout.setFormAlignment(Qt.AlignLeft); form_layout.setContentsMargins(0, 0, 0, 0); form_layout.setSpacing(10)

        # Група 1: Персональні дані
        personal_data_group = QGroupBox("Персональні дані вступника")
        personal_data_group.setObjectName("groupBox")
        personal_form_layout = QFormLayout(); personal_form_layout.setLabelAlignment(Qt.AlignLeft); personal_form_layout.setFormAlignment(Qt.AlignLeft); personal_form_layout.setContentsMargins(0, 0, 0, 0); personal_form_layout.setSpacing(10)

        # ПІБ
        name_layout = QHBoxLayout(); name_layout.setContentsMargins(0, 0, 0, 0); name_layout.setSpacing(10)
        self.last_name_input = self.create_input_field()
        self.first_name_input = self.create_input_field()
        self.middle_name_input = self.create_input_field()
        self.last_name_input.setObjectName("inputField")
        self.first_name_input.setObjectName("inputField")
        self.middle_name_input.setObjectName("inputField")
        self.last_name_input.setPlaceholderText("Прізвище")
        self.first_name_input.setPlaceholderText("Ім'я")
        self.middle_name_input.setPlaceholderText("По-батькові")
        name_layout.addWidget(QLabel("Прізвище <span style='color: red;'>*</span>:"))
        name_layout.addWidget(self.last_name_input)
        name_layout.addWidget(QLabel("Ім'я <span style='color: red;'>*</span>:"))
        name_layout.addWidget(self.first_name_input)
        name_layout.addWidget(QLabel("По-батькові:"))
        name_layout.addWidget(self.middle_name_input)
        personal_form_layout.addRow(name_layout)

        self.pip_input = self.create_input_field()
        self.pip_input.setObjectName("inputField")
        self.pip_input.setPlaceholderText("ПІП у родовому відмінку")
        personal_form_layout.addRow("ПІП родовий відмінок <span style='color: red;'>*</span>:", self.pip_input)

        # Свідоцтво
        cert_layout = QHBoxLayout(); cert_layout.setContentsMargins(0, 0, 0, 0); cert_layout.setSpacing(10)
        self.cert_number_input = self.create_input_field(validator=QRegExpValidator(QRegExp(r"[А-ЯІЇЄҐ№ 0-9]*"), self))
        self.cert_number_input.setObjectName("inputField")
        self.cert_number_input.setInputMask("AA №00000000")  # Маска з пробілом перед "№"
        self.cert_number_input.setStyleSheet("letter-spacing: 2px;")
        self.cert_number_input.setPlaceholderText("АА №12345678")
        self.cert_issue_date_input = DateLineEdit(self)
        self.cert_issue_date_input.setObjectName("inputField")
        cert_layout.addWidget(QLabel("Номер свідоцтва <span style='color: red;'>*</span>:"))
        cert_layout.addWidget(self.cert_number_input)
        cert_layout.addWidget(QLabel("Дата видачі свідоцтва:"))
        cert_layout.addWidget(self.cert_issue_date_input)
        personal_form_layout.addRow(cert_layout)

        self.school_name_input = self.create_input_field()
        self.address_input = self.create_input_field()
        self.school_name_input.setObjectName("inputField")
        self.address_input.setObjectName("inputField")
        self.school_name_input.setPlaceholderText("Назва школи")
        self.address_input.setPlaceholderText("Місто, вулиця, будинок...")
        personal_form_layout.addRow("Назва школи:", self.school_name_input)
        personal_form_layout.addRow("Адреса проживання:", self.address_input)

        # Контакти та громадянство
        contact_layout = QHBoxLayout(); contact_layout.setContentsMargins(0, 0, 0, 0); contact_layout.setSpacing(10)
        self.phone_input = PhoneLineEdit(self)
        self.phone_input.setObjectName("inputField")
        self.citizenship_input = self.create_input_field()
        self.citizenship_input.setObjectName("inputField")
        self.citizenship_input.setText("України")
        self.date_birth_input = DateLineEdit(self)
        self.date_birth_input.setObjectName("inputField")
        contact_layout.addWidget(QLabel("Телефон:"))
        contact_layout.addWidget(self.phone_input)
        contact_layout.addWidget(QLabel("Громадянство:"))
        contact_layout.addWidget(self.citizenship_input)
        contact_layout.addWidget(QLabel("Дата народження:"))
        contact_layout.addWidget(self.date_birth_input)
        personal_form_layout.addRow(contact_layout)

        # Паспорт
        passport_layout = QHBoxLayout(); passport_layout.setContentsMargins(0, 0, 0, 0); passport_layout.setSpacing(10)
        self.passport_number_input = self.create_input_field(validator=QRegExpValidator(QRegExp(r"^[А-ЯІЇЄҐ]{0,2}\d{6,9}$|^$"), self))
        self.passport_number_input.setObjectName("inputField")
        self.passport_number_input.setPlaceholderText("123456789 або AA123456")
        self.issued_by_input = self.create_input_field()
        self.issued_by_input.setObjectName("inputField")
        self.issued_by_input.setPlaceholderText("Напр., 071 або МВС України")
        self.issue_date_input = DateLineEdit(150, self)
        self.issue_date_input.setObjectName("inputField")
        self.id_code_input = self.create_input_field(150, validator=QRegExpValidator(QRegExp(r"^\d{10}$|^$"), self))
        self.id_code_input.setObjectName("inputField")
        self.id_code_input.setPlaceholderText("10 цифр")
        passport_layout.addWidget(QLabel("Номер паспорта:"))
        passport_layout.addWidget(self.passport_number_input)
        passport_layout.addWidget(QLabel("Ким виданий:"))
        passport_layout.addWidget(self.issued_by_input)
        passport_layout.addWidget(QLabel("Дата видачі:"))
        passport_layout.addWidget(self.issue_date_input)
        passport_layout.addWidget(QLabel("Ідентифікаційний код:"))
        passport_layout.addWidget(self.id_code_input)
        personal_form_layout.addRow(passport_layout)

        personal_data_group.setLayout(personal_form_layout)

        # Група 2: Дані батьків
        parents_data_group = QGroupBox("Дані батьків")
        parents_data_group.setObjectName("groupBox")
        parents_layout = QHBoxLayout(); parents_layout.setContentsMargins(0, 0, 0, 0); parents_layout.setSpacing(10)

        father_layout = QVBoxLayout()
        father_layout.addWidget(QLabel("Прізвище батька:"))
        self.father_last_name_input = self.create_input_field()
        self.father_last_name_input.setObjectName("inputField")
        self.father_last_name_input.setPlaceholderText("Прізвище")
        father_layout.addWidget(self.father_last_name_input)
        father_layout.addWidget(QLabel("Ім'я батька:"))
        self.father_first_name_input = self.create_input_field()
        self.father_first_name_input.setObjectName("inputField")
        self.father_first_name_input.setPlaceholderText("Ім'я")
        father_layout.addWidget(self.father_first_name_input)
        father_layout.addWidget(QLabel("По-батькові батька:"))
        self.father_middle_name_input = self.create_input_field()
        self.father_middle_name_input.setObjectName("inputField")
        self.father_middle_name_input.setPlaceholderText("По-батькові")
        father_layout.addWidget(self.father_middle_name_input)
        father_layout.addWidget(QLabel("Місце роботи та посада батька:"))
        self.father_job_input = self.create_input_field()
        self.father_job_input.setObjectName("inputField")
        self.father_job_input.setPlaceholderText("Місце роботи, посада")
        father_layout.addWidget(self.father_job_input)
        father_layout.addWidget(QLabel("Телефон батька:"))
        self.father_phone_input = PhoneLineEdit(self)
        self.father_phone_input.setObjectName("inputField")
        father_layout.addWidget(self.father_phone_input)

        mother_layout = QVBoxLayout()
        mother_layout.addWidget(QLabel("Прізвище матері:"))
        self.mother_last_name_input = self.create_input_field()
        self.mother_last_name_input.setObjectName("inputField")
        self.mother_last_name_input.setPlaceholderText("Прізвище")
        mother_layout.addWidget(self.mother_last_name_input)
        mother_layout.addWidget(QLabel("Ім'я матері:"))
        self.mother_first_name_input = self.create_input_field()
        self.mother_first_name_input.setObjectName("inputField")
        self.mother_first_name_input.setPlaceholderText("Ім'я")
        mother_layout.addWidget(self.mother_first_name_input)
        mother_layout.addWidget(QLabel("По-батькові:"))
        self.mother_middle_name_input = self.create_input_field()
        self.mother_middle_name_input.setObjectName("inputField")
        self.mother_middle_name_input.setPlaceholderText("По-батькові")
        mother_layout.addWidget(self.mother_middle_name_input)
        mother_layout.addWidget(QLabel("Місце роботи та посада:"))
        self.mother_job_input = self.create_input_field()
        self.mother_job_input.setObjectName("inputField")
        self.mother_job_input.setPlaceholderText("Місце роботи, посада")
        mother_layout.addWidget(self.mother_job_input)
        mother_layout.addWidget(QLabel("Телефон матері:"))
        self.mother_phone_input = PhoneLineEdit(self)
        self.mother_phone_input.setObjectName("inputField")
        mother_layout.addWidget(self.mother_phone_input)

        parents_layout.addLayout(father_layout)
        parents_layout.addLayout(mother_layout)
        parents_data_group.setLayout(parents_layout)

        # Група 3: Оцінки
        grades_group = QGroupBox("Оцінки")
        grades_group.setObjectName("groupBox")
        grades_form_layout = QHBoxLayout(); grades_form_layout.setContentsMargins(0, 0, 0, 0); grades_form_layout.setSpacing(10)
        self.algebra_input = self.create_input_field(validator=QIntValidator(1, 12, self))
        self.geometry_input = self.create_input_field(validator=QIntValidator(1, 12, self))
        self.ukr_language_input = self.create_input_field(validator=QIntValidator(1, 12, self))
        self.ukr_literature_input = self.create_input_field(validator=QIntValidator(1, 12, self))
        self.algebra_input.setObjectName("inputField")
        self.geometry_input.setObjectName("inputField")
        self.ukr_language_input.setObjectName("inputField")
        self.ukr_literature_input.setObjectName("inputField")
        self.algebra_input.setPlaceholderText("1–12")
        self.geometry_input.setPlaceholderText("1–12")
        self.ukr_language_input.setPlaceholderText("1–12")
        self.ukr_literature_input.setPlaceholderText("1–12")
        grades_form_layout.addWidget(QLabel("Алгебра:"))
        grades_form_layout.addWidget(self.algebra_input)
        grades_form_layout.addWidget(QLabel("Геометрія:"))
        grades_form_layout.addWidget(self.geometry_input)
        grades_form_layout.addWidget(QLabel("Українська мова:"))
        grades_form_layout.addWidget(self.ukr_language_input)
        grades_form_layout.addWidget(QLabel("Українська література:"))
        grades_form_layout.addWidget(self.ukr_literature_input)
        grades_group.setLayout(grades_form_layout)

        # Група 4: Інші дані
        other_data_group = QGroupBox("Інші дані")
        other_data_group.setObjectName("groupBox")
        other_data_form_layout = QFormLayout(); other_data_form_layout.setLabelAlignment(Qt.AlignLeft); other_data_form_layout.setFormAlignment(Qt.AlignLeft); other_data_form_layout.setContentsMargins(0, 0, 0, 0); other_data_form_layout.setSpacing(10)
        other_data_form_layout.setLabelAlignment(Qt.AlignLeft)
        other_data_form_layout.setFormAlignment(Qt.AlignLeft)
        self.hostel_need_input = QComboBox(self)
        self.hostel_need_input.setObjectName("comboBox")
        self.hostel_need_input.addItems(["Ні", "Так"])
        self.hostel_need_input.setFixedWidth(150)
        self.gender_input = QComboBox(self)
        self.gender_input.setObjectName("comboBox")
        self.gender_input.addItems(["Чоловіча", "Жіноча"])
        self.gender_input.setFixedWidth(150)
        other_data_form_layout.addRow("Потреба в гуртожитку:", self.hostel_need_input)
        other_data_form_layout.addRow("Стать:", self.gender_input)
        other_data_group.setLayout(other_data_form_layout)

        form_layout.addWidget(personal_data_group)
        form_layout.addWidget(parents_data_group)
        form_layout.addWidget(grades_group)
        form_layout.addWidget(other_data_group)

        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)

        # Кнопки
        button_layout = QHBoxLayout(); button_layout.setContentsMargins(0, 20, 0, 0); button_layout.setSpacing(10)
        
        self.input_button = QPushButton("Ввести нового вступника", self)
        self.input_button.setObjectName("greenButton")
        self.input_button.setEnabled(False)
        self.input_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.input_button.clicked.connect(self.submit_applicant_data)
        button_layout.addWidget(self.input_button)

        self.edit_button = QPushButton("Редагувати вступника", self)
        self.edit_button.setObjectName("editButton")
        self.edit_button.setEnabled(False)
        self.edit_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.edit_button.clicked.connect(self.edit_applicant_data)
        button_layout.addWidget(self.edit_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Форматування тексту
        self.last_name_input.textChanged.connect(lambda: self.format_text_input(self.last_name_input))
        self.first_name_input.textChanged.connect(lambda: self.format_text_input(self.first_name_input))
        self.middle_name_input.textChanged.connect(lambda: self.format_text_input(self.middle_name_input))
        # self.school_name_input.textChanged.connect(lambda: self.format_text_input(self.school_name_input))
        self.father_last_name_input.textChanged.connect(lambda: self.format_text_input(self.father_last_name_input))
        self.father_first_name_input.textChanged.connect(lambda: self.format_text_input(self.father_first_name_input))
        self.father_middle_name_input.textChanged.connect(lambda: self.format_text_input(self.father_middle_name_input))
        self.mother_last_name_input.textChanged.connect(lambda: self.format_text_input(self.mother_last_name_input))
        self.mother_first_name_input.textChanged.connect(lambda: self.format_text_input(self.mother_first_name_input))
        self.mother_middle_name_input.textChanged.connect(lambda: self.format_text_input(self.mother_middle_name_input))

        # Перевірка обов’язкових полів
        self.last_name_input.textChanged.connect(self.check_required_fields)
        self.first_name_input.textChanged.connect(self.check_required_fields)
        self.pip_input.textChanged.connect(self.check_required_fields)
        self.cert_number_input.textChanged.connect(self.check_required_fields)

    def create_input_field(self, width=None, validator=None):
        """Створює поле вводу з валідатором."""
        input_field = QLineEdit(self)
        if width:
            input_field.setFixedWidth(width)
        if validator:
            input_field.setValidator(validator)
        return input_field

    def format_text_input(self, input_field):
        """Форматує текст: перша літера велика, решта малі, та оновлює ПІП."""
        text = input_field.text().strip().capitalize()
        input_field.setText(text)
        if input_field in [self.last_name_input, self.first_name_input, self.middle_name_input]:
            self.update_pip_input()

    def update_pip_input(self):
        """Автоматично заповнює поле ПІП у родовому відмінку з великої літери."""
        last_name = self.last_name_input.text().strip()
        first_name = self.first_name_input.text().strip()
        middle_name = self.middle_name_input.text().strip()

        if not last_name or not first_name:
            return

        def to_genitive(name, gender='masc'):
            name = name.lower()
            if gender == 'masc':
                if name.endswith('о') or name.endswith('ь'):
                    return name[:-1] + 'я'
                elif name.endswith('й'):
                    return name[:-1] + 'я'
                else:
                    return name + 'а'
            elif gender == 'fem':
                if name.endswith('а'):
                    return name[:-1] + 'и'
                elif name.endswith('я'):
                    return name[:-1] + 'і'
                else:
                    return name
            return name

        gender = 'fem' if middle_name.endswith(('івна', 'ївна')) else 'masc'
        gen_last_name = to_genitive(last_name, gender).title()
        gen_first_name = to_genitive(first_name, gender).title()
        gen_middle_name = to_genitive(middle_name, gender).title() if middle_name else ""

        pip = f"{gen_last_name} {gen_first_name}"
        if gen_middle_name:
            pip += f" {gen_middle_name}"
        self.pip_input.setText(pip.strip())

    def format_date_input(self, input_field):
        """Автоматично додає крапки для формату DD.MM.YYYY."""
        text = input_field.text().replace(".", "")
        cursor_pos = input_field.cursorPosition()
        new_text = ""

        for i, char in enumerate(text):
            if not char.isdigit():
                continue
            new_text += char
            if i == 1 or i == 3:
                new_text += "."

        if len(new_text) > 10:
            new_text = new_text[:10]

        input_field.blockSignals(True)
        input_field.setText(new_text)
        input_field.setCursorPosition(min(cursor_pos + (new_text.count(".") - text.count(".")), len(new_text)))
        input_field.blockSignals(False)

    def validate_date(self, date_str):
        """Перевіряє, чи дата є валідною."""
        try:
            datetime.strptime(date_str, "%d.%m.%Y")
            return True
        except ValueError:
            return False

    def search_applicant(self):
        """Шукає вступника за прізвищем, ім'ям або номером свідоцтва."""
        search_text = self.search_input.text().strip()
        if not search_text:
            show_error(self, "Будь ласка, введіть дані для пошуку.")
            return

        repo = ApplicantRepository()
        try:
            # Чистимо пошуковий текст
            cleaned_search = re.sub(r"[ №\u00A0]", "", search_text.upper())
            
            # Пошук через SQL (поки що напряму через репозиторій для гнучкості пошуку)
            query = ""
            params = ()
            
            if re.match(r"^[А-ЯІЇЄҐ]{0,2}\d{8}$", cleaned_search) or re.match(r"^\d{8}$", cleaned_search):
                query = """
                    SELECT * FROM applicant_personal_data_evening 
                    WHERE REPLACE(REPLACE(REPLACE(UPPER(cert_number), ' ', ''), '№', ''), ' ', '') LIKE %s
                """
                params = (f"%{cleaned_search}",)
            else:
                search_parts = search_text.split()
                if len(search_parts) == 1:
                    query = "SELECT * FROM applicant_personal_data_evening WHERE LOWER(last_name) LIKE LOWER(%s)"
                    params = (f"%{search_text}%",)
                elif len(search_parts) >= 2:
                    query = """
                        SELECT * FROM applicant_personal_data_evening
                        WHERE LOWER(last_name) LIKE LOWER(%s) AND LOWER(first_name) LIKE LOWER(%s)
                    """
                    params = (f"%{search_parts[0]}%", f"%{search_parts[1]}%")

            applicant = repo.execute_query(query, params, fetch_all=False)
            if applicant:
                self.populate_fields(applicant)
                self.edit_button.setEnabled(True)
                self.edit_button
                self.cancel_button.setEnabled(True)
                self.cancel_button
                self.input_button.setEnabled(False)
                self.input_button
                show_success(self, "Дані вступника знайдено.")
            else:
                show_error(self, "Вступник не знайдений.")
                self.clear_all_fields()
        except Exception as e:
            log_error(f"Помилка при пошуку вступника {search_text}", e)
            show_error(self, f"Помилка при пошуку: {str(e)}")
    def submit_applicant_data(self):
        """Зберігає дані вступника через репозиторій."""
        data = [
            self.first_name_input.text().strip(), self.last_name_input.text().strip(), self.middle_name_input.text().strip(),
            self.pip_input.text().strip(), self.phone_input.text().strip(), self.citizenship_input.text().strip(),
            self.cert_number_input.text().strip(), self.passport_number_input.text().strip(), self.issued_by_input.text().strip(),
            self.issue_date_input.text().strip(), self.id_code_input.text().strip(), self.address_input.text().strip(),
            self.father_first_name_input.text().strip(), self.father_last_name_input.text().strip(), self.father_middle_name_input.text().strip(),
            self.father_job_input.text().strip(), self.father_phone_input.text().strip(), self.mother_first_name_input.text().strip(),
            self.mother_last_name_input.text().strip(), self.mother_middle_name_input.text().strip(), self.mother_phone_input.text().strip(),
            self.mother_job_input.text().strip(), self.hostel_need_input.currentText().strip(), self.gender_input.currentText().strip(),
            self.algebra_input.text().strip(), self.geometry_input.text().strip(), self.ukr_language_input.text().strip(),
            self.ukr_literature_input.text().strip(), self.school_name_input.text().strip(), self.cert_issue_date_input.text().strip(),
            self.date_birth_input.text().strip()
        ]

        repo = ApplicantRepository()
        try:
            if repo.is_applicant_exists(data[0], data[1], data[2], data[6], data[7], data[10], form_type='zaoch'):
                show_error(self, "Вступник із такими даними вже існує!")
                return

            if repo.add_applicant(data, form_type='zaoch'):
                show_success(self, "Дані вступника успішно збережено!")
                log_info(f"Додано вступника (заочна): {data[1]} {data[0]}")
                self.clear_all_fields()
            else:
                show_error(self, "Помилка при збереженні даних.")
        except Exception as e:
            log_error("Критична помилка при збереженні вступника (заочна)", e)
            show_error(self, f"Помилка: {str(e)}")
    def edit_applicant_data(self):
        """Оновлює дані вступника через репозиторій."""
        data = [
            self.first_name_input.text().strip(), self.last_name_input.text().strip(), self.middle_name_input.text().strip(),
            self.pip_input.text().strip(), self.phone_input.text().strip(), self.citizenship_input.text().strip(),
            self.cert_number_input.text().strip(), self.passport_number_input.text().strip(), self.issued_by_input.text().strip(),
            self.issue_date_input.text().strip(), self.id_code_input.text().strip(), self.address_input.text().strip(),
            self.father_first_name_input.text().strip(), self.father_last_name_input.text().strip(), self.father_middle_name_input.text().strip(),
            self.father_job_input.text().strip(), self.father_phone_input.text().strip(), self.mother_first_name_input.text().strip(),
            self.mother_last_name_input.text().strip(), self.mother_middle_name_input.text().strip(), self.mother_phone_input.text().strip(),
            self.mother_job_input.text().strip(), self.hostel_need_input.currentText().strip(), self.gender_input.currentText().strip(),
            self.algebra_input.text().strip(), self.geometry_input.text().strip(), self.ukr_language_input.text().strip(),
            self.ukr_literature_input.text().strip(), self.school_name_input.text().strip(), self.cert_issue_date_input.text().strip(),
            self.date_birth_input.text().strip()
        ]

        repo = ApplicantRepository()
        try:
            # Оновлення через SQL (поки що напряму через ревізію методу в майбутньому)
            columns = [
                "first_name", "last_name", "middle_name", "pip", "phone", "citizenship", "cert_number", 
                "passport_number", "issued_by", "issue_date", "id_code", "address", "father_first_name", 
                "father_last_name", "father_middle_name", "father_job", "father_phone", "mother_first_name", 
                "mother_last_name", "mother_middle_name", "mother_phone", "mother_job", "hostel_need", 
                "gender", "algebra", "geometry", "ukr_language", "ukr_literature", "school_name", 
                "cert_issue_date", "date_birth"
            ]
            set_clause = ", ".join([f"{col}=%s" for col in columns])
            query = f"UPDATE applicant_personal_data_evening SET {set_clause} WHERE cert_number=%s"
            
            params = tuple(data) + (data[6],)
            
            repo._connect()
            repo.cursor.execute(query, params)
            repo.conn.commit()
            repo._close()

            show_success(self, "Дані вступника успішно оновлено!")
            log_info(f"Оновлено вступника (заочна): {data[6]}")
            self.clear_all_fields()
        except Exception as e:
            log_error(f"Помилка при оновленні вступника {data[6]}", e)
            show_error(self, f"Помилка: {str(e)}")

    def clear_all_fields(self):
        """Очищує всі поля введення."""
        self.first_name_input.clear()
        self.last_name_input.clear()
        self.middle_name_input.clear()
        self.pip_input.clear()
        self.phone_input.clear()
        self.citizenship_input.setText("України")
        self.date_birth_input.clear()
        self.cert_number_input.clear()
        self.cert_issue_date_input.clear()
        self.passport_number_input.clear()
        self.issued_by_input.clear()
        self.issue_date_input.clear()
        self.id_code_input.clear()
        self.address_input.clear()
        self.father_first_name_input.clear()
        self.father_last_name_input.clear()
        self.father_middle_name_input.clear()
        self.father_job_input.clear()
        self.father_phone_input.clear()
        self.mother_first_name_input.clear()
        self.mother_last_name_input.clear()
        self.mother_middle_name_input.clear()
        self.mother_phone_input.clear()
        self.mother_job_input.clear()
        self.algebra_input.clear()
        self.geometry_input.clear()
        self.ukr_language_input.clear()
        self.ukr_literature_input.clear()
        self.school_name_input.clear()
        self.hostel_need_input.setCurrentIndex(0)
        self.gender_input.setCurrentIndex(0)
        self.input_button.setEnabled(False)
        self.input_button
        self.edit_button.setEnabled(False)
        self.edit_button
        self.cancel_button.setEnabled(False)
        self.cancel_button

    def cancel_search(self):
        """Скасовує пошук і очищає форму."""
        self.clear_all_fields()
        self.search_input.clear()

    def populate_fields(self, applicant):
        """Автоматично заповнює поля форми знайденими даними."""
        self.first_name_input.setText(applicant[1] or "")
        self.last_name_input.setText(applicant[2] or "")
        self.middle_name_input.setText(applicant[3] or "")
        self.pip_input.setText(applicant[4] or "")
        self.phone_input.setText(applicant[5] or "")
        self.citizenship_input.setText(applicant[6] or "")
        self.date_birth_input.setText(applicant[31] or "")
        self.cert_number_input.setText(applicant[7] or "")
        self.cert_issue_date_input.setText(applicant[30] or "")
        self.passport_number_input.setText(applicant[8] or "")
        self.issued_by_input.setText(applicant[9] or "")
        self.issue_date_input.setText(applicant[10] or "")
        self.id_code_input.setText(applicant[11] or "")
        self.address_input.setText(applicant[12] or "")
        self.school_name_input.setText(applicant[29] or "")
        self.father_first_name_input.setText(applicant[13] or "")
        self.father_last_name_input.setText(applicant[14] or "")
        self.father_middle_name_input.setText(applicant[15] or "")
        self.father_job_input.setText(applicant[16] or "")
        self.father_phone_input.setText(applicant[17] or "")
        self.mother_first_name_input.setText(applicant[18] or "")
        self.mother_last_name_input.setText(applicant[19] or "")
        self.mother_middle_name_input.setText(applicant[20] or "")
        self.mother_phone_input.setText(applicant[21] or "")
        self.mother_job_input.setText(applicant[22] or "")
        self.algebra_input.setText(str(applicant[25]) if applicant[25] is not None else "")
        self.geometry_input.setText(str(applicant[26]) if applicant[26] is not None else "")
        self.ukr_language_input.setText(str(applicant[27]) if applicant[27] is not None else "")
        self.ukr_literature_input.setText(str(applicant[28]) if applicant[28] is not None else "")
        self.hostel_need_input.setCurrentText(applicant[23] or "Ні")
        self.gender_input.setCurrentText(applicant[24] or "Чоловіча")

    def check_required_fields(self):
        """Перевіряє, чи всі обов'язкові поля заповнені."""
        is_fields_filled = (
            self.last_name_input.text().strip() and
            self.first_name_input.text().strip() and
            self.pip_input.text().strip() and
            self.cert_number_input.text().strip() and
            len(self.cert_number_input.text().strip().split("№")[1]) == 8
        )
        if self.edit_button.isEnabled():
            self.input_button.setEnabled(False)
            self.input_button
            self.edit_button.setEnabled(True)
            self.edit_button
            self.cancel_button.setEnabled(True)
            self.cancel_button
        else:
            if is_fields_filled:
                self.input_button.setEnabled(True)
                self.input_button
            else:
                self.input_button.setEnabled(False)
                self.input_button
                self.edit_button.setEnabled(False)
                self.edit_button
                self.cancel_button.setEnabled(False)
                self.cancel_button

    def show_error_message(self, message):
        """Показ повідомлення про помилку на 5 секунд."""
        self._show_message(message, "red")

    def show_success_message(self, message):
        """Показ повідомлення про успішний пошук на 5 секунд."""
        self._show_message(message, "green")

    def _show_message(self, message, color):
        """Відображає повідомлення на вказаний час."""
        # Видаляємо попереднє повідомлення, якщо воно є
        if hasattr(self, '_current_label') and self._current_label:
            self._current_label.hide()
            self.layout().removeWidget(self._current_label)
            self._current_label.deleteLater()
            self._current_label = None

        # Створюємо нове повідомлення
        label = QLabel(message, self)
        label.setStyleSheet(f"color: {color};")
        label.setObjectName("message_label")
        label.setAlignment(Qt.AlignCenter)
        self.layout().insertWidget(0, label)
        
        # Зберігаємо поточне повідомлення
        self._current_label = label

        # Приховуємо повідомлення через 5 секунд
        QTimer.singleShot(5000, self._current_label.hide)