from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidgetItem, QMenu, QAction
)
from PyQt5.QtCore import Qt, QPoint
from pages.admin.function_admin import BaseTableWidget
from db.connect_db import setup_database
from utils.logger import log_error, log_info

class NumericItem(QTableWidgetItem):
    """Кастомний елемент таблиці для правильного сортування чисел (балів)."""
    def __lt__(self, other):
        try:
            return float(self.text().replace(',', '.')) < float(other.text().replace(',', '.'))
        except ValueError:
            return self.text() < other.text()

class ListEntranceScores(BaseTableWidget):
    def __init__(self):
        # Поля, які ми будемо використовувати для фільтрації
        self.specialities = []
        self.selected_specialities = set()
        
        super().__init__(
            table_name="entrance_scores",
            headers=["Номер справи", "ПІБ вступника", "Спеціальність", "Бал", "Середній бал атестата", "Ранг мот. листа", "Статус", "Тип фінансовання", "Код пільги", "Тип пільги"],
            sql_queries={
                "SELECT": "", # Ми перепишемо load_data
                "DELETE": "DELETE FROM entrance_scores WHERE number_sprava = %s"
            },
            columns_name=["number_sprava", "full_name", "name_specialnosti", "score", "gpa_score", "motivation_rank", "status", "finanse", "kod_pilgi", "type_pilgi"],
            label_text="Введення балів вступних випробувань",
            combo_columns={6: ["З’явився", "Не з’явився", "Незадовільно"]},
            hide_id=False, # Показуємо номер справи
            can_add=False,
            can_delete=False
        )
        
        # Додаємо обробку кліку по заголовку
        self.table.setSortingEnabled(False) # Відключаємо стандартне сортування
        self.table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        
        # Завантажуємо спеціальності та дані
        self.load_all_specialities()
        self.selected_specialities = set(self.specialities)
        self.load_data(reset=True)

    def on_header_clicked(self, index):
        """Показує меню фільтрації або сортує по балах."""
        if index == 2: # "Спеціальність"
            menu = QMenu(self)
            menu.setObjectName("contextMenu")
            
            # Дія "Всі"
            all_action = QAction("Всі", self, checkable=True)
            all_action.setChecked(len(self.selected_specialities) == len(self.specialities))
            all_action.triggered.connect(self.toggle_all_specialities)
            menu.addAction(all_action)
            menu.addSeparator()

            # Перелік спеціальностей
            for spec in sorted(self.specialities):
                action = QAction(spec, self, checkable=True)
                action.setChecked(spec in self.selected_specialities)
                action.triggered.connect(lambda checked, s=spec: self.on_speciality_toggled(s, checked))
                menu.addAction(action)

            header = self.table.horizontalHeader()
            pos = QPoint(header.sectionPosition(index), header.rect().bottom())
            menu.exec_(header.mapToGlobal(pos))
            
        elif index == 3: # "Бал"
            # Сортуємо вручну
            order = getattr(self, f"sort_order_{index}", Qt.AscendingOrder)
            new_order = Qt.DescendingOrder if order == Qt.AscendingOrder else Qt.AscendingOrder
            setattr(self, f"sort_order_{index}", new_order)
            
            self.table.sortItems(index, new_order)
            
            # Вмикаємо іконку-стрілочку тільки для цієї колонки
            self.table.horizontalHeader().setSortIndicatorShown(True)
            self.table.horizontalHeader().setSortIndicator(index, new_order)

    def toggle_all_specialities(self, checked):
        if checked:
            self.selected_specialities = set(self.specialities)
        else:
            self.selected_specialities = set()
        self.load_data(reset=True)

    def on_speciality_toggled(self, spec, checked):
        if checked:
            self.selected_specialities.add(spec)
        else:
            self.selected_specialities.discard(spec)
            
        # Якщо обрані всі, показуємо як "Всі"
        if len(self.selected_specialities) == len(self.specialities):
            self.toggle_all_specialities(True)
        elif not self.selected_specialities:
            self.toggle_all_specialities(False)
        else:
            self.load_data(reset=True)

    def load_all_specialities(self):
        """Завантажує всі унікальні спеціальності для фільтра як у списку студентів."""
        try:
            query = """
                SELECT name_specialnosti, 'денна' AS form FROM specialities_day
                UNION
                SELECT name_specialnosti, 'заочна' AS form FROM specialities_evening
                UNION
                SELECT DISTINCT name_specialnosti, 'денна скорочена' AS form FROM personal_case_day_scor
                ORDER BY name_specialnosti
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            self.specialities = [f"{name} ({form})" for name, form in results]
        except Exception as e:
            log_error("Помилка завантаження спеціальностей", e)

    def load_data(self, reset=False, update_last=False, full_load=False):
        """Завантаження даних із підтримкою фільтрації за кількома спеціальностями."""
        if self.is_loading: return
        if reset:
            self.current_offset = 0
            self.table.setRowCount(0)

        if not self.selected_specialities:
            self.table.setRowCount(0)
            return

        self.is_loading = True
        self.show_loader()

        try:
            # Готуємо плейсхолдери для фільтра IN
            placeholders = ', '.join(['%s'] * len(self.selected_specialities))
            
            query = f"""
                WITH all_cases AS (
                    SELECT TRIM(number_sprava) as number_sprava, CONCAT(name_specialnosti, ' (денна)') as full_spec, cert_number, finanse, is_cancelled FROM personal_case_day WHERE CONCAT(name_specialnosti, ' (денна)') IN ({placeholders})
                    UNION ALL
                    SELECT TRIM(number_sprava) as number_sprava, CONCAT(name_specialnosti, ' (денна скорочена)') as full_spec, cert_number, finanse, is_cancelled FROM personal_case_day_scor WHERE CONCAT(name_specialnosti, ' (денна скорочена)') IN ({placeholders})
                    UNION ALL
                    SELECT TRIM(number_sprava) as number_sprava, CONCAT(name_specialnosti, ' (заочна)') as full_spec, cert_number, finanse, is_cancelled FROM personal_case_evening WHERE CONCAT(name_specialnosti, ' (заочна)') IN ({placeholders})
                ),
                all_applicants AS (
                    SELECT cert_number, last_name || ' ' || first_name || ' ' || middle_name as full_name FROM applicant_personal_data_day
                    UNION
                    SELECT cert_number, last_name || ' ' || first_name || ' ' || middle_name as full_name FROM applicant_personal_data_evening
                ),
                all_benefits AS (
                    SELECT ab.cert_number, 
                           STRING_AGG(ab.kod_pilgi, ', ') as kod_pilgi,
                           STRING_AGG(ben.type_pilgi, ', ') as type_pilgi
                    FROM (
                        SELECT cert_number, kod_pilgi FROM applicant_benefits_day
                        UNION
                        SELECT cert_number, kod_pilgi FROM applicant_benefits_evening
                    ) ab
                    LEFT JOIN benefits ben ON ab.kod_pilgi = ben.kod_pilgi
                    GROUP BY ab.cert_number
                )
                SELECT 
                    c.number_sprava, 
                    a.full_name, 
                    c.full_spec, 
                    s.score, 
                    s.gpa_score,
                    s.motivation_rank,
                    s.status,
                    c.finanse,
                    b.kod_pilgi,
                    b.type_pilgi,
                    c.is_cancelled
                FROM all_cases c
                JOIN all_applicants a ON c.cert_number = a.cert_number
                LEFT JOIN entrance_scores s ON TRIM(c.number_sprava) = TRIM(s.number_sprava)
                LEFT JOIN all_benefits b ON c.cert_number = b.cert_number
                ORDER BY c.number_sprava ASC
            """
            
            # Передаємо список спеціальностей для кожного блоку UNION
            params = list(self.selected_specialities) * 3
            
            self.cursor.execute(query, params)
            records = self.cursor.fetchall()

            from PyQt5.QtGui import QColor
            self.table.blockSignals(True)
            for row_data in records:
                is_cancelled = row_data[-1]  # Остання колонка - is_cancelled
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                for col, data in enumerate(row_data[:-1]):  # Пропускаємо останню колонку
                    val = str(data) if data is not None else ""
                    # Для балів та рангу, якщо NULL, показуємо порожньо
                    if (col in [3, 4, 5]) and data is None: val = ""
                    # Для статусу
                    if col == 6:
                        if is_cancelled:
                            val = "Скасовано"
                        elif data is None:
                            val = "З’явився"
                    
                    if col in [3, 4, 5]:
                        item = NumericItem(val)  # Використовуємо кастомний клас для чисел
                    else:
                        item = QTableWidgetItem(val)
                        
                    # Не редаговані поля
                    if col < 3 or col >= 7 or is_cancelled:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                    # Підсвічуємо скасовані справи червоним
                    if is_cancelled:
                        item.setBackground(QColor(255, 180, 180))

                    self.table.setItem(row_position, col, item)
            
            self.table.blockSignals(False)

        except Exception as e:
            log_error("Помилка при завантаженні балів", e)
            self.show_error_message(f"Помилка завантаження: {e}")
        finally:
            self.hide_loader()
            self.is_loading = False

    def update_record(self, row, column):
        """Переписаний метод оновлення для роботи з INSERT ... ON CONFLICT."""
        if column < 3 or column >= 7: return # Не редаговані поля
        
        try:
            # Безепечне отримання даних із клітинок
            item_sprava = self.table.item(row, 0)
            item_score = self.table.item(row, 3)
            item_gpa = self.table.item(row, 4)
            item_rank = self.table.item(row, 5)
            item_status = self.table.item(row, 6)

            if not item_sprava:
                return

            number_sprava = item_sprava.text().strip()
            score_val = item_score.text().strip() if item_score else ""
            gpa_val = item_gpa.text().strip() if item_gpa else ""
            rank_val = item_rank.text().strip() if item_rank else ""
            status_val = item_status.text().strip() if item_status else "З’явився"

            # Автоматично ставимо 0, якщо вступник не з'явився або отримав незадовільно
            if status_val in ["Не з’явився", "Незадовільно"]:
                score_val = "0"
                if item_score and item_score.text().strip() != "0":
                    self.table.blockSignals(True)
                    item_score.setText("0")
                    self.table.blockSignals(False)

            # Валідація рангу
            rank_db = int(rank_val) if rank_val.isdigit() else None

            # Валідація балів
            def clean_float(val):
                if val == "": return None
                try:
                    return float(val.replace(",", "."))
                except ValueError:
                    return None

            score_db = clean_float(score_val)
            gpa_db = clean_float(gpa_val)

            # Використовуємо UPSERT (INSERT ... ON CONFLICT)
            query = """
                INSERT INTO entrance_scores (number_sprava, score, gpa_score, status, motivation_rank)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (number_sprava) 
                DO UPDATE SET 
                    score = EXCLUDED.score, 
                    gpa_score = EXCLUDED.gpa_score,
                    status = EXCLUDED.status, 
                    motivation_rank = EXCLUDED.motivation_rank
            """
            self.cursor.execute(query, (number_sprava, score_db, gpa_db, status_val, rank_db))
            self.conn.commit()
            self.show_success_message("Дані збережено")
            log_info(f"Оновлено бали для справи {number_sprava}: Бал={score_val}, Атестат={gpa_val}, Статус={status_val}")
            
        except Exception as e:
            log_error(f"Помилка оновлення балу", e)
            self.show_error_message(f"Помилка збереження: {e}")
