from pages.admin.function_admin import BaseTableWidget

class ListSpravaDen(BaseTableWidget):
    def __init__(self):
        super().__init__(
            table_name="public.personal_case_day",
            headers=[
               "ID",
            "Номер справи", "Код галузі", "Спеціальність", "Дата створення справи", "ПІП секретаря", "Фінансування",
            "Номер свідоцтва про освіту", "Скасована заява"
            ],
            sql_queries={
                "SELECT": """
                    SELECT id, number_sprava, kod_galuzi, name_specialnosti, 
                        TO_CHAR(date_sprava, 'DD.MM.YYYY') AS formatted_date, 
                        name_secretar, finanse, cert_number, is_cancelled
                    FROM public.personal_case_day
                    ORDER BY id
                """,
                
                "DELETE": "DELETE FROM public.personal_case_day WHERE id = %s"
            },
            columns_name = [
               "id", "number_sprava", "kod_galuzi", "name_specialnosti", "date_sprava", "name_secretar", "finanse", "cert_number", "is_cancelled"
            
            ], 
            label_text="Список особових справ (денна)",
            default_values={
                "number_sprava": "",
                "kod_galuzi": "",
                "name_specialnosti": "",
                "date_sprava": "current_date",
                "name_secretar": "",
                "finanse": "",
                "cert_number": "",
                "is_cancelled": False
            },
            pre_insert_callbacks={
                "kod_galuzi": lambda: self.fetch_single_value("SELECT kod_galuzi FROM knowledge_field LIMIT 1")
            },
            checkbox_columns=[8],   # is_cancelled
            cancelled_column=8      # індекс колонки is_cancelled для підсвітки
        )

    def fetch_single_value(self, query):
        """Виконує SQL-запит і повертає одне значення."""
        try:
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            self.show_error_message(f"Помилка при отриманні даних: {str(e)}", "general")
            return None