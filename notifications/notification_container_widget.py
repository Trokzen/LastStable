# notifications/notification_container_widget.py
import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QApplication
from PySide6.QtCore import Qt
from .notification_item_widget import NotificationItemWidget

class NotificationContainerWidget(QWidget):
    def __init__(self):
        super().__init__()
        # --- Настройка окна ---
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # --- Основной макет ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- QScrollArea для содержимого ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # --- Виджет-контейнер для уведомлений ---
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(1)
        self.content_layout.addStretch()

        # Устанавливаем виджет содержимого в ScrollArea
        self.scroll_area.setWidget(self.content_widget)

        # Добавляем ScrollArea в основной макет
        main_layout.addWidget(self.scroll_area)

        # --- Размеры и позиционирование ---
        self.setFixedSize(350, 200)
        self._reposition()

        # Скрываем контейнер по умолчанию
        self.setVisible(False)

    def _reposition(self):
        """Позиционирует окно в правом нижнем углу экрана."""
        screen_geo = QApplication.primaryScreen().availableGeometry()
        x = screen_geo.right() - self.width() - 10
        y = screen_geo.bottom() - self.height() - 10
        self.move(x, y)

    def add_notification(self, title, message, icon_type, duration_ms):
        """Добавляет новое уведомление в контейнер."""
        # Создаем элемент уведомления, передавая self как container_widget
        item_widget = NotificationItemWidget(title, message, icon_type, duration_ms, container_widget=self, parent=self.content_widget) # <-- Передаем self

        # Найти позицию для вставки (перед stretch)
        insert_position = self.content_layout.count() - 1

        # Вставляем новый элемент уведомления
        self.content_layout.insertWidget(insert_position, item_widget)

        # Показываем контейнер, если он был скрыт
        if not self.isVisible():
            self.show()

        print(f"Python: Уведомление добавлено в контейнер: {title}")

    # --- МЕТОД: Обработка удаления элемента ---
    def on_item_removed(self):
        """Вызывается дочерним NotificationItemWidget при его удалении."""
        # Проверяем, остались ли *настоящие* уведомления (не считая stretch)
        num_items = self.content_layout.count()
        num_real_items = num_items - 1 # Вычитаем stretch

        if num_real_items <= 0:
            # Если не осталось реальных уведомлений, скрываем контейнер
            print("Python: Уведомления закончились, контейнер скрывается.")
            self.hide()
        else:
            print(f"Python: Уведомление удалено, осталось {num_real_items} уведомлений.")

    def showEvent(self, event):
        """Переопределяем, чтобы корректно позиционировать при показе."""
        super().showEvent(event)
        self._reposition()
