from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox,
    QFormLayout, QGroupBox, QScrollArea, QHBoxLayout, QCheckBox
)
from PyQt5.QtGui import QCursor, QRegExpValidator
from PyQt5.QtCore import Qt, QTimer, QDate, QRegExp
from datetime import datetime
from db.repository import CaseRepository, SecretaryRepository, SpecialtyRepository, ApplicantRepository
from utils.logger import log_error, log_info
from utils.notifications import show_error, show_success
import re

class InputSpravaDen(QWidget):
    def __init__(self):
        super(InputSpravaDen, self).__init__()

        # Основний лейаут
        layout = QVBoxLayout(self); layout.setContentsMargins(10, 10, 10, 10); layout.setSpacing(10)

        # Заголовок
        label = QLabel("Форма для введення особової справи вступника", self)
        layout.addWidget(label)

        # Пошук
        search_layout = QHBoxLayout(); search_layout.setContentsMargins(0, 0, 0, 0); search_layout.setSpacing(10)
        self.search_input = QLineEdit(self)
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Пошук за номером справи або свідоцтву освіти...")
        self.search_input.setMaxLength(100)
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Шукати", self)
        self.search_button.setObjectName("searchButton")
        self.search_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.search_button.clicked.connect(self.search_sprava)
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
        form_layout = QVBoxLayout(container); form_layout.setContentsMargins(0, 0, 0, 0); form_layout.setSpacing(10)

        # Група: Ввід даних особової справи
        sprava_data_group = QGroupBox("Ввід даних особової справи")
        sprava_data_group.setObjectName("groupBox")
        sprava_form_layout = QFormLayout(); sprava_form_layout.setLabelAlignment(Qt.AlignLeft); sprava_form_layout.setFormAlignment(Qt.AlignLeft); sprava_form_layout.setContentsMargins(0, 0, 0, 0); sprava_form_layout.setSpacing(10)

        # Поля для вводу даних
        self.number_sprava_input = self.create_input_field("Номер справи")
        self.number_sprava_input.setObjectName("inputField")
        sprava_form_layout.addRow("Номер справи <span style='color: red;'>*</span>:", self.number_sprava_input)

        self.kod_galuzi_input = QComboBox(self)
        self.kod_galuzi_input.setObjectName("comboBox")
        self.kod_galuzi_input.setEnabled(False)  # Вимикаємо редагування користувачем
        sprava_form_layout.addRow("Код галузі:", self.kod_galuzi_input)

        self.name_specialnosti_input = QComboBox(self)
        self.name_specialnosti_input.setObjectName("comboBox")
        spec_repo = SpecialtyRepository()
        try:
            # Галузі
            fields = spec_repo.execute_query("SELECT kod_galuzi FROM knowledge_field")
            if fields:
                self.kod_galuzi_input.clear()
                for f in fields:
                    self.kod_galuzi_input.addItem(f[0])
                    
            # Спеціальності
            specialties = spec_repo.get_specialties_day()
            if specialties:
                for spec in specialties:
                    self.name_specialnosti_input.addItem(spec[1])
        except Exception as e:
            log_error("Помилка завантаження спеціальностей або галузей", e)
        
        self.name_specialnosti_input.currentIndexChanged.connect(self.update_kod_galuzi)
        sprava_form_layout.addRow("Назва спеціальності:", self.name_specialnosti_input)

        self.date_sprava_input = self.create_input_field("Дата створення справи", validator=QRegExpValidator(QRegExp(r"^\d{2}\.\d{2}\.\d{4}$|^$"), self))
        self.date_sprava_input.setObjectName("inputField")
        self.date_sprava_input.setStyleSheet("letter-spacing: 2px;")
        self.date_sprava_input.textChanged.connect(lambda: self.format_date_input(self.date_sprava_input))
        self.date_sprava_input.setText(QDate.currentDate().toString("dd.MM.yyyy"))
        sprava_form_layout.addRow("Дата справи <span style='color: red;'>*</span>:", self.date_sprava_input)

        self.name_secretar_input = QComboBox(self)
        self.name_secretar_input.setObjectName("comboBox")
        sec_repo = SecretaryRepository()
        try:
            secretaries = sec_repo.get_secretaries_day()
            if secretaries:
                for sec in secretaries:
                    self.name_secretar_input.addItem(sec[0])
        except Exception as e:
            log_error("Помилка завантаження секретарів", e)
        sprava_form_layout.addRow("Прізвище, ім'я секретаря:", self.name_secretar_input)

        self.finanse_input = QComboBox(self)
        self.finanse_input.setObjectName("comboBox")
        self.finanse_input.addItems(["Бюджет", "Контракт"])
        sprava_form_layout.addRow("Фінансування:", self.finanse_input)

        self.cert_number_input = self.create_input_field(validator=QRegExpValidator(QRegExp(r"[А-ЯІЇЄҐ№ 0-9]*"), self))
        self.cert_number_input.setObjectName("inputField")
        self.cert_number_input.setInputMask("AA №00000000")
        self.cert_number_input.setStyleSheet("letter-spacing: 2px;")
        self.cert_number_input.setPlaceholderText("АА №12345678")
        sprava_form_layout.addRow("Номер свідоцтва про освіту <span style='color: red;'>*</span>:", self.cert_number_input)
        
        self.short_form_checkbox = QCheckBox("Скорочена форма навчання", self)
        self.short_form_checkbox.setObjectName("shortFormCheckbox")
        self.short_form_checkbox.stateChanged.connect(self.toggle_nmt_checkbox)
        sprava_form_layout.addRow("", self.short_form_checkbox)

        self.nmt_checkbox = QCheckBox("Наявність НМТ", self)
        self.nmt_checkbox.setObjectName("nmtCheckbox")
        self.nmt_checkbox.hide()
        sprava_form_layout.addRow("", self.nmt_checkbox)
        sprava_data_group.setLayout(sprava_form_layout)
        form_layout.addWidget(sprava_data_group)

        # Кнопки
        self.save_button = QPushButton("Зберегти особову справу", self)
        self.save_button.setObjectName("greenButton")
        self.save_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_sprava)

        self.update_button = QPushButton("Редагувати справу", self)
        self.update_button.setObjectName("editButton")
        self.update_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.update_button.setEnabled(False)
        self.update_button.clicked.connect(self.update_sprava)
        
        button_layout = QHBoxLayout(); button_layout.setContentsMargins(0, 20, 0, 0); button_layout.setSpacing(10)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.update_button)
        form_layout.addLayout(button_layout)
        

        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)

        self.setLayout(layout)

        # Перевірка обов’язкових полів
        self.number_sprava_input.textChanged.connect(self.check_fields_filled)
        self.cert_number_input.textChanged.connect(self.check_fields_filled)
        self.date_sprava_input.textChanged.connect(self.check_fields_filled)

    def create_input_field(self, placeholder="", input_mask=None, validator=None):
        field = QLineEdit(self)
        field.setPlaceholderText(placeholder)
        if input_mask:
            field.setInputMask(input_mask)
        if validator:
            field.setValidator(validator)
        return field

    def format_date_input(self, input_field):
        text = input_field.text().replace(".", "")
        cursor_pos = input_field.cursorPosition()
        new_text = ""
        for i, char in enumerate(text):
            if not char.isdigit(): continue
            new_text += char
            if i == 1 or i == 3: new_text += "."
        if len(new_text) > 10: new_text = new_text[:10]
        input_field.blockSignals(True)
        input_field.setText(new_text)
        input_field.setCursorPosition(min(cursor_pos + (new_text.count(".") - text.count(".")), len(new_text)))
        input_field.blockSignals(False)

    def check_fields_filled(self):
        cert_number = self.cert_number_input.text().strip()
        cert_valid = cert_number and len(cert_number.split("№")[-1]) == 8
        is_fields_filled = (
            self.number_sprava_input.text().strip() and
            cert_valid and
            self.date_sprava_input.text().strip() and
            self.validate_date(self.date_sprava_input.text())
        )
        if is_fields_filled and not self.update_button.isEnabled():
            self.save_button.setEnabled(True)
            self.save_button
        else:
            self.save_button.setEnabled(False)
            self.save_button

    def validate_date(self, date_str):
        try:
            datetime.strptime(date_str, "%d.%m.%Y")
            return True
        except ValueError:
            return False

    def search_sprava(self):
        search_text = self.search_input.text().strip()
        if not search_text:
            show_error(self, "Будь ласка, введіть дані для пошуку.")
            return

        repo = CaseRepository()
        try:
            sprava = repo.search_case_by_number_or_cert(search_text, is_short_form=False)
            is_short = False
            if not sprava:
                sprava = repo.search_case_by_number_or_cert(search_text, is_short_form=True)
                is_short = True

            if sprava:
                self.short_form_checkbox.setChecked(is_short)
                self.populate_fields(sprava)
                self.update_button.setEnabled(True)
                self.update_button
                self.cancel_button.setEnabled(True)
                self.cancel_button
                self.save_button.setEnabled(False)
                self.save_button
                show_success(self, f"Справу {search_text} знайдено!")
            else:
                show_error(self, "Справу не знайдено!")
                self.clear_all_fields()
        except Exception as e:
            log_error(f"Помилка при пошуку справи {search_text}", e)
            show_error(self, f"Помилка: {str(e)}")

    def save_sprava(self):
        data = {
            "number_sprava": self.number_sprava_input.text().strip(),
            "kod_galuzi": self.kod_galuzi_input.currentText().strip(),
            "name_specialnosti": self.name_specialnosti_input.currentText().strip(),
            "date_sprava": self.date_sprava_input.text().strip(),
            "name_secretar": self.name_secretar_input.currentText().strip(),
            "finanse": self.finanse_input.currentText().strip(),
            "cert_number": self.cert_number_input.text().strip(),
            "zno_nmt_checkbox": "true" if self.short_form_checkbox.isChecked() and self.nmt_checkbox.isChecked() else "false"
        }

        is_short = self.short_form_checkbox.isChecked()
        repo = CaseRepository()
        app_repo = ApplicantRepository()

        try:
            if not app_repo.execute_query("SELECT 1 FROM applicant_personal_data_day WHERE cert_number = %s", (data["cert_number"],), fetch_all=False):
                show_error(self, f"Вступника з свідоцтвом {data['cert_number']} не знайдено!")
                return

            if repo.add_case(data, is_short):
                show_success(self, "Справу успішно додано!")
                log_info(f"Додано справу {data['number_sprava']} для {data['cert_number']}")
                self.clear_all_fields()
            else:
                show_error(self, "Помилка при збереженні (можливо, номер справи вже існує).")
        except Exception as e:
            log_error(f"Критична помилка при збереженні справи {data['number_sprava']}", e)
            show_error(self, f"Помилка: {str(e)}")

    def update_sprava(self):
        data = {
            "number_sprava": self.number_sprava_input.text().strip(),
            "kod_galuzi": self.kod_galuzi_input.currentText().strip(),
            "name_specialnosti": self.name_specialnosti_input.currentText().strip(),
            "date_sprava": self.date_sprava_input.text().strip(),
            "name_secretar": self.name_secretar_input.currentText().strip(),
            "finanse": self.finanse_input.currentText().strip(),
            "cert_number": self.cert_number_input.text().strip(),
            "zno_nmt_checkbox": "true" if self.short_form_checkbox.isChecked() and self.nmt_checkbox.isChecked() else "false"
        }

        repo = CaseRepository()
        try:
            if repo.update_case(data, self.short_form_checkbox.isChecked()):
                show_success(self, "Дані справи оновлено!")
                log_info(f"Оновлено справу {data['number_sprava']}")
                self.clear_all_fields()
            else:
                show_error(self, "Не вдалося оновити справу.")
        except Exception as e:
            log_error(f"Помилка при оновленні справи {data['number_sprava']}", e)
            show_error(self, f"Помилка: {str(e)}")

    def clear_all_fields(self):
        self.number_sprava_input.clear()
        self.kod_galuzi_input.setCurrentIndex(0)
        self.name_specialnosti_input.setCurrentIndex(0)
        self.date_sprava_input.setText(QDate.currentDate().toString("dd.MM.yyyy"))
        self.name_secretar_input.setCurrentIndex(0)
        self.finanse_input.setCurrentIndex(0)
        self.cert_number_input.clear()
        self.search_input.clear()
        self.short_form_checkbox.setChecked(False)
        self.nmt_checkbox.setChecked(False)
        self.nmt_checkbox.hide()
        self.save_button.setEnabled(False)
        self.save_button
        self.update_button.setEnabled(False)
        self.update_button
        self.cancel_button.setEnabled(False)
        self.cancel_button

    def toggle_nmt_checkbox(self):
        if self.short_form_checkbox.isChecked():
            self.nmt_checkbox.show()
        else:
            self.nmt_checkbox.hide()
            self.nmt_checkbox.setChecked(False)

    def populate_fields(self, sprava):
        self.number_sprava_input.setText(sprava[1] or "")
        self.kod_galuzi_input.setCurrentText(sprava[2] or "")
        self.name_specialnosti_input.setCurrentText(sprava[3] or "")
        self.date_sprava_input.setText(sprava[4].strftime('%d.%m.%Y') if sprava[4] else "")
        self.name_secretar_input.setCurrentText(sprava[5] or "")
        self.finanse_input.setCurrentText(sprava[6] or "Бюджет")
        self.cert_number_input.setText(sprava[7] or "")
        if self.short_form_checkbox.isChecked():
            self.nmt_checkbox.setChecked(sprava[8].lower() == "true" if len(sprava) > 8 else False)
        else:
            self.nmt_checkbox.setChecked(False)
            self.nmt_checkbox.hide()

    def cancel_search(self):
        self.clear_all_fields()
        self.search_input.clear()

    def update_kod_galuzi(self):
        selected_specialty = self.name_specialnosti_input.currentText().strip()
        if not selected_specialty:
            self.kod_galuzi_input.setCurrentIndex(-1)
            self.name_secretar_input.setCurrentIndex(-1)
            return
            
        spec_repo = SpecialtyRepository()
        sec_repo = SecretaryRepository()
        
        try:
            # Оновлюємо код галузі
            kod = spec_repo.get_kod_galuzi_by_specialty(selected_specialty, form_type='day')
            if kod:
                self.kod_galuzi_input.setCurrentText(kod)
            else:
                self.kod_galuzi_input.setCurrentIndex(-1)
                
            # Оновлюємо прізвище секретаря
            sec_name = sec_repo.get_secretary_by_specialty(selected_specialty, form_type='day')
            if sec_name:
                self.name_secretar_input.setCurrentText(sec_name)
                
        except Exception as e:
            log_error("Помилка при оновленні пов'язаних полів (галузь/секретар)", e)