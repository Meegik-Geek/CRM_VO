from pages.admin.reports.report_utils import BaseReportPage
from pages.admin.reports.reports_druk_denne import DocumentPrinter
from utils.notifications import show_success, show_error
from datetime import datetime

class AdminProtocolCamp(BaseReportPage):
    """Сторінка 'Протоколи/Допуски вступної кампанії' з дворівневою навігацією."""
    def __init__(self, category=None):
        super().__init__("Протоколи/Допуски вступної кампанії", "Друк протоколів та допусків")
        self.document_printer = DocumentPrinter(self.show_success_message, self.show_error_message)
        self.init_ui_components()

    def init_ui_components(self):
        # 1. Сині кнопки (навігація)
        nav_buttons = [
            ("Додатки для протоколів", "dodatki"),
            ("Допуск (денна)", "dopusk_day"),
            ("Допуск (денна скорочена)", "dopusk_scor"),
            ("Допуск (заочне)", "dopusk_zaoch"),
        ]
        self.add_navigation_buttons(nav_buttons)

        # 2. Зелені кнопки (дії) з описами
        self.set_general_description("Оберіть тип документа для перегляду опису та подальшого друку.")

        self.add_action_button("dodatki", "Друк додатків до протоколів", self.dodatki_protokol_denne_page,
                               "Формування переліку вступників за обраний період для включення до протоколів засідань приймальної комісії.")
        
        desc_dopusk = "Офіційний лист допуску вступників до складання вступних випробувань. Містить список абітурієнтів, розбитих на групи за спеціальностями."
        self.add_action_button("dopusk_day", "Друк допуску (денна)", self.print_dopusk_page, desc_dopusk)
        self.add_action_button("dopusk_scor", "Друк допуску (скорочена)", self.print_dopusk_scor_page, desc_dopusk)
        self.add_action_button("dopusk_zaoch", "Друк допуску (заочне)", self.print_dopusk_zaoch_page, desc_dopusk)

    def print_dopusk_page(self):
        self.show_print_dialog(
            "Друк допуску до вступних випробувань",
            lambda dialog: self.handle_print(dialog, self.document_printer.print_dopusk_page),
            [{"type": "combo", "label": "Назва спеціальності", "name": "Назва спеціальності"},
             {"type": "number", "label": "Кількість людей в групі", "name": "Кількість людей в групі"}]
        )

    def print_dopusk_scor_page(self):
        self.show_print_dialog(
            "Друк допуску до вступних випробувань (денна) скорочена",
            lambda dialog: self.handle_print(dialog, self.document_printer.print_dopusk_scor_page),
            [{"type": "combo", "label": "Назва спеціальності", "name": "Назва спеціальності"},
             {"type": "number", "label": "Кількість людей в групі", "name": "Кількість людей в групі"}]
        )

    def print_dopusk_zaoch_page(self):
        self.show_print_dialog(
            "Друк допуску до вступних випробувань (заочне)",
            lambda dialog: self.handle_print(dialog, self.document_printer.print_dopusk_zaoch_page),
            [{"type": "combo", "label": "Назва спеціальності", "name": "Назва спеціальності", "source_table": "specialities_evening"},
             {"type": "number", "label": "Кількість людей в групі", "name": "Кількість людей в групі"}]
        )

    def dodatki_protokol_denne_page(self):
        self.show_print_dialog(
            "Друк додатків до протоколів (денна)",
            self.handle_dodatki_protokol_denne_print,
            [{"type": "text", "label": "Початкова дата", "name": "Початкова дата", "placeholder": "dd.mm.yyyy"},
             {"type": "text", "label": "Кінцева дата", "name": "Кінцева дата", "placeholder": "dd.mm.yyyy"}]
        )

    def handle_dodatki_protokol_denne_print(self, dialog):
        fields = dialog.get_field_values()
        start_date = fields['Початкова дата']
        end_date = fields['Кінцева дата']
        try:
            start_date_obj = datetime.strptime(start_date, '%d.%m.%Y').date()
            end_date_obj = datetime.strptime(end_date, '%d.%m.%Y').date()
            if start_date_obj > end_date_obj:
                raise ValueError("Початкова дата не може бути пізніше кінцевої дати.")
            start_date = start_date_obj.strftime('%Y-%m-%d')
            end_date = end_date_obj.strftime('%Y-%m-%d')
        except ValueError as e:
            show_error(self, f"Помилка введення дат: {str(e)}")
            return
        self.document_printer.print_dodatki_protokol_denne_page(start_date, end_date, dialog)

    def handle_print(self, dialog, print_method):
        fields = dialog.get_field_values()
        specialty_name = fields.get('Назва спеціальності')
        group_size_input = fields.get('Кількість людей в групі', '').strip()
        group_size = None
        if group_size_input:
            try:
                group_size = int(group_size_input)
            except ValueError:
                show_error(self, "Некоректне значення для 'Кількість людей в групі'. Введіть ціле число.")
                return
        print_method(specialty_name, group_size, dialog)

    def show_error_message(self, message):
        show_error(self, message)

    def show_success_message(self, message):
        show_success(self, message)
