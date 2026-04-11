from pages.admin.function_admin import BaseTableWidget

class ListGaluzZnan(BaseTableWidget):
    def __init__(self):
        super().__init__(
            table_name="public.knowledge_field",
            headers=[
                 "ID", "Код галузі", "Назва галузі"
            ],
            sql_queries={
                "SELECT": """
                    SELECT id, kod_galuzi, name_galuzi 
                    FROM public.knowledge_field 
                    ORDER BY id
                """,
                
                "DELETE": "DELETE FROM public.knowledge_field WHERE id = %s"
            },
            columns_name = [
                 "id", "kod_galuzi", "name_galuzi"
            ], 
            label_text="Список галузі знань",
            default_values={
                "kod_galuzi":"",
                "name_galuzi":""
                  
            }
        )

