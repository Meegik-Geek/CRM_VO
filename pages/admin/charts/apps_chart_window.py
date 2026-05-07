import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# Спробуємо імпортувати matplotlib
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from db.connect_db import setup_database, close_database

# Палітра кольорів для форм навчання
FORM_COLORS = {
    "(денна)": "#3498db",   # Синій
    "(скр.)":  "#e67e22",   # Оранжевий
    "(заочна)": "#2ecc71",  # Зелений
}
FORM_COLORS_DEFAULT = "#9b59b6"  # Фіолетовий (якщо форма невідома)

WINDOW_STYLE = """
    QMainWindow {
        background-color: #1a1a2e;
    }
    QWidget#centralWidget {
        background-color: #1a1a2e;
    }
    QLabel#chartTitle {
        color: #e0e0e0;
        font-size: 22px;
        font-weight: bold;
        padding: 12px;
    }
    QLabel#statusLabel {
        color: #7f8c8d;
        font-size: 12px;
        padding: 4px 12px;
    }
    QPushButton#refreshBtn {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 6px;
        font-size: 13px;
        font-weight: bold;
        padding: 8px 20px;
    }
    QPushButton#refreshBtn:hover {
        background-color: #2980b9;
    }
    QPushButton#closeBtn {
        background-color: #44475a;
        color: #bbb;
        border: none;
        border-radius: 6px;
        font-size: 13px;
        padding: 8px 20px;
    }
    QPushButton#closeBtn:hover {
        background-color: #5a5e78;
        color: white;
    }
"""


class AppsChartWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Моніторинг поданих заяв")
        self.resize(1200, 700)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(WINDOW_STYLE)

        # Основний віджет
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(16, 8, 16, 12)

        # Заголовок
        self.title_label = QLabel("Кількість поданих заяв за спеціальностями")
        self.title_label.setObjectName("chartTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.title_label)

        # ── Нижня панель (створюємо ДО update_chart) ──
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

        # Область графіка
        if HAS_MATPLOTLIB:
            self.figure = Figure(facecolor='#1a1a2e')
            self.canvas = FigureCanvas(self.figure)
            self.main_layout.addWidget(self.canvas, stretch=1)

            self.btn_refresh.clicked.connect(self.update_chart)

            # Таймер автооновлення — 60 сек (легкий SELECT COUNT, не навантажує базу)
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_chart)
            self.timer.start(60_000)

            # Початкова побудова
            self.update_chart()
        else:
            err = QLabel(
                "Бібліотека matplotlib не встановлена.\n\n"
                "Виконайте в терміналі:  pip install matplotlib"
            )
            err.setAlignment(Qt.AlignCenter)
            err.setStyleSheet("color: #e74c3c; font-size: 16px; font-weight: bold;")
            self.main_layout.addWidget(err)

        self.main_layout.addLayout(bottom)

    # ─────────────────────── Дані ───────────────────────
    def get_data(self):
        """Збирає кількість заяв з усіх таблиць, показуючи ВСІ спеціальності (навіть з 0 заяв)."""
        data = {}
        conn = setup_database()
        if not conn:
            return data

        try:
            cursor = conn.cursor()

            # Конфігурація: довідник спеціальностей → таблиця заяв → суфікс
            config = [
                ("specialities_day",  "personal_case_day",      "(денна)"),
                ("specialities_day",  "personal_case_day_scor", "(скр.)"),
                ("specialities_evening","personal_case_evening",    "(заочна)"),
            ]

            for spec_table, case_table, suffix in config:
                # Перевіряємо чи існують обидві таблиці
                for t in (spec_table, case_table):
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public' AND table_name = %s
                        )
                    """, (t,))
                    if not cursor.fetchone()[0]:
                        break
                else:
                    # Обидві таблиці існують — LEFT JOIN для повного списку
                    cursor.execute(f"""
                        SELECT s.name_specialnosti, COUNT(c.id)
                        FROM public.{spec_table} s
                        LEFT JOIN public.{case_table} c
                            ON c.name_specialnosti = s.name_specialnosti
                            AND c.is_cancelled = FALSE
                        GROUP BY s.name_specialnosti
                        ORDER BY s.name_specialnosti
                    """)
                    for spec, count in cursor.fetchall():
                        label = f"{spec} {suffix}"
                        data[label] = count

            cursor.close()
        except Exception:
            pass
        finally:
            close_database(conn)

        return data

    # ─────────────────────── Графік ───────────────────────
    def update_chart(self):
        if not HAS_MATPLOTLIB:
            return

        data = self.get_data()

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#1a1a2e')

        if not data:
            ax.text(0.5, 0.5, "Немає даних для відображення",
                    ha='center', va='center', fontsize=16, color='#7f8c8d')
            ax.axis('off')
            self.canvas.draw()
            return

        # Групуємо дані за формою навчання (порядок: денна, скорочена, заочна)
        groups = [
            ("(денна)",  "Денна форма"),
            ("(скр.)",   "Скорочена форма"),
            ("(заочна)", "Заочна форма"),
        ]

        ordered_labels = []
        ordered_values = []
        ordered_colors = []
        separator_positions = []  # Позиції для горизонтальних ліній-роздільників

        for suffix, group_name in groups:
            group_items = [(k, v) for k, v in sorted(data.items()) if suffix in k]
            if not group_items:
                continue

            if ordered_labels:
                # Додаємо позицію роздільника перед новою групою
                separator_positions.append(len(ordered_labels) - 0.5)

            color = FORM_COLORS.get(suffix, FORM_COLORS_DEFAULT)
            for label, value in group_items:
                ordered_labels.append(label)
                ordered_values.append(value)
                ordered_colors.append(color)

        # Інвертуємо порядок, щоб денна була ЗВЕРХУ (barh малює знизу вгору)
        ordered_labels.reverse()
        ordered_values.reverse()
        ordered_colors.reverse()
        # Перераховуємо позиції роздільників після інверсії
        total = len(ordered_labels)
        separator_positions = [total - 1 - pos for pos in separator_positions]

        # Малюємо горизонтальні бари
        y_pos = range(len(ordered_labels))
        bars = ax.barh(y_pos, ordered_values, color=ordered_colors, edgecolor='none', height=0.65)

        # Підписи значень праворуч від кожного бару
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.3, bar.get_y() + bar.get_height() / 2,
                    f'{int(width)}',
                    va='center', ha='left',
                    fontsize=12, fontweight='bold', color='#ecf0f1')

        # Підписи спеціальностей ліворуч
        ax.set_yticks(y_pos)
        ax.set_yticklabels(ordered_labels, fontsize=10, color='#bdc3c7')

        # Горизонтальні лінії-роздільники між групами
        for pos in separator_positions:
            ax.axhline(y=pos, color='#44475a', linewidth=1.5, linestyle='--', alpha=0.7)

        # Прибираємо шкалу X та рамки
        ax.set_xticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.tick_params(left=False)

        # Невеликий відступ справа для цифр
        max_val = max(ordered_values) if ordered_values else 1
        ax.set_xlim(0, max_val * 1.15)

        self.figure.tight_layout()
        self.canvas.draw()

        # Оновлюємо статус
        now = datetime.now().strftime("%H:%M:%S")
        total = sum(ordered_values)
        self.status_label.setText(f"Всього заяв: {total}  ·  Оновлено о {now}  ·  Авто-оновлення: 60 сек")

