from db.connect_db import setup_database, close_database, get_setting
from utils.logger import log_error

class BaseRepository:
    """Базовий клас для репозиторіїв з основними операціями."""
    def __init__(self):
        self.conn = None
        self.cursor = None

    def _connect(self):
        self.conn = setup_database()
        self.cursor = self.conn.cursor()

    def _close(self):
        if self.conn:
            close_database(self.conn)

    def execute_query(self, query, params=None, fetch_all=True):
        """Виконує SQL-запит та повертає результат."""
        try:
            self._connect()
            self.cursor.execute(query, params or ())
            if fetch_all:
                result = self.cursor.fetchall()
            else:
                result = self.cursor.fetchone()
            return result
        except Exception as e:
            log_error(f"Помилка при виконанні запиту: {query}", e)
            return None
        finally:
            self._close()

class InstitutionRepository(BaseRepository):
    """Репозиторій для роботи з даними закладу та налаштуваннями."""
    
    def get_all_settings(self):
        return self.execute_query("SELECT key, value FROM settings")

    def get_institution_info(self):
        return self.execute_query("SELECT * FROM institution_info", fetch_all=False)

class SpecialtyRepository(BaseRepository):
    """Репозиторій для роботи зі спеціальностями."""

    def get_specialties(self, form_type='day'):
        """Повертає список спеціальностей для обраної форми навчання."""
        table = "specialities_day" if form_type == 'day' else "specialities_evening"
        query = f"""
            SELECT s.kod_specialnosti, s.name_specialnosti, k.name_galuzi 
            FROM {table} s
            LEFT JOIN knowledge_field k ON s.kod_galuzi = k.kod_galuzi
        """
        return self.execute_query(query)

    def get_specialties_day(self):
        return self.get_specialties('day')

    def get_specialties_evening(self):
        return self.get_specialties('zaoch')

    def get_kod_galuzi_by_specialty(self, name, form_type='day'):
        """Повертає код галузі для конкретної спеціальності."""
        table = "specialities_day" if form_type == 'day' else "specialities_evening"
        query = f"SELECT kod_galuzi FROM {table} WHERE name_specialnosti = %s"
        result = self.execute_query(query, (name,), fetch_all=False)
        return result[0] if result else None

