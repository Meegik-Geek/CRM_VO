from pages.admin.reports.report_utils import BaseReportPage
from pages.admin.reports.reports_druk_denne import DocumentPrinter
from utils.notifications import show_success, show_error

class AdminZvitCamp(BaseReportPage):
    """Сторінка 'Звіти вступної кампанії' з дворівневою навігацією."""
    def __init__(self, category=None):
        super().__init__("Звіти вступної кампанії", "Друк звітів")
        self.document_printer = DocumentPrinter(self.show_success_message, self.show_error_message)
        self.init_ui_components()

    def init_ui_components(self):
        # 1. Сині кнопки (навігація)
        nav_buttons = [
            # 1. Результати випробувань
            ("Результати вступних випробувань (денна)", "results_exams_denne"),
            ("Результати вступних випробувань (денна скорочена)", "results_exams_denne_skor"),
            ("Результати вступних випробувань (заочна)", "results_exams_zaochna"),
            
            # 2. Ранжування мотиваційних листів
            ("Результати ранжування мот. листів (денна)", "results_motivation_denne"),
            ("Результати ранжування мот. листів (денна скорочена)", "results_motivation_denne_skor"),
            ("Результати ранжування мот. листів (заочна)", "results_motivation_zaochna"),

            # 3. Ранжування за середнім балом
            ("Результати ранжування серед. бал (денна)", "results_gpa_denne"),
            ("Результати ранжування серед. бал (денна скорочена)", "results_gpa_denne_skor"),
            ("Результати ранжування серед. бал (заочна)", "results_gpa_zaochna"),

            # 4. Рейтингові списки
            ("Рейтингові списки вступників (денна)", "rating_lists_denne"),
            ("Рейтингові списки вступників (денна скорочена)", "rating_lists_denne_skor"),
            ("Рейтингові списки вступників (заочна)", "rating_lists_zaochna"),
        ]
        self.add_navigation_buttons(nav_buttons)

        # 2. Зелені кнопки (дії) з описами
        self.set_general_description("Оберіть категорію звіту у списку вище, щоб переглянути деталі та роздрукувати документ.")

        desc_exams = "Звіт містить результати вступних випробувань (співбесід або іспитів). Використовується для фіксації оцінок вступників за обраною спеціальністю."
        self.add_action_button("results_exams_denne", "Друк результатів випробувань (денна)", 
                               lambda: self.print_results_exams_dialog("day"), desc_exams)
        self.add_action_button("results_exams_denne_skor", "Друк результатів випробувань (скорочена)", 
                               lambda: self.print_results_exams_dialog("day_scor"), desc_exams)
        self.add_action_button("results_exams_zaochna", "Друк результатів випробувань (заочна)", 
                               lambda: self.print_results_exams_dialog("evening"), desc_exams)
        
        # Ранжування мотиваційних листів
        desc_motivation = "Документ містить список вступників з однаковими балами, відсортований за пріоритетністю їхніх мотиваційних листів. Допомагає визначити черговість при однаковому конкурсному балі."
        self.add_action_button("results_motivation_denne", "Друк ранжування (денна)", 
                               lambda: self.print_motivation_ranking_dialog("day"), desc_motivation)
        self.add_action_button("results_motivation_denne_skor", "Друк ранжування (скорочена)", 
                               lambda: self.print_motivation_ranking_dialog("day_scor"), desc_motivation)
        self.add_action_button("results_motivation_zaochna", "Друк ранжування (заочна)", 
                               lambda: self.print_motivation_ranking_dialog("evening"), desc_motivation)
        
        # Ранжування за середнім балом (нове)
        desc_gpa = "Звіт для вирішення спірних ситуацій: містить вступників з однаковими балами, відсортованих за середнім балом атестата (GPA) та датою подачі документів."
        self.add_action_button("results_gpa_denne", "Друк ранжування сер. бал (денна)", 
                               lambda: self.print_gpa_ranking_dialog("day"), desc_gpa)
        self.add_action_button("results_gpa_denne_skor", "Друк ранжування сер. бал (скорочена)", 
                               lambda: self.print_gpa_ranking_dialog("day_scor"), desc_gpa)
        self.add_action_button("results_gpa_zaochna", "Друк ранжування сер. бал (заочна)", 
                               lambda: self.print_gpa_ranking_dialog("evening"), desc_gpa)

        # Рейтингові списки
        desc_rating = "Підсумковий рейтинговий список усіх вступників на спеціальність. Враховує пільги, результати іспитів та середній бал. Кольором виділені особи, що рекомендуються до зарахування (Бюджет/Контракт)."
        self.add_action_button("rating_lists_denne", "Друк рейтингів (денна)", 
                               lambda: self.print_rating_list_dialog("day"), desc_rating)
        self.add_action_button("rating_lists_denne_skor", "Друк рейтингів (скорочена)", 
                               lambda: self.print_rating_list_dialog("day_scor"), desc_rating)
        self.add_action_button("rating_lists_zaochna", "Друк рейтингів (заочна)", 
                               lambda: self.print_rating_list_dialog("evening"), desc_rating)

    def print_results_exams_dialog(self, form_type):
        """Показ діалогу для результатів іспитів."""
        source_table = "specialities_day"
        if form_type == "evening":
            source_table = "specialities_evening"
            
        self.show_print_dialog(
            "Параметри друку результатів випробувань",
            lambda dialog: self.handle_results_print(dialog, form_type),
            [{"type": "combo", "label": "Назва спеціальності", "name": "Назва спеціальності", "source_table": source_table},
             {"type": "number", "label": "Кількість людей в групі (необов'язково)", "name": "Кількість людей в групі"}]
        )

    def print_motivation_ranking_dialog(self, form_type):
        """Показ діалогу для ранжування мотиваційних листів."""
        source_table = "specialities_day"
        if form_type == "evening":
            source_table = "specialities_evening"
            
        self.show_print_dialog(
            "Параметри друку ранжування мотиваційних листів",
            lambda dialog: self.document_printer.print_motivation_ranking_all_forms(
                dialog.get_field_values().get('Назва спеціальності'),
                form_type, 
                dialog
            ),
            [{"type": "combo", "label": "Назва спеціальності", "name": "Назва спеціальності", "source_table": source_table}]
        )

    def print_rating_list_dialog(self, form_type):
        """Показ діалогу для рейтингових списків."""
        source_table = "specialities_day"
        if form_type == "evening":
            source_table = "specialities_evening"
            
        self.show_print_dialog(
            "Параметри друку рейтингового списку",
            lambda dialog: self.document_printer.print_rating_list_all_forms(
                dialog.get_field_values().get('Назва спеціальності'),
                form_type, 
                dialog
            ),
            [{"type": "combo", "label": "Назва спеціальності", "name": "Назва спеціальності", "source_table": source_table}]
        )

    def print_gpa_ranking_dialog(self, form_type):
        """Показ діалогу для ранжування за середнім балом."""
        source_table = "specialities_day"
        if form_type == "evening":
            source_table = "specialities_evening"
            
        self.show_print_dialog(
            "Параметри друку ранжування за середнім балом",
            lambda dialog: self.document_printer.print_gpa_ranking_all_forms(
                dialog.get_field_values().get('Назва спеціальності'),
                form_type, 
                dialog
            ),
            [{"type": "combo", "label": "Назва спеціальності", "name": "Назва спеціальності", "source_table": source_table}]
        )

    def handle_results_print(self, dialog, form_type):
        fields = dialog.get_field_values()
        specialty_name = fields.get('Назва спеціальності')
        group_size_input = fields.get("Кількість людей в групі", "").strip()
        
        group_size = 0
        if group_size_input:
            try:
                group_size = int(group_size_input)
            except ValueError:
                show_error(self, "Некоректний формат кількості людей.")
                return

        self.document_printer.print_results_exams_all_forms(specialty_name, group_size, form_type, dialog)

    def show_error_message(self, message):
        show_error(self, message)

    def show_success_message(self, message):
        show_success(self, message)
