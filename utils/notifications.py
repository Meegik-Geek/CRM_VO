from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QApplication, QGraphicsOpacityEffect, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QFont, QColor

class ToastNotification(QWidget):
    """Кастомне спливаюче сповіщення (Toast)."""
    _active_toast = None  # Статична змінна для відстеження активного сповіщення
    
    def __init__(self, parent, message, color="#333", icon="ℹ", duration=3000, position='top'):
        super().__init__(parent)
        
        # Закриваємо попереднє сповіщення, якщо воно є
        if ToastNotification._active_toast:
            try:
                ToastNotification._active_toast.hide_notification()
            except:
                pass
        ToastNotification._active_toast = self

        self.position = position
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Основний контейнер
        self.container = QWidget(self)
        self.container.setObjectName("toastContainer")
        self.container.setMinimumHeight(40) # Зменшена висота
        
        # Перетворення кольору в RGBA для прозорості (80%)
        rgba = self._hex_to_rgba(color, 0.8)
        
        self.container.setStyleSheet(f"""
            QWidget#toastContainer {{
                background-color: {rgba};
                border-bottom: 1px solid rgba(0,0,0,0.1);
            }}
            QLabel {{
                color: white;
                font-size: 12px;
                font-weight: 500;
            }}
        """)
        
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(40, 5, 40, 5) # Мінімальні відступи
        layout.setSpacing(12)
        
        # Іконка
        self.icon_label = QLabel(icon)
        icon_font = QFont()
        icon_font.setPointSize(13)
        icon_font.setBold(True)
        self.icon_label.setFont(icon_font)
        self.icon_label.setFixedWidth(25)
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)
        
        # Повідомлення
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignCenter)
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
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
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
            main_window = self.parent_widget.window()
            while main_window.parentWidget():
                main_window = main_window.parentWidget().window()
                if main_window.inherits("QMainWindow"):
                    break
            
            window_pos = main_window.mapToGlobal(QPoint(0, 0))
            
            target_area = self.parent_widget
            if target_area.inherits("QDialog") and target_area.parentWidget():
                target_area = target_area.parentWidget()
            
            area_rect = target_area.rect()
            area_pos = target_area.mapToGlobal(QPoint(0, 0))
            
            self.setFixedWidth(area_rect.width())
            self.adjustSize() 
            
            x = area_pos.x()
            
            if self.position == 'bottom':
                y = window_pos.y() + main_window.height() - self.height() - 40
            else:
                # Зверху вікна
                y = window_pos.y() 
            
            self.move(x, y)
        
        self.show()
        
        # Анімація появи
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()
        
        self.timer.start(self.duration)

    def hide_notification(self):
        """Ховає сповіщення з анімацією."""
        if self.animation.state() == QPropertyAnimation.Running and self.animation.endValue() == 0.0:
            return # Вже ховається
            
        self.animation.stop()
        self.animation.setStartValue(self.opacity_effect.opacity())
        self.animation.setEndValue(0.0)
        
        # Відключаємо попередні підключення, щоб уникнути подвійного виклику deleteLater
        try:
            self.animation.finished.disconnect()
        except:
            pass
            
        self.animation.finished.connect(self.on_hidden)
        self.animation.start()

    def on_hidden(self):
        """Викликається після завершення анімації зникнення."""
        if ToastNotification._active_toast == self:
            ToastNotification._active_toast = None
        self.deleteLater()

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

