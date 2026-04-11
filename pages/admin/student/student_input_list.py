from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout,
    QGroupBox, QTableWidget, QTableWidgetItem, QScrollArea,
    QPushButton, QMenu, QAction, QFileDialog, QStyledItemDelegate, QComboBox, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QColor, QCursor
import pandas as pd
from db.connect_db import setup_database
from utils.notifications import show_success, show_error
from utils.logger import log_error, log_info

class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, options, parent=None):
        super(ComboBoxDelegate, self).__init__(parent)
        self.options = options

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.setObjectName("comboBox")
        combo.addItems(self.options)
        return combo

    def setEditorData(self, editor, index):
        current_text = index.data(Qt.DisplayRole)
        idx = editor.findText(current_text)
        if idx >= 0:
            editor.setCurrentIndex(idx)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

class ListInputStudent(QWidget):
    def __init__(self):
        super(ListInputStudent, self).__init__()
        
 
 
        self.specialities = []
        self.selected_specialities = set()
        self.loaded_ids = set()  # Для відстеження унікальних записів
        self.setup_ui()
        self.conn = setup_database()
        self.cursor = self.conn.cursor()
        self.load_specialities()
        self.selected_specialities = set(self.specialities)
        self.load_data()

    def setup_ui(self):
        """Set up the interface for the list of applicants."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        label = QLabel("Список вступників для редагування студентів", self)
        label.setObjectName("titleLabel")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        scroll_area = QScrollArea(self)
        scroll_area.setObjectName("scrollArea")
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
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

        self.table = QTableWidget(self)
        self.table.setObjectName("tableWidget")
        self.table.setColumnCount(10)
        headers = [
            "ID",
            "Номер справи",
            "Спеціальність",
            "Прізвище",
            "Ім'я",
            "По-батькові",
            "Номер свідоцтва",
            "Фінансування",
            "Номер групи",
            "Дата створення справи"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.setColumnHidden(0, True)
        self.table.setAlternatingRowColors(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        header.setMinimumSectionSize(120)
        scroll_area.setWidget(self.table)

        self.table.setSortingEnabled(False)
        self.table.resizeColumnsToContents()

        search_group = QGroupBox("Пошук / Експорт")
        search_group.setObjectName("groupBox")
        search_layout = QHBoxLayout(search_group)
        
        self.search_input = QLineEdit(self)
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Введіть текст для пошуку...")
        self.search_input.textChanged.connect(self.search_table)

        self.export_button = QPushButton("Експорт", self)
        self.export_button.setObjectName("searchButton")
        self.export_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.export_button.clicked.connect(self.export_to_excel)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.export_button)
        layout.addWidget(search_group)

        self.table.cellChanged.connect(self.update_student_record)
        self.table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        

        # Встановлення делегата для стовпця "Фінансування"
        self.table.setItemDelegateForColumn(7, ComboBoxDelegate(["", "Державна форма", "Платна форма"], self.table))

    def export_to_excel(self):
        """Export the table data to an Excel file."""
        path, _ = QFileDialog.getSaveFileName(self, "Зберегти файл", "", "Excel Files (*.xlsx)")
        if path:
            data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for column in range(self.table.columnCount()):
                    item = self.table.item(row, column)
                    widget = self.table.cellWidget(row, column)
                    if widget and isinstance(widget, QComboBox):
                        row_data.append(widget.currentText())
                    else:
                        row_data.append(item.text() if item else "")
                data.append(row_data)
            
            headers = [self.table.horizontalHeaderItem(column).text() for column in range(self.table.columnCount())]
            df = pd.DataFrame(data, columns=headers)
            df.to_excel(path, index=False, engine='openpyxl')
            log_info(f"Адмін: Експортовано список студентів у {path}")
            self.show_success_message("Експорт успішно завершено!", "general")

    def show_loader(self):
        """Показати індикатор завантаження."""
        self.loading_label.show()
        self.table.setEnabled(False)

    def hide_loader(self):
        """Сховати індикатор завантаження."""
        self.loading_label.hide()
        self.table.setEnabled(True)

    def load_specialities(self):
        """Load all specialities for filter menu, including day_scor from personal_case_day_scor."""
        query = """
            SELECT name_specialnosti, 'денна' AS form FROM specialities_day
            UNION
            SELECT name_specialnosti, 'заочна' AS form FROM specialities_evening
            UNION
            SELECT DISTINCT name_specialnosti, 'денна скорочена' AS form FROM personal_case_day_scor
            ORDER BY name_specialnosti
        """
        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            self.specialities = [f"{name} ({form})" for name, form in results]
        except Exception as e:
            self.show_error_message(f"Помилка завантаження спеціальностей: {str(e)}", "general")

    def on_header_clicked(self, index):
        """Показати меню фільтрів при натисканні на заголовок стовпця 'Спеціальність'."""
        if index == 2:
            menu = QMenu(self)
            all_action = QAction("Всі", self, checkable=True)
            all_action.setChecked(len(self.selected_specialities) == len(self.specialities))
            all_action.triggered.connect(lambda checked: self.toggle_all_specialities(checked))
            menu.addAction(all_action)
            menu.setObjectName("contextMenu")
            menu.addSeparator()

            for speciality in sorted(self.specialities):
                action = QAction(speciality, self, checkable=True)
                action.setChecked(speciality in self.selected_specialities)
                action.triggered.connect(lambda checked, s=speciality: self.on_speciality_toggled(s, checked))
                menu.addAction(action)

            header = self.table.horizontalHeader()
            pos = QPoint(header.sectionPosition(index), header.rect().top())
            menu.exec_(header.mapToGlobal(pos))

    def toggle_all_specialities(self, checked):
        """Активувати або деактивувати всі спеціальності."""
        if checked:
            self.selected_specialities = set(self.specialities)
        else:
            self.selected_specialities = set()
        
        self.loaded_ids.clear()
        self.load_data()

    def on_speciality_toggled(self, speciality, checked):
        """Оновлення обраних спеціальностей і повторне завантаження даних."""
        if checked:
            self.selected_specialities.add(speciality)
        else:
            self.selected_specialities.discard(speciality)

        if len(self.selected_specialities) == len(self.specialities):
            self.toggle_all_specialities(True)
        elif not self.selected_specialities:
            self.toggle_all_specialities(False)
        else:
            
            self.loaded_ids.clear()
            self.load_data()

    def load_data(self):
        """Завантаження всіх вступників у таблицю з урахуванням фільтрації."""
        self.show_loader()
        self.table.blockSignals(True)
        self.table.setRowCount(0)

        filters = []
        params = []

        if self.selected_specialities:
            filters_placeholder = ', '.join(['%s'] * len(self.selected_specialities))
            params.extend(self.selected_specialities)

            query = f"""
                SELECT * FROM (
                    SELECT pc.id, 
                        pc.number_sprava,
                        CONCAT(pc.name_specialnosti, ' (денна)') AS full_specialnost,
                        pd.last_name, 
                        pd.first_name, 
                        pd.middle_name,
                        pd.cert_number, 
                        COALESCE(s.finanse, '') AS finanse,
                        COALESCE(s.group_number, '') AS group_number,
                        TO_CHAR(pc.date_sprava, 'DD.MM.YYYY') AS date_sprava
                    FROM personal_case_day pc
                    LEFT JOIN student s ON s.number_sprava_day = pc.number_sprava
                    JOIN applicant_personal_data_day pd ON pd.cert_number = pc.cert_number
                    WHERE CONCAT(pc.name_specialnosti, ' (денна)') IN ({filters_placeholder})

                    UNION ALL

                    SELECT pc.id, 
                        pc.number_sprava,
                        CONCAT(pc.name_specialnosti, ' (заочна)') AS full_specialnost,
                        pd.last_name, 
                        pd.first_name, 
                        pd.middle_name,
                        pd.cert_number, 
                        COALESCE(s.finanse, '') AS finanse,
                        COALESCE(s.group_number, '') AS group_number,
                        TO_CHAR(pc.date_sprava, 'DD.MM.YYYY') AS date_sprava
                    FROM personal_case_evening pc
                    LEFT JOIN student s ON s.number_sprava_evening = pc.number_sprava
                    JOIN applicant_personal_data_evening pd ON pd.cert_number = pc.cert_number
                    WHERE CONCAT(pc.name_specialnosti, ' (заочна)') IN ({filters_placeholder})

                    UNION ALL

                    SELECT pc.id, 
                        pc.number_sprava,
                        CONCAT(pc.name_specialnosti, ' (денна скорочена)') AS full_specialnost,
                        pd.last_name, 
                        pd.first_name, 
                        pd.middle_name,
                        pd.cert_number, 
                        COALESCE(s.finanse, '') AS finanse,
                        COALESCE(s.group_number, '') AS group_number,
                        TO_CHAR(pc.date_sprava, 'DD.MM.YYYY') AS date_sprava
                    FROM personal_case_day_scor pc
                    LEFT JOIN student s ON s.number_sprava_day_scor = pc.number_sprava
                    JOIN applicant_personal_data_day pd ON pd.cert_number = pc.cert_number
                    WHERE CONCAT(pc.name_specialnosti, ' (денна скорочена)') IN ({filters_placeholder})
                ) AS all_cases
                ORDER BY number_sprava
            """

            params *= 3  # для трьох блоків фільтра

            try:
                self.cursor.execute(query, params)
                rows = self.cursor.fetchall()

                for row_data in rows:
                    row_position = self.table.rowCount()
                    self.table.insertRow(row_position)
                    for col, data in enumerate(row_data):
                        if col == 7:  # "Фінансування"
                            combo = QComboBox(self.table)
                            combo.setObjectName("comboBox")
                            combo.addItems(["", "Державна форма", "Платна форма"])
                            combo.setCurrentText(str(data))
                            combo.currentIndexChanged.connect(
                                lambda _, r=row_position, c=col: self.update_student_record(r, c)
                            )
                            self.table.setCellWidget(row_position, col, combo)
                        else:
                            item = QTableWidgetItem(str(data))
                            if col != 8:  # "Номер групи" можна редагувати
                                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            self.table.setItem(row_position, col, item)

            except Exception as e:
                self.show_error_message(f"Помилка завантаження даних: {str(e)}", "general", rollback=True)

        self.table.blockSignals(False)
        self.hide_loader()


    def search_table(self):
        """Пошук у таблиці."""
        search_text = self.search_input.text().strip().lower()
        self.table.blockSignals(True)
        self.clear_highlight()
      
        self.loaded_ids.clear()

        if not search_text:
            self.load_data()
            return

        found_any = False
        for row in range(self.table.rowCount()):
            match = any(
                search_text in (self.table.item(row, col).text() if self.table.item(row, col) else "").lower()
                for col in range(self.table.columnCount())
            )
            self.highlight_row(row, match)
            self.table.setRowHidden(row, not match)
            if match and not found_any:
                self.table.scrollToItem(self.table.item(row, 0), QTableWidget.PositionAtCenter)
                found_any = True

        self.no_results_label.setVisible(not found_any)
        self.table.setVisible(found_any)

        self.table.blockSignals(False)

    def update_student_record(self, row, column):
        """Оновлення запису студента."""
        if column not in [7, 8]:  # Оновлюємо лише для "Фінансування" і "Номер групи"
            return

        try:
            id_value = self.get_table_item_text(row, 0)
            name_specialnosti = self.get_table_item_text(row, 2)
            cert_number = self.get_table_item_text(row, 6)
            finanse = self.get_table_item_text(row, 7) or None
            group_number = self.get_table_item_text(row, 8) or None
            number_sprava = self.get_table_item_text(row, 1)

            if "заочна" in name_specialnosti.lower():
                number_sprava_column = "number_sprava_evening"
            elif "денна скорочена" in name_specialnosti.lower():
                number_sprava_column = "number_sprava_day_scor"
            else:
                number_sprava_column = "number_sprava_day"

            if not finanse:
                query = f"DELETE FROM student WHERE {number_sprava_column} = %s"
                params = (number_sprava,)
                self.cursor.execute(query, params)
                self.conn.commit()
                self.table.blockSignals(True)
                self.table.setItem(row, 8, QTableWidgetItem(""))
                self.table.blockSignals(False)
                log_info(f"Адмін: Видалено запис студента (справа: {number_sprava})")
                self.show_success_message(f"Запис видалено для справи: {number_sprava}")
                return

            query = f"""
                INSERT INTO student (id, {number_sprava_column}, cert_number, name_specialnosti, group_number, finanse)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id)
                DO UPDATE SET
                    {number_sprava_column} = EXCLUDED.{number_sprava_column},
                    cert_number = EXCLUDED.cert_number,
                    name_specialnosti = EXCLUDED.name_specialnosti,
                    group_number = COALESCE(EXCLUDED.group_number, student.group_number),
                    finanse = EXCLUDED.finanse
            """
            params = (id_value, number_sprava, cert_number, name_specialnosti, group_number, finanse)
            self.cursor.execute(query, params)
            self.conn.commit()
            log_info(f"Адмін: Оновлено дані студента (справа: {number_sprava}, фінанси: {finanse}, група: {group_number})")
            self.show_success_message(f"Запис оновлено для справи: {number_sprava}")

        except Exception as e:
            self.show_error_message(f"Помилка оновлення запису: {str(e)}", rollback=True)

    def get_table_item_text(self, row, column):
        """Отримання тексту з таблиці, враховуючи виджети."""
        try:
            item = self.table.item(row, column)
            if item:
                return item.text().strip()

            widget = self.table.cellWidget(row, column)
            if isinstance(widget, QComboBox):
                return widget.currentText().strip()

            return None
        except IndexError:
            
            return None

    

    def show_error_message(self, message, rollback=False):
        """Displays an error message using Toast (bottom)."""
        if rollback and hasattr(self, 'conn') and self.conn:
            try:
                self.conn.rollback()
            except Exception as e:
                log_error("Помилка при скасуванні транзакції", e)
        show_error(self, message)

    def show_success_message(self, message):
        """Displays a success message using Toast (bottom)."""
        show_success(self, message)

    def clear_highlight(self):
        """Очистити підсвічування та повернути видимість усіх рядків."""
        self.no_results_label.hide()
        self.table.show()
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(QColor(Qt.white))

    def highlight_row(self, row, match):
        """Підсвічування рядка."""
        color = QColor(120, 250, 155) if match else QColor(Qt.white)
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(color)