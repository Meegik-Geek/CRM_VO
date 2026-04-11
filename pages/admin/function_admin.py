from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QGroupBox,
    QTableWidget, QTableWidgetItem, QScrollArea, QPushButton, QMenu, QAction,
    QHeaderView, QFileDialog, QAbstractItemView, QStyledItemDelegate, QComboBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QCursor, QBrush
import pandas as pd
from db.connect_db import setup_database
from utils.notifications import show_success, show_error
from utils.logger import log_error, log_info

class ComboDelegate(QStyledItemDelegate):
    """Делегат для відображення випадаючого списку в клітинці таблиці."""
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.items)
        return editor

    def setEditorData(self, editor, index):
        value = index.data(Qt.EditRole)
        if value:
            editor.setCurrentText(str(value))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

class BaseTableWidget(QWidget):
    """Універсальний клас для відображення та обробки таблиць."""

    def __init__(self, table_name, headers, sql_queries, columns_name, label_text, default_values=None, pre_insert_callbacks=None, checkbox_columns=None, combo_columns=None, hide_id=True, can_add=True, can_delete=True, cancelled_column=None):
        super(BaseTableWidget, self).__init__()
        self.table_name = table_name
        self.headers = headers
        self.sql_queries = sql_queries
        self.label_text = label_text
        self.columns_name = columns_name
        self.default_values = default_values or {}
        self.pre_insert_callbacks = pre_insert_callbacks or {}
        self.checkbox_columns = checkbox_columns or [] # Список індексів колонок-чекбоксів
        self.combo_columns = combo_columns or {} # Словник {індекс: [варіанти]}
        self.hide_id = hide_id # Чи приховувати першу колонку (ID)
        self.can_add = can_add
        self.can_delete = can_delete
        self.cancelled_column = cancelled_column  # Індекс колонки «Скасована заява»
        # Налаштування підключення
        self.conn = setup_database()
        self.cursor = self.conn.cursor()
        self.page_size = 50
        self.current_offset = 0
        self.is_loading = False

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Налаштування інтерфейсу."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label = QLabel(self.label_text, self)
        label.setObjectName("titleLabel")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("scrollArea")
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Налаштування таблиці
        self.table = QTableWidget(self)
        self.table.setObjectName("tableWidget")
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.setAlternatingRowColors(True)
        self.table.setColumnHidden(0, self.hide_id)  # Ховаємо ID за замовчуванням
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        header.setMinimumSectionSize(120)
        
        scroll_area.setWidget(self.table)
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()

        # Налаштування випадаючих списків
        for col_index, items in self.combo_columns.items():
            self.table.setItemDelegateForColumn(col_index, ComboDelegate(items, self.table))

        self.loading_label = QLabel("Завантаження даних...", self)
        self.loading_label.setObjectName("loadingLabel")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.hide()
        layout.addWidget(self.loading_label)

        # Напис "Результатів не знайдено"
        self.no_results_label = QLabel("Результатів не знайдено", self)
        self.no_results_label.setObjectName("noResultsLabel")
        self.no_results_label.setAlignment(Qt.AlignCenter)
        self.no_results_label.setStyleSheet("color: #888; font-size: 16px; font-weight: bold; margin: 20px;")
        self.no_results_label.hide()
        layout.addWidget(self.no_results_label)

        # Панель для пошуку та експорту
        group_title = "Додати запис / Пошук / Експорт" if self.can_add else "Пошук / Експорт"
        search_group = QGroupBox(group_title)
        search_group.setObjectName("groupBox")
        search_layout = QHBoxLayout(search_group)

        self.add_button = QPushButton("+", self)
        self.add_button.setObjectName("searchButton")
        self.add_button.setStyleSheet("background-color: #4CAF50;")
        self.add_button.clicked.connect(self.add_new_row)
        self.add_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.add_button.setVisible(self.can_add)

        self.search_input = QLineEdit(self)
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Введіть текст для пошуку...")
        self.search_input.textChanged.connect(self.search_table)

        self.export_button = QPushButton("Експорт", self)
        self.export_button.setObjectName("searchButton")
        self.export_button.clicked.connect(self.export_to_excel)
        self.export_button.setCursor(QCursor(Qt.PointingHandCursor))
        search_layout.addWidget(self.add_button)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.export_button)
        layout.addWidget(search_group)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.context_menu)

        self.table.cellChanged.connect(self.update_record)
        self.table.verticalScrollBar().valueChanged.connect(self.check_scroll_position)

    def export_to_excel(self):
        """Export the table data to an Excel file"""
        path, _ = QFileDialog.getSaveFileName(self, "Зберегти файл", "", "Excel Files (*.xlsx)")
        if path:
            data = []
            for row in range(self.table.rowCount()):
                # Пропускаємо приховані рядки (наприклад, відфільтровані пошуком)
                if self.table.isRowHidden(row):
                    continue
                
                # Пропускаємо рядок із кнопкою "+" (якщо є)
                if self.can_add and self.table.cellWidget(row, 0) is not None:
                    continue

                row_data = []
                for column in range(self.table.columnCount()):
                    # Пропускаємо приховані колонки (наприклад, ID)
                    if self.table.isColumnHidden(column):
                        continue
                        
                    item = self.table.item(row, column)
                    
                    # Обробка чекбоксів
                    if hasattr(self, 'checkbox_columns') and column in getattr(self, 'checkbox_columns', []):
                        val = "Так" if item and item.checkState() == Qt.Checked else "Ні"
                        row_data.append(val)
                    else:
                        row_data.append(item.text() if item else "")
                data.append(row_data)
            
            headers = [self.table.horizontalHeaderItem(column).text() for column in range(self.table.columnCount()) if not self.table.isColumnHidden(column)]
            df = pd.DataFrame(data, columns=headers)
            df.to_excel(path, index=False, engine='openpyxl')
            self.show_success_message("Експорт успішно завершено!", "general")

    def add_plus_button_row(self):
        """Add a '+' button in the last row for adding new entries"""
        if self.table.rowCount() > 0 and isinstance(self.table.cellWidget(self.table.rowCount() - 1, 0), QPushButton):
            self.table.removeRow(self.table.rowCount() - 1)
        
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        
        self.add_button = QPushButton("+", self)
        self.add_button.setObjectName("searchButton")
        self.add_button.setStyleSheet("background-color: #4CAF50;")
        self.add_button.clicked.connect(self.add_new_row)
        self.table.setCellWidget(row_position, 0, self.add_button)
        self.table.verticalHeader().setSectionResizeMode(row_position, QHeaderView.Fixed)
        self.table.scrollToBottom()

    def show_loader(self):
        """Показати індикатор завантаження."""
        self.loading_label.show()
        self.table.setEnabled(False)

    def hide_loader(self):
        """Сховати індикатор завантаження."""
        self.loading_label.hide()
        self.table.setEnabled(True)

    def check_scroll_position(self):
        """Перевірка позиції скролу для підвантаження даних."""
        scroll_bar = self.table.verticalScrollBar()
        if scroll_bar.value() == scroll_bar.maximum() and not self.is_loading:
            self.load_data()

    def search_table(self):
        """Пошук у таблиці з підсвічуванням знайдених рядків."""
        search_text = self.search_input.text().strip().lower()

        if self.current_offset > 0:
            self.load_data(reset=True, full_load=True)

        self.table.blockSignals(True)

        if not search_text:
            self.table.blockSignals(False)
            self.clear_highlight()
            return

        found_any = False
        self.first_match_row = None
        for row in range(self.table.rowCount()):
            match = any(
                search_text in (self.table.item(row, col).text() if self.table.item(row, col) else "").lower()
                for col in range(self.table.columnCount())
            )
            self.highlight_row(row, match)
            self.table.setRowHidden(row, not match)
            found_any |= match

        self.no_results_label.setVisible(not found_any)
        self.table.setVisible(found_any)

        self.table.blockSignals(False)

    def scroll_to_row(self, row):
        """Прокручує таблицю до заданого рядка."""
        scroll_bar = self.table.verticalScrollBar()
        target_scroll_value = row
        scroll_bar.setValue(target_scroll_value)

    def _is_row_cancelled(self, row):
        """Перевіряє, чи заява у рядку скасована."""
        if self.cancelled_column is None:
            return False
        item = self.table.item(row, self.cancelled_column)
        if item is None:
            return False
        return item.checkState() == Qt.Checked

    def highlight_row(self, row, match):
        """Підсвічує рядок зеленим при пошуку; зберігає червоний для скасованих."""
        if match and self.first_match_row is None:
            self.first_match_row = row + 1
        if self.first_match_row is not None:
            self.scroll_to_row(self.first_match_row - 4)

        is_cancelled = self._is_row_cancelled(row)
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                if match:
                    item.setBackground(QColor(120, 250, 155))  # зелений пошук
                elif is_cancelled:
                    item.setBackground(QColor(255, 180, 180))  # червоний скасовані
                else:
                    item.setBackground(QBrush())  # порожній браш -> стандартне чергування

    def clear_highlight(self):
        """Очищує підсвічування пошуку; відновлює стандартні кольори сіро/біло."""
        self.no_results_label.hide()
        self.table.show()
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)
            is_cancelled = self._is_row_cancelled(row)
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    if is_cancelled:
                        item.setBackground(QColor(255, 180, 180))  # червоний для скасованих
                    else:
                        item.setBackground(QBrush())  # порожній браш -> автоматичне чергування сіро/біло
        self.table.blockSignals(False)

    def context_menu(self, position):
        """Display context menu on right-click"""
        if not self.can_delete:
            return
            
        menu = QMenu()
        delete_action = QAction("Видалити запис", self)
        menu.setObjectName("contextMenu")
        menu.setCursor(QCursor(Qt.PointingHandCursor))
        delete_action.triggered.connect(self.delete_record)
        menu.addAction(delete_action)
        menu.exec_(self.table.viewport().mapToGlobal(position))

    def show_error_message(self, message, target=None, rollback=False):
        """Displays an error message using Toast (bottom)."""
        if rollback and hasattr(self, 'conn') and self.conn:
            try:
                self.conn.rollback()
            except Exception as e:
                log_error("Помилка при скасуванні транзакції", e)
        show_error(self, message)

    def show_success_message(self, message, target=None):
        """Displays a success message using Toast (bottom)."""
        show_success(self, message)

    def update_record(self, row, column):
        """Оновлює запис у базі даних."""
        try:
            record_id_item = self.table.item(row, 0)
            record_id = record_id_item.text() if record_id_item else None

            if not record_id:
                self.show_error_message("ID запису відсутній. Неможливо оновити запис.", "general")
                return

            if column in self.checkbox_columns:
                is_checked = self.table.item(row, column).checkState() == Qt.Checked
                # Для колонки "Скасована заява" зберігаємо True/False в базу
                if column == self.cancelled_column:
                    new_value = is_checked  # boolean
                    # Оновлюємо підсвітку рядка в реальному часі
                    color = QColor(255, 180, 180) if is_checked else QColor(Qt.white)
                    self.table.blockSignals(True)
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        if item:
                            item.setBackground(color)
                    self.table.blockSignals(False)
                else:
                    new_value = "Так" if is_checked else "Ні"
            else:
                new_value = self.table.item(row, column).text()

            if column < len(self.columns_name):
                column_name = self.columns_name[column]
            else:
                self.show_error_message("Некоректна колонка. Неможливо оновити запис.", "general")
                return

            query_check = f"SELECT {column_name} FROM {self.table_name} WHERE id = %s"
            self.cursor.execute(query_check, (record_id,))
            result = self.cursor.fetchone()

            if not result:
                self.show_error_message(f"Запис із ID {record_id} не знайдено.", "general")
                return

            original_value = result[0]

            if new_value != original_value and str(new_value) != str(original_value):
                query_update = f"UPDATE {self.table_name} SET {column_name} = %s WHERE id = %s"
                self.cursor.execute(query_update, (new_value, record_id))
                self.conn.commit()
                log_info(f"Адмін: Оновлено запис у {self.table_name} (ID: {record_id}, {column_name} -> {new_value})")
                self.show_success_message("Запис оновлено!")
        except Exception as e:
            self.show_error_message(f"Помилка при оновленні запису: {str(e)}", "general", rollback=True)


    def delete_record(self):
        """Delete selected record"""
        row = self.table.currentRow()
        record_id = self.table.item(row, 0)
        
        if record_id:
            try:
                query = self.sql_queries["DELETE"]
                self.cursor.execute(query, (record_id.text(),))
                self.conn.commit()
                log_info(f"Адмін: Видалено запис із {self.table_name} (ID: {record_id.text()})")
                self.table.removeRow(row)
                self.load_data(reset=True)
                self.show_success_message("Запис видалено.")
            except Exception as e:
                self.show_error_message(f"Помилка при видаленні запису: {str(e)}", "general", rollback=True)

    def load_data(self, reset=False, update_last=False, full_load=False):
        """Завантаження даних частинами або повністю."""
        if self.is_loading:
            return

        if reset:
            self.current_offset = 0
            self.table.setRowCount(0)

        if full_load:
            offset = 0
            limit = None
        elif update_last:
            offset = max(0, self.current_offset - 5)
            limit = 5
        else:
            offset = self.current_offset
            limit = self.page_size

        self.is_loading = True
        self.show_loader()

        try:
            query = self.sql_queries["SELECT"]
            if limit is not None:
                query += f" LIMIT {limit} OFFSET {offset}"

            self.cursor.execute(query)
            records = self.cursor.fetchall()

            existing_ids = set()
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item:
                    existing_ids.add(item.text())

            self.table.blockSignals(True)

            for row_data in records:
                if str(row_data[0]) in existing_ids:
                    continue

                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                for column_number, data in enumerate(row_data):
                    if column_number in self.checkbox_columns:
                        item = QTableWidgetItem()
                        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                        item.setCheckState(Qt.Checked if str(data) in ("True", "Так", "true") else Qt.Unchecked)
                        item.setText("")
                    else:
                        item = QTableWidgetItem(str(data) if data is not None else "")
                    
                    self.table.setItem(row_position, column_number, item)

                # Підсвічуємо червоним, якщо це скасована заява
                if self.cancelled_column is not None:
                    is_cancelled = str(row_data[self.cancelled_column]) in ("True", "Так", "true")
                    if is_cancelled:
                        red = QColor(255, 180, 180)
                        for col in range(self.table.columnCount()):
                            if self.table.item(row_position, col):
                                self.table.item(row_position, col).setBackground(red)

            if not (update_last or full_load):
                self.current_offset += len(records)


            if len(records) < (limit if limit else len(records)):
                self.table.verticalScrollBar().setValue(self.table.verticalScrollBar().maximum())
                self.table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
            else:
                self.table.setVerticalScrollMode(QTableWidget.ScrollPerItem)

        except Exception as e:
            self.show_error_message(f"Помилка при завантаженні даних: {str(e)}", "general", rollback=True)

        finally:
            self.table.blockSignals(False)
            self.hide_loader()
            self.is_loading = False

    def add_new_row(self):
        """Додає новий запис до бази даних з динамічними значеннями."""
        try:
            for column, callback in self.pre_insert_callbacks.items():
                if callable(callback):
                    self.default_values[column] = callback()
                elif isinstance(callback, str):
                    self.cursor.execute(callback)
                    result = self.cursor.fetchone()
                    if result:
                        self.default_values[column] = result[0]
                    else:
                        raise ValueError(f"Не вдалося отримати значення для '{column}'")

            columns = []
            values = []
            placeholders = []

            for key, value in self.default_values.items():
                if value == "current_date":
                    columns.append(key)
                    placeholders.append("current_date")
                else:
                    columns.append(key)
                    placeholders.append("%s")
                    values.append(value)

            query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            self.cursor.execute(query, values)
            self.conn.commit()
            log_info(f"Адмін: Додано новий запис у {self.table_name}")

            self.load_data(reset=True)
            self.show_success_message("Новий запис успішно додано.")

        except Exception as e:
            self.show_error_message(f"Помилка при додаванні запису: {str(e)}", "general", rollback=True)