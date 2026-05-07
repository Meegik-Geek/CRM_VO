from pages.admin.reports.report_utils import BaseReportPage
from pages.admin.reports.reports_druk_denne import DocumentPrinter
from utils.notifications import show_success, show_error

class AdminJournalCamp(BaseReportPage):
    """Сторінка 'Журнали вступної кампанії' з дворівневою навігацією."""
    def __init__(self, category=None):
        super().__init__("Журнали вступної кампанії", "Друк журналів")
        self.document_printer = DocumentPrinter(self.show_success_message, self.show_error_message)
        self.init_ui_components()

    def init_ui_components(self):
        # 1. Сині кнопки (навігація)
        nav_buttons = [
            ("Журнал реєстрації вступників", "registr"),
            ("Алфавітний журнал вступників", "alfavit"),
            ("Журнал спеціальних умов", "spec_umovi"),
            ("Журнал звіт (пільги, оцінки)", "spec_zvit"),
            ("Експорт даних вступників", "export"),
            ("Журнал скасованих справ", "cancelled"),
        ]
        self.add_navigation_buttons(nav_buttons)

        # 2. Зелені кнопки (дії) з описами
        self.set_general_description("Оберіть потрібний журнал, щоб переглянути його призначення та сформувати документ.")

        self.add_action_button("registr", "Друк журналу реєстрації", self.registr_vstupnik_page,
                               "Основний журнал реєстрації всіх заяв вступників. Містить інформацію про дату подачі, ПІБ, спеціальність та номер особової справи.")
        self.add_action_button("alfavit", "Друк алфавітного журналу", self.alfavit_vstupnik_page,
                               "Список усіх вступників, впорядкований за алфавітом. Зручний для швидкого пошуку абітурієнта та перевірки його даних.")
        self.add_action_button("spec_umovi", "Друк журналу спец. умов", self.spec_umovi_vstupnik_page,
                               "Журнал реєстрації вступників, які мають спеціальні умови вступу (пільги, квоти). Використовується для контролю за категоріями пільговиків.")
        self.add_action_button("spec_zvit", "Друк журналу пільги/оцінки", self.spec_zvit_vstupnik_page,
                               "Детальний звіт, що містить інформацію про пільги, оцінки за вступні випробування та середній бал атестата.")
        self.add_action_button("export", "Виконати експорт даних", self.export_date_vstupnik_page,
                               "Повний експорт усіх даних вступників у формат Word. Документ містить розгорнуту інформацію про кожного абітурієнта.")
        self.add_action_button("cancelled", "Експорт скасованих справ", self.cancelled_cases_page,
                               "Журнал справ, які були офіційно скасовані (відкликані) вступниками. Містить причину та дату скасування.")

    def registr_vstupnik_page(self):
        self.document_printer.print_registr_vstupnik_page()

    def alfavit_vstupnik_page(self):
        self.document_printer.print_alfavit_vstupnik_page()

    def spec_umovi_vstupnik_page(self):
        self.document_printer.print_spec_umovi_vstupnik_page()

    def spec_zvit_vstupnik_page(self):
        self.show_print_dialog(
            "Друк звіту вступників (пільги, оцінки)",
            self.handle_spec_zvit_vstupnik_print,
            [{"type": "combo", "label": "Форма навчання", "name": "Форма навчання"}]
        )

    def handle_spec_zvit_vstupnik_print(self, dialog):
        fields = dialog.get_field_values()
        study_form = fields['Форма навчання']
        if not study_form:
            show_error(self, "Будь ласка, виберіть форму навчання.")
            return
        self.document_printer.print_spec_zvit_vstupnik_page(study_form, dialog)

    def export_date_vstupnik_page(self):
        self.document_printer.print_export_date_vstupnik()

    def cancelled_cases_page(self):
        self.document_printer.print_cancelled_cases_journal()

    def show_error_message(self, message):
        show_error(self, message)

    def show_success_message(self, message):
        show_success(self, message)