class ApplicantRepository(BaseRepository):
    """Репозиторій для роботи з даними вступників."""

    def is_applicant_exists(self, first_name, last_name, middle_name, cert_number, passport_number=None, id_code=None, form_type='day'):
        """Перевіряє, чи існує вже вступник з такими даними."""
        table = "applicant_personal_data_day" if form_type == 'day' else "applicant_personal_data_evening"
        query = f"""
            SELECT 1 
            FROM {table} 
            WHERE (first_name = %s AND last_name = %s AND middle_name = %s) 
               OR (cert_number = %s)
               OR (passport_number = %s AND passport_number != '')
               OR (id_code = %s AND id_code != '')
        """
        result = self.execute_query(query, (first_name, last_name, middle_name, cert_number, passport_number or '', id_code or ''), fetch_all=False)
        return result is not None

    def add_applicant(self, data_list, form_type='day'):
        """Додає нового вступника через список значень."""
        table = "applicant_personal_data_day" if form_type == 'day' else "applicant_personal_data_evening"
        columns = [
            "first_name", "last_name", "middle_name", "pip", "phone", "citizenship", "cert_number",
            "passport_number", "issued_by", "issue_date", "id_code", "address", "father_first_name",
            "father_last_name", "father_middle_name", "father_job", "father_phone", "mother_first_name",
            "mother_last_name", "mother_middle_name", "mother_phone", "mother_job", "hostel_need",
            "gender", "algebra", "geometry", "ukr_language", "ukr_literature", "school_name",
            "cert_issue_date", "date_birth"
        ]
        placeholders = ", ".join(["%s"] * len(columns))
        col_names = ", ".join(columns)
        
        query = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
        
        try:
            self._connect()
            self.cursor.execute(query, tuple(data_list))
            self.conn.commit()
            return True
        except Exception as e:
            if self.conn: self.conn.rollback()
            log_error(f"Помилка при додаванні вступника ({form_type})", e)
            return False
        finally:
            self._close()

    def add_applicant_day(self, data_list):
        return self.add_applicant(data_list, 'day')

    def add_applicant_zaoch(self, data_list):
        return self.add_applicant(data_list, 'zaoch')

    def update_applicant(self, data_list, form_type='day'):
        """Оновлює дані вступника."""
        table = "applicant_personal_data_day" if form_type == 'day' else "applicant_personal_data_evening"
        columns = [
            "first_name", "last_name", "middle_name", "pip", "phone", "citizenship", "cert_number",
            "passport_number", "issued_by", "issue_date", "id_code", "address", "father_first_name",
            "father_last_name", "father_middle_name", "father_job", "father_phone", "mother_first_name",
            "mother_last_name", "mother_middle_name", "mother_phone", "mother_job", "hostel_need",
            "gender", "algebra", "geometry", "ukr_language", "ukr_literature", "school_name",
            "cert_issue_date", "date_birth"
        ]
        set_clause = ", ".join([f"{c} = %s" for c in columns])
        query = f"UPDATE {table} SET {set_clause} WHERE cert_number = %s"
        
        # Переконуємось, що cert_number є в кінці для WHERE
        # Припускаємо, що cert_number це 7-й елемент (індекс 6)
        vals = list(data_list)
        vals.append(data_list[6]) # cert_number для WHERE
        
        try:
            self._connect()
            self.cursor.execute(query, tuple(vals))
            self.conn.commit()
            return True
        except Exception as e:
            if self.conn: self.conn.rollback()
            log_error(f"Помилка при оновленні вступника {data_list[1]} {data_list[0]} у {table}", e)
            return False
        finally:
            self._close()

    def update_applicant_day(self, data_list):
        return self.update_applicant(data_list, 'day')

    def update_applicant_zaoch(self, data_list):
        return self.update_applicant(data_list, 'zaoch')

    def search_applicants_by_specialty(self, specialty_name, form_type='day'):
        """Пошук вступників за спеціальністю з усіма даними (для списків)."""
        pd_table = "applicant_personal_data_day" if form_type == 'day' else "applicant_personal_data_evening"
        os_table = "personal_case_day" if form_type == 'day' else "personal_case_evening"
        pv_table = "applicant_benefits_day" if form_type == 'day' else "applicant_benefits_evening"
        
        query = f"""
        SELECT pd.last_name, pd.first_name, pd.middle_name, os.number_sprava, 
               TO_CHAR(os.date_sprava, 'DD.MM.YYYY') AS date_sprava, pd.phone, 
               pd.passport_number, pd.cert_number, 
               COALESCE(STRING_AGG(DISTINCT pv.kod_pilgi::TEXT, ', '), 'Немає') AS kod_pilgi,
               COALESCE(STRING_AGG(DISTINCT pi.name_pilgi::TEXT, ', '), 'Немає') AS pilgi,
               COALESCE(STRING_AGG(DISTINCT pv.document_pilgi::TEXT, ', '), 'Немає') AS document_pilgi
        FROM {pd_table} AS pd
        JOIN {os_table} AS os ON pd.cert_number = os.cert_number
        LEFT JOIN {pv_table} AS pv ON pd.cert_number = pv.cert_number
        LEFT JOIN benefits AS pi ON pv.kod_pilgi = pi.kod_pilgi
        WHERE os.name_specialnosti = %s
        GROUP BY pd.last_name, pd.first_name, pd.middle_name, os.number_sprava, os.date_sprava, 
                 pd.phone, pd.passport_number, pd.cert_number
        """
        return self.execute_query(query, (specialty_name,))
