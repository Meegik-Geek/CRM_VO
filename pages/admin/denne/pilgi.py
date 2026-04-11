from pages.admin.function_admin import BaseTableWidget

class ListPilgi(BaseTableWidget):
    def __init__(self):
        super().__init__(
            table_name="public.benefits",
            headers=[
                "ID", "Код пільги", "Назва пільги", "Тип пільги", "Бал"
            ],
            sql_queries={
                "SELECT": """
                    SELECT id, kod_pilgi, name_pilgi, type_pilgi, bal
                    FROM public.benefits
                    ORDER BY id
                """,
                
                "DELETE": "DELETE FROM public.benefits WHERE id = %s"
            },
            columns_name = [
                "id", "kod_pilgi", "name_pilgi", "type_pilgi", "bal"
            ], 
            label_text="Список пільг",
            default_values={
                "kod_pilgi": 0,
                "name_pilgi":"",
                "type_pilgi": "Загальна",
                "bal": 0
            },
            combo_columns={3: ["Загальна", "Вступ за співбесідою", "Переведення на бюджет"]}
        )
