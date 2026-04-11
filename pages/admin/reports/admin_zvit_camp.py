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
            ("Результати вступних випробувань (денна)", "results_exams_denne"),
            ("Результати ранжування мот. листів (денна)", "results_motivation_denne"),
            ("Рейтингові списки вступників (денна)", "rating_lists_denne"),
            ("Результати вступних випробувань (денна скорочена)", "results_exams_denne_skor"),
            ("Результати ранжування мот. листів (денна скорочена)", "results_motivation_denne_skor"),
            ("Рейтингові списки вступників (денна скорочена)", "rating_lists_denne_skor"),
            ("Результати вступних випробувань (заочна)", "results_exams_zaochna"),
            ("Результати ранжування мот. листів (заочна)", "results_motivation_zaochna"),
            ("Рейтингові списки вступників (заочна)", "rating_lists_zaochna"),
        ]
        self.add_navigation_buttons(nav_buttons)

        # 2. Зелені кнопки (дії)
        self.add_action_button("results_exams_denne", "Друк результатів випробувань (денна)", 
                               lambda: self.print_results_exams_dialog("day"))
        self.add_action_button("results_exams_denne_skor", "Друк результатів випробувань (скорочена)", 
                               lambda: self.print_results_exams_dialog("day_scor"))
        self.add_action_button("results_exams_zaochna", "Друк результатів випробувань (заочна)", 
                               lambda: self.print_results_exams_dialog("evening"))
        
        # Ранжування мотиваційних листів
        self.add_action_button("results_motivation_denne", "Друк ранжування (денна)", 
                               lambda: self.print_motivation_ranking_dialog("day"))
        self.add_action_button("results_motivation_denne_skor", "Друк ранжування (скорочена)", 
                               lambda: self.print_motivation_ranking_dialog("day_scor"))
        self.add_action_button("results_motivation_zaochna", "Друк ранжування (заочна)", 
                               lambda: self.print_motivation_ranking_dialog("evening"))
        
        # Рейтингові списки (нове)
        self.add_action_button("rating_lists_denne", "Друк рейтингів (денна)", 
                               lambda: self.print_rating_list_dialog("day"))
        self.add_action_button("rating_lists_denne_skor", "Друк рейтингів (скорочена)", 
                               lambda: self.print_rating_list_dialog("day_scor"))
        self.add_action_button("rating_lists_zaochna", "Друк рейтингів (заочна)", 
                               lambda: self.print_rating_list_dialog("evening"))

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
