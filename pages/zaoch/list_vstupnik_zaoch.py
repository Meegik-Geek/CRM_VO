from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox,
    QScrollArea, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt5.QtGui import QCursor, QFontMetrics
from PyQt5.QtCore import Qt, QTimer
from db.repository import SpecialtyRepository, ApplicantRepository
from utils.logger import log_error, log_info
from utils.notifications import show_error, show_success

class ListVstupnikZaoch(QWidget):
    def __init__(self):
        super().__init__()

        # Основний лейаут для форми
        layout = QVBoxLayout(self); layout.setContentsMargins(10, 10, 10, 10); layout.setSpacing(10)

        # Заголовок форми
        label = QLabel("Форма для пошуку вступників за спеціальністю (заочної форми)", self)
        layout.addWidget(label)

        # Горизонтальний лейаут для вибору спеціальності та кнопки пошуку
        search_layout = QHBoxLayout(); search_layout.setContentsMargins(0, 0, 0, 0); search_layout.setSpacing(10)

        # Випадаючий список для вибору спеціальності
        self.specialty_combo = QComboBox(self)
        self.specialty_combo.setObjectName("comboBox")
        
        self.specialty_combo.setCurrentIndex(0)
        search_layout.addWidget(self.specialty_combo)
        
        # Заповнюємо список спеціальностей з бази даних
        self.populate_specialty_combo()

        # Кнопка пошуку
        self.search_button = QPushButton("Шукати", self)
        self.search_button.setObjectName("searchButton")
        
        self.search_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.search_button.clicked.connect(self.search_vstupnik)
        search_layout.addWidget(self.search_button)

        # Додаємо горизонтальний лейаут до основного лейауту
        layout.addLayout(search_layout)

        # Прокручувана область для відображення таблиці з результатами
        self.scroll_area = QScrollArea(self); self.scroll_area.setFrameShape(QScrollArea.NoFrame); self.scroll_area.setViewportMargins(0, 0, 0, 0); self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setWidgetResizable(True)
        self.table = QTableWidget()  # Таблиця для відображення результатів
        self.table.setObjectName("tableWidget")
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        header.setMinimumSectionSize(120)

        self.scroll_area.setWidget(self.table)
        layout.addWidget(self.scroll_area)

        # Мітка для індикатора завантаження
        self.loading_label = QLabel("Завантаження даних...", self)
        self.loading_label.setObjectName("loadingLabel")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.hide()  # Ховаємо індикатор за замовчуванням
        layout.addWidget(self.loading_label)

        # Налаштування основного лейаута
        self.setLayout(layout)

    def show_loader(self):
        """Показати індикатор завантаження."""
        self.loading_label.show()
        self.table.setEnabled(False)  # Забороняємо взаємодію з таблицею

    def hide_loader(self):
        """Сховати індикатор завантаження."""
        self.loading_label.hide()
        self.table.setEnabled(True)  # Дозволяємо взаємодію з таблицею

    def populate_specialty_combo(self):
        """Завантаження спеціальностей (заочна)."""
        repo = SpecialtyRepository()
        try:
            specialties = repo.get_specialties(form_type='zaoch')
            self.specialty_combo.clear()
            for s in specialties:
                # Використовуємо назву прямо з бази, вона вже містить код
                display_text = s[1]
                self.specialty_combo.addItem(display_text, s[1]) 
        except Exception as e:
            log_error("Помилка завантаження спеціальностей для списку (заочна)", e)

    def search_vstupnik(self):
        """Пошук вступників через репозиторій."""
        # Отримуємо назву спеціальності з даних елемента (currentData)
        selected_specialty = self.specialty_combo.currentData()
        
        if not selected_specialty:
            # Fallback
            text = self.specialty_combo.currentText().strip()
            if text:
                parts = text.split(" ", 1)
                selected_specialty = parts[1] if len(parts) > 1 else text
            else:
                show_error(self, "Оберіть спеціальність!")
                return

        self.show_loader()
        repo = ApplicantRepository()
        try:
            results = repo.search_applicants_by_specialty(selected_specialty, form_type='zaoch')

            if results:
                self.populate_table(results)
                show_success(self, f"Знайдено {len(results)} вступників!")
            else:
                self.table.setRowCount(0)
                show_error(self, "Результатів не знайдено.")
        except Exception as e:
            log_error(f"Помилка пошуку вступників для {selected_specialty}", e)
            show_error(self, f"Помилка: {str(e)}")
        finally:
            self.hide_loader()

    def populate_table(self, results):
        """Заповнює таблицю даними про вступників."""
        self.table.clear()
        self.table.setColumnCount(11)
        self.table.setRowCount(len(results))
        self.table.setHorizontalHeaderLabels([
            "Прізвище", "Ім'я", "По-батькові", "Номер справи", "Дата подачі", 
            "Телефон", "Паспорт", "Свідоцтво", "Код пільги", "Назва пільги", "Документи пільги"
        ])
        
        # Заповнення рядків таблиці
        for row_idx, row_data in enumerate(results):
            for col_idx, item in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(item)))
        
        # Налаштування ширини стовпців
        self.adjust_column_widths()

    def adjust_column_widths(self):
        """Налаштування ширини стовпців на основі заголовків і вмісту."""
        font = self.table.font()
        metrics = QFontMetrics(font)
        header = self.table.horizontalHeader()

        for col in range(self.table.columnCount()):
            # Обчислюємо ширину заголовка
            header_text = self.table.horizontalHeaderItem(col).text()
            header_width = metrics.boundingRect(header_text).width() + 20  # Додаємо відступи

            # Обчислюємо максимальну ширину вмісту
            max_content_width = header_width  # Початкова ширина = ширина заголовка
            for row in range(self.table.rowCount()):
                item = self.table.item(row, col)
                if item:
                    content_width = metrics.boundingRect(item.text()).width() + 20  # Додаємо відступи
                    max_content_width = max(max_content_width, content_width)

            # Встановлюємо ширину стовпця
            self.table.setColumnWidth(col, max_content_width)