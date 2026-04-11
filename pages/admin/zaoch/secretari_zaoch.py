from pages.admin.function_admin import BaseTableWidget

class ListSecretariZao(BaseTableWidget):
    def __init__(self):
        super().__init__(
            table_name="public.secretaries_evening",
            headers=[
               "ID", "Прізвище та ініціали секретарів", "Код спеціальності"
            ],
            sql_queries={
                "SELECT": """
                    SELECT id, name_secretar, kod_specialnosti
                    FROM public.secretaries_evening  
                    ORDER BY id
                """,
                
                "DELETE": "DELETE FROM public.secretaries_evening WHERE id = %s"
            },
            columns_name = [
                "id", "name_secretar", "kod_specialnosti"
            ], 
            label_text="Список секретарів (заочна форма)",
            default_values={
                "name_secretar":"",
                "kod_specialnosti":""
            }
        )

            
             
         

