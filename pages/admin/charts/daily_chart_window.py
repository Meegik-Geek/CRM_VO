from datetime import datetime, timedelta
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer

try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from db.connect_db import setup_database, close_database

WINDOW_STYLE = """
    QMainWindow { background-color: #1a1a2e; }
    QWidget#centralWidget { background-color: #1a1a2e; }
    QLabel#chartTitle {
        color: #e0e0e0; font-size: 22px; font-weight: bold; padding: 12px;
    }
    QLabel#statusLabel {
        color: #7f8c8d; font-size: 12px; padding: 4px 12px;
    }
    QPushButton#refreshBtn {
        background-color: #3498db; color: white; border: none;
        border-radius: 6px; font-size: 13px; font-weight: bold; padding: 8px 20px;
    }
    QPushButton#refreshBtn:hover { background-color: #2980b9; }
    QPushButton#closeBtn {
        background-color: #44475a; color: #bbb; border: none;
        border-radius: 6px; font-size: 13px; padding: 8px 20px;
    }
    QPushButton#closeBtn:hover { background-color: #5a5e78; color: white; }
"""


class DailyChartWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Динаміка подання заяв за останні 5 днів")
        self.resize(900, 600)
        self.setMinimumSize(700, 450)
        self.setStyleSheet(WINDOW_STYLE)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(16, 8, 16, 12)

        # Заголовок
        self.title_label = QLabel("Подані заяви за останні 5 днів")
        self.title_label.setObjectName("chartTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.title_label)

        # Нижня панель (ДО update_chart)
        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 4, 0, 0)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        bottom.addWidget(self.status_label)
        bottom.addStretch()

        self.btn_refresh = QPushButton("⟳ Оновити")
        self.btn_refresh.setObjectName("refreshBtn")
        self.btn_refresh.setFixedHeight(36)
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        bottom.addWidget(self.btn_refresh)

        self.btn_close = QPushButton("Закрити")
        self.btn_close.setObjectName("closeBtn")
        self.btn_close.setFixedHeight(36)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.close)
        bottom.addWidget(self.btn_close)

        # Графік
        if HAS_MATPLOTLIB:
            self.figure = Figure(facecolor='#1a1a2e')
            self.canvas = FigureCanvas(self.figure)
            self.main_layout.addWidget(self.canvas, stretch=1)

            self.btn_refresh.clicked.connect(self.update_chart)

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_chart)
            self.timer.start(60_000)

            self.update_chart()
        else:
            err = QLabel("Бібліотека matplotlib не встановлена.\n\npip install matplotlib")
            err.setAlignment(Qt.AlignCenter)
            err.setStyleSheet("color: #e74c3c; font-size: 16px; font-weight: bold;")
            self.main_layout.addWidget(err)

        self.main_layout.addLayout(bottom)

    # ─────────────────────── Дані ───────────────────────
    def get_data(self):
        """Збирає кількість заяв за останні 5 днів з усіх таблиць."""
        # Готуємо словник з нулями для останніх 5 днів
        today = datetime.now().date()
        days = {}
        for i in range(4, -1, -1):  # від 4 днів тому до сьогодні
            d = today - timedelta(days=i)
            days[d] = 0

        conn = setup_database()
        if not conn:
            return days

        try:
            cursor = conn.cursor()

            tables = ["personal_case_day", "personal_case_day_scor", "personal_case_evening"]
            start_date = today - timedelta(days=4)

            for table in tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = %s
                    )
                """, (table,))
                if not cursor.fetchone()[0]:
                    continue

                cursor.execute(f"""
                    SELECT date_sprava::date AS day, COUNT(*)
                    FROM public.{table}
                    WHERE is_cancelled = FALSE
                      AND date_sprava::date >= %s
                    GROUP BY day
                    ORDER BY day
                """, (start_date,))

                for day, count in cursor.fetchall():
                    if day in days:
                        days[day] += count

            cursor.close()
        except Exception:
            pass
        finally:
            close_database(conn)

        return days

    # ─────────────────────── Графік ───────────────────────
    def update_chart(self):
        if not HAS_MATPLOTLIB:
            return

        data = self.get_data()

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#1a1a2e')

        dates = list(data.keys())
        values = list(data.values())

        if not any(values):
            ax.text(0.5, 0.5, "Немає даних за останні 5 днів",
                    ha='center', va='center', fontsize=16, color='#7f8c8d')
            ax.axis('off')
            self.canvas.draw()
            return

        # Лінійний графік з точками
        ax.plot(dates, values, color='#3498db', linewidth=3, marker='o',
                markersize=10, markerfacecolor='#2ecc71', markeredgecolor='white',
                markeredgewidth=2, zorder=5)

        # Заливка під лінією
        ax.fill_between(dates, values, alpha=0.15, color='#3498db')

        # Цифри над точками
        for d, v in zip(dates, values):
            ax.annotate(f'{v}',
                        xy=(d, v), xytext=(0, 14),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=14, fontweight='bold', color='#ecf0f1')

        # Підписи дат
        ax.set_xticks(dates)
        ax.set_xticklabels([d.strftime("%d.%m") for d in dates],
                           fontsize=12, color='#bdc3c7')

        # Прибираємо шкалу Y та рамки
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#44475a')
        ax.spines['left'].set_visible(False)
        ax.tick_params(bottom=False)

        # Відступ зверху для цифр
        if max(values) > 0:
            ax.set_ylim(0, max(values) * 1.3)

        self.figure.tight_layout()
        self.canvas.draw()

        # Статус
        now = datetime.now().strftime("%H:%M:%S")
        total = sum(values)
        self.status_label.setText(f"Всього за 5 днів: {total}  ·  Оновлено о {now}  ·  Авто-оновлення: 60 сек")
