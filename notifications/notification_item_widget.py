# notifications/notification_item_widget.py
import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPalette, QFont, QColor

class NotificationItemWidget(QWidget):
    def __init__(self, title, message, icon_type, duration_ms, container_widget, parent=None):
        super().__init__(parent)
        # --- УВЕЛИЧЕНО: Фиксированная высота для каждого уведомления ---
        self.setFixedHeight(120) # <-- Увеличено с 80 до 120 (примерно в 1.5 раза)
        # --- ---
        self.setAutoFillBackground(True)

        # --- Сохраняем ссылку на контейнер ---
        self.container_widget = container_widget
        # --- ---

        # --- УВЕЛИЧЕНО: Установка шрифта ---
        font = QFont("Arial", 9) # <-- Увеличен размер шрифта (примерно в 1.5 раза от 9, если был 9)
        self.setFont(font)
        # --- ---

        # --- Настройка фона в зависимости от типа ---
        palette = self.palette()
        if icon_type == "Error":
            # Красный фон для ошибок (время истекло)
            palette.setColor(QPalette.Window, QColor(244, 67, 54))  # Material Red 500
        elif icon_type == "Warning":
            # Желтый фон для предупреждений (осталось 5 минут)
            palette.setColor(QPalette.Window, QColor(255, 193, 7))  # Material Amber 500
        elif icon_type == "Success":
            # Зеленый фон для успеха (начало действия)
            palette.setColor(QPalette.Window, QColor(76, 175, 80))  # Material Green 500
        elif icon_type == "Information":
            # Светло-серый фон для информационных уведомлений
            palette.setColor(QPalette.Window, Qt.lightGray)
        else:
            palette.setColor(QPalette.Window, Qt.white)
        self.setPalette(palette)
        # --- ---

        # --- Макет для содержимого ---
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # --- Содержимое уведомления ---
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)

        self.title_label = QLabel(title)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-weight: bold;") # Убедимся, что заголовок жирный
        # self.title_label.setFont(font) # Применить шрифт, если установлен

        # --- УВЕЛИЧЕНО: QLabel для сообщения с ограничением высоты ---
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        # self.message_label.setFont(font) # Применить шрифт, если установлен
        self.message_label.setMaximumHeight(60) # <-- Ограничиваем высоту текста (примерное значение)
        self.message_label.setOpenExternalLinks(True) # Позволяет открывать ссылки в message
        # self.message_label.setTextInteractionFlags(Qt.TextSelectableByMouse) # Позволяет выделять текст
        # --- ---

        content_layout.addWidget(self.title_label)
        content_layout.addWidget(self.message_label)
        content_layout.addStretch()

        # --- Кнопка закрытия ---
        close_button = QPushButton("×")
        # --- УВЕЛИЧЕНО: Размер кнопки ---
        close_button.setFixedSize(25, 25) # <-- Увеличено с 20x20 до 25x25 (примерно в 1.5 раза)
        # --- ---
        close_button.setStyleSheet(
            "QPushButton {"
            "   border: 1px solid gray;"
            "   border-radius: 12px;" # --- УВЕЛИЧЕНО: Радиус для круглой кнопки ---
            "   font-weight: bold;"
            "   font-size: 12px;" # <-- Увеличен размер шрифта на кнопке
            "   background-color: lightgray;"
            "}"
            "QPushButton:hover {"
            "   background-color: #ffcccc;"
            "}"
        )
        # close_button.setFont(font) # Применить шрифт, если установлен
        close_button.clicked.connect(self._on_close_clicked)

        # --- Добавляем элементы в основной макет ---
        main_layout.addLayout(content_layout)
        main_layout.addWidget(close_button)

        # --- Таймер для автоскрытия ---
        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.timeout.connect(self._on_timer_timeout)
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.start(duration_ms)

    def _on_close_clicked(self):
        print(f"Python: Уведомление закрыто вручную: {self.title_label.text()}")
        self._cleanup()

    def _on_timer_timeout(self):
        print(f"Python: Время уведомления истекло: {self.title_label.text()}")
        self._cleanup()

    def _cleanup(self):
        self.auto_hide_timer.stop()

        parent_layout = self.parent().layout()
        if parent_layout:
            parent_layout.removeWidget(self)

        self.hide()
        self.deleteLater()

        # --- УВЕДОМЛЯЕМ РОДИТЕЛЬСКИЙ КОНТЕЙНЕР ОБ УДАЛЕНИИ ---
        if hasattr(self.container_widget, 'on_item_removed'):
            self.container_widget.on_item_removed()
        # --- ---

