from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox,
    QFormLayout, QGroupBox, QScrollArea, QHBoxLayout, QCheckBox
)
from PyQt5.QtGui import QCursor, QRegExpValidator
from PyQt5.QtCore import Qt, QTimer, QDate, QRegExp
from datetime import datetime, date
from db.repository import CaseRepository, SpecialtyRepository, SecretaryRepository, ApplicantRepository
from utils.logger import log_error, log_info
from utils.notifications import show_error, show_success
import re

class InputSpravaZaoch(QWidget):
    def __init__(self):
        super(InputSpravaZaoch, self).__init__()

        # Основний лейаут
        layout = QVBoxLayout(self); layout.setContentsMargins(10, 10, 10, 10); layout.setSpacing(10)

        # Повідомлення більше не потрібні в самому класі, бо використовуються глобальні QMessageBox


        # Заголовок
        label = QLabel("Форма для введення особової справи вступника (заочної форми)", self)
        layout.addWidget(label)

        # Пошук
        search_layout = QHBoxLayout(); search_layout.setContentsMargins(0, 0, 0, 0); search_layout.setSpacing(10)
        self.search_input = QLineEdit(self)
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Пошук за номером справи або свідоцтвом освіти...")
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
        sprava_data_group = QGroupBox("Ввід даних особової справи (заочної форми)")
        sprava_data_group.setObjectName("groupBox")
        sprava_form_layout = QFormLayout(); sprava_form_layout.setLabelAlignment(Qt.AlignLeft); sprava_form_layout.setFormAlignment(Qt.AlignLeft); sprava_form_layout.setContentsMargins(0, 0, 0, 0); sprava_form_layout.setSpacing(10)

        self.number_sprava_input = self.create_input_field("Номер справи")
        self.number_sprava_input.setObjectName("inputField")
        sprava_form_layout.addRow("Номер справи <span style='color: red;'>*</span>:", self.number_sprava_input)

        self.kod_galuzi_input = QComboBox(self)
        self.kod_galuzi_input.setObjectName("comboBox")
        self.kod_galuzi_input.setEnabled(False)  # Вимикаємо редагування користувачем
        # Завантажуємо дані будуть в __init__ або окремому методі
        sprava_form_layout.addRow("Код галузі:", self.kod_galuzi_input)

        self.name_specialnosti_input = QComboBox(self)
        self.name_specialnosti_input.setObjectName("comboBox")
        self.name_specialnosti_input.currentIndexChanged.connect(self.update_kod_galuzi)
        sprava_form_layout.addRow("Назва спеціальності:", self.name_specialnosti_input)
        
        self.load_initial_data()

        self.date_sprava_input = self.create_input_field("Дата створення справи", validator=QRegExpValidator(QRegExp(r"^\d{2}\.\d{2}\.\d{4}$|^$"), self))
        self.date_sprava_input.setObjectName("inputField")
        self.date_sprava_input.setStyleSheet("letter-spacing: 2px;")
        self.date_sprava_input.textChanged.connect(lambda: self.format_date_input(self.date_sprava_input))
        self.date_sprava_input.setText(QDate.currentDate().toString("dd.MM.yyyy"))
        sprava_form_layout.addRow("Дата справи <span style='color: red;'>*</span>:", self.date_sprava_input)

        self.name_secretar_input = QComboBox(self)
        self.name_secretar_input.setObjectName("comboBox")
        sprava_form_layout.addRow("Прізвище, ім'я секретаря:", self.name_secretar_input)
        self.load_secretaries()

        self.finanse_input = QComboBox(self)
        self.finanse_input.setObjectName("comboBox")
        self.finanse_input.addItems(["Бюджет", "Контракт"])
        sprava_form_layout.addRow("Фінансування:", self.finanse_input)

        self.cert_number_input = self.create_input_field(validator=QRegExpValidator(QRegExp(r"[А-ЯІЇЄҐ№ 0-9]*"), self))
        self.cert_number_input.setObjectName("inputField")
        self.cert_number_input.setInputMask("AA №00000000")  # Маска з пробілом перед "№"
        self.cert_number_input.setStyleSheet("letter-spacing: 2px;")
        self.cert_number_input.setPlaceholderText("АА №12345678")
        sprava_form_layout.addRow("Номер свідоцтва про освіту <span style='color: red;'>*</span>:", self.cert_number_input)

        self.zno_nmt_checkbox = QCheckBox("Наявність результатів ЗНО або НМТ")
        self.zno_nmt_checkbox.setObjectName("checkBox")
        self.zno_nmt_checkbox.setFixedHeight(30)
        sprava_form_layout.addRow("", self.zno_nmt_checkbox)

        sprava_data_group.setLayout(sprava_form_layout)
        form_layout.addWidget(sprava_data_group)

        # Кнопки для збереження та редагування
        button_layout = QHBoxLayout(); button_layout.setContentsMargins(0, 20, 0, 0); button_layout.setSpacing(10)
        self.save_button = QPushButton("Зберегти особову справу", self)
        self.save_button.setObjectName("greenButton")
        self.save_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_button.setEnabled(False)
        self.save_button
        self.save_button.clicked.connect(self.save_sprava)
        button_layout.addWidget(self.save_button)

        self.update_button = QPushButton("Редагувати справу", self)
        self.update_button.setObjectName("editButton")
        self.update_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.update_button.setEnabled(False)
        self.update_button
        self.update_button.clicked.connect(self.update_sprava)
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
        """Створює поле вводу з опціональним маскою та валідатором."""
        field = QLineEdit(self)
        field.setPlaceholderText(placeholder)
        field.setFixedHeight(30)
        if input_mask:
            field.setInputMask(input_mask)
        if validator:
            field.setValidator(validator)
        return field

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

    def check_fields_filled(self):
        """Активує кнопку збереження, коли всі обов'язкові поля заповнені."""
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
        """Перевіряє, чи дата є валідною."""
        try:
            datetime.strptime(date_str, "%d.%m.%Y")
            return True
        except ValueError:
            return False

    def load_initial_data(self):
        """Завантажує початкові дані (галузі, спеціальності)."""
        spec_repo = SpecialtyRepository()
        try:
            # Галузі
            fields = spec_repo.execute_query("SELECT kod_galuzi FROM knowledge_field")
            self.kod_galuzi_input.clear()
            for f in fields:
                self.kod_galuzi_input.addItem(f[0])
            
            # Спеціальності (заочна)
            specs = spec_repo.get_specialties(form_type='zaoch')
            self.name_specialnosti_input.clear()
            for s in specs:
                self.name_specialnosti_input.addItem(s[1])
        except Exception as e:
            log_error("Помилка при завантаженні початкових даних справи", e)

    def load_secretaries(self):
        """Завантажує секретарів (заочна)."""
        sec_repo = SecretaryRepository()
        try:
            secs = sec_repo.get_secretaries(form_type='zaoch')
            self.name_secretar_input.clear()
            for s in secs:
                self.name_secretar_input.addItem(s[0])
        except Exception as e:
            log_error("Помилка завантаження секретарів", e)

    def search_sprava(self):
        """Пошук справи через репозиторій."""
        search_text = self.search_input.text().strip()
        if not search_text:
            show_error(self, "Будь ласка, введіть дані для пошуку.")
            return

        repo = CaseRepository()
        try:
            # Чистимо пошуковий текст
            cleaned_search = re.sub(r"[ №\u00A0]", "", search_text.upper())
            
            # Пошук за номером справи або свідоцтвом
            query = """
                SELECT * FROM personal_case_evening 
                WHERE number_sprava = %s OR REPLACE(REPLACE(REPLACE(UPPER(cert_number), ' ', ''), '№', ''), ' ', '') LIKE %s
            """
            sprava = repo.execute_query(query, (search_text, f"%{cleaned_search}"), fetch_all=False)

            if sprava:
                self.populate_fields(sprava)
                self.update_button.setEnabled(True)
                self.update_button
                self.cancel_button.setEnabled(True)
                self.cancel_button
                self.save_button.setEnabled(False)
                self.save_button
                show_success(self, f"Справу знайдено!")
            else:
                show_error(self, "Справу не знайдено!")
                self.clear_all_fields()
        except Exception as e:
            log_error(f"Помилка при пошуку справи {search_text}", e)
            show_error(self, f"Помилка: {str(e)}")

    def populate_fields(self, sprava):
        """Заповнює поля форми даними з бази даних."""
        self.number_sprava_input.setText(str(sprava[1]) if sprava[1] else "")
        self.kod_galuzi_input.setCurrentText(str(sprava[2]) if sprava[2] else "")
        self.name_specialnosti_input.setCurrentText(str(sprava[3]) if sprava[3] else "")
        date_sprava = sprava[4]
        if isinstance(date_sprava, date):
            self.date_sprava_input.setText(date_sprava.strftime("%d.%m.%Y"))
        else:
            self.date_sprava_input.setText(str(date_sprava) if date_sprava else "")
        self.name_secretar_input.setCurrentText(str(sprava[5]) if sprava[5] else "")
        self.finanse_input.setCurrentText(str(sprava[6]) if sprava[6] else "")
        self.cert_number_input.setText(str(sprava[7]) if sprava[7] else "")
        self.zno_nmt_checkbox.setChecked(sprava[8].lower() == 'true')

    def save_sprava(self):
        """Збереження справи через репозиторій."""
        data = {
            "number_sprava": self.number_sprava_input.text().strip(),
            "kod_galuzi": self.kod_galuzi_input.currentText().strip(),
            "name_specialnosti": self.name_specialnosti_input.currentText().strip(),
            "date_sprava": self.date_sprava_input.text().strip(),
            "name_secretar": self.name_secretar_input.currentText().strip(),
            "finanse": self.finanse_input.currentText().strip(),
            "cert_number": self.cert_number_input.text().strip(),
            "zno_nmt_checkbox": 'true' if self.zno_nmt_checkbox.isChecked() else 'false'
        }

        if not data["number_sprava"] or not data["cert_number"]:
            show_error(self, "Заповніть обов'язкові поля!")
            return

        repo = CaseRepository()
        app_repo = ApplicantRepository()
        try:
            # Перевірка вступника
            if not app_repo.execute_query("SELECT 1 FROM applicant_personal_data_evening WHERE cert_number = %s", (data["cert_number"],), fetch_all=False):
                show_error(self, f"Вступника з свідоцтвом {data['cert_number']} не знайдено!")
                return

            if repo.add_case(data, form_type='zaoch'):
                show_success(self, "Справу успішно додано!")
                log_info(f"Додано справу {data['number_sprava']} для {data['cert_number']} (заочна)")
                self.clear_all_fields()
            else:
                show_error(self, "Помилка при збереженні справи.")
        except Exception as e:
            log_error(f"Помилка збереження справи {data['number_sprava']}", e)
            show_error(self, f"Помилка: {str(e)}")

    def update_sprava(self):
        """Оновлення справи через репозиторій."""
        data = {
            "number_sprava": self.number_sprava_input.text().strip(),
            "kod_galuzi": self.kod_galuzi_input.currentText().strip(),
            "name_specialnosti": self.name_specialnosti_input.currentText().strip(),
            "date_sprava": self.date_sprava_input.text().strip(),
            "name_secretar": self.name_secretar_input.currentText().strip(),
            "finanse": self.finanse_input.currentText().strip(),
            "cert_number": self.cert_number_input.text().strip(),
            "zno_nmt_checkbox": 'true' if self.zno_nmt_checkbox.isChecked() else 'false'
        }

        repo = CaseRepository()
        try:
            if repo.update_case(data, form_type='zaoch'):
                show_success(self, "Дані справи оновлено!")
                log_info(f"Оновлено справу {data['number_sprava']} (заочна)")
                self.clear_all_fields()
            else:
                show_error(self, "Не вдалося оновити справу.")
        except Exception as e:
            log_error(f"Помилка оновлення справи {data['number_sprava']}", e)
            show_error(self, f"Помилка: {str(e)}")

    def clear_all_fields(self):
        """Очищає всі поля форми."""
        self.number_sprava_input.clear()
        self.kod_galuzi_input.setCurrentIndex(0)
        self.name_specialnosti_input.setCurrentIndex(0)
        self.date_sprava_input.setText(QDate.currentDate().toString("dd.MM.yyyy"))
        self.name_secretar_input.setCurrentIndex(0)
        self.finanse_input.setCurrentIndex(0)
        self.cert_number_input.clear()
        self.zno_nmt_checkbox.setChecked(False)
        self.search_input.clear()
        self.save_button.setEnabled(False)
        self.save_button
        self.update_button.setEnabled(False)
        self.update_button
        self.cancel_button.setEnabled(False)
        self.cancel_button

    def cancel_search(self):
        """Скасовує пошук і очищає форму."""
        self.clear_all_fields()
        self.search_input.clear()

    def update_kod_galuzi(self):
        """Автоматично підставляє код галузі та секретаря."""
        selected_specialty = self.name_specialnosti_input.currentText().strip()
        if not selected_specialty:
            self.kod_galuzi_input.setCurrentIndex(-1)
            self.name_secretar_input.setCurrentIndex(-1)
            return

        repo = SpecialtyRepository()
        sec_repo = SecretaryRepository()
        try:
            # Оновлюємо код галузі
            res = repo.execute_query("SELECT kod_galuzi FROM specialities_evening WHERE name_specialnosti = %s", (selected_specialty,), fetch_all=False)
            if res:
                self.kod_galuzi_input.setCurrentText(res[0])
            else:
                self.kod_galuzi_input.setCurrentIndex(-1)
                
            # Оновлюємо прізвище секретаря
            sec_name = sec_repo.get_secretary_by_specialty(selected_specialty, form_type='zaoch')
            if sec_name:
                self.name_secretar_input.setCurrentText(sec_name)
        except Exception as e:
            log_error(f"Помилка при оновленні пов'язаних полів для {selected_specialty}", e)

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