class BenefitRepository(BaseRepository):
    """Репозиторій для роботи з пільгами вступників."""

    def get_all_benefit_types(self):
        """Повертає всі доступні коди пільг."""
        return self.execute_query("SELECT kod_pilgi, name_pilgi FROM benefits")

    def search_benefits_by_cert(self, cert_number, form_type='day'):
        """Шукає всі пільги вступника за номером свідоцтва (нормалізований пошук)."""
        table = "applicant_benefits_day" if form_type == 'day' else "applicant_benefits_evening"
        # Використовуємо REPLACE для ігнорування пробілів та знаку № при пошуку
        query = f"""
            SELECT * FROM {table} 
            WHERE REPLACE(REPLACE(cert_number, ' ', ''), '№', '') ILIKE %s
        """
        return self.execute_query(query, (f"%{cert_number}%",))

    def add_benefit(self, cert_number, kod_pilgi, document_pilgi, form_type='day'):
        """Додає нову пільгу вступнику."""
        table = "applicant_benefits_day" if form_type == 'day' else "applicant_benefits_evening"
        query = f"""
            INSERT INTO {table} (cert_number, kod_pilgi, document_pilgi)
            VALUES (%s, %s, %s)
        """
        try:
            self._connect()
            self.cursor.execute(query, (cert_number, kod_pilgi, document_pilgi))
            self.conn.commit()
            return True
        except Exception as e:
            if self.conn: self.conn.rollback()
            log_error(f"Помилка при додаванні пільги ({cert_number}, {kod_pilgi}) у {table}", e)
            return False
        finally:
            self._close()

    def update_benefit(self, cert_number, kod_pilgi, document_pilgi, form_type='day'):
        """Оновлює дані існуючої пільги."""
        table = "applicant_benefits_day" if form_type == 'day' else "applicant_benefits_evening"
        query = f"""
            UPDATE {table}
            SET document_pilgi = %s
            WHERE cert_number = %s AND kod_pilgi = %s
        """
        try:
            self._connect()
            self.cursor.execute(query, (document_pilgi, cert_number, kod_pilgi))
            self.conn.commit()
            return True
        except Exception as e:
            if self.conn: self.conn.rollback()
            log_error(f"Помилка при оновленні пільги ({cert_number}, {kod_pilgi}) у {table}", e)
            return False
        finally:
            self._close()

    def delete_benefit(self, cert_number, kod_pilgi, form_type='day'):
        """Видаляє пільгу вступника."""
        table = "applicant_benefits_day" if form_type == 'day' else "applicant_benefits_evening"
        query = f"DELETE FROM {table} WHERE cert_number = %s AND kod_pilgi = %s"
        try:
            self._connect()
            self.cursor.execute(query, (cert_number, kod_pilgi))
            self.conn.commit()
            return True
        except Exception as e:
            if self.conn: self.conn.rollback()
            log_error(f"Помилка при видаленні пільги ({cert_number}, {kod_pilgi}) у {table}", e)
            return False
        finally:
            self._close()
class SecretaryRepository(BaseRepository):
    """Репозиторій для роботи з даними секретарів."""

    def get_secretaries(self, form_type='day'):
        """Повертає список ПІП секретарів для обраної форми."""
        table = "secretaries_day" if form_type == 'day' else "secretaries_evening"
        return self.execute_query(f"SELECT name_secretar FROM {table}")

    def get_secretaries_day(self):
        return self.get_secretaries('day')

    def get_secretary_by_specialty(self, specialty_name, form_type='day'):
        """Повертає секретаря для обраної спеціальності."""
        specialty_table = "specialities_day" if form_type == 'day' else "specialities_evening"
        secretary_table = "secretaries_day" if form_type == 'day' else "secretaries_evening"
        
        query = f"""
            SELECT sec.name_secretar 
            FROM {secretary_table} sec
            JOIN {specialty_table} spec ON sec.kod_specialnosti = spec.kod_specialnosti
            WHERE spec.name_specialnosti = %s
            LIMIT 1
        """
        result = self.execute_query(query, (specialty_name,), fetch_all=False)
        return result[0] if result else None

