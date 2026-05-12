from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QGroupBox,
    QTableWidget, QTableWidgetItem, QScrollArea, QPushButton, QMenu, QAction,
    QHeaderView, QFileDialog, QAbstractItemView, QStyledItemDelegate, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, QSettings
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
        editor.setFrame(False) # Прибираємо рамку, щоб вписати в клітинку
        # Відкриваємо список одразу
        QTimer.singleShot(0, editor.showPopup)
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
        self.all_data_loaded = False

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
        self.table = QTableWidget(self); self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.setObjectName("tableWidget")
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.CurrentChanged) # Редагування в один клік (при зміні фокусу)
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
        if scroll_bar.value() == scroll_bar.maximum() and not self.is_loading and not self.all_data_loaded:
            self.load_data()

    def search_table(self):
        """Пошук у таблиці з підсвічуванням знайдених рядків."""
        search_text = self.search_input.text().strip().lower()

        # Якщо ми ще не завантажили всі дані для пошуку - робимо це один раз
        if not self.all_data_loaded:
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

        if found_any:
            self.table.setAlternatingRowColors(False)
        else:
            self.table.setAlternatingRowColors(True)

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
        
        # Визначаємо колір підсвічування залежно від теми
        settings = QSettings("MyApp", "Settings")
        theme = settings.value("theme", "light")
        
        if theme == "grey":
            # Приглушений темно-зелений для темної теми
            highlight_color = QColor(35, 80, 50) 
        else:
            # М'який пастельний зелений для світлої теми
            highlight_color = QColor(180, 245, 190)

        is_cancelled = self._is_row_cancelled(row)
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                if match:
                    item.setBackground(highlight_color)
                elif is_cancelled:
                    item.setBackground(QColor(255, 180, 180))
                else:
                    item.setBackground(QBrush())

        if match and self.first_match_row == row + 1:
            self.scroll_to_row(max(0, row - 4))

    def clear_highlight(self):
        """Очищує підсвічування пошуку; відновлює стандартні кольори сіро/біло."""
        self.no_results_label.hide()
        self.table.show()
        self.table.setAlternatingRowColors(True)
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
        if self.is_loading: # Жорсткий захист від оновлення під час завантаження
            return

        try:
            record_id_item = self.table.item(row, 0)
            record_id = record_id_item.text() if record_id_item else None

            if not record_id:
                return

            if column in self.checkbox_columns:
                is_checked = self.table.item(row, column).checkState() == Qt.Checked
                if column == self.cancelled_column:
                    new_value = is_checked
                    # Оновлюємо підсвітку в реальному часі
                    color = QColor(255, 180, 180) if is_checked else QColor(Qt.white)
                    self.table.blockSignals(True)
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        if item: item.setBackground(color)
                    self.table.blockSignals(False)
                else:
                    new_value = "Так" if is_checked else "Ні"
            else:
                new_value = self.table.item(row, column).text()

            column_name = self.columns_name[column]
            
            # Перевірка чи значення дійсно змінилося
            self.cursor.execute(f"SELECT {column_name} FROM {self.table_name} WHERE id = %s", (record_id,))
            res = self.cursor.fetchone()
            if res and (str(res[0]) == str(new_value)):
                return

            self.cursor.execute(f"UPDATE {self.table_name} SET {column_name} = %s WHERE id = %s", (new_value, record_id))
            self.conn.commit()
            log_info(f"Адмін: Оновлено {self.table_name} (ID: {record_id}, {column_name} -> {new_value})")
            self.show_success_message("Запис оновлено!")
        except Exception as e:
            self.show_error_message(f"Помилка оновлення: {str(e)}", rollback=True)

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

        self.table.blockSignals(True) # Блокуємо сигнали ОДРАЗУ

        if reset:
            self.current_offset = 0
            self.table.setRowCount(0)
            self.all_data_loaded = False

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
            
            # Якщо завантажили все або менше сторінки
            if limit and len(records) < limit:
                self.all_data_loaded = True
            elif limit is None:
                self.all_data_loaded = True

            existing_ids = set()
            for r in range(self.table.rowCount()):
                it = self.table.item(r, 0)
                if it: existing_ids.add(it.text())

            for row_data in records:
                if str(row_data[0]) in existing_ids:
                    continue

                row_pos = self.table.rowCount()
                self.table.insertRow(row_pos)
                for col_idx, data in enumerate(row_data):
                    if col_idx in self.checkbox_columns:
                        item = QTableWidgetItem()
                        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                        item.setCheckState(Qt.Checked if str(data) in ("True", "Так", "true") else Qt.Unchecked)
                    else:
                        item = QTableWidgetItem(str(data) if data is not None else "")
                    self.table.setItem(row_pos, col_idx, item)

                if self.cancelled_column is not None:
                    if str(row_data[self.cancelled_column]) in ("True", "Так", "true"):
                        for c in range(self.table.columnCount()):
                            if self.table.item(row_pos, c):
                                self.table.item(row_pos, c).setBackground(QColor(255, 180, 180))

            if not (update_last or full_load):
                self.current_offset += len(records)

            if len(records) < (limit if limit else 1):
                self.table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
            else:
                self.table.setVerticalScrollMode(QTableWidget.ScrollPerItem)

        except Exception as e:
            self.show_error_message(f"Помилка завантаження: {str(e)}", rollback=True)
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
                    res = self.cursor.fetchone()
                    if res: self.default_values[column] = res[0]

            cols = []
            vals = []
            places = []
            for k, v in self.default_values.items():
                cols.append(k)
                if v == "current_date": places.append("current_date")
                else:
                    places.append("%s")
                    vals.append(v)

            query = f"INSERT INTO {self.table_name} ({', '.join(cols)}) VALUES ({', '.join(places)})"
            self.cursor.execute(query, vals)
            self.conn.commit()
            self.load_data(reset=True)
            self.show_success_message("Запис додано!")
        except Exception as e:
            self.show_error_message(f"Помилка додавання: {str(e)}", rollback=True)