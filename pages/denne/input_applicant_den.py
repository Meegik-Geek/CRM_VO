from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox,
    QFormLayout, QGroupBox, QScrollArea, QHBoxLayout
)
from PyQt5.QtGui import QCursor, QIntValidator, QRegExpValidator
from PyQt5.QtCore import Qt, QTimer, QRegExp
from datetime import datetime
from db.repository import ApplicantRepository
from utils.logger import log_error, log_info
from utils.notifications import show_error, show_success
import re

class InputApplicantDen(QWidget):
    def __init__(self):
        super(InputApplicantDen, self).__init__()

        # Основний лейаут
        layout = QVBoxLayout(self)

        # Заголовок
        label = QLabel("Форма для введення нового вступника", self)
        
        layout.addWidget(label)

        # Пошук
        search_layout = QHBoxLayout()
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
        self.cancel_button.setStyleSheet("background-color: #E0E0E0; color: #707070;")
        self.cancel_button.clicked.connect(self.cancel_search)
        search_layout.addWidget(self.cancel_button)

        layout.addLayout(search_layout)

        # Прокручувана область
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        form_layout = QFormLayout(container)

        # Група 1: Персональні дані
        personal_data_group = QGroupBox("Персональні дані вступника")
        personal_data_group.setObjectName("groupBox")
        personal_form_layout = QFormLayout()

        # ПІБ
        name_layout = QHBoxLayout()
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
        cert_layout = QHBoxLayout()
        self.cert_number_input = self.create_input_field(validator=QRegExpValidator(QRegExp(r"[А-ЯІЇЄҐ№ 0-9]*"), self))
        self.cert_number_input.setObjectName("inputField")
        self.cert_number_input.setInputMask("AA №00000000")  # Маска з пробілом перед "№"
        self.cert_number_input.setStyleSheet("letter-spacing: 2px;")
        self.cert_number_input.setPlaceholderText("АА №12345678")
        # self.cert_number_input.textEdited.connect(self.validate_cert_number_input)
        
        self.cert_issue_date_input = self.create_input_field(validator=QRegExpValidator(QRegExp(r"^\d{2}\.\d{2}\.\d{4}$|^$"), self))
        self.cert_issue_date_input.setObjectName("inputField")
        self.cert_issue_date_input.textChanged.connect(lambda: self.format_date_input(self.cert_issue_date_input))
        self.cert_issue_date_input.setPlaceholderText("ДД.ММ.РРРР")
        self.cert_issue_date_input.setStyleSheet("letter-spacing: 2px;")
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
        contact_layout = QHBoxLayout()
        self.phone_input = self.create_input_field()
        self.phone_input.setObjectName("inputField")
        self.phone_input.setInputMask("+380#########")
        self.phone_input.setStyleSheet("letter-spacing: 2px;")
        self.phone_input.setPlaceholderText("+380123456789")
        self.citizenship_input = self.create_input_field()
        self.citizenship_input.setObjectName("inputField")
        self.citizenship_input.setText("України")
        self.date_birth_input = self.create_input_field(validator=QRegExpValidator(QRegExp(r"^\d{2}\.\d{2}\.\d{4}$|^$"), self))
        self.date_birth_input.setObjectName("inputField")
        self.date_birth_input.setStyleSheet("letter-spacing: 2px;")
        self.date_birth_input.textChanged.connect(lambda: self.format_date_input(self.date_birth_input))
        self.date_birth_input.setPlaceholderText("ДД.ММ.РРРР")
        contact_layout.addWidget(QLabel("Телефон:"))
        contact_layout.addWidget(self.phone_input)
        contact_layout.addWidget(QLabel("Громадянство:"))
        contact_layout.addWidget(self.citizenship_input)
        contact_layout.addWidget(QLabel("Дата народження:"))
        contact_layout.addWidget(self.date_birth_input)
        personal_form_layout.addRow(contact_layout)

        # Паспорт
        passport_layout = QHBoxLayout()
        self.passport_number_input = self.create_input_field( validator=QRegExpValidator(QRegExp(r"^[А-ЯІЇЄҐ]{0,2}\d{6,9}$|^$"), self))
        self.passport_number_input.setObjectName("inputField")
        self.passport_number_input.setPlaceholderText("123456789 або AA123456")
        self.issued_by_input = self.create_input_field()
        self.issued_by_input.setObjectName("inputField")
        self.issued_by_input.setPlaceholderText("Напр., 071 або МВС України")
        self.issue_date_input = self.create_input_field(150, validator=QRegExpValidator(QRegExp(r"^\d{2}\.\d{2}\.\d{4}$|^$"), self))
        self.issue_date_input.setObjectName("inputField")
        self.issue_date_input.textChanged.connect(lambda: self.format_date_input(self.issue_date_input))
        self.issue_date_input.setStyleSheet("letter-spacing: 2px;")
        self.issue_date_input.setPlaceholderText("ДД.ММ.РРРР")
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
        parents_layout = QHBoxLayout()

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
        self.father_phone_input = self.create_input_field()
        self.father_phone_input.setObjectName("inputField")
        self.father_phone_input.setInputMask("+380#########")
        self.father_phone_input.setStyleSheet("letter-spacing: 2px;")
        self.father_phone_input.setPlaceholderText("+380993456789")
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
        self.mother_phone_input = self.create_input_field()
        self.mother_phone_input.setObjectName("inputField")
        self.mother_phone_input.setInputMask("+380#########")
        self.mother_phone_input.setStyleSheet("letter-spacing: 2px;")
        self.mother_phone_input.setPlaceholderText("+380993456789")
        mother_layout.addWidget(self.mother_phone_input)

        parents_layout.addLayout(father_layout)
        parents_layout.addLayout(mother_layout)
        parents_data_group.setLayout(parents_layout)

        # Група 3: Оцінки
        grades_group = QGroupBox("Оцінки")
        grades_group.setObjectName("groupBox")
        grades_form_layout = QHBoxLayout()
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
        other_data_form_layout = QFormLayout()
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
        self.input_button = QPushButton("Ввести нового вступника", self)
        self.input_button.setObjectName("inputButton")
        self.input_button.setEnabled(False)
        self.input_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.input_button.setStyleSheet("background-color: #E0E0E0; color: #adadad;")
        self.input_button.clicked.connect(self.submit_applicant_data)
        layout.addWidget(self.input_button)

        self.edit_button = QPushButton("Редагувати вступника", self)
        self.edit_button.setObjectName("editButton")
        self.edit_button.setEnabled(False)
        self.edit_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.edit_button.setStyleSheet("background-color: #E0E0E0; color: #adadad;")
        self.edit_button.clicked.connect(self.edit_applicant_data)
        layout.addWidget(self.edit_button)

        # Повідомлення
        self.message_label = QLabel(self)
        self.message_label.setObjectName("errorLabel")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.hide()
        layout.insertWidget(0, self.message_label)

        self.success_label = QLabel(self)
        self.success_label.setObjectName("successLabel")
        self.success_label.setAlignment(Qt.AlignCenter)
        self.success_label.hide()
        layout.insertWidget(0, self.success_label)

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

        gender = 'masc'
        if middle_name.endswith(('івна', 'ївна')):
            gender = 'fem'
        elif middle_name.endswith(('ович', 'йович')):
            gender = 'masc'

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
        """Пошук вступника через репозиторій."""
        search_text = self.search_input.text().strip()
        if not search_text:
            show_error(self, "Введіть текст для пошуку!")
            return

        repo = ApplicantRepository()
        try:
            # Очищення для пошуку за свідоцтвом
            cleaned_search = re.sub(r"[ №\u00A0]", "", search_text.upper())
            
            # Пошук за ПІБ або свідоцтвом (денна форма)
            query = """
            SELECT * FROM applicant_personal_data_day 
            WHERE REPLACE(REPLACE(REPLACE(UPPER(cert_number), ' ', ''), '№', ''), ' ', '') LIKE %s
               OR LOWER(last_name) LIKE LOWER(%s)
            """
            applicant = repo.execute_query(query, (f"%{cleaned_search}", f"%{search_text}%"), fetch_all=False)

            if applicant:
                self.populate_fields(applicant)
                self.edit_button.setEnabled(True)
                self.edit_button.setStyleSheet("background-color: #FFA500; color: white;")
                self.cancel_button.setEnabled(True)
                self.cancel_button.setStyleSheet("font-size: 13px; background-color: #FF9999; color: white;")
                self.input_button.setEnabled(False)
                self.input_button.setStyleSheet("background-color: #E0E0E0; color: #adadad;")
                show_success(self, "Вступника знайдено!")
            else:
                show_error(self, "Вступника не знайдено.")
                self.clear_all_fields()
        except Exception as e:
            log_error(f"Помилка при пошуку вступника {search_text}", e)
            show_error(self, f"Помилка: {str(e)}")



    def edit_applicant_data(self):
        """Оновлення даних вступника через репозиторій."""
        data = [
            self.first_name_input.text().strip(), self.last_name_input.text().strip(),
            self.middle_name_input.text().strip(), self.pip_input.text().strip(),
            self.phone_input.text().strip(), self.citizenship_input.text().strip(),
            self.cert_number_input.text().strip(), self.passport_number_input.text().strip(),
            self.issued_by_input.text().strip(), self.issue_date_input.text().strip(),
            self.id_code_input.text().strip(), self.address_input.text().strip(),
            self.father_first_name_input.text().strip(), self.father_last_name_input.text().strip(),
            self.father_middle_name_input.text().strip(), self.father_job_input.text().strip(),
            self.father_phone_input.text().strip(), self.mother_first_name_input.text().strip(),
            self.mother_last_name_input.text().strip(), self.mother_middle_name_input.text().strip(),
            self.mother_phone_input.text().strip(), self.mother_job_input.text().strip(),
            self.hostel_need_input.currentText().strip(), self.gender_input.currentText().strip(),
            self.algebra_input.text().strip(), self.geometry_input.text().strip(),
            self.ukr_language_input.text().strip(), self.ukr_literature_input.text().strip(),
            self.school_name_input.text().strip(), self.cert_issue_date_input.text().strip(),
            self.date_birth_input.text().strip()
        ]

        if not data[0] or not data[1] or not data[6]:
            show_error(self, "Заповніть обов'язкові поля!")
            return

        repo = ApplicantRepository()
        try:
            if repo.update_applicant_day(data):
                show_success(self, "Дані оновлено!")
                log_info(f"Оновлено дані вступника {data[1]} {data[0]} ({data[6]})")
                self.clear_all_fields()
                self.search_input.clear()
            else:
                show_error(self, "Не вдалося оновити дані.")
        except Exception as e:
            log_error(f"Помилка оновлення вступника {data[6]}", e)
            show_error(self, f"Помилка: {str(e)}")

    def clear_all_fields(self):
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
        self.input_button.setStyleSheet("background-color: #E0E0E0; color: #adadad;")
        self.edit_button.setEnabled(False)
        self.edit_button.setStyleSheet("background-color: #E0E0E0; color: #adadad;")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setStyleSheet("background-color: #E0E0E0; color: #adadad;")

    def cancel_search(self):
        """Скасовує пошук і очищає форму."""
        self.clear_all_fields()
        self.search_input.clear()

    def populate_fields(self, applicant):
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
        is_fields_filled = (
            self.last_name_input.text().strip() and
            self.first_name_input.text().strip() and
            self.pip_input.text().strip() and
            self.cert_number_input.text().strip() and
            len(self.cert_number_input.text().strip().split("№")[1]) == 8
        )
        if self.edit_button.isEnabled():
            # Режим редагування після пошуку
            self.input_button.setEnabled(False)
            self.input_button.setStyleSheet("background-color: #E0E0E0; color: #adadad;")
            self.edit_button.setEnabled(True)
            self.edit_button.setStyleSheet("background-color: #FFA500; color: white;")
            self.cancel_button.setEnabled(True)
            self.cancel_button.setStyleSheet(" background-color: #FF9999; color: white;")
        else:
            # Режим введення нового вступника
            if is_fields_filled:
                self.input_button.setEnabled(True)
                self.input_button.setStyleSheet("background-color: #32CD32; color: white;")
            else:
                self.input_button.setEnabled(False)
                self.input_button.setStyleSheet("background-color: #E0E0E0; color: #adadad;")
                self.edit_button.setEnabled(False)
                self.edit_button.setStyleSheet("background-color: #E0E0E0; color: #adadad;")
                self.cancel_button.setEnabled(False)
                self.cancel_button.setStyleSheet("background-color: #E0E0E0; color: #adadad;")

    def submit_applicant_data(self):
        """Збирає дані з форми та зберігає нового вступника через репозиторій."""
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        middle_name = self.middle_name_input.text().strip()
        pip = self.pip_input.text().strip()
        phone = self.phone_input.text().strip()
        citizenship = self.citizenship_input.text().strip()
        date_birth = self.date_birth_input.text().strip()
        cert_number = self.cert_number_input.text().strip()
        cert_issue_date = self.cert_issue_date_input.text().strip()
        passport_number = self.passport_number_input.text().strip()
        issued_by = self.issued_by_input.text().strip()
        issue_date = self.issue_date_input.text().strip()
        id_code = self.id_code_input.text().strip()
        address = self.address_input.text().strip()
        father_first_name = self.father_first_name_input.text().strip()
        father_last_name = self.father_last_name_input.text().strip()
        father_middle_name = self.father_middle_name_input.text().strip()
        father_job = self.father_job_input.text().strip()
        father_phone = self.father_phone_input.text().strip()
        mother_first_name = self.mother_first_name_input.text().strip()
        mother_last_name = self.mother_last_name_input.text().strip()
        mother_middle_name = self.mother_middle_name_input.text().strip()
        mother_phone = self.mother_phone_input.text().strip()
        mother_job = self.mother_job_input.text().strip()
        algebra = self.algebra_input.text().strip()
        geometry = self.geometry_input.text().strip()
        ukr_language = self.ukr_language_input.text().strip()
        ukr_literature = self.ukr_literature_input.text().strip()
        hostel_need = self.hostel_need_input.currentText().strip()
        gender = self.gender_input.currentText().strip()
        school_name = self.school_name_input.text().strip()

        # Валідація обов'язкових полів
        missing = []
        if not first_name: missing.append("Ім'я")
        if not last_name: missing.append("Прізвище")
        if not pip: missing.append("ПІП (родовий)")
        if not cert_number: missing.append("Номер свідоцтва")
        
        if missing:
            show_error(self, f"Заповніть обов’язкові поля: {', '.join(missing)}")
            return

        # Валідація дат
        for date_val, label in [(date_birth, "нар."), (cert_issue_date, "свід."), (issue_date, "пасп.")]:
            if date_val and not self.validate_date(date_val):
                show_error(self, f"Некоректна дата {label}!")
                return

        repo = ApplicantRepository()
        
        try:
            # Перевірка на дублікати
            if repo.is_applicant_exists(first_name, last_name, middle_name, cert_number, passport_number, id_code):
                show_error(self, "Вступник із такими даними вже існує!")
                return

            # Підготовка даних для вставки
            data = [
                first_name, last_name, middle_name, pip, phone, citizenship, cert_number,
                passport_number, issued_by, issue_date, id_code, address, father_first_name,
                father_last_name, father_middle_name, father_job, father_phone, mother_first_name,
                mother_last_name, mother_middle_name, mother_phone, mother_job, hostel_need,
                gender, algebra, geometry, ukr_language, ukr_literature, school_name,
                cert_issue_date, date_birth
            ]
            
            if repo.add_applicant_day(data):
                show_success(self, "Дані збережено успішно!")
                log_info(f"Додано нового вступника: {last_name} {first_name} ({cert_number})")
                self.clear_all_fields()
            else:
                show_error(self, "Не вдалося зберегти дані в базі.")

        except Exception as e:
            log_error("Критична помилка при збереженні вступника", e)
            show_error(self, f"Помилка при збереженні: {str(e)}")

    def show_error_message(self, message):
        """Збережено для сумісності з внутрішніми викликами, але використовує уніфіковані вікна."""
        show_error(self, message)

    def show_success_message(self, message):
        """Збережено для сумісності з внутрішніми викликами, але використовує уніфіковані вікна."""
        show_success(self, message)

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