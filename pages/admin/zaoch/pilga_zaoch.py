from pages.admin.function_admin import BaseTableWidget

class ListPilgaZao(BaseTableWidget):
    def __init__(self):
        super().__init__(
            table_name="public.applicant_benefits_evening",
            headers=[
                "ID", "Номер свідоцтва про освіту", "Код пільги", "Документи про пільгу"
            ],
            sql_queries={
                "SELECT": """
                    SELECT id, cert_number, kod_pilgi, document_pilgi
                    FROM public.applicant_benefits_evening  
                    ORDER BY id
                """,
                
                "DELETE": "DELETE FROM public.applicant_benefits_evening WHERE id = %s"
            },
            columns_name = [
                "id", "cert_number", "kod_pilgi", "document_pilgi"
            ], 
            label_text="Список пільг вступників (заочна форма)",
            default_values={
                "cert_number":"",
                "kod_pilgi":0,
                "document_pilgi":"", 
                  
            }
        )

            
             
         