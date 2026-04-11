from pages.admin.function_admin import BaseTableWidget

class ListSecretariDen(BaseTableWidget):
    def __init__(self):
        super().__init__(
            table_name="public.secretaries_day",
            headers=[
               "ID", "Прізвище та ініціали секретарів", "Код спеціальності"
            ],
            sql_queries={
                "SELECT": """
                    SELECT id, name_secretar, kod_specialnosti
                    FROM public.secretaries_day  
                    ORDER BY id
                """,
                
                "DELETE": "DELETE FROM public.secretaries_day WHERE id = %s"
            },
            columns_name = [
                "id", "name_secretar", "kod_specialnosti"
            ], 
            label_text="Список секретарів (денна форма)",
            default_values={
                "name_secretar":"",
                "kod_specialnosti":""
            }
        )

            
             
         

