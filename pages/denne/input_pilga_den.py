from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox,
    QFormLayout, QGroupBox, QScrollArea, QHBoxLayout, QTextEdit, QSizePolicy
)
from PyQt5.QtGui import QCursor,  QRegExpValidator
from PyQt5.QtCore import Qt, QTimer, QRegExp
from db.repository import BenefitRepository, ApplicantRepository
from utils.logger import log_error, log_info
from utils.notifications import show_error, show_success
import re
class InputPilgaDen(QWidget):
    def __init__(self):
        super(InputPilgaDen, self).__init__()

        # Змінні для збереження знайдених пільг та індексу поточної пільги
        self.found_pilgas = []
        self.current_pilga_index = 0
        self.is_editing = False  # Стан, який показує, чи редагується пільга


        layout = QVBoxLayout(self); layout.setContentsMargins(10, 10, 10, 10); layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop)
        # Основний лейаут для форми
        label = QLabel("Форма для введення пільги вступника", self)
        layout.addWidget(label)

        # Search section
        search_layout = QHBoxLayout(); search_layout.setContentsMargins(0, 0, 0, 0); search_layout.setSpacing(10)
        self.search_input = QLineEdit(self)
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Пошук за номером свідоцтва про освіту...")
        self.search_input.setMaxLength(100)
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Шукати", self)
        self.search_button.setObjectName("searchButton")
        self.search_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.search_button.clicked.connect(self.search_pilga)
        search_layout.addWidget(self.search_button)

        self.clear_button = QPushButton("Очистити форму", self)
        self.clear_button.setObjectName("clearButton")
        self.clear_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.clear_button.clicked.connect(self.clear_form)
        search_layout.addWidget(self.clear_button)

        self.cancel_button = QPushButton("Скасувати пошук", self)
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_search)
        search_layout.addWidget(self.cancel_button)

        layout.addLayout(search_layout)

        # Scrollable area
        scroll_area = QScrollArea(self); scroll_area.setFrameShape(QScrollArea.NoFrame); scroll_area.setViewportMargins(0, 0, 0, 0); scroll_area.setContentsMargins(0, 0, 0, 0)
        scroll_area.setWidgetResizable(True)
        container = QWidget(); container.setObjectName("formContainer")
        form_layout = QVBoxLayout(container); form_layout.setContentsMargins(0, 0, 0, 0); form_layout.setSpacing(10)

        # Benefits data group
        pilga_data_group = QGroupBox("Ввід даних пільги вступника")
        pilga_data_group.setObjectName("groupBox")
        pilga_form_layout = QFormLayout(); pilga_form_layout.setLabelAlignment(Qt.AlignLeft); pilga_form_layout.setFormAlignment(Qt.AlignLeft); pilga_form_layout.setContentsMargins(0, 0, 0, 0); pilga_form_layout.setSpacing(10)
        self.cert_number_input = self.create_input_field("Номер свідоцтва про освіту", input_mask="AA №00000000", validator=QRegExpValidator(QRegExp(r"[А-ЯІЇЄҐ№ 0-9]*"), self))
        self.cert_number_input.setObjectName("inputField")
        self.cert_number_input.setStyleSheet("letter-spacing: 2px;")
        
        self.kod_pilgi_input = QComboBox(self)
        self.kod_pilgi_input.setObjectName("comboBox")
        self.load_pilgi_kody()
        self.document_pilgi_input = self.create_input_field("Документи про пільгу", field_type='multiline')
        self.document_pilgi_input.setObjectName("inputField")

        pilga_form_layout.addRow("Номер свідоцтва про освіту:", self.cert_number_input)
        pilga_form_layout.addRow("Код пільги:", self.kod_pilgi_input)
        pilga_form_layout.addRow("Документи про пільгу:", self.document_pilgi_input)

        pilga_data_group.setLayout(pilga_form_layout)
        form_layout.addWidget(pilga_data_group)

        # Navigation buttons
        navigation_layout = QHBoxLayout(); navigation_layout.setContentsMargins(0, 0, 0, 0); navigation_layout.setSpacing(10); navigation_layout.setContentsMargins(0, 0, 0, 0); navigation_layout.setSpacing(20)
        navigation_layout.setContentsMargins(0, 0, 0, 0)
        navigation_layout.setSpacing(40)
        navigation_layout.addStretch(1)

        self.prev_button = QPushButton("Попередня", self)
        self.prev_button.setObjectName("navButton")
        self.prev_button.setAccessibleName("prev")
        self.prev_button.setEnabled(False)
        self.prev_button
        self.prev_button.clicked.connect(self.show_previous_pilga)
        navigation_layout.addWidget(self.prev_button)

        self.delete_button = QPushButton("Видалити пільгу", self)
        self.delete_button.setObjectName("navButton")
        self.delete_button.setAccessibleName("delete")
        self.delete_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.delete_button.setEnabled(False)
        self.delete_button
        self.delete_button.clicked.connect(self.delete_pilga)
        navigation_layout.addWidget(self.delete_button)

        self.next_button = QPushButton("Наступна", self)
        self.next_button.setObjectName("navButton")
        self.next_button.setAccessibleName("next")
        self.next_button.setEnabled(False)
        self.next_button
        self.next_button.clicked.connect(self.show_next_pilga)
        navigation_layout.addWidget(self.next_button)

        navigation_layout.addStretch(1)
        form_layout.addLayout(navigation_layout)

        # Save and update buttons
        button_layout = QHBoxLayout(); button_layout.setContentsMargins(0, 20, 0, 0); button_layout.setSpacing(10)
        self.save_button = QPushButton("Зберегти пільгу", self)
        self.save_button.setObjectName("greenButton")
        self.save_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_pilga)
        button_layout.addWidget(self.save_button)

        self.update_button = QPushButton("Редагувати пільгу", self)
        self.update_button.setObjectName("editButton")
        self.update_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.update_button.setEnabled(False)
        self.update_button.clicked.connect(self.update_pilga)
        button_layout.addWidget(self.update_button)

        form_layout.addLayout(button_layout)

        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)

        self.setLayout(layout)
        
        self.save_button.setEnabled(False)
        self.document_pilgi_input.textChanged.connect(self.check_fields_filled)
        self.cert_number_input.textChanged.connect(self.check_fields_filled)
        self.kod_pilgi_input.currentTextChanged.connect(self.check_fields_filled)

    def search_pilga(self):
        """Шукає пільги за свідоцтвом про освіту через репозиторій."""
        cert_number = self.search_input.text().strip()
        if not cert_number:
            show_error(self, "Будь ласка, введіть номер свідоцтва для пошуку.")
            return

        repo = BenefitRepository()
        try:
            # Чистимо пошуковий текст для нормалізації
            cleaned_search = re.sub(r"[ №\u00A0]", "", cert_number.upper())
            
            # Пошук пільг
            self.found_pilgas = repo.search_benefits_by_cert(cleaned_search)

            if self.found_pilgas:
                self.current_pilga_index = 0
                self.populate_fields(self.found_pilgas[self.current_pilga_index])
                show_success(self, f"Знайдено {len(self.found_pilgas)} пільг!")
                self.is_editing = True
                self.update_button.setEnabled(True)
                self.update_button
                self.save_button.setEnabled(False)
                self.save_button
                self.cancel_button.setEnabled(True)
                self.cancel_button
            else:
                show_error(self, "Пільги не знайдено!")
                self.clear_form()
                self.is_editing = False
                self.update_button.setEnabled(False)
                self.update_button
                self.cancel_button.setEnabled(False)
                self.cancel_button

            self.update_navigation_buttons()
        except Exception as e:
            log_error(f"Помилка при пошуку пільги ({cert_number})", e)
            show_error(self, f"Помилка при пошуку: {str(e)}")
        
        self.check_fields_filled()
   
        

        self.check_fields_filled()
    def populate_fields(self, pilga):
        """Заповнює поля форми даними з бази даних"""
        self.cert_number_input.setText(str(pilga[1]) if pilga[1] else "")
        self.kod_pilgi_input.setCurrentText(str(pilga[2]) if pilga[2] else "")
        self.document_pilgi_input.setText(str(pilga[3]) if pilga[3] else "")

    def update_navigation_buttons(self):
        """Оновлює стан кнопок навігації та видалення залежно від кількості знайдених пільг"""
        has_pilgas = len(self.found_pilgas) > 0
        more_than_one_pilga = len(self.found_pilgas) > 1

        if self.current_pilga_index > 0 and more_than_one_pilga:
            self.prev_button.setEnabled(True)
            self.prev_button
        else:
            self.prev_button.setEnabled(False)
            self.prev_button

        if self.current_pilga_index < len(self.found_pilgas) - 1 and more_than_one_pilga:
            self.next_button.setEnabled(True)
            self.next_button
        else:
            self.next_button.setEnabled(False)
            self.next_button

        if has_pilgas:
            self.delete_button.setEnabled(True)
            self.delete_button
        else:
            self.delete_button.setEnabled(False)
            self.delete_button

    def show_previous_pilga(self):
        """Перемикає на попередню пільгу"""
        if self.current_pilga_index > 0:
            self.current_pilga_index -= 1
            self.populate_fields(self.found_pilgas[self.current_pilga_index])
            self.update_navigation_buttons()

    def show_next_pilga(self):
        """Перемикає на наступну пільгу"""
        if self.current_pilga_index < len(self.found_pilgas) - 1:
            self.current_pilga_index += 1
            self.populate_fields(self.found_pilgas[self.current_pilga_index])
            self.update_navigation_buttons()

    def create_input_field(self, placeholder="", input_mask=None, field_type='text', validator=None):
        """Створює поле вводу з опціональним маскою та типом поля."""
        if field_type == 'multiline':
            field = QTextEdit(self)
            field.setPlaceholderText(placeholder)
              # Set a reasonable height for multiline
        else:
            field = QLineEdit(self)
            field.setPlaceholderText(placeholder)
            
            if input_mask:
                field.setInputMask(input_mask)
            if validator:
                field.setValidator(validator)
        return field
    

    def check_fields_filled(self):
        """Активує кнопку збереження, коли всі обов'язкові поля заповнені"""
        cert_number = self.cert_number_input.text().strip()
        cert_valid = cert_number and len(cert_number.split("№")[-1]) == 8
        is_fields_filled = (
            cert_valid and
            self.kod_pilgi_input.currentText().strip() and
            self.document_pilgi_input.toPlainText().strip()
        )
        if not self.is_editing and is_fields_filled:
            self.save_button.setEnabled(True)
            self.save_button
        else:
            self.save_button.setEnabled(False)
            self.save_button

    def save_pilga(self):
        """Зберігає нову пільгу через репозиторій."""
        cert_number = self.cert_number_input.text().strip()
        kod_pilgi = self.kod_pilgi_input.currentText().strip()
        document_pilgi = self.document_pilgi_input.toPlainText().strip()

        if not cert_number or len(cert_number.split("№")[-1]) != 8:
            show_error(self, "Номер свідоцтва має містити рівно 8 цифр після '№'!")
            return
        if not kod_pilgi:
            show_error(self, "Виберіть код пільги!")
            return
        if not document_pilgi:
            show_error(self, "Введіть документи про пільгу!")
            return

        repo = BenefitRepository()
        app_repo = ApplicantRepository()

        try:
            # Перевірка існування абітурієнта
            # Примітка: search_benefits_by_cert може бути використаний для перевірки, 
            # але краще мати метод в ApplicantRepository для пошуку за cert_number
            # Поки що використаємо пряму перевірку через execute_query або додамо метод
            if not app_repo.execute_query("SELECT 1 FROM applicant_personal_data_day WHERE cert_number = %s", (cert_number,), fetch_all=False):
                show_error(self, f"Абітурієнта з свідоцтвом {cert_number} не знайдено!")
                return

            if repo.add_benefit(cert_number, kod_pilgi, document_pilgi):
                show_success(self, "Пільгу успішно додано!")
                log_info(f"Додано пільгу ({kod_pilgi}) для {cert_number}")
                self.clear_form()
            else:
                show_error(self, "Не вдалося зберегти пільгу в базі.")

        except Exception as e:
            log_error(f"Критична помилка при збереженні пільги ({cert_number})", e)
            show_error(self, f"Помилка: {str(e)}")

    def update_pilga(self):
        """Оновлює дані пільги через репозиторій."""
        cert_number = self.cert_number_input.text().strip()
        kod_pilgi = self.kod_pilgi_input.currentText().strip()
        document_pilgi = self.document_pilgi_input.toPlainText().strip()

        if not self.is_editing:
            show_error(self, "Спершу виберіть пільгу для редагування!")
            return

        repo = BenefitRepository()
        try:
            if repo.update_benefit(cert_number, kod_pilgi, document_pilgi):
                show_success(self, "Пільгу успішно оновлено!")
                log_info(f"Оновлено пільгу ({kod_pilgi}) для {cert_number}")
                self.clear_form()
                self.search_input.clear()
                self.found_pilgas = []
                self.update_navigation_buttons()
                self.update_button.setEnabled(False)
                self.is_editing = False
            else:
                show_error(self, "Не вдалося оновити пільгу.")
        except Exception as e:
            log_error(f"Помилка при оновленні пільги ({cert_number})", e)
            show_error(self, f"Помилка: {str(e)}")

    def delete_pilga(self):
        """Видаляє пільгу через репозиторій."""
        cert_number = self.cert_number_input.text().strip()
        kod_pilgi = self.kod_pilgi_input.currentText().strip()

        repo = BenefitRepository()
        try:
            if repo.delete_benefit(cert_number, kod_pilgi):
                show_success(self, "Пільгу успішно видалено!")
                log_info(f"Видалено пільгу ({kod_pilgi}) для {cert_number}")
                
                self.found_pilgas.pop(self.current_pilga_index)
                if self.found_pilgas:
                    self.current_pilga_index = min(self.current_pilga_index, len(self.found_pilgas) - 1)
                    self.populate_fields(self.found_pilgas[self.current_pilga_index])
                else:
                    self.clear_form()
                self.update_navigation_buttons()
            else:
                show_error(self, "Не вдалося видалити пільгу.")
        except Exception as e:
            log_error(f"Помилка при видаленні пільги ({cert_number})", e)
            show_error(self, f"Помилка: {str(e)}")

    def load_pilgi_kody(self):
        """Завантажує коди пільг через репозиторій."""
        self.kod_pilgi_input.clear()
        repo = BenefitRepository()
        try:
            kod_pilgi_list = repo.get_all_benefit_types()
            if kod_pilgi_list:
                for kod_pilgi in kod_pilgi_list:
                    self.kod_pilgi_input.addItem(str(kod_pilgi[0]))
        except Exception as e:
            log_error("Помилка завантаження кодів пільг", e)
            show_error(self, "Не вдалося завантажити список пільг.")

    def clear_form(self):
        """Очищає всі поля форми, скидає стан пільг і кнопки"""
        self.cert_number_input.clear()
        self.kod_pilgi_input.setCurrentIndex(0)
        self.document_pilgi_input.clear()
        self.search_input.clear()
        self.found_pilgas = []
        self.current_pilga_index = 0
        self.is_editing = False
        self.save_button.setEnabled(False)
        self.save_button
        self.update_button.setEnabled(False)
        self.update_button
        self.cancel_button.setEnabled(False)
        self.cancel_button
        self.update_navigation_buttons()

    def cancel_search(self):
        """Скасовує пошук і очищає форму"""
        self.clear_form()

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