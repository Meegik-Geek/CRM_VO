from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QApplication, QGraphicsOpacityEffect, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QFont, QColor

class ToastNotification(QWidget):
    """Кастомне спливаюче сповіщення (Toast)."""
    
    def __init__(self, parent, message, color="#333", icon="ℹ", duration=3000, position='top'):
        super().__init__(parent)
        self.position = position
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Основний контейнер
        self.container = QWidget(self)
        self.container.setObjectName("toastContainer")
        # Перетворення кольору в RGBA для прозорості (90%)
        rgba = self._hex_to_rgba(color, 0.9)
        
        self.container.setStyleSheet(f"""
            QWidget#toastContainer {{
                background-color: {rgba};
               
            }}
            QLabel {{
                color: white;
                font-size: 12px;
                font-weight: 500;
                
            }}
        """)
        
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(40, 0, 40, 0)
        #layout.setAlignment(Qt.AlignCenter) # Центрування всього вмісту
        #layout.setSpacing(15)
        
        # Іконка
        self.icon_label = QLabel(icon)
        icon_font = QFont()
        icon_font.setPointSize(14) # Трохи зменшим для кращого вписування
        icon_font.setBold(True)
        self.icon_label.setFont(icon_font)
        self.icon_label.setFixedWidth(20) # Фіксована ширина
        self.icon_label.setFixedHeight(20) # ТУТ: Фіксована висота, щоб не розпирало банер
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)
        
        # Повідомлення
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignCenter) # Центрування самого тексту
        layout.addWidget(self.message_label)
        
        # Ефект прозорості для анімації
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        # Таймер для закриття
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_notification)
        
        # Анімація
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.addWidget(self.container)
        
        self.duration = duration
        self.parent_widget = parent

    def _hex_to_rgba(self, hex, alpha):
        hex = hex.lstrip('#')
        lv = len(hex)
        rgb = tuple(int(hex[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"

    def show_notification(self):
        """Відображає сповіщення по ширині right_panel під заголовком ГОЛОВНОГО вікна."""
        if self.parent_widget:
            # Шукаємо саме головне вікно (QMainWindow) додатка для Y-координати
            main_window = self.parent_widget.window()
            # Йдемо вгору, поки не знайдемо QMainWindow або поки є батьки
            while main_window.parentWidget():
                main_window = main_window.parentWidget().window()
                if main_window.inherits("QMainWindow"):
                    break
            
            window_pos = main_window.mapToGlobal(QPoint(0, 0))
            
            # Знаходимо "робочу область" (right_panel або саму сторінку)
            # Якщо parent_widget - це діалог, беремо його батька як орієнтир для ширини
            target_area = self.parent_widget
            if target_area.inherits("QDialog") and target_area.parentWidget():
                target_area = target_area.parentWidget()
            
            # Глобальна геометрія цільової області для X та ширини
            area_rect = target_area.rect()
            area_pos = target_area.mapToGlobal(QPoint(0, 0))
            
            # Встановлюємо ширину як у правої панелі
            self.setFixedWidth(area_rect.width())
            self.adjustSize() 
            
            x = area_pos.x()
            
            if self.position == 'bottom':
                # Знизу вікна (над нижньою межею)
                y = window_pos.y() + main_window.height() - self.height() - 40
            else:
                # Зверху вікна (під заголовком)
                y = window_pos.y() - 8 
            
            self.move(x, y)
        
        self.show()
        
        # Анімація появи
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()
        
        self.timer.start(self.duration)

    def hide_notification(self):
        """Ховає сповіщення з анімацією."""
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.deleteLater)
        self.animation.start()

def show_success(parent, message, title=None, position='top'):
    """Відображає сучасне сповіщення про успіх."""
    toast = ToastNotification(parent, message, color="#2ECC71", icon="✔", position=position)
    toast.show_notification()

def show_error(parent, message, title=None, position='top'):
    """Відображає сучасне сповіщення про помилку."""
    toast = ToastNotification(parent, message, color="#E74C3C", icon="✖", position=position)
    toast.show_notification()

def show_warning(parent, message, title=None, position='top'):
    """Відображає сучасне сповіщення про попередження."""
    toast = ToastNotification(parent, message, color="#F1C40F", icon="⚠", position=position)
    toast.show_notification()

class LocalizedMessageBox(QMessageBox):
    """QMessageBox з українськими кнопками."""
    def __init__(self, parent=None, icon=QMessageBox.Information, title="Повідомлення", message="", buttons=QMessageBox.Ok):
        super().__init__(parent)
        self.setIcon(icon)
        self.setWindowTitle(title)
        self.setText(message)
        self.setStandardButtons(buttons)
        
        # Переклад кнопок
        self.button_translations = {
            QMessageBox.Ok: "Добре",
            QMessageBox.Yes: "Так",
            QMessageBox.No: "Ні",
            QMessageBox.Cancel: "Скасувати",
            QMessageBox.Close: "Закрити",
            QMessageBox.Save: "Зберегти",
            QMessageBox.Discard: "Відхилити"
        }
        
        for btn_type, text in self.button_translations.items():
            button = self.button(btn_type)
            if button:
                button.setText(text)

def show_info(parent, message, title="Інформація"):
    """Показує інформаційне вікно з кнопкою ОК."""
    msg = LocalizedMessageBox(parent, QMessageBox.Information, title, message, QMessageBox.Ok)
    return msg.exec_()

def show_warning_msg(parent, message, title="Увага"):
    """Показує вікно попередження з кнопкою ОК."""
    msg = LocalizedMessageBox(parent, QMessageBox.Warning, title, message, QMessageBox.Ok)
    return msg.exec_()

def show_error_msg(parent, message, title="Помилка"):
    """Показує вікно помилки з кнопкою ОК."""
    msg = LocalizedMessageBox(parent, QMessageBox.Critical, title, message, QMessageBox.Ok)
    return msg.exec_()

def ask_confirmation(parent, message, title="Підтвердження"):
    """Запитує підтвердження (Так/Ні). Повертає True, якщо обрано Так."""
    msg = LocalizedMessageBox(parent, QMessageBox.Question, title, message, QMessageBox.Yes | QMessageBox.No)
    msg.setDefaultButton(QMessageBox.No)
    reply = msg.exec_()
    return reply == QMessageBox.Yes