class CaseRepository(BaseRepository):
    """Репозиторій для роботи з особовими справами вступників."""

    def search_case_by_number_or_cert(self, search_text, is_short_form=False, form_type='day'):
        """Шукає справу за номером або свідоцтвом."""
        if form_type == 'day':
            table = "personal_case_day_scor" if is_short_form else "personal_case_day"
        else:
            table = "personal_case_evening"
            
        # Простий пошук за точним співпадінням спочатку
        query = f"SELECT * FROM {table} WHERE number_sprava = %s OR cert_number = %s"
        return self.execute_query(query, (search_text, search_text), fetch_all=False)

    def add_case(self, data_dict, is_short_form=False, form_type='day'):
        """Додає нову особову справу."""
        if form_type == 'day':
            table = "personal_case_day_scor" if is_short_form else "personal_case_day"
        else:
            table = "personal_case_evening"

        columns = ["number_sprava", "kod_galuzi", "name_specialnosti", "date_sprava", "name_secretar", "finanse", "cert_number"]
        if is_short_form or form_type == 'zaoch':
            columns.append("zno_nmt_checkbox")
        
        placeholders = ", ".join(["%s"] * len(columns))
        col_names = ", ".join(columns)
        query = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
        
        vals = [data_dict.get(c) for c in columns]
        
        try:
            self._connect()
            self.cursor.execute(query, tuple(vals))
            self.conn.commit()
            return True
        except Exception as e:
            if self.conn: self.conn.rollback()
            log_error(f"Помилка при додаванні справи {data_dict.get('number_sprava')} у {table}", e)
            return False
        finally:
            self._close()

    def update_case(self, data_dict, is_short_form=False, form_type='day'):
        """Оновлює дані особової справи."""
        if form_type == 'day':
            table = "personal_case_day_scor" if is_short_form else "personal_case_day"
        else:
            table = "personal_case_evening"

        columns = ["kod_galuzi", "name_specialnosti", "date_sprava", "name_secretar", "finanse", "cert_number"]
        if is_short_form or form_type == 'zaoch':
            columns.append("zno_nmt_checkbox")
        
        set_clause = ", ".join([f"{c} = %s" for c in columns])
        query = f"UPDATE {table} SET {set_clause} WHERE number_sprava = %s"
        
        vals = [data_dict.get(c) for c in columns]
        vals.append(data_dict.get("number_sprava"))
        
        try:
            self._connect()
            self.cursor.execute(query, tuple(vals))
            self.conn.commit()
            return True
        except Exception as e:
            if self.conn: self.conn.rollback()
            log_error(f"Помилка при оновленні справи {data_dict.get('number_sprava')} у {table}", e)
            return False
        finally:
            self._close()

class InstitutionRepository(BaseRepository):
    """Репозиторій для роботи з даними навчального закладу."""

    def get_info(self):
        """Повертає інформацію про заклад."""
        return self.execute_query("SELECT * FROM institution_info", fetch_all=False)

    def update_info(self, data_dict):
        """Оновлює інформацію про заклад."""
        columns = ["full_name", "short_name", "address", "director_name", "contact_phone", "logo_path"]
        set_clause = ", ".join([f"{c} = %s" for c in columns])
        query = f"UPDATE institution_info SET {set_clause} WHERE id = 1" # Assuming one record
        
        vals = [data_dict.get(c) for c in columns]
        try:
            self._connect()
            self.cursor.execute(query, tuple(vals))
            self.conn.commit()
            return True
        except Exception as e:
            if self.conn: self.conn.rollback()
            log_error("Помилка оновлення даних закладу", e)
            return False
        finally:
            self._close()

class SettingsRepository(BaseRepository):
    """Репозиторій для роботи з системними налаштуваннями."""

    def get_all_settings(self):
        """Повертає всі налаштування у вигляді словника."""
        rows = self.execute_query("SELECT key, value FROM settings")
        return {row[0]: row[1] for row in rows}

    def get_setting(self, key, default=None):
        """Повертає значення конкретного налаштування."""
        from db.connect_db import get_setting
        return get_setting(key, default)

    def set_setting(self, key, value):
        """Оновлює або додає налаштування."""
        query = "INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
        try:
            self._connect()
            self.cursor.execute(query, (key, str(value)))
            self.conn.commit()
            return True
        except Exception as e:
            if self.conn: self.conn.rollback()
            log_error(f"Помилка встановлення налаштування '{key}'", e)
            return False
        finally:
            self._close()
