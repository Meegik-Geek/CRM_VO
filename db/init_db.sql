-- Повна схема бази даних системи «Вступ 2026»
-- Включає основні таблиці та таблиці для забезпечення автономності проєкту

-- 1. СИСТЕМНІ ТАБЛИЦІ ТА НАЛАШТУВАННЯ
CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR(50) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS institution_info (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    short_name VARCHAR(100),
    address TEXT,
    director_name TEXT,
    contact_phone VARCHAR(20),
    logo_path TEXT
);

-- 2. ДОВІДНИКИ (Генералізовані)

-- Галузі знань
CREATE TABLE IF NOT EXISTS knowledge_field (
    id SERIAL PRIMARY KEY,
    kod_galuzi VARCHAR(20) UNIQUE,
    name_galuzi TEXT
);

-- Пільги (загальні)
CREATE TABLE IF NOT EXISTS benefits (
    id SERIAL PRIMARY KEY,
    kod_pilgi VARCHAR(20) UNIQUE,
    name_pilgi TEXT,
    type_pilgi VARCHAR(100),
    bal NUMERIC(5,2)
);

-- Спеціальності (Денна форма)
CREATE TABLE IF NOT EXISTS specialities_day (
    id SERIAL PRIMARY KEY,
    kod_specialnosti VARCHAR(20),
    kod_galuzi VARCHAR(20),
    name_specialnosti TEXT,
    licensed_volume INTEGER DEFAULT 0,
    state_places INTEGER DEFAULT 0
);

-- Спеціальності (Заочна/Вечірня форма)
CREATE TABLE IF NOT EXISTS specialities_evening (
    id SERIAL PRIMARY KEY,
    kod_specialnosti VARCHAR(20),
    kod_galuzi VARCHAR(20),
    name_specialnosti TEXT,
    licensed_volume INTEGER DEFAULT 0,
    state_places INTEGER DEFAULT 0
);

