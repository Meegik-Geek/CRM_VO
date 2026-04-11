from pages.admin.function_admin import BaseTableWidget

class ListExamZao(BaseTableWidget):
    def __init__(self):
        super().__init__(
            table_name="public.entrance_examinations_evening",
            headers=[
                "ID", "Код і назва спеціальності", "Тип екзамену", "Назва екзамену", "Дата екзамену", "Час екзамену"
            ],
            sql_queries={
                "SELECT": """
                    SELECT id, name_specialnosti, type_examen, name_examen, TO_CHAR(date_examen, 'DD.MM.YYYY') AS formatted_date, time_examen
                    FROM public.entrance_examinations_evening
                    ORDER BY id
                """,
                
                "DELETE": "DELETE FROM public.entrance_examinations_evening WHERE id = %s"
            },
            columns_name = [
                "id", "name_specialnosti", "type_examen", "name_examen", "date_examen", "time_examen"
            ], 
            label_text="Список вступних випробувань (заочна форма)",
            default_values={
                "name_specialnosti":"",
                "type_examen":"Співбесіда",
                "name_examen": "Співбесіда з української мови та математики",
                "date_examen": None,
                "time_examen":"", 
                  
            }
        )
