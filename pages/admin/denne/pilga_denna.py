from pages.admin.function_admin import BaseTableWidget

class ListPilgaDen(BaseTableWidget):
    def __init__(self):
        super().__init__(
            table_name="public.applicant_benefits_day",
            headers=[
                "ID", "Номер свідоцтва про освіту", "Код пільги", "Документи про пільгу"
            ],
            sql_queries={
                "SELECT": """
                    SELECT id, cert_number, kod_pilgi, document_pilgi
                    FROM public.applicant_benefits_day  
                    ORDER BY id
                """,
                
                "DELETE": "DELETE FROM public.applicant_benefits_day WHERE id = %s"
            },
            columns_name = [
                "id", "cert_number", "kod_pilgi", "document_pilgi"
            ], 
            label_text="Список пільг вступників (денна форма)",
            default_values={
                "cert_number":"",
                "kod_pilgi":0,
                "document_pilgi":"", 
                  
            }
        )

            
             
         