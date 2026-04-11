from pages.admin.function_admin import BaseTableWidget

class ListVstupnikDen(BaseTableWidget):
    def __init__(self):
        super().__init__(
            table_name="public.applicant_personal_data_day",
            headers=[
                "ID", "Прізвище", "Ім'я", "По-батькові", "ПІП", "Телефон", "Громадянство",
                "Номер свідоцтва", "Номер паспорта", "Ким виданий", "Дата видачі", "Ідентифікаційний код",
                "Адреса", "Ім'я батька", "Прізвище батька", "По-батькові батька", "Робота батька", "Телефон батька",
                "Ім'я матері", "Прізвище матері", "По-батькові матері", "Телефон матері", "Робота матері",
                "Потреба в гуртожитку", "Стать", "Алгебра", "Геометрія", "Укр. мова", "Укр. література",
                "Школа", "Дата видачі свідоцтва", "Дата народження"
            ],
            sql_queries={
                "SELECT": """
                    SELECT id, last_name, first_name, middle_name, pip, phone, citizenship,
                           cert_number, passport_number, issued_by, issue_date, id_code, address,
                           father_first_name, father_last_name, father_middle_name, father_job, father_phone,
                           mother_first_name, mother_last_name, mother_middle_name, mother_phone, mother_job,
                           hostel_need, gender, algebra, geometry, ukr_language, ukr_literature, school_name,
                           cert_issue_date, date_birth
                    FROM public.applicant_personal_data_day
                    ORDER BY id
                """,
                
                "DELETE": "DELETE FROM public.applicant_personal_data_day WHERE id = %s"
            },
            columns_name = [
                "id", "last_name", "first_name", "middle_name", "pip", "phone", "citizenship",
                "cert_number", "passport_number", "issued_by", "issue_date", "id_code", "address",
                "father_first_name", "father_last_name", "father_middle_name", "father_job", "father_phone",
                "mother_first_name", "mother_last_name", "mother_middle_name", "mother_phone", "mother_job",
                "hostel_need", "gender", "algebra", "geometry", "ukr_language", "ukr_literature",
                "school_name", "cert_issue_date", "date_birth"
            ], 
            label_text="Список вступників (денна форма)",
            default_values={
                "last_name":"",
                 "first_name":"",
                  "middle_name":"", 
                  "pip":"", 
                  "phone":"",
                   "citizenship":"",
                    "cert_number":"",
                    "passport_number":"",
                    "issued_by":"",
                    "issue_date":"",
                    "id_code":"",
                    "address":"",
                    "father_first_name":"",
                    "father_last_name":"", 
                    "father_middle_name":"",
                    "father_job":"", 
                    "father_phone":"",
                    "mother_first_name":"", 
                    "mother_last_name":"", 
                    "mother_middle_name":"", 
                    "mother_phone":"", 
                    "mother_job":"",
                    "hostel_need":"", 
                    "gender":"", 
                    "algebra":"", 
                    "geometry":"", 
                    "ukr_language":"", 
                    "ukr_literature":"",
                    "school_name":"", 
                    "cert_issue_date":"", 
                    "date_birth":""
            }
        )
