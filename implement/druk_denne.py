import os
from docxtpl import DocxTemplate
import tempfile
from db.repository import CaseRepository, ApplicantRepository, BenefitRepository
from db.connect_db import get_setting
from utils.logger import log_error
from utils.notifications import show_error, show_success

class DocumentPrinter:
    def __init__(self):
        """Ініціалізація принтера через репозиторії."""
        self.case_repo = CaseRepository()
        self.app_repo = ApplicantRepository()
        self.benefit_repo = BenefitRepository()

    def _get_common_data(self):
        """Повертає загальні дані для всіх звітів."""
        return {
            "institution_name": get_setting("college_name", "Назва закладу"),
            "institution_short_name": get_setting("college_short_name", "Скорочена назва"),
            "resp_secretary": get_setting("resp_secretary", ""),
            "deputy_secretary": get_setting("deputy_secretary", ""),
            "legal_counsel": get_setting("legal_counsel", ""),
            "edebo_admin": get_setting("edebo_admin", ""),
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
        """Друкує першої сторінки анкети (денна)."""
        try:
            # Визначаємо, чи це скорочена форма
            is_scor = self.case_repo.execute_query("SELECT COUNT(*) FROM personal_case_day_scor WHERE number_sprava = %s", (sprava_number,), fetch_all=False)[0] > 0
            table_name = "personal_case_day_scor" if is_scor else "personal_case_day"
            template_path = f"templates/denne_scor/Анкета вступника 1 сторінка.docx" if is_scor else "templates/denne/Анкета вступника 1 сторінка.docx"

            query = f"""
                SELECT pd.last_name, pd.first_name, pd.middle_name, pd.school_name, pd.address, pd.phone, pd.date_birth, pd.citizenship, pd.hostel_need, pd.passport_number, pd.issued_by, pd.id_code
                FROM applicant_personal_data_day AS pd 
                JOIN {table_name} AS os ON pd.cert_number = os.cert_number 
                WHERE os.number_sprava = %s
            """
            result = self.case_repo.execute_query(query, (sprava_number,), fetch_all=False)
            if result:
                data = {
                    "last_name": result[0], "first_name": result[1], "middle_name": result[2], "school_name": result[3],
                    "address": result[4], "phone": result[5], "date_birth": result[6], "citizenship": result[7],
                    "hostel_need": result[8], "passport_number": result[9], "issued_by": result[10], "id_code": result[11],
                }
                self.fill_and_print_template(template_path, data, dialog, "Друк успішний!")
            else:
                show_error(dialog, "Справу не знайдено!")
        except Exception as e:
            log_error(f"Помилка друку анкети (стор.1) для {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")

    def print_second_page(self, sprava_number, dialog):
        """Друкує другу сторінку анкети (денна)."""
        try:
            is_scor = self.case_repo.execute_query("SELECT COUNT(*) FROM personal_case_day_scor WHERE number_sprava = %s", (sprava_number,), fetch_all=False)[0] > 0
            table_name = "personal_case_day_scor" if is_scor else "personal_case_day"
            template_path = f"templates/denne_scor/Анкета вступника 2 сторінка.docx" if is_scor else "templates/denne/Анкета вступника 2 сторінка.docx"

            query = f"""
                SELECT pd.school_name, pd.cert_number, pd.cert_issue_date, pd.father_last_name, pd.father_first_name, pd.father_middle_name, pd.father_phone, pd.father_job,
                       pd.mother_last_name, pd.mother_first_name, pd.mother_middle_name, pd.mother_phone, pd.mother_job, pd.first_name, pd.last_name            
                FROM applicant_personal_data_day AS pd 
                JOIN {table_name} AS os ON pd.cert_number = os.cert_number 
                WHERE os.number_sprava = %s
            """
            result = self.case_repo.execute_query(query, (sprava_number,), fetch_all=False)
            if result:
                data = {
                    "school_name": result[0], "cert_number": result[1], "cert_issue_date": result[2], "father_last_name": result[3],
                    "father_first_name": result[4], "father_middle_name": result[5], "father_phone": result[6], "father_job": result[7],
                    "mother_last_name": result[8], "mother_first_name": result[9], "mother_middle_name": result[10], "mother_phone": result[11],
                    "mother_job": result[12], "first_name": result[13], "last_name": result[14].upper()
                }
                self.fill_and_print_template(template_path, data, dialog, "Друк успішний!")
            else:
                show_error(dialog, "Справу не знайдено!")
        except Exception as e:
            log_error(f"Помилка друку анкети (стор.2) для {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")

    def print_titulka(self, sprava_number, dialog):
        """Друк титульної сторінки (денна)."""
        try:
            is_scor = self.case_repo.execute_query("SELECT COUNT(*) FROM personal_case_day_scor WHERE number_sprava = %s", (sprava_number,), fetch_all=False)[0] > 0
            table_name = "personal_case_day_scor" if is_scor else "personal_case_day"
            template_path = f"templates/denne_scor/Особова cправа вступника.docx" if is_scor else "templates/denne/Особова cправа вступника.docx"

            query = f"""
                SELECT pd.first_name, pd.last_name, pd.middle_name, os.number_sprava, os.name_specialnosti, gz.name_galuzi
                FROM applicant_personal_data_day AS pd
                JOIN {table_name} AS os ON pd.cert_number = os.cert_number
                JOIN knowledge_field AS gz ON os.kod_galuzi = gz.kod_galuzi
                WHERE os.number_sprava = %s
            """
            result = self.case_repo.execute_query(query, (sprava_number,), fetch_all=False)
            if result:
                data = {
                    "first_name": result[0], "last_name": result[1], "middle_name": result[2],
                    "number_sprava": result[3], "name_specialnosti": result[4], "name_galuzi": result[5]
                }
                self.fill_and_print_template(template_path, data, dialog, "Друк успішний!")
            else:
                show_error(dialog, "Справу не знайдено!")
        except Exception as e:
            log_error(f"Помилка друку титулки для {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")

    def print_pilga(self, sprava_number, kod_pilgi, dialog):
        """Друк документа пільги (денна)."""
        try:
            is_scor = self.case_repo.execute_query("SELECT COUNT(*) FROM personal_case_day_scor WHERE number_sprava = %s", (sprava_number,), fetch_all=False)[0] > 0
            table_name = "personal_case_day_scor" if is_scor else "personal_case_day"
            template_path = f"templates/denne_scor/Пільга.docx" if is_scor else "templates/denne/Пільга.docx"

            exam_table = "entrance_examinations_day_scor" if is_scor else "entrance_examinations_day"
            query = f"""
                SELECT pd.first_name, pd.last_name, pd.middle_name, TO_CHAR(os.date_sprava, 'DD.MM.YYYY') AS date_sprava, os.name_specialnosti,
                       pv.document_pilgi, pv.kod_pilgi, pi.bal, pi.type_pilgi, pi.name_pilgi, ee.name_examen
                FROM applicant_personal_data_day AS pd
                JOIN {table_name} AS os ON pd.cert_number = os.cert_number
                JOIN applicant_benefits_day AS pv ON pd.cert_number = pv.cert_number
                JOIN benefits AS pi ON pv.kod_pilgi = pi.kod_pilgi
                LEFT JOIN {exam_table} AS ee ON TRIM(os.name_specialnosti) = TRIM(ee.name_specialnosti)
                WHERE os.number_sprava = %s AND pv.kod_pilgi = %s
            """
            result = self.case_repo.execute_query(query, (sprava_number, kod_pilgi), fetch_all=False)
            if result:
                data = {
                    "first_name": result[0], "last_name": result[1], "middle_name": result[2], "date_sprava": result[3],
                    "name_specialnosti": result[4], "document_pilgi": result[5], "kod_pilgi": result[6], "bal": result[7],
                    "type_pilgi": result[8], "name_pilgi": result[9], "name_examen": result[10] or ""
                }
                self.fill_and_print_template(template_path, data, dialog, "Друк успішний!")
            else:
                show_error(dialog, "Пільгу не знайдено!")
        except Exception as e:
            log_error(f"Помилка друку пільги для {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")
    def print_result_first_page(self, sprava_number, dialog):
        """Друк результатів випробувань (денна, стор.1)."""
        try:
            is_scor = self.case_repo.execute_query("SELECT COUNT(*) FROM personal_case_day_scor WHERE number_sprava = %s", (sprava_number,), fetch_all=False)[0] > 0
            table_name = "personal_case_day_scor" if is_scor else "personal_case_day"
            exam_table = "entrance_examinations_day_scor" if is_scor else "entrance_examinations_day"
            template_path = f"templates/denne_scor/Аркуш вступних випробувань 1 сторінка.docx" if is_scor else "templates/denne/Аркуш вступних випробувань 1 сторінка.docx"

            query = f"""
                SELECT pd.first_name, pd.last_name, pd.middle_name, os.name_specialnosti, os.number_sprava, ee.type_examen, TO_CHAR(ee.date_examen, 'DD.MM.YYYY') AS date_examen, ee.time_examen, ee.name_examen
                FROM applicant_personal_data_day AS pd
                JOIN {table_name} AS os ON pd.cert_number = os.cert_number
                JOIN {exam_table} AS ee ON os.name_specialnosti = ee.name_specialnosti
                WHERE os.number_sprava = %s
            """
            result = self.case_repo.execute_query(query, (sprava_number,), fetch_all=False)
            if result:
                data = {
                    "first_name": result[0], "last_name": result[1], "middle_name": result[2], "name_specialnosti": result[3],
                    "number_sprava": result[4], "type_examen": result[5], "date_examen": result[6], "time_examen": result[7],
                    "name_examen": result[8]
                }
                self.fill_and_print_template(template_path, data, dialog, "Друк успішний!")
            else:
                show_error(dialog, "Справу не знайдено!")
        except Exception as e:
            log_error(f"Помилка друку результатів для {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")
    def print_result_second_page(self, sprava_number, dialog):
        """Друк результатів випробувань (денна, стор.2)."""
        try:
            is_scor = self.case_repo.execute_query("SELECT COUNT(*) FROM personal_case_day_scor WHERE number_sprava = %s", (sprava_number,), fetch_all=False)[0] > 0
            table_name = "personal_case_day_scor" if is_scor else "personal_case_day"
            template_path = f"templates/denne_scor/Аркуш вступних випробувань 2 сторінка.docx" if is_scor else "templates/denne/Аркуш вступних випробувань 2 сторінка.docx"

            exam_table = "entrance_examinations_day_scor" if is_scor else "entrance_examinations_day"
            query = f"""
                SELECT pd.first_name, pd.last_name, pd.middle_name, os.number_sprava, ee.type_examen, ee.name_examen, 
                       os.name_specialnosti
                FROM applicant_personal_data_day AS pd
                JOIN {table_name} AS os ON pd.cert_number = os.cert_number
                LEFT JOIN {exam_table} AS ee ON TRIM(os.name_specialnosti) = TRIM(ee.name_specialnosti)
                WHERE os.number_sprava = %s
            """
            result = self.case_repo.execute_query(query, (sprava_number,), fetch_all=False)
            if result:
                data = {
                    "number_sprava": result[3], "type_examen": result[4] or "", "name_examen": result[5] or "",
                    "name_specialnosti": result[6]
                }
                self.fill_and_print_template(template_path, data, dialog, "Друк успішний!")
            else:
                show_error(dialog, "Справу не знайдено!")
        except Exception as e:
            log_error(f"Помилка друку результатів (стор.2) для {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")

    def print_osobova_sprava(self, sprava_number, dialog):
        """Друк опису справи (денна)."""
        try:
            is_scor = self.case_repo.execute_query("SELECT COUNT(*) FROM personal_case_day_scor WHERE number_sprava = %s", (sprava_number,), fetch_all=False)[0] > 0
            table_name = "personal_case_day_scor" if is_scor else "personal_case_day"
            exam_table = "entrance_examinations_day_scor" if is_scor else "entrance_examinations_day"
            template_path = f"templates/denne_scor/Опис особової справи вступника.docx" if is_scor else "templates/denne/Опис особової справи вступника.docx"

            query = f"""
                SELECT pd.first_name, pd.last_name, pd.middle_name, pd.passport_number, pd.issued_by, pd.issue_date, pd.cert_number, pd.cert_issue_date,
                       os.name_specialnosti, os.number_sprava, TO_CHAR(os.date_sprava, 'DD.MM.YYYY') AS date_sprava, os.name_secretar,
                       TO_CHAR(ee.date_examen, 'DD.MM.YYYY') AS date_examen
                FROM applicant_personal_data_day AS pd
                JOIN {table_name} AS os ON pd.cert_number = os.cert_number
                LEFT JOIN {exam_table} AS ee ON os.name_specialnosti = ee.name_specialnosti
                WHERE os.number_sprava = %s
            """
            result = self.case_repo.execute_query(query, (sprava_number,), fetch_all=False)
            if result:
                data = {
                    "first_name": result[0], "last_name": result[1], "middle_name": result[2], "passport_number": result[3],
                    "issued_by": result[4], "issue_date": result[5], "cert_number": result[6], "cert_issue_date": result[7],
                    "name_specialnosti": result[8], "number_sprava": result[9], "date_sprava": result[10], "name_secretar": result[11],
                    "date_examen": result[12]
                }
                self.fill_and_print_template(template_path, data, dialog, "Друк успішний!")
            else:
                show_error(dialog, "Справу не знайдено!")
        except Exception as e:
            log_error(f"Помилка друку опису справи для {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")
    def print_vstupna_zayava(self, sprava_number, dialog):
        """Друк заяви (денна)."""
        try:
            is_scor = self.case_repo.execute_query("SELECT COUNT(*) FROM personal_case_day_scor WHERE number_sprava = %s", (sprava_number,), fetch_all=False)[0] > 0
            table_name = "personal_case_day_scor" if is_scor else "personal_case_day"
            exam_table = "entrance_examinations_day_scor" if is_scor else "entrance_examinations_day"
            template_path = f"templates/denne_scor/Заява на вступні випробування.docx" if is_scor else "templates/denne/Заява на вступні випробування.docx"

            query = f"""
                SELECT pd.first_name, pd.last_name, pd.middle_name, os.name_specialnosti, TO_CHAR(ee.date_examen, 'DD.MM.YYYY') AS date_examen, pd.school_name, pd.cert_number, pd.phone
                FROM applicant_personal_data_day AS pd
                JOIN {table_name} AS os ON pd.cert_number = os.cert_number
                LEFT JOIN {exam_table} AS ee ON os.name_specialnosti = ee.name_specialnosti
                WHERE os.number_sprava = %s
            """
            result = self.case_repo.execute_query(query, (sprava_number,), fetch_all=False)
            if result:
                data = {
                    "first_name": result[0], "last_name": result[1], "middle_name": result[2], "name_specialnosti": result[3],
                    "date_examen": result[4], "school_name": result[5], "cert_number": result[6], "phone": result[7]
                }
                self.fill_and_print_template(template_path, data, dialog, "Друк успішний!")
            else:
                show_error(dialog, "Справу не знайдено!")
        except Exception as e:
            log_error(f"Помилка друку заяви для {sprava_number}", e)
            show_error(dialog, f"Помилка: {str(e)}")