import os
from docxtpl import DocxTemplate
import tempfile
from db.repository import CaseRepository, ApplicantRepository
from db.connect_db import get_setting
from utils.logger import log_error, log_info
from utils.notifications import show_error, show_success

class DocumentPrinter:
    def __init__(self):
        """Ініціалізація принтера через репозиторії."""
        self.case_repo = CaseRepository()
        self.app_repo = ApplicantRepository()
        
    def _get_common_data(self):
        """Повертає загальні дані (назва закладу тощо)."""
        return {
            "institution_name": get_setting("college_name", "Назва закладу"),
            "institution_short_name": get_setting("college_short_name", "Скорочена назва"),
            "resp_secretary": get_setting("resp_secretary", "Людмила ЧАЙКА"),
            "deputy_secretary": get_setting("deputy_secretary", "Костянтин СИДОРУК"),
            "legal_counsel": get_setting("legal_counsel", "Тетяна ДЕНІСОВА"),
            "edebo_admin": get_setting("edebo_admin", "Наталія ХОРУНЖА"),
        }

    def fill_and_print_template(self, template_path, data, dialog, success_message):
        """Заповнює шаблон DOCX, зберігає і друкує файл"""
        try:
            # Додаємо загальні дані (назва закладу) до звіту
            report_data = self._get_common_data()
            report_data.update(data)
            
            output_path = self.fill_docx_template(report_data, template_path)
            self.print_docx(output_path)
            if dialog:
                dialog.accept()  # Закриваємо діалог після успішного друку
            show_success(dialog, success_message) # Тепер сповіщення спливає з самого верху
        except Exception as e:
            show_error(dialog, f"Помилка при друці: {str(e)}")
    

    @staticmethod
    def fill_docx_template(data, template_path):
        """Заповнює DOCX-шаблон даними за допомогою docxtpl та зберігає результат у тимчасовий файл."""
        try:
            doc = DocxTemplate(template_path)
            doc.render(data)
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
            doc.save(output_file.name)
            return output_file.name
        except Exception as e:
            raise FileNotFoundError(f"Помилка відкриття шаблону: {str(e)}")

    @staticmethod
    def print_docx(file_path):
        """Друк DOCX-файлу на принтер"""
        try:
            if os.name == 'nt':
                os.startfile(file_path, "print")
            else:
                os.system(f"lp {file_path}")
        except Exception as e:
            raise RuntimeError(f"Помилка друку файлу: {str(e)}")

    def print_first_page(self, sprava_number, dialog):
        """Друкує першу сторінку анкети (заочна)."""
        query = """
            SELECT * FROM applicant_personal_data_evening AS pd 
            JOIN personal_case_evening AS os ON pd.cert_number = os.cert_number 
            WHERE os.number_sprava = %s
        """
        try:
            result = self.case_repo.execute_query(query, (sprava_number,), fetch_all=False)
            if result:
                data = {
                    "first_name": result[1], "last_name": result[2], "middle_name": result[3],
                    "school_name": result[29], "address": result[12], "phone": result[5],
                    "citizenship": result[6], "passport_number": result[7], "issued_by": result[8],
                    "id_code": result[10], "hostel_need": result[23], "date_birth": result[31]
                }
                self.fill_and_print_template("templates/zaoch/Анкета вступника 1 сторінка.docx", data, dialog, "Друк успішний!")
            else:
                show_error(dialog, "Справу не знайдено!")
        except Exception as e:
            log_error(f"Помилка друку анкети (стор.1) для {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")

    def print_second_page(self, sprava_number, dialog):
        """Друкує другу сторінку анкети (заочна)."""
        query = """
            SELECT pd.school_name, pd.cert_number, pd.cert_issue_date,
                   pd.father_last_name, pd.father_first_name, pd.father_middle_name, pd.father_phone, pd.father_job,
                   pd.mother_last_name, pd.mother_first_name, pd.mother_middle_name, pd.mother_phone, pd.mother_job,
                   pd.first_name, pd.last_name            
            FROM applicant_personal_data_evening AS pd 
            JOIN personal_case_evening AS os ON pd.cert_number = os.cert_number 
            WHERE os.number_sprava = %s
        """
        try:
            result = self.case_repo.execute_query(query, (sprava_number,), fetch_all=False)
            if result:
                data = {
                    "school_name": result[0], "cert_number": result[1], "cert_issue_date": result[2],
                    "father_last_name": result[3], "father_first_name": result[4], "father_middle_name": result[5],
                    "father_phone": result[6], "father_job": result[7], "mother_last_name": result[8],
                    "mother_first_name": result[9], "mother_middle_name": result[10], "mother_phone": result[11],
                    "mother_job": result[12], "first_name": result[13], "last_name": result[14].upper()
                }
                self.fill_and_print_template("templates/zaoch/Анкета вступника 2 сторінка.docx", data, dialog, "Друк успішний!")
            else:
                show_error(dialog, "Справу не знайдено!")
        except Exception as e:
            log_error(f"Помилка друку анкети (стор.2) для {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")

    def print_titulka(self, sprava_number, dialog):
        """Друк титульної сторінки (заочна)."""
        query = """
            SELECT pd.first_name, pd.last_name, pd.middle_name,
                   os.number_sprava, os.name_specialnosti,
                   gz.name_galuzi
            FROM applicant_personal_data_evening AS pd
            JOIN personal_case_evening AS os ON pd.cert_number = os.cert_number
            JOIN knowledge_field AS gz ON os.kod_galuzi = gz.kod_galuzi
            WHERE os.number_sprava = %s
        """
        try:
            result = self.case_repo.execute_query(query, (sprava_number,), fetch_all=False)
            if result:
                data = {
                    "first_name": result[0], "last_name": result[1], "middle_name": result[2],
                    "number_sprava": result[3], "name_specialnosti": result[4], "name_galuzi": result[5]
                }
                self.fill_and_print_template("templates/zaoch/Особова cправа вступника.docx", data, dialog, "Друк успішний!")
            else:
                show_error(dialog, "Справу не знайдено!")
        except Exception as e:
            log_error(f"Помилка друку титулки для {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")

    def print_pilga(self, sprava_number, kod_pilgi, dialog):
        """Друк документа пільги (заочна)."""
        query = """
            SELECT pd.first_name, pd.last_name, pd.middle_name,
                   TO_CHAR(os.date_sprava, 'DD.MM.YYYY') AS date_sprava, 
                   os.name_specialnosti,
                   pv.document_pilgi, pv.kod_pilgi,
                   pi.bal, pi.type_pilgi, pi.name_pilgi,
                   ee.name_examen
            FROM applicant_personal_data_evening AS pd
            JOIN personal_case_evening AS os ON pd.cert_number = os.cert_number
            JOIN applicant_benefits_evening AS pv ON pd.cert_number = pv.cert_number
            JOIN benefits AS pi ON pv.kod_pilgi = pi.kod_pilgi
            LEFT JOIN entrance_examinations_evening AS ee ON TRIM(os.name_specialnosti) = TRIM(ee.name_specialnosti)
            WHERE os.number_sprava = %s AND pv.kod_pilgi = %s
        """
        try:
            result = self.case_repo.execute_query(query, (sprava_number, kod_pilgi), fetch_all=False)
            if result:
                data = {
                    "first_name": result[0], "last_name": result[1], "middle_name": result[2],
                    "date_sprava": result[3], "name_specialnosti": result[4], "document_pilgi": result[5],
                    "kod_pilgi": result[6], "bal": result[7], "type_pilgi": result[8], "name_pilgi": result[9],
                    "name_examen": result[10] or ""
                }
                self.fill_and_print_template("templates/zaoch/Пільга.docx", data, dialog, "Друк успішний!")
            else:
                show_error(dialog, "Пільгу не знайдено!")
        except Exception as e:
            log_error(f"Помилка друку пільги {kod_pilgi} для {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")

    def print_result_first_page(self, sprava_number, dialog):
        """Друк першої сторінки аркушу результатів (заочна)."""
        query = """
            SELECT pd.first_name, pd.last_name, pd.middle_name,
                   os.name_specialnosti, os.number_sprava,
                   ee.type_examen, TO_CHAR(ee.date_examen, 'DD.MM.YYYY') AS date_examen, ee.time_examen, ee.name_examen
            FROM applicant_personal_data_evening AS pd
            JOIN personal_case_evening AS os ON pd.cert_number = os.cert_number
            LEFT JOIN entrance_examinations_evening AS ee ON os.name_specialnosti = ee.name_specialnosti
            WHERE os.number_sprava = %s AND (os.zno_nmt_checkbox IS NULL OR os.zno_nmt_checkbox != 'true')
        """
        try:
            result = self.case_repo.execute_query(query, (sprava_number,), fetch_all=False)
            if result:
                data = {
                    "first_name": result[0] or "", "last_name": result[1] or "", "middle_name": result[2] or "",
                    "name_specialnosti": result[3] or "", "number_sprava": result[4] or "",
                    "type_examen": result[5] or "", "date_examen": result[6] or "", "time_examen": result[7] or "",
                    "name_examen": result[8] or ""
                }
                self.fill_and_print_template("templates/zaoch/Аркуш вступних випробувань 1 сторінка.docx", data, dialog, "Друк успішний!")
            else:
                show_error(dialog, f"Справу '{sprava_number}' не знайдено або є НМТ")
        except Exception as e:
            log_error(f"Помилка друку результатів (стор.1) для {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")

    def print_result_second_page(self, sprava_number, dialog):
        """Друк другої сторінки аркушу результатів (заочна)."""
        try:
            query = """
            SELECT pd.first_name, pd.last_name, pd.middle_name, os.number_sprava, ee.type_examen, ee.name_examen, 
                   os.name_specialnosti
            FROM applicant_personal_data_evening AS pd
            JOIN personal_case_evening AS os ON pd.cert_number = os.cert_number
            LEFT JOIN entrance_examinations_evening AS ee ON TRIM(os.name_specialnosti) = TRIM(ee.name_specialnosti)
            WHERE os.number_sprava = %s
        """
            result = self.case_repo.execute_query(query, (sprava_number,), fetch_all=False)
            if result:
                data = {
                    "number_sprava": result[3], "type_examen": result[4] or "", "name_examen": result[5] or "",
                    "name_specialnosti": result[6]
                }
                self.fill_and_print_template("templates/zaoch/Аркуш вступних випробувань 2 сторінка.docx", data, dialog, "Друк успішний!")
            else:
                show_error(dialog, "Справу не знайдено!")
        except Exception as e:
            log_error(f"Помилка друку результатів (стор.2) для {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")

    def print_osobova_sprava(self, sprava_number, dialog):
        """Друк опису особової справи (заочна)."""
        query = """
            SELECT pd.first_name, pd.last_name, pd.middle_name, pd.passport_number, pd.issued_by, pd.issue_date, pd.cert_number, pd.cert_issue_date,
                   os.name_specialnosti, os.number_sprava, TO_CHAR(os.date_sprava, 'DD.MM.YYYY') AS date_sprava, os.name_secretar
            FROM applicant_personal_data_evening AS pd
            JOIN personal_case_evening AS os ON pd.cert_number = os.cert_number
            WHERE os.number_sprava = %s
        """
        try:
            result = self.case_repo.execute_query(query, (sprava_number,), fetch_all=False)
            if result:
                data = {
                    "first_name": result[0], "last_name": result[1], "middle_name": result[2],
                    "passport_number": result[3], "issued_by": result[4], "issue_date": result[5],
                    "cert_number": result[6], "cert_issue_date": result[7], "name_specialnosti": result[8],
                    "number_sprava": result[9], "date_sprava": result[10], "name_secretar": result[11]
                }
                self.fill_and_print_template("templates/zaoch/Опис особової справи вступника.docx", data, dialog, "Друк успішний!")
            else:
                show_error(dialog, "Справу не знайдено!")
        except Exception as e:
            log_error(f"Помилка друку опису справи {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")

    def print_vstupna_zayava(self, sprava_number, dialog):
        """Друк заяви на вступні випробування (заочна)."""
        query = """
            SELECT pd.first_name, pd.last_name, pd.middle_name, os.name_specialnosti, 
                   TO_CHAR(ee.date_examen, 'DD.MM.YYYY') AS date_examen, pd.school_name, pd.cert_number, pd.phone
            FROM applicant_personal_data_evening AS pd
            JOIN personal_case_evening AS os ON pd.cert_number = os.cert_number
            LEFT JOIN entrance_examinations_evening AS ee ON os.name_specialnosti = ee.name_specialnosti
            WHERE os.number_sprava = %s
        """
        try:
            result = self.case_repo.execute_query(query, (sprava_number,), fetch_all=False)
            if result:
                data = {
                    "first_name": result[0], "last_name": result[1], "middle_name": result[2],
                    "name_specialnosti": result[3], "date_examen": result[4] or "",
                    "school_name": result[5], "cert_number": result[6], "phone": result[7]
                }
                self.fill_and_print_template("templates/zaoch/Заява на вступні випробування.docx", data, dialog, "Друк успішний!")
            else:
                show_error(dialog, "Справу не знайдено!")
        except Exception as e:
            log_error(f"Помилка друку заяви для {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")