-- Секретарі
CREATE TABLE IF NOT EXISTS secretaries_day (
    id SERIAL PRIMARY KEY,
    name_secretar TEXT,
    kod_specialnosti VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS secretaries_evening (
    id SERIAL PRIMARY KEY,
    name_secretar TEXT,
    kod_specialnosti VARCHAR(20)
);

-- 3. ПЕРСОНАЛЬНІ ДАНІ ВСТУПНИКІВ

CREATE TABLE IF NOT EXISTS applicant_personal_data_day (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    middle_name VARCHAR(100),
    pip TEXT, -- ПІП у родовому відмінку для документів
    phone VARCHAR(20),
    citizenship VARCHAR(100),
    cert_number VARCHAR(50) UNIQUE,
    passport_number VARCHAR(50),
    issued_by TEXT,
    issue_date VARCHAR(20),
    id_code VARCHAR(20),
    address TEXT,
    father_first_name VARCHAR(100),
    father_last_name VARCHAR(100),
    father_middle_name VARCHAR(100),
    father_job TEXT,
    father_phone VARCHAR(20),
    mother_first_name VARCHAR(100),
    mother_last_name VARCHAR(100),
    mother_middle_name VARCHAR(100),
    mother_phone VARCHAR(20),
    mother_job TEXT,
    hostel_need VARCHAR(10),
    gender VARCHAR(20),
    algebra VARCHAR(10),
    geometry VARCHAR(10),
    ukr_language VARCHAR(10),
    ukr_literature VARCHAR(10),
    school_name TEXT,
    cert_issue_date VARCHAR(20),
    date_birth VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS applicant_personal_data_evening (
    LIKE applicant_personal_data_day INCLUDING ALL
);

-- Пільги вступників
CREATE TABLE IF NOT EXISTS applicant_benefits_day (
    id SERIAL PRIMARY KEY,
    cert_number VARCHAR(50) REFERENCES applicant_personal_data_day(cert_number),
    kod_pilgi VARCHAR(20) REFERENCES benefits(kod_pilgi),
    document_pilgi TEXT
);

CREATE TABLE IF NOT EXISTS applicant_benefits_evening (
    id SERIAL PRIMARY KEY,
    cert_number VARCHAR(50) REFERENCES applicant_personal_data_evening(cert_number),
    kod_pilgi VARCHAR(20) REFERENCES benefits(kod_pilgi),
    document_pilgi TEXT
);

-- 4. ОСОБОВІ СПРАВИ ТА ПРОЦЕС ВСТУПУ

CREATE TABLE IF NOT EXISTS personal_case_day (
    id SERIAL PRIMARY KEY,
    number_sprava VARCHAR(50) UNIQUE,
    kod_galuzi VARCHAR(20),
    name_specialnosti TEXT,
    date_sprava DATE,
    name_secretar TEXT,
    finanse VARCHAR(50),
    cert_number VARCHAR(50) REFERENCES applicant_personal_data_day(cert_number),
    is_cancelled BOOLEAN DEFAULT FALSE  -- Скасована заява
);

CREATE TABLE IF NOT EXISTS personal_case_day_scor (
    id SERIAL PRIMARY KEY,
    number_sprava VARCHAR(50) UNIQUE,
    kod_galuzi VARCHAR(20),
    name_specialnosti TEXT,
    date_sprava DATE,
    name_secretar TEXT,
    finanse VARCHAR(50),
    cert_number VARCHAR(50) REFERENCES applicant_personal_data_day(cert_number),
    zno_nmt_checkbox VARCHAR(10), -- "true"/"false" для сумісності з поточним кодом
    is_cancelled BOOLEAN DEFAULT FALSE  -- Скасована заява
);

CREATE TABLE IF NOT EXISTS personal_case_evening (
    id SERIAL PRIMARY KEY,
    number_sprava VARCHAR(50) UNIQUE,
    kod_galuzi VARCHAR(20),
    name_specialnosti TEXT,
    date_sprava DATE,
    name_secretar TEXT,
    finanse VARCHAR(50),
    cert_number VARCHAR(50) REFERENCES applicant_personal_data_evening(cert_number),
    zno_nmt_checkbox VARCHAR(10),
    is_cancelled BOOLEAN DEFAULT FALSE  -- Скасована заява
);

-- Вступні випробування (Екзамени)
CREATE TABLE IF NOT EXISTS entrance_examinations_day (
    id SERIAL PRIMARY KEY,
    name_specialnosti TEXT,
    type_examen TEXT,
    date_examen DATE,
    time_examen VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS entrance_examinations_day_scor (
    LIKE entrance_examinations_day INCLUDING ALL
);

CREATE TABLE IF NOT EXISTS entrance_examinations_evening (
    LIKE entrance_examinations_day INCLUDING ALL
);

-- Бали за вступні випробування
CREATE TABLE IF NOT EXISTS entrance_scores (
    number_sprava VARCHAR(50) PRIMARY KEY,
    score NUMERIC(5,2),
    status VARCHAR(50) DEFAULT 'З’явився',
    motivation_rank INTEGER
);

-- 5. СТУДЕНТИ (Результат зарахування)
CREATE TABLE IF NOT EXISTS student (
    id SERIAL PRIMARY KEY,
    number_sprava_day VARCHAR(50),
    number_sprava_evening VARCHAR(50),
    number_sprava_day_scor VARCHAR(50),
    cert_number VARCHAR(50),
    name_specialnosti TEXT,
    group_number VARCHAR(50),
    finanse VARCHAR(50)
);

-- 6. ПОЧАТКОВІ ДАНІ (SEED DATA)

INSERT INTO settings (key, value, description) VALUES 
('college_name', 'Назва вашого навчального закладу', 'Використовується в заголовках програми та звітах'),
('current_version', '1.0.0', 'Версія ПЗ'),
('update_source', 'https://example.com/updates', 'Шлях до сервера оновлень'),
('backup_path', 'C:\\Vstup_Backups', 'Шлях до папки для резервних копій БД'),
('backup_frequency', 'daily', 'Частота бекапу (3h, daily, weekly, off)'),
('backup_time', '00:00', 'Час щоденного бекапу (HH:MM)'),
('backup_last_run', '', 'Дата останнього успішного запуску бекапу'),
('global_latest_version', '1.0.0-0', 'Глобальна версія системи на GitHub'),
('admin_approved_version', '1.0.0-0', 'Версія, яку затвердив адміністратор'),
('update_delivery_method', 'NONE', 'Як роздавати: LOCAL, INTERNET, NONE'),
('update_path', '', 'Шлях для оновлення (UNC папка сервера або URL-посилання)');

INSERT INTO institution_info (full_name, short_name) VALUES 
('Ваш навчальний заклад', 'ВНЗ');


