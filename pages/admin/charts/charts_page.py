from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from pages.admin.reports.report_utils import BaseReportPage
from pages.admin.charts.apps_chart_window import AppsChartWindow
from pages.admin.charts.daily_chart_window import DailyChartWindow

# Глобальний список для зберігання посилань на вікна графіків
# Це не дозволить Python закривати вікна при переході між пунктами меню
opened_charts = []

class ChartsPage(BaseReportPage):
    def __init__(self):
        super().__init__("Аналітичні графіки", "Аналітичні графіки")
        self.init_charts_ui()

    def init_charts_ui(self):
        self.set_general_description("Оберіть тип графіка для візуалізації даних вступної кампанії.")
        
        # Сині кнопки навігації
        self.add_navigation_buttons([
            ("Заяви за спеціальностями", "apps_chart"),
            ("Заяви за останні 5 днів", "daily_chart"),
        ])
        
        # Секції дій
        self.add_action_button(
            key="apps_chart",
            text="Відкрити графік",
            handler=self.open_apps_chart,
            description=(
                "Графік відображає кількість поданих заяв по кожній спеціальності.\n"
                "Окремі стовпці для денної, скороченої та заочної форм навчання.\n\n"
                "Відкривається в окремому вікні з автооновленням."
            )
        )
        
        self.add_action_button(
            key="daily_chart",
            text="Відкрити графік",
            handler=self.open_daily_chart,
            description=(
                "Лінійний графік показує динаміку подання заяв за останні 5 днів.\n"
                "Дані включають усі форми навчання (денна, скорочена, заочна).\n\n"
                "Відкривається в окремому вікні з автооновленням."
            )
        )

    def open_apps_chart(self):
        """Відкриває вікно з графіком за спеціальностями."""
        global opened_charts
        try:
            w = AppsChartWindow()
            w.show()
            opened_charts.append(w)
            opened_charts = [c for c in opened_charts if c.isVisible()]
        except Exception as e:
            from utils.notifications import show_error
            show_error(self, f"Помилка: {e}")

    def open_daily_chart(self):
        """Відкриває вікно з графіком за останні 5 днів."""
        global opened_charts
        try:
            w = DailyChartWindow()
            w.show()
            opened_charts.append(w)
            opened_charts = [c for c in opened_charts if c.isVisible()]
        except Exception as e:
            from utils.notifications import show_error
            show_error(self, f"Помилка: {e}")
