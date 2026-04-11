from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, 
    QFormLayout, QGroupBox, QScrollArea, QHBoxLayout, QDialog, QComboBox
)
from PyQt5.QtGui import QCursor, QIntValidator
from PyQt5.QtCore import Qt
from db.connect_db import setup_database, close_database
from utils.notifications import show_success, show_error

class PrintDialog(QDialog):
    """Діалогове вікно для введення параметрів друку."""
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

                label = QLabel(field_label)
                label.setObjectName("dialogLabel")
                layout.addWidget(label)

                if field_type == 'text':
                    self.fields[field_name] = QLineEdit(self)
                    self.fields[field_name].setObjectName("inputField")
                    self.fields[field_name].setPlaceholderText(field.get('placeholder', ''))
                    self.fields[field_name].textChanged.connect(self.validate_fields)
                    layout.addWidget(self.fields[field_name])

                elif field_type == 'number':
                    self.fields[field_name] = QLineEdit(self)
                    self.fields[field_name].setObjectName("inputField")
                    self.fields[field_name].setValidator(QIntValidator(1, 9999, self))
                    self.fields[field_name].textChanged.connect(self.validate_fields)
                    layout.addWidget(self.fields[field_name])

                elif field_type == 'combo':
                    self.fields[field_name] = QComboBox(self)
                    self.fields[field_name].setObjectName("comboBox")
                    self.fields[field_name].currentIndexChanged.connect(self.validate_fields)
                    layout.addWidget(self.fields[field_name])
                    if field_name == 'Назва спеціальності':
                        source_table = field.get('source_table', 'specialities_day')
                        self.load_specialnosti(source_table)
                    if field_name == 'Форма навчання':
                        self.fields[field_name].addItems(["денна", "денна (скорочена)", "заочна"])

        buttons_layout = QHBoxLayout()
        buttons_layout.setObjectName("buttonLayout")
        self.save_btn = QPushButton("Зберегти", self)
        self.save_btn.setObjectName("printButton") # Зелений стиль
        self.save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_btn.setFixedSize(110, 40)
        self.save_btn.clicked.connect(lambda: self.print_handler(self))
        buttons_layout.addWidget(self.save_btn)
        layout.addLayout(buttons_layout)
        self.validate_fields()

    def load_specialnosti(self, table_name='specialities_day'):
        if not self.conn: return
        try:
            cursor = self.conn.cursor()
            query = f"SELECT name_specialnosti FROM public.{table_name}"
            cursor.execute(query)
            specialnosti = cursor.fetchall()
            for (name,) in specialnosti:
                self.fields['Назва спеціальності'].addItem(name)
        except Exception as e:
            print(f"Помилка завантаження спеціальностей: {e}")

    def get_field_values(self):
        return {name: field.currentText() if isinstance(field, QComboBox) else field.text()
                for name, field in self.fields.items()}

    def validate_fields(self):
        if not hasattr(self, 'save_btn'): return
        all_filled = True
        for name, field in self.fields.items():
            if isinstance(field, QComboBox):
                if field.currentIndex() == -1 or not field.currentText().strip():
                    all_filled = False
                    break
            else:
                # Якщо в назві поля є "необов'язково", не блокуємо кнопку при його порожнечі
                field_label = ""
                parent_layout = self.layout()
                for i in range(parent_layout.count()):
                    item = parent_layout.itemAt(i)
                    if item.widget() == field:
                        prev_item = parent_layout.itemAt(i-1)
                        if prev_item and prev_item.widget() and isinstance(prev_item.widget(), QLabel):
                            field_label = prev_item.widget().text()
                        break
                
                if "необов'язково" not in field_label.lower():
                    if not field.text().strip():
                        all_filled = False
                        break
        self.save_btn.setEnabled(all_filled)

    def closeEvent(self, event):
        try:
            if self.conn: close_database(self.conn)
        except: pass
        super().closeEvent(event)

class BaseReportPage(QWidget):
    """Базовий клас для сторінок друку з дворівневою навігацією."""
    def __init__(self, title_text, group_title):
        super().__init__()
        self.title_text = title_text
        self.group_title = group_title
        self.action_buttons = {}
        self.init_base_ui()

    def init_base_ui(self):
        layout = QVBoxLayout(self)
        title_label = QLabel(self.title_text, self)
        title_label.setObjectName("titleLabel")
        layout.addWidget(title_label)
        
        # Контейнер для синіх кнопок (Main category)
        self.nav_layout = QVBoxLayout()
        layout.addLayout(self.nav_layout)

        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("scrollArea")
        scroll_area.setWidgetResizable(True)
        container = QWidget()
        form_layout = QFormLayout(container)

        self.document_group = QGroupBox(self.group_title)
        self.document_group.setObjectName("groupBox")
        
        # Використовуємо центральний контейнер для вертикального центрування
        self.button_layout = QVBoxLayout(self.document_group)
        self.button_layout.setSpacing(20)
        self.button_layout.addStretch(1) # Пружина зверху
        
        # Створюємо спеціальний індекс для вставки кнопок (після першої пружини)
        # Але насправді ми просто будемо вставляти перед останньою пружиною, яку додамо зараз
        self.button_layout.addStretch(1) # Пружина знизу
        
        form_layout.addRow(self.document_group)
        scroll_area.setWidget(container)
        layout.addWidget(scroll_area)
        self.setLayout(layout)

    def add_navigation_buttons(self, buttons_config):
        """Створює сітку синіх кнопок навігації."""
        buttons_per_row = 3
        current_row_layout = QHBoxLayout()
        
        for i, (text, key) in enumerate(buttons_config, start=1):
            btn = QPushButton(text, self)
            btn.setObjectName("mainButton") # Синя кнопка
            btn.setFixedHeight(40)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(lambda checked, k=key: self.show_action_button(k))
            current_row_layout.addWidget(btn)
            
            if i % buttons_per_row == 0:
                self.nav_layout.addLayout(current_row_layout)
                current_row_layout = QHBoxLayout()
        
        if current_row_layout.count() > 0:
            self.nav_layout.addLayout(current_row_layout)

    def add_action_button(self, key, text, handler):
        """Створює приховану зелену кнопку друку."""
        btn = QPushButton(text, self)
        btn.setObjectName("printButton") # Зелена кнопка
        btn.setFixedHeight(50)
        btn.setFixedWidth(400)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setVisible(False)
        btn.clicked.connect(handler)
        # Вставляємо кнопку між двома пружинами (індекс 1)
        self.button_layout.insertWidget(1, btn, alignment=Qt.AlignCenter)
        self.action_buttons[key] = btn
        return btn

    def show_action_button(self, key):
        """Показує обрану кнопку друку та приховує інші."""
        for k, btn in self.action_buttons.items():
            btn.setVisible(k == key)

    def show_print_dialog(self, title, handler, fields_config):
        dialog = PrintDialog(self, title, handler, extra_fields=fields_config)
        dialog.exec()
