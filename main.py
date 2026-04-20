# main.py
# =============================================================================
# СТАНДАРТНЫЕ БИБЛИОТЕКИ PYTHON
# =============================================================================
import datetime
import html
import logging
import os
import re
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional, Set

# =============================================================================
# БИБЛИОТЕКА PYSIDE6 - ОСНОВНЫЕ МОДУЛИ
# =============================================================================

# Графики и диаграммы
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice

# Базовые классы и утилиты Qt Core
from PySide6.QtCore import (
    QDateTime, QObject, Property, QSettings, QTimer,
    QUrl, Qt, Signal, Slot
)

# Графический интерфейс и обработка документов
from PySide6.QtGui import QGuiApplication, QIcon, QAction, QTextDocument

# Мультимедиа (звуковые уведомления)
from PySide6.QtMultimedia import QSoundEffect

# Печать и работа с принтерами
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

# QML движок для работы с QML интерфейсами
from PySide6.QtQml import QQmlApplicationEngine

# Виджеты и элементы интерфейса
from PySide6.QtWidgets import (
    QApplication, QMenu, QMessageBox, QSystemTrayIcon
)

from notifications.notification_container_widget import NotificationContainerWidget
# =============================================================================
# ЛОКАЛЬНЫЕ МОДУЛИ ПРИЛОЖЕНИЯ
# =============================================================================

# Менеджеры базы данных
from db.sqlite_database_manager import SQLiteDatabaseManager  # Основная БД SQLite
from db.sqlite_config import SQLiteConfigManager            # Конфигурация в SQLite
from werkzeug.security import check_password_hash


class ApplicationData(QObject):
    """Класс для передачи данных и управления логикой в QML."""
    # Сигналы для обновления свойств в QML
    currentTimeChanged = Signal()
    currentDateChanged = Signal()
    dutyOfficerChanged = Signal()
    workplaceNameChanged = Signal()
    # --- Новые сигналы ---
    loginScreenRequested = Signal()  # Сигнал для перехода на экран входа
    mainScreenRequested = Signal()   # Сигнал для перехода на основной экран
    settingsChanged = Signal() # Новый сигнал для уведомления об изменении настроек
    postNumberChanged = Signal()
    postNameChanged = Signal()
    localTimeChanged = Signal()
    moscowTimeChanged = Signal()
    localDateChanged = Signal()   # Сигнал для изменения местной даты
    moscowDateChanged = Signal()  # Сигнал для изменения московской даты    
    timeSettingsChanged = Signal() # Сигнал для обновления настроек времени
    backgroundImagePathChanged = Signal()
    algorithmsListChanged = Signal()
    printFontFamilyChanged = Signal()
    printFontSizeChanged = Signal()
    printFontStyleChanged = Signal()
    # --- СИГНАЛЫ ДЛЯ ШРИФТА ИНТЕРФЕЙСА ---
    fontFamilyChanged = Signal()
    fontSizeChanged = Signal()
    fontStyleChanged = Signal()

    def load_initial_settings(self):
        """Загружает начальные настройки при запуске приложения"""
        try:
            if self.sqlite_config_manager:
                settings = self.sqlite_config_manager.get_app_settings()
                if settings:
                    # Обновляем свойства приложения
                    if 'workplace_name' in settings and settings['workplace_name']:
                        self._workplace_name = settings['workplace_name']
                        self.workplaceNameChanged.emit()
                    
                    if 'post_number' in settings and settings['post_number']:
                        self._post_number = str(settings['post_number'])
                        self.postNumberChanged.emit()
                    
                    if 'post_name' in settings and settings['post_name']:
                        self._post_name = settings['post_name']
                        self.postNameChanged.emit()
                    
                    updated_time_props = False
                    
                    if 'custom_time_label' in settings and settings['custom_time_label']:
                        self._custom_time_label = settings['custom_time_label']
                        updated_time_props = True
                        print(f"Python: Загружено custom_time_label: '{self._custom_time_label}'")

                    # Загружаем смещение как число секунд
                    if 'custom_time_offset_seconds' in settings and isinstance(settings['custom_time_offset_seconds'], int):
                        self._custom_time_offset_seconds = settings['custom_time_offset_seconds']
                        updated_time_props = True
                        print(f"Python: Загружено custom_time_offset_seconds: {self._custom_time_offset_seconds}")

                    if 'show_moscow_time' in settings:
                        # Преобразуем 1/0 из SQLite в True/False
                        self._show_moscow_time = bool(settings['show_moscow_time'])
                        updated_time_props = True
                        print(f"Python: Загружено show_moscow_time: {self._show_moscow_time}")

                    # Загружаем смещение Москвы как число секунд
                    if 'moscow_time_offset_seconds' in settings and isinstance(settings['moscow_time_offset_seconds'], int):
                        self._moscow_time_offset_seconds = settings['moscow_time_offset_seconds']
                        updated_time_props = True
                        print(f"Python: Загружено moscow_time_offset_seconds: {self._moscow_time_offset_seconds}")

                    if updated_time_props:
                        print("Python: Некоторые настройки времени обновлены из БД.")
                        # Принудительно обновляем рассчитываемые времена
                        self.update_time()
                        # Уведомляем QML об изменении настроек времени
                        self.timeSettingsChanged.emit()
                    # --- ---
                    
                    # --- НОВОЕ: Загрузка настроек внешнего вида ---
                    updated_appearance_props = False
                    
                    # Путь к фоновому изображению/эмблеме
                    if 'background_image_path' in settings:
                        bg_image_path = settings['background_image_path']
                        # Устанавливаем путь, если он не None и не пустая строка
                        if bg_image_path is not None and str(bg_image_path).strip() != "":
                            self._background_image_path = str(bg_image_path).strip()
                        else:
                            # Если путь None или пустая строка, оставляем как есть (None или дефолтный путь)
                            # self._background_image_path = None # <-- Опционально: явно установить None
                            pass 
                        self.backgroundImagePathChanged.emit() # <-- ВАЖНО: Уведомляем QML
                        updated_appearance_props = True
                        print(f"Python: Загружен background_image_path: '{self._background_image_path}'")

                    # ... (здесь можно добавить загрузку других настроек внешнего вида: font_family, font_size и т.д.) ...
                    
                    # --- НОВОЕ: Загрузка настроек шрифта печати ---
                    updated_print_props = False
                    if 'print_font_family' in settings and settings['print_font_family']:
                        self._print_font_family = settings['print_font_family']
                        self.printFontFamilyChanged.emit()
                        updated_print_props = True
                        print(f"Python: Загружен print_font_family: {self._print_font_family}")

                    if 'print_font_size' in settings and isinstance(settings['print_font_size'], int):
                        self._print_font_size = settings['print_font_size']
                        self.printFontSizeChanged.emit()
                        updated_print_props = True
                        print(f"Python: Загружен print_font_size: {self._print_font_size}")
                    
                    # --- ДОБАВЛЕНО: Загрузка начертания шрифта печати ---
                    if 'print_font_style' in settings and settings['print_font_style']:
                        self._print_font_style = settings['print_font_style']
                        self.printFontStyleChanged.emit() # <-- Добавлено
                        updated_print_props = True
                        print(f"Python: Загружен print_font_style: {self._print_font_style}")

                    # font_family, font_size, font_style

                    if 'font_family' in settings and settings['font_family']:
                        self._font_family = settings['font_family']
                        updated_appearance_props = True
                        print(f"Python: Загружен font_family: {self._font_family}")

                    if 'font_size' in settings and settings['font_size']:
                        self._font_size = settings['font_size']
                        updated_appearance_props = True
                        print(f"Python: Загружен font_size: {self._font_size}")

                    if 'font_style' in settings and settings['font_style']:
                        self._font_style = settings['font_style']
                        updated_appearance_props = True
                        print(f"Python: Загружен font_style: {self._font_style}")

                    # --- Загрузка use_persistent_reminders и sound_enabled ---
                    if 'use_persistent_reminders' in settings:
                        # Преобразуем 1/0 из SQLite в True/False
                        self._use_persistent_reminders = bool(settings['use_persistent_reminders'])
                        print(f"Python: Загружено use_persistent_reminders: {self._use_persistent_reminders}")

                    if 'sound_enabled' in settings:
                        # Преобразуем 1/0 из SQLite в True/False
                        self._sound_enabled = bool(settings['sound_enabled'])
                        print(f"Python: Загружен sound_enabled: {self._sound_enabled}")
                    # --- ---

                    if updated_appearance_props:
                        self.fontFamilyChanged.emit()
                        self.fontSizeChanged.emit()
                        self.fontStyleChanged.emit()
                        print("Python: Некоторые настройки внешнего вида обновлены из БД.")
                        # Уведомляем QML об общем изменении настроек (если нужно)
                        # self.settingsChanged.emit() # <-- Опционально: если используется глобальный сигнал
                    # --- ---
                    
                    print(f"Python: Начальные настройки (включая время и внешний вид) загружены.")
        except Exception as e:
            print(f"Python: Ошибка при загрузке начальных настроек (включая время и внешний вид): {e}")
            import traceback
            traceback.print_exc()


    def __init__(self, app, engine, sqlite_config_manager):
        """
        Инициализирует контекст данных приложения.
        :param app: Экземпляр QApplication.
        :param engine: Экземпляр QQmlApplicationEngine.
        :param sqlite_config_manager: Экземпляр SQLiteConfigManager.
        """
        super().__init__()
        self.app = app
        self.engine = engine
        # --- Менеджеры БД ---
        self.sqlite_config_manager = sqlite_config_manager
        # Инициализируем database_manager сразу, чтобы он был доступен для всех операций
        from db.sqlite_database_manager import SQLiteDatabaseManager
        self.database_manager = SQLiteDatabaseManager('duty_app.db')
        # --- ---
        self.window = None # Ссылка на ApplicationWindow из QML
        self._current_user = None # Данные вошедшего пользователя

        # --- Инициализация свойств (временно из заглушек, позже из БД) ---
        self._workplace_name = "Рабочее место дежурного"
        self._duty_officer = "Не выбран"
        self._current_time = QDateTime.currentDateTime().toString("hh:mm:ss")
        self._current_date = QDateTime.currentDateTime().toString("dd.MM.yyyy")
        self._post_number = "1"  # Значение по умолчанию
        self._post_name = "Дежурство по части"  # Значение по умолчанию
                # --- НОВЫЕ свойства для времени ---
        self._local_time = self._current_time # Инициализируем как текущее
        self._moscow_time = self._current_time # Инициализируем как текущее
        self._custom_time_label = "Местное время" # Значение по умолчанию
        self._custom_time_offset_seconds = 0 # Смещение в секундах (удобнее для расчетов)
        self._show_moscow_time = True
        self._moscow_time_offset_seconds = 0 # Смещение Москвы в секундах
        # --- ИНИЦИАЛИЗАЦИЯ НОВЫХ СВОЙСТВ ДЛЯ ДАТ ---
        self._local_date = self._current_date # <-- Новое внутреннее свойство
        self._moscow_date = self._current_date # <-- Новое внутреннее свойство
        self._print_font_family = "Arial" # Значение по умолчанию
        self._print_font_size = 12        # Значение по умолчанию
        # --- НОВОЕ СВОЙСТВО ДЛЯ НАЧЕРТАНИЯ ШРИФТА ПЕЧАТИ ---
        self._print_font_style = "normal" # Значение по умолчанию # <-- Добавлено
        # --- ---
        # Инициализируем путь к эмблеме значением по умолчанию или None
        self._background_image_path = None # <-- ИЛИ путь к дефолтной эмблеме, если нужно

        # --- ИНИЦИАЛИЗАЦИЯ СВОЙСТВ ШРИФТА ИНТЕРФЕЙСА ---
        self._font_family = None
        self._font_size = None
        self._font_style = None

        # --- ИНИЦИАЛИЗАЦИЯ СВОЙСТВ УВЕДОМЛЕНИЙ ---
        # Инициализируем внутренние переменные до загрузки из БД, чтобы избежать AttributeError
        # Значения по умолчанию - отключено, пока не загружено из БД
        self._use_persistent_reminders = False
        self._sound_enabled = False
        # --- ---

        # Загружаем начальные настройки
        self.load_initial_settings()

        self.tray_icon = None
        self.close_confirmation_shown = False

        # Таймер для обновления времени
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        # self.timer.start(1000) # Запускаем таймер позже, когда основной экран активен

        # Подключаемся к сигналу, когда объекты QML созданы
        self.engine.objectCreated.connect(self.on_qml_objects_created)
        # --- Атрибуты для уведомлений ---
        # Хранит ID action_executions, для которых было показано уведомление определенного типа
        # Формат: {action_exec_id: set(status_types)}
        self._notified_action_executions: Dict[int, Set[str]] = {}
        self._notification_timer: Optional[QTimer] = None
        self._sound_approaching: Optional[QSoundEffect] = None
        self._sound_overdue: Optional[QSoundEffect] = None
        # --- ИНИЦИАЛИЗАЦИЯ КОНТЕЙНЕРА УВЕДОМЛЕНИЙ ---
        self.notification_container = NotificationContainerWidget()



    def on_qml_objects_created(self, obj, url):
        """Вызывается, когда QML объекты загружены."""
        if obj is not None and url.fileName() == "main.qml":
            self.window = obj
            self.setup_tray()
            print("Python: QML объекты загружены. Ссылка на window установлена.")

    def setup_tray(self):
        """Настройка иконки в системном трее."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("Системный трей недоступен.")
            return

        # --- Создание иконки трея ---
        icon_path = Path(__file__).parent / "resources" / "images" / "placeholder_emblem.png"
        self.tray_icon = QSystemTrayIcon(QIcon(str(icon_path)), self.app)
        self.tray_icon.setToolTip("ВПО «Алгоритм-ДЧ»")

        # --- Создание контекстного меню для трея ---
        tray_menu = QMenu()
        restore_action = QAction("Восстановить", tray_menu)
        minimize_action = QAction("Свернуть", tray_menu)
        maximize_action = QAction("Развернуть", tray_menu)
        quit_action = QAction("Выход", tray_menu)

        restore_action.triggered.connect(self.restore_window)
        minimize_action.triggered.connect(self.minimize_window)
        maximize_action.triggered.connect(self.maximize_window)
        quit_action.triggered.connect(self.quit_app)

        tray_menu.addAction(restore_action)
        tray_menu.addAction(minimize_action)
        tray_menu.addAction(maximize_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()
        print("Иконка в трее создана и показана.")

    def update_time(self):
        """Обновляет текущее время, местное время и московское время."""
        now_system = QDateTime.currentDateTime() # Время системы QDateTime
        
        # --- Обновляем основное (системное) время и ДАТУ ---
        self._current_time = now_system.toString("hh:mm:ss")
        # --- ОБНОВЛЕНО: Обновляем и системную дату ---
        self._current_date = now_system.toString("dd.MM.yyyy") 
        # --- ---
        self.currentTimeChanged.emit()
        # --- ОБНОВЛЕНО: Эмитируем сигнал о смене системной даты ---
        self.currentDateChanged.emit() 
        # --- ---

        # --- Рассчитываем и обновляем местное время и ДАТУ ---
        # Создаем QDateTime для местного времени на основе системного
        local_dt = now_system.addSecs(self._custom_time_offset_seconds)
        self._local_time = local_dt.toString("hh:mm:ss")
        # --- НОВОЕ: Рассчитываем и обновляем местную дату ---
        self._local_date = local_dt.toString("dd.MM.yyyy") 
        # --- ---
        self.localTimeChanged.emit()
        # --- НОВОЕ: Эмитируем сигнал о смене местной даты ---
        self.localDateChanged.emit() 
        # --- ---

        # --- Рассчитываем и обновляем московское время и ДАТУ ---
        # Создаем QDateTime для московского времени на основе системного
        moscow_dt = now_system.addSecs(self._moscow_time_offset_seconds)
        self._moscow_time = moscow_dt.toString("hh:mm:ss")
        # --- НОВОЕ: Рассчитываем и обновляем московскую дату ---
        self._moscow_date = moscow_dt.toString("dd.MM.yyyy") 
        # --- ---
        self.moscowTimeChanged.emit()
        # --- НОВОЕ: Эмитируем сигнал о смене московской даты ---
        self.moscowDateChanged.emit() 
        # --- ---

    # --- Свойства для QML ---
    @Property(str, notify=workplaceNameChanged)
    def workplaceName(self):
        return self._workplace_name

    @Property(str, notify=dutyOfficerChanged)
    def dutyOfficer(self):
        return self._duty_officer

    @Property(str, notify=currentTimeChanged)
    def currentTime(self):
        return self._current_time

    @Property(str, notify=currentDateChanged)
    def currentDate(self):
        return self._current_date
    
    @Property(str, notify=postNumberChanged)
    def postNumber(self):
        return self._post_number

    @Property(str, notify=postNameChanged)
    def postName(self):
        return self._post_name

    @Property(str, notify=localTimeChanged)
    def localTime(self):
        return self._local_time

    @Property(str, notify=moscowTimeChanged)
    def moscowTime(self):
        return self._moscow_time

    # --- СВОЙСТВА ДЛЯ ДАТ ---
    @Property(str, notify=localDateChanged) # <-- Новый сигнал
    def localDate(self):
        """Настраиваемая местная дата."""
        return self._local_date # <-- Новое внутреннее свойство

    @Property(str, notify=moscowDateChanged) # <-- Новый сигнал
    def moscowDate(self):
        """Московская дата."""
        return self._moscow_date # <-- Новое внутреннее свойство
    # --- ---

    @Property(str, notify=timeSettingsChanged)
    def customTimeLabel(self):
        return self._custom_time_label

    @Property(bool, notify=timeSettingsChanged)
    def showMoscowTime(self):
        return self._show_moscow_time

    @Property(str, notify=backgroundImagePathChanged)
    def backgroundImagePath(self):
        return self._background_image_path

    @Property(str, notify=printFontFamilyChanged)
    def printFontFamily(self):
        return self._print_font_family

    @Property(int, notify=printFontSizeChanged)
    def printFontSize(self):
        return self._print_font_size

    # --- НОВОЕ СВОЙСТВО ДЛЯ НАЧЕРТАНИЯ ШРИФТА ПЕЧАТИ ---
    @Property(str, notify=printFontStyleChanged) # <-- Добавлено
    def printFontStyle(self):                   # <-- Добавлено
        return self._print_font_style           # <-- Добавлено

    @Property(str, notify=fontFamilyChanged)
    def fontFamily(self):
        return self._font_family

    @Property(int, notify=fontSizeChanged)
    def fontSize(self):
        return self._font_size

    @Property(str, notify=fontStyleChanged)
    def fontStyle(self):
        return self._font_style

    @Slot(str)
    def setDutyOfficer(self, name):
        """Слот для установки дежурного из QML."""
        self._duty_officer = name
        self.dutyOfficerChanged.emit()

    @Slot(str)
    def setWorkplaceName(self, name):
        """Слот для установки названия рабочего места из QML."""
        self._workplace_name = name
        self.workplaceNameChanged.emit()

    # --- НОВЫЕ СЛОТЫ ДЛЯ УПРАВЛЕНИЯ СОСТОЯНИЕМ ПРИЛОЖЕНИЯ ---

    @Slot()
    def requestLoginScreen(self):
        """Слот для запроса перехода на экран входа."""
        print("Python: Запрошен переход на экран входа.")
        self.loginScreenRequested.emit()

    @Slot()
    def requestMainScreen(self):
        """Слот для запроса перехода на основной экран."""
        print("Python: Запрошен переход на основной экран.")
        # Здесь можно добавить дополнительную логику инициализации
        self.mainScreenRequested.emit()
        # Запускаем таймер только когда основной экран активен
        if not self.timer.isActive():
            self.timer.start(1000)

    # --- СЛОТЫ ДЛЯ АУТЕНТИФИКАЦИИ ---

    @Slot(str, str, result='QVariant') # Возвращаем bool (успех) или str (ошибка)
    def authenticateAndLogin(self, login, password):
        """
        Слот для аутентификации пользователя и входа в систему.
        :param login: Логин пользователя.
        :param password: Пароль пользователя.
        :return: True если успех, иначе строка с сообщением об ошибке.
        """
        print(f"Python: Попытка аутентификации для логина '{login}'...")
        
        if not login or not password:
            return "Логин и пароль не могут быть пустыми."

        # 1. Проверяем, есть ли конфигурация подключения к PG
        pg_config = self.sqlite_config_manager.get_connection_config()
        if not pg_config:
             return "Конфигурация подключения к БД не найдена. Перейдите в 'Настройки'."

        # Проверяем, не пустой ли пароль в конфиге
        if not pg_config.get('password'):
             return "Пароль подключения к БД не задан. Перейдите в 'Настройки'."

        # 2. Проверяем подключение к базе данных
        try:
            if not self.database_manager.test_connection():
                 return "Не удалось подключиться к базе данных SQLite. Проверьте настройки."
        except Exception as e:
             print(f"Python: Ошибка подключения к SQLite: {e}")
             return f"Ошибка подключения к БД: {e}"

        # 3. Пытаемся аутентифицировать пользователя
        try:
            user_data = self.database_manager.authenticate_user(login, password)
            if user_data:
                print(f"Python: Пользователь {user_data['login']} аутентифицирован успешно.")
                # TODO: Сохранить user_data в self для дальнейшего использования
                self._current_user = user_data
                # Запуск таймера уведомлений
                self._start_notification_timer() 
                # 4. Переключаемся на основной экран
                self.requestMainScreen()
                return True # Успех
            else:
                print(f"Python: Аутентификация для '{login}' не удалась.")
                return "Неверный логин или пароль."
        except Exception as e:
             print(f"Python: Неизвестная ошибка при аутентификации: {e}")
             return "Ошибка аутентификации."

    @Slot()
    def openConnectionSettings(self):
        """
        Слот для открытия диалога настроек подключения к БД.
        Пока просто выводим сообщение.
        """
        print("Python: Запрошено открытие настроек подключения к БД.")
        # TODO: Реализовать открытие диалога настроек (QML Dialog или отдельное окно)
        # Например, можно использовать QML Dialog внутри LoginView.qml
        # или создать отдельный QML компонент и управлять им отсюда.
        # Пока выведем в консоль.
        print("Python: Диалог настроек подключения (TODO).")
        return "Открытие настроек подключения (функция в разработке)."

    # --- СЛОТЫ ДЛЯ РАБОТЫ С НАСТРОЙКАМИ ПОДКЛЮЧЕНИЯ К БД ---

    @Slot(result='QVariant') # QVariantMap в Python это dict
    def getPgConnectionConfig(self):
        """
        Возвращает текущую конфигурацию подключения к PostgreSQL из SQLite.
        Вызывается QML при открытии диалога настроек подключения.
        """
        print("Python: QML запросил конфигурацию подключения к PG.")
        if self.sqlite_config_manager:
            try:
                config = self.sqlite_config_manager.get_connection_config()
                if config:
                    print(f"Python: Конфигурация PG загружена из SQLite.")
                    # Отправляем конфиг в QML (без пароля)
                    safe_config = {k: v for k, v in config.items() if k != 'password'}
                    return safe_config
                else:
                    print("Python: Конфигурация PG в SQLite не найдена.")
                    return {}
            except Exception as e:
                print(f"Python: Ошибка при получении конфигурации PG из SQLite: {e}")
        else:
            print("Python: SQLiteConfigManager не инициализирован.")
        return {}

    @Slot('QVariant', result='QVariant')
    def savePgConnectionConfig(self, new_config):
        """
        Сохраняет новую конфигурацию подключения к PostgreSQL в SQLite.
        Вызывается QML при нажатии "Сохранить" в диалоге настроек подключения.
        :param new_config: Словарь с новыми настройками подключения.
        :return: True если успешно, иначе строка с сообщением об ошибке.
        """
        print(f"Python: QML отправил обновление конфигурации подключения к PG. Исходный тип new_config: {type(new_config)}, Значение: {new_config}")
        
        # Преобразование QJSValue/QVariant в словарь Python
        if hasattr(new_config, 'toVariant'):
            new_config = new_config.toVariant()
            print(f"Python: QJSValue (new_config) преобразован в: {new_config}")

        # Проверка типа и содержимого
        if not isinstance(new_config, dict):
            error_msg = f"Некорректный тип данных конфигурации. Ожидался dict, получен {type(new_config)}."
            print(f"Python: {error_msg}")
            return error_msg

        if not new_config:
            error_msg = "Получен пустой словарь конфигурации."
            print(f"Python: {error_msg}")
            return error_msg

        # Проверяем наличие обязательных ключей
        required_keys = ["host", "port", "dbname", "user"]
        missing_keys = [key for key in required_keys if key not in new_config]
        if missing_keys:
            error_msg = f"В конфигурации отсутствуют обязательные поля: {missing_keys}"
            print(f"Python: {error_msg}")
            return error_msg

        if self.sqlite_config_manager:
            try:
                # 1. Получаем текущую конфигурацию
                current_config = self.sqlite_config_manager.get_connection_config()
                current_password = current_config.get('password') if current_config else ""

                # 2. Проверяем, передан ли новый пароль
                new_password = new_config.get('new_password')  # Из QML приходит как 'new_password'
                
                # 3. Определяем, какой пароль использовать
                if new_password and new_password.strip():  # Если передан новый пароль и он не пустой
                    final_password = new_password.strip()
                    print(f"Python: Используется новый пароль из QML")
                else:
                    final_password = current_password  # Используем старый пароль
                    print(f"Python: Используется существующий пароль из БД")

                # 4. Подготавливаем полную конфигурацию для сохранения
                try:
                    full_new_config = {
                        "host": str(new_config.get("host", "")),
                        "port": int(new_config.get("port")), # Преобразуем в int
                        "dbname": str(new_config.get("dbname", "")),
                        "user": str(new_config.get("user", "")),
                        "password": final_password  # Используем правильный пароль
                    }
                except (ValueError, TypeError) as e:
                    error_msg = f"Ошибка преобразования данных конфигурации: {e}. Проверьте правильность введенных значений (особенно порт)."
                    print(f"Python: {error_msg}")
                    return error_msg

                # 5. Проверка обязательных полей
                if not all([full_new_config['host'], full_new_config['dbname'], full_new_config['user']]):
                    error_msg = "Хост, имя БД и пользователь не могут быть пустыми строками."
                    print(f"Python: {error_msg}")
                    return error_msg

                # 6. Сохраняем в SQLite
                self.sqlite_config_manager.save_connection_config(**full_new_config)
                print("Python: Конфигурация подключения к PG успешно сохранена в SQLite.")
                return True # Успех
            except Exception as e:
                error_msg = f"Ошибка сохранения конфигурации PG в SQLite: {e}"
                print(f"Python: {error_msg}")
                import traceback
                traceback.print_exc()
                return error_msg
        else:
            error_msg = "SQLiteConfigManager не инициализирован."
            print(f"Python: {error_msg}")
            return error_msg

    # --- СЛОТЫ ДЛЯ РАБОТЫ С НАСТРОЙКАМИ ПРИЛОЖЕНИЯ ---

    @Slot(result='QVariant')
    def getFullSettings(self):
        """
        Возвращает полный словарь настроек приложения из SQLite.
        Вызывается QML при открытии экрана настроек.
        """
        print("Python: QML запросил полные настройки приложения из SQLite.")
        if self.sqlite_config_manager:
            try:
                settings = self.sqlite_config_manager.get_app_settings()
                if settings:
                    print(f"Python: Настройки приложения загружены из SQLite")
                    return settings
                else:
                    print("Python: Настройки приложения не найдены в SQLite.")
                    return {}
            except Exception as e:
                print(f"Python: Ошибка при получении настроек: {e}")
                import traceback
                traceback.print_exc()
                return {}
        else:
            print("Python: SQLiteConfigManager не инициализирован.")
            return {}

    @Slot('QVariant', result='QVariant')
    def updateSettings(self, new_settings):
        """
        Обновляет настройки приложения в SQLite из QML.
        :param new_settings: Словарь новых настроек.
        :return: True если успешно, иначе строка с сообщением об ошибке.
        """
        print("Python: QML отправил обновление настроек приложения в SQLite:", new_settings)
        
        # Преобразование QJSValue/QVariant в словарь Python
        if hasattr(new_settings, 'toVariant'):
            new_settings = new_settings.toVariant()
            print(f"Python: QJSValue (new_settings) преобразован в: {new_settings}")

        # Проверка типа и содержимого
        if not isinstance(new_settings, dict):
            error_msg = f"Некорректный тип данных настроек. Ожидался dict, получен {type(new_settings)}."
            print(f"Python: {error_msg}")
            return error_msg

        if not new_settings:
            error_msg = "Получен пустой словарь настроек."
            print(f"Python: {error_msg}")
            return error_msg

        if self.sqlite_config_manager:
            try:
                success = self.sqlite_config_manager.update_app_settings(new_settings)
                if success:
                    print("Python: Настройки приложения успешно обновлены в SQLite.")
                    # --- Обновляем локальные свойства ApplicationData в реальном времени ---
                    updated_props = False
                    updated_time_props = False # Флаг для отслеживания изменений времени
                    # Обновляем локальные свойства ApplicationData в реальном времени
                    updated_properties = False
                    if 'workplace_name' in new_settings and new_settings['workplace_name'] is not None:
                        self._workplace_name = str(new_settings['workplace_name'])
                        self.workplaceNameChanged.emit()
                        updated_properties = True
                        print(f"Python: Обновлено workplace_name: {self._workplace_name}")
                    
                    if 'post_number' in new_settings and new_settings['post_number'] is not None:
                        self._post_number = str(new_settings['post_number'])
                        self.postNumberChanged.emit()
                        updated_properties = True
                        print(f"Python: Обновлен post_number: {self._post_number}")

                    if 'post_name' in new_settings and new_settings['post_name'] is not None:
                        self._post_name = str(new_settings['post_name'])
                        self.postNameChanged.emit()
                        updated_properties = True
                        print(f"Python: Обновлен post_name: {self._post_name}")
                    
                    if 'custom_time_label' in new_settings:
                        self._custom_time_label = str(new_settings['custom_time_label'])
                        self.timeSettingsChanged.emit() # Уведомляем об изменении метки
                        updated_props = True
                        updated_time_props = True
                        print(f"Python: Обновлен custom_time_label: {self._custom_time_label}")

                    if 'custom_time_offset_seconds' in new_settings:
                         # Убедимся, что это целое число
                         try:
                             offset_secs = int(new_settings['custom_time_offset_seconds'])
                             self._custom_time_offset_seconds = offset_secs
                             updated_props = True
                             updated_time_props = True
                             print(f"Python: Обновлен custom_time_offset_seconds: {self._custom_time_offset_seconds}")
                         except (ValueError, TypeError):
                             print(f"Python: Ошибка преобразования custom_time_offset_seconds: {new_settings['custom_time_offset_seconds']}")

                    if 'show_moscow_time' in new_settings:
                        # Преобразуем в булево
                        self._show_moscow_time = bool(new_settings['show_moscow_time'])
                        self.timeSettingsChanged.emit() # Уведомляем об изменении флага показа
                        updated_props = True
                        updated_time_props = True
                        print(f"Python: Обновлен show_moscow_time: {self._show_moscow_time}")
                        
                    if 'moscow_time_offset_seconds' in new_settings:
                         # Убедимся, что это целое число
                         try:
                             moscow_offset_secs = int(new_settings['moscow_time_offset_seconds'])
                             self._moscow_time_offset_seconds = moscow_offset_secs
                             updated_props = True
                             updated_time_props = True
                             print(f"Python: Обновлен moscow_time_offset_seconds: {self._moscow_time_offset_seconds}")
                         except (ValueError, TypeError):
                             print(f"Python: Ошибка преобразования moscow_time_offset_seconds: {new_settings['moscow_time_offset_seconds']}")

                    # --- Обновляем свойства, связанные с внешним видом ---
                    if 'background_image_path' in new_settings and new_settings['background_image_path'] is not None:
                        self._background_image_path = str(new_settings['background_image_path']) if new_settings['background_image_path'] else None
                        self.backgroundImagePathChanged.emit() # <-- Сигнал для backgroundImagePath
                        updated_properties = True
                        print(f"Python: Обновлен background_image_path: {self._background_image_path}")

                    if 'use_persistent_reminders' in new_settings:
                        # Преобразуем 1/0 из SQLite в True/False
                        self._use_persistent_reminders = bool(new_settings['use_persistent_reminders'])
                        print(f"Python: Обновлен _use_persistent_reminders: {self._use_persistent_reminders}")
                        # updated_props или другой флаг можно добавить, если нужно уведомлять QML об этом изменении

                    if 'sound_enabled' in new_settings:
                        # Преобразуем 1/0 из SQLite в True/False
                        self._sound_enabled = bool(new_settings['sound_enabled'])
                        print(f"Python: Обновлен _sound_enabled: {self._sound_enabled}")
                        # updated_props или другой флаг можно добавить, если нужно уведомлять QML об этом изменении

                    if updated_properties:
                        print("Python: Локальные свойства обновлены.")
                        self.settingsChanged.emit()
                        # --- Если изменялись настройки времени, обновляем рассчитываемые времена ---
                        if updated_time_props:
                            print("Python: Обнаружены изменения настроек времени. Пересчет localTime/moscowTime...")
                            self.update_time() # Пересчитываем localTime и moscowTime
                        # --- ---
                        # Уведомляем QML об общем изменении настроек (если нужно)
                        # self.settingsChanged.emit() # (если такой сигнал используется глобально)

                    # --- НОВОЕ: Обновление локальных свойств ApplicationData для шрифта печати ---
                    updated_print_props = False
                    if 'print_font_family' in new_settings:
                        self._print_font_family = new_settings['print_font_family']
                        self.printFontFamilyChanged.emit()
                        updated_print_props = True
                        print(f"Python: Обновлен print_font_family: {self._print_font_family}")

                    if 'print_font_size' in new_settings:
                        self._print_font_size = new_settings['print_font_size']
                        self.printFontSizeChanged.emit()
                        updated_print_props = True
                        print(f"Python: Обновлен print_font_size: {self._print_font_size}")
                    
                    # --- ДОБАВЛЕНО: Обновление начертания шрифта печати ---
                    if 'print_font_style' in new_settings:
                        self._print_font_style = new_settings['print_font_style']
                        self.printFontStyleChanged.emit() # <-- Добавлено
                        updated_print_props = True
                        print(f"Python: Обновлен print_font_style: {self._print_font_style}")

                    # Внутри updateSettings(), после:
                    if 'font_family' in new_settings:
                        self._font_family = new_settings['font_family']
                        self.fontFamilyChanged.emit()
                        updated_props = True

                    if 'font_size' in new_settings:
                        self._font_size = int(new_settings['font_size'])
                        self.fontSizeChanged.emit()
                        updated_props = True

                    if 'font_style' in new_settings:
                        self._font_style = new_settings['font_style']
                        self.fontStyleChanged.emit()
                        updated_props = True
                    
                    return True
                else:
                    error_msg = "Не удалось обновить настройки приложения в SQLite."
                    print(f"Python: {error_msg}")
                    return error_msg
                    
            except Exception as e:
                error_msg = f"Ошибка БД SQLite при обновлении настроек: {e}"
                print(f"Python: {error_msg}")
                import traceback
                traceback.print_exc()
                return error_msg
        else:
            error_msg = "SQLiteConfigManager не инициализирован."
            print(f"Python: {error_msg}")
            return error_msg

    # --- СЛОТЫ ДЛЯ РАБОТЫ С ДОЛЖНОСТНЫМИ ЛИЦАМИ (ПОЛЬЗОВАТЕЛЯМИ) ---

    @Slot(result=list) # Возвращаем список словарей
    def getDutyOfficersList(self):
        """Возвращает список всех активных должностных лиц для QML."""
        try:
            if self.database_manager:
                officers = self.database_manager.get_all_users()
            else:
                # Заглушка, если нет подключения
                officers = [
                    {'id': 1, 'rank': 'ст. лейтенант', 'last_name': 'Иванов', 'first_name': 'Иван', 'middle_name': 'Иванович', 'phone': '123-456-789', 'is_active': 1, 'is_admin': 0},
                    {'id': 2, 'rank': 'лейтенант', 'last_name': 'Петров', 'first_name': 'Пётр', 'middle_name': 'Петрович', 'phone': '987-654-321', 'is_active': 1, 'is_admin': 0},
                ]
            print(f"Python: QML запросил список должностных лиц. Найдено: {len(officers)}")
            # ВАЖНО: PySide/Qt может требовать простые типы данных.
            # Если объекты row_factory sqlite3.Row не сериализуются корректно,
            # преобразуем их в словари явно.
            result = []
            for officer in officers:
                # officer уже должен быть dict благодаря row_factory, но на всякий случай
                if isinstance(officer, dict):
                    result.append(officer)
                else:
                    # Если это sqlite3.Row, преобразуем
                    result.append(dict(officer))
            return result
        except Exception as e:
            print(f"Python: Ошибка при получении списка должностных лиц: {e}")
            import traceback
            traceback.print_exc() # Для более детального лога ошибок
            return []

    @Slot('QVariant', result=int) # Принимает QVariantMap (dict), возвращает int (ID нового пользователя или -1 в случае ошибки)
    def addDutyOfficer(self, officer_data):
        """
        Добавляет нового должностного лица в PostgreSQL.
        :param officer_data: Словарь с данными нового пользователя.
        :return: ID нового пользователя, если успешно, иначе -1.
        """
        print("Python: QML отправил запрос на добавление нового пользователя (должностного лица).")
        print(f"Python: Исходные данные officer_data (тип: {type(officer_data)}): {officer_data}")

        # --- НОВОЕ: Преобразование QJSValue/QVariant в словарь Python ---
        # Это решает проблему "QJSValue object at ..."
        if hasattr(officer_data, 'toVariant'): # Проверка для QJSValue
            officer_data = officer_data.toVariant()
            print(f"Python: QJSValue (officer_data) преобразован в: {officer_data}")
        # --- ---

        # --- УЛУЧШЕННАЯ проверка типа и содержимого ---
        if not isinstance(officer_data, dict):
             print(f"Python: Ошибка - officer_data не является словарем. Получен тип: {type(officer_data)}")
             return -1 # Возвращаем -1 в случае ошибки типа

        if not officer_data:
             print("Python: Ошибка - officer_data пуст.")
             return -1 # Возвращаем -1 в случае пустых данных
        # --- ---

        if self.database_manager:
            try:
                # --- Подготовка данных для передачи в менеджер БД ---
                # Убедимся, что все ключи присутствуют и имеют правильный тип/значение по умолчанию
                prepared_data = {
                    'rank': str(officer_data.get('rank', '')).strip(),
                    'last_name': str(officer_data.get('last_name', '')).strip(),
                    'first_name': str(officer_data.get('first_name', '')).strip(),
                    'middle_name': str(officer_data.get('middle_name', '')).strip() or None, # '' или None -> None
                    'phone': str(officer_data.get('phone', '')).strip() or None, # '' или None -> None
                    'is_active': 1 if officer_data.get('is_active') else 0, # Преобразуем в 1/0
                    'is_admin': 1 if officer_data.get('is_admin') else 0,   # Преобразуем в 1/0
                    'login': str(officer_data.get('login', '')).strip(), # <-- Новое поле
                    'new_password': str(officer_data.get('new_password', '')) if officer_data.get('new_password') else '', # <-- Новое поле
                }

                # --- Базовая валидация обязательных полей ---
                if not all([prepared_data['rank'], prepared_data['last_name'], prepared_data['first_name'], prepared_data['login']]): # <-- Обновить проверку
                    print("Python: Ошибка - Звание, Фамилия, Имя и Логин обязательны для заполнения.")
                    return -1
                # --- ---

                print(f"Python: Подготовленные данные для добавления: {prepared_data}")

                # --- Вызов метода менеджера БД ---
                # Убедитесь, что метод в вашем SQLiteDatabaseManager называется create_user
                new_id = self.database_manager.create_user(prepared_data) # Используем create_user
                # --- ---

                if isinstance(new_id, int) and new_id > 0:
                    print(f"Python: Новый пользователь успешно добавлен с ID: {new_id}")
                    return new_id # Возвращаем ID нового пользователя
                else:
                    print(f"Python: Менеджер БД вернул некорректный ID: {new_id}")
                    return -1 # Возвращаем -1, если ID некорректный

            except Exception as e:
                # --- Улучшенная обработка исключений ---
                print(f"Python: Исключение при добавлении пользователя: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc() # Печатаем трассировку для отладки
                return -1 # Возвращаем -1 в случае любого исключения
                # --- ---
        else:
             print("Python: Ошибка - Нет подключения к БД SQLite (database_manager не инициализирован).")
             return -1 # Возвращаем -1, если нет подключения к БД

    @Slot(int, 'QVariant', result=bool) # Принимает int (ID) и QVariantMap (dict), возвращает bool
    def updateDutyOfficer(self, officer_id: int, officer_data: 'QVariant') -> bool:
        """
        Обновляет данные существующего должностного лица в PostgreSQL.
        :param officer_id: ID пользователя для обновления.
        :param officer_ Словарь с новыми данными пользователя.
        :return: True если успешно, иначе False.
        """
        print(f"Python: QML отправил запрос на обновление пользователя (должностного лица) с ID {officer_id}.")
        print(f"Python: Исходные данные officer_data (тип: {type(officer_data)}): {officer_data}")

        # --- Преобразование QJSValue/QVariant в словарь Python ---
        if hasattr(officer_data, 'toVariant'):
            officer_data = officer_data.toVariant()
            print(f"Python: QJSValue (officer_data) преобразован в: {officer_data}")
        # --- ---

        # --- УЛУЧШЕННАЯ проверка типа и содержимого ---
        if not isinstance(officer_data, dict):
             print(f"Python: Ошибка - officer_data не является словарем. Получен тип: {type(officer_data)}")
             return False

        if not officer_data:
             print("Python: Ошибка - officer_data пуст.")
             return False
        # --- ---

        if self.database_manager:
            try:
                # --- Подготовка данных для передачи в менеджер БД ---
                # Фильтруем и готовим только разрешенные поля
                prepared_data = {}
                allowed_fields = ['rank', 'last_name', 'first_name', 'middle_name', 'phone', 'is_active', 'is_admin', 'login', 'new_password']
                for key, value in officer_data.items():
                    if key in allowed_fields:
                        if key in ['is_active', 'is_admin']:
                            prepared_data[key] = 1 if value else 0 # Преобразуем в 1/0
                        else: # rank, last_name, first_name, middle_name, phone
                            prepared_data[key] = str(value).strip() if value is not None else None
                            # Для необязательных текстовых полей: пустая строка -> None
                            if key in ['middle_name', 'phone'] and prepared_data[key] == "":
                                prepared_data[key] = None

                print(f"Python: Подготовленные данные для обновления: {prepared_data}")

                # --- Базовая валидация обязательных полей ---
                if not all([prepared_data.get('rank'), prepared_data.get('last_name'), prepared_data.get('first_name')]):
                     print("Python: Ошибка - Звание, Фамилия и Имя обязательны для заполнения.")
                     return False
                # --- ---

                # --- Вызов метода менеджера БД ---
                # Убедитесь, что метод в вашем PostgreSQLDatabaseManager называется update_user
                success = self.database_manager.update_user(officer_id, prepared_data) # Используем update_user
                # --- ---

                if success:
                    print(f"Python: Пользователь с ID {officer_id} успешно обновлен.")
                    return True
                else:
                    print(f"Python: Не удалось обновить пользователя с ID {officer_id}.")
                    return False

            except Exception as e:
                print(f"Python: Исключение при обновлении пользователя {officer_id}: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
             print("Python: Ошибка - Нет подключения к БД SQLite.")
             return False

    @Slot(int, result=bool) # Принимает int (ID), возвращает bool
    def deleteDutyOfficer(self, officer_id: int) -> bool:
        """
        Полностью удаляет должностное лицо из PostgreSQL.
        :param officer_id: ID пользователя для удаления.
        :return: True если успешно, иначе False.
        """
        print(f"Python: QML отправил запрос на полное удаление пользователя с ID {officer_id}.")

        if not isinstance(officer_id, int) or officer_id <= 0:
             print(f"Python: Ошибка - Некорректный ID пользователя: {officer_id}")
             return False

        if self.database_manager:
            try:
                # --- Вызов обновленного метода менеджера БД ---
                # Ранее: success = self.database_manager.deactivate_user(officer_id)
                success = self.database_manager.delete_user(officer_id) # <-- Используем delete_user
                # --- ---

                if success:
                    print(f"Python: Пользователь с ID {officer_id} успешно удален из БД.")
                    return True
                else:
                    print(f"Python: Не удалось удалить пользователя с ID {officer_id}.")
                    return False

            except Exception as e:
                print(f"Python: Исключение при удалении пользователя {officer_id}: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
             print("Python: Ошибка - Нет ����дк��ючения к ������Д PostgreSQL.")
             return False
    
    
    # --- НОВЫЙ СЛОТ: Получение списка ВСЕХ пользователей ---
    @Slot(result=list)
    def getAllDutyOfficersList(self):
        """
        Возвращает список ВСЕХ д��лж����остных лиц (активных и неактивных) для QML.
        Используется, например, для выбора дежурного из полного списка.
        """
        try:
            if self.database_manager:
                # Вызываем метод, который теперь возвращает всех пользователей
                officers = self.database_manager.get_all_users()  # <-- Изменено на get_all_users
            else:
                # Заглушка, если нет подключения
                officers = [
                    {'id': 1, 'rank': 'ст. лейтенант (заглушка)', 'last_name': 'Иванов', 'first_name': 'Иван', 'middle_name': 'Иванович', 'phone': '123-456-789', 'is_active': 1, 'is_admin': 0, 'login': 'ivanov_ii'},
                    {'id': 2, 'rank': 'лейтенант (заглушка)', 'last_name': 'Петров', 'first_name': 'Пётр', 'middle_name': 'Петрович', 'phone': '987-654-321', 'is_active': 0, 'is_admin': 0, 'login': 'petrov_pp'}, # <-- Неактивный
                ]
            print(f"Python: QML запросил список ВСЕХ должностных лиц. Найдено: {len(officers)}")
            
            # Преобразуем в нужный формат
            result = []
            for officer in officers:
                if isinstance(officer, dict):
                    result.append(officer)
                else:
                    result.append(dict(officer))
            print(f"Python: Отправка списка ВСЕХ в QML: {result}")
            return result
        except Exception as e:
            print(f"Python: Ошибка при получении списка ВСЕХ должностных лиц: {e}")
            import traceback
            traceback.print_exc()
            return []
    # --- ---

    @Slot(int) # Принимает int (ID дежурного)
    # --- ---
    @Slot(int)
    def setCurrentDutyOfficer(self, officer_id: int):
        """
        Устанавливает выбранного дежурного.
        :param officer_id: ID нового дежурного.
        """
        print(f"Python: QML установил текущего дежурного: ID {officer_id}")
        try:
            # --- Отладка: Проверка database_manager ---
            if not hasattr(self, 'database_manager') or self.database_manager is None:
                 print("Python: Ошибка - Менеджер БД SQLite (database_manager) не инициализирован.")
                 return
            print("Python: Менеджер БД SQLite (database_manager) инициализирован.")
            # --- ---

            # --- Отладка: Вызов метода менеджера БД ---
            print(f"Python: Вызов self.database_manager.set_current_duty_officer({officer_id})...")
            self.database_manager.set_current_duty_officer(officer_id) # <-- Вызываем метод менеджера БД
            print("Python: Метод set_current_duty_officer успешно выполнен.")
            # --- ---
            
            # --- Отладка: Получение данных о новом дежурном ---
            print(f"Python: Вызов self.database_manager.get_duty_officer_by_id({officer_id})...")
            officer = self.database_manager.get_duty_officer_by_id(officer_id) # <-- Вызываем метод менеджера БД
            print(f"Python: Получены данные дежурного: {officer}")
            # --- ---
            
            # --- Отладка: Обновление свойства _duty_officer ---
            if officer:
                # Формируем строку "Звание Фамилия И.О."
                name = f"{officer['rank']} {officer['last_name']} {officer['first_name'][0]}."
                if officer['middle_name']:
                    name += f"{officer['middle_name'][0]}."
                old_duty_officer = self._duty_officer
                self._duty_officer = name
                print(f"Python: Свойство _duty_officer обновлено с '{old_duty_officer}' на '{self._duty_officer}'")
            else:
                old_duty_officer = self._duty_officer
                self._duty_officer = "Не выбран"
                print(f"Python: Дежурный не найден. Свойство _duty_officer обновлено с '{old_duty_officer}' на '{self._duty_officer}'")
            # --- ---
            
            # --- Отладка: Эмитирование сигнала ---
            print("Python: Эмитирование сигнала dutyOfficerChanged...")
            self.dutyOfficerChanged.emit() # Уведомляем QML об изменении
            print("Python: Сигнал dutyOfficerChanged эмитирован.")
            # --- ---
            
            print(f"Python: Текущий дежурный установлен: {self._duty_officer}")
        except Exception as e:
            print(f"Python: Ошибка установки текущего дежурного: {e}")
            import traceback
            traceback.print_exc()

    # --- Новые слоты для управления окном из QML ---
    @Slot()
    def minimizeToTray(self):
        """Слот для сворачивания окна в трей по запросу из QML."""
        print("Вызов minimizeToTray из QML") # Для отладки
        if self.tray_icon and self.tray_icon.isVisible():
            if not self.close_confirmation_shown:
                # Создаем QMessageBox БЕЗ родителя QWidget
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setWindowTitle("Программа свернута")
                msg_box.setText("Программа продолжит выполнение в системном трее.\nДля завершения программы выберите 'Выход' в контекстном меню на значке программы.")
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.exec() # Показываем окно
                self.close_confirmation_shown = True

            self.window.hide() # Скрываем QML окно
            print("Окно скрыто") # Для отладки
        else:
             print("Трей не доступен или не показан") # Для отладки

    @Slot()
    def restore_window(self):
        if self.window:
            self.window.showNormal()
            self.window.raise_()
            self.window.requestActivate()
            self.close_confirmation_shown = False # Сброс флага
            print("Окно восстановлено") # Для отладки


    # --- СЛОТЫ ДЛЯ РАБОТЫ С ALGORITHMS ---

    @Slot(result=list)
    def getAllAlgorithmsList(self) -> list:
        """Возвращает список всех алгоритмов для QML."""
        try:
            if self.database_manager:
                algorithms = self.database_manager.get_all_algorithms()
            else:
                # Заглушка, если нет подключения
                algorithms = [
                    {'id': 1, 'name': 'Алгоритм 1 (заглушка)', 'category': 'повседневная деятельность', 'time_type': 'оперативное', 'description': 'Описание алгоритма 1'},
                    {'id': 2, 'name': 'Алгоритм 2 (заглушка)', 'category': 'кризисные ситуации', 'time_type': 'астрономическое', 'description': 'Описание алгоритма 2'},
                ]
            print(f"Python: QML запросил список алгоритмов. Найдено: {len(algorithms)}")
            result = []
            for alg in algorithms:
                if isinstance(alg, dict):
                    result.append(alg)
                else:
                    result.append(dict(alg))
            return result
        except Exception as e:
            print(f"Python: Ошибка при получении списка алгоритмов: {e}")
            import traceback
            traceback.print_exc()
            return []

    @Slot(int, result='QVariant')
    def getAlgorithmById(self, algorithm_id: int) -> 'QVariant':
        """Возвращает данные алгоритма по ID для QML."""
        try:
            if not isinstance(algorithm_id, int) or algorithm_id <= 0:
                print(f"Python: Ошибка - Некорректный ID алгоритма: {algorithm_id}")
                return None

            if self.database_manager:
                algorithm = self.database_manager.get_algorithm_by_id(algorithm_id)
                if algorithm:
                    print(f"Python: QML запросил алгоритм ID {algorithm_id}. Найден: {algorithm['name']}")
                    return algorithm
                else:
                    print(f"Python: Алгоритм ID {algorithm_id} не найден.")
                    return None
            else:
                print("Python: Ошибка - Нет подключения к БД SQLite.")
                return None
        except Exception as e:
            print(f"Python: Ошибка при получении алгоритма ID {algorithm_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    @Slot('QVariant', result=int)
    def addAlgorithm(self, algorithm_data: 'QVariant') -> int:
        """Добавляет новый алгоритм."""
        print("Python: QML отправил запрос на добавление нового алгоритма.")
        
        if hasattr(algorithm_data, 'toVariant'):
            algorithm_data = algorithm_data.toVariant()
            print(f"Python: QJSValue (algorithm_data) преобразован в: {algorithm_data}")

        if not isinstance(algorithm_data, dict):
            print(f"Python: Ошибка - algorithm_data не является словарем. Получен тип: {type(algorithm_data)}")
            return -1
        if not algorithm_data:
            print("Python: Ошибка - algorithm_data пуст.")
            return -1

        if self.database_manager:
            try:
                # Подготовка данных
                required_fields = ['name', 'category', 'time_type']
                missing_fields = [field for field in required_fields if field not in algorithm_data or not algorithm_data[field]]
                if missing_fields:
                    print(f"Python: Ошибка - Отсутствуют обязательные поля: {missing_fields}")
                    return -1

                prepared_data = {
                    'name': str(algorithm_data.get('name', '')).strip(),
                    'category': str(algorithm_data.get('category', '')).strip(),
                    'time_type': str(algorithm_data.get('time_type', '')).strip(),
                    'description': str(algorithm_data.get('description', '')).strip() if algorithm_data.get('description') is not None else ""
                }

                if not all([prepared_data['name'], prepared_data['category'], prepared_data['time_type']]):
                    print("Python: Ошибка - Название, категория и тип времени не могут быть пустыми.")
                    return -1

                new_id = self.database_manager.create_algorithm(prepared_data)
                if isinstance(new_id, int) and new_id > 0:
                    print(f"Python: Новый алгоритм успешно добавлен с ID: {new_id}")
                    return new_id
                else:
                    print(f"Python: Менеджер БД вернул некорректный ID: {new_id}")
                    return -1
            except Exception as e:
                print(f"Python: Исключение при добавлении алгоритма: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return -1
        else:
            print("Python: Ошибка - Нет подключения к БД SQLite.")
            return -1

    @Slot(int, 'QVariant', result=bool)
    def updateAlgorithm(self, algorithm_id: int, algorithm_data: 'QVariant') -> bool:
        """Обновляет существующий алгоритм."""
        print(f"Python: QML отправил запрос на обновление алгоритма ID {algorithm_id}.")
        
        if hasattr(algorithm_data, 'toVariant'):
            algorithm_data = algorithm_data.toVariant()
            print(f"Python: QJSValue (algorithm_data) преобразован в: {algorithm_data}")

        if not isinstance(algorithm_data, dict):
            print(f"Python: Ошибка - algorithm_data не является словарем. Получен тип: {type(algorithm_data)}")
            return False
        if not algorithm_data:
            print("Python: Ошибка - algorithm_data пуст.")
            return False
        if not isinstance(algorithm_id, int) or algorithm_id <= 0:
            print(f"Python: Ошибка - Некорректный ID алгоритма: {algorithm_id}")
            return False

        if self.database_manager:
            try:
                # Подготовка данных (фильтрация разрешенных полей)
                allowed_fields = ['name', 'category', 'time_type', 'description']
                prepared_data = {}
                for key, value in algorithm_data.items():
                    if key in allowed_fields:
                        if key in ['name', 'category', 'time_type']:
                            prepared_data[key] = str(value).strip() if value is not None else ""
                        else: # description
                            prepared_data[key] = str(value).strip() if value is not None else ""

                if not prepared_data:
                    print("Python: Ошибка - Нет данных для обновления.")
                    return False

                success = self.database_manager.update_algorithm(algorithm_id, prepared_data)
                if success:
                    print(f"Python: Алгоритм ID {algorithm_id} успешно обновлен.")
                    return True
                else:
                    print(f"Python: Не удалось обновить алгоритм ID {algorithm_id}.")
                    return False
            except Exception as e:
                print(f"Python: Исключение при обновлении алгоритма {algorithm_id}: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("Python: Ошибка - Нет подключения к БД SQLite.")
            return False

    @Slot(int, result=bool)
    def deleteAlgorithm(self, algorithm_id: int) -> bool:
        """Удаляет алгоритм."""
        print(f"Python: QML отправил запрос на удаление алгоритма ID {algorithm_id}.")
        
        if not isinstance(algorithm_id, int) or algorithm_id <= 0:
            print(f"Python: Ошибка - Некорректный ID алгоритма: {algorithm_id}")
            return False

        if self.database_manager:
            try:
                success = self.database_manager.delete_algorithm(algorithm_id)
                if success:
                    print(f"Python: Алгоритм ID {algorithm_id} успешно удален.")
                    return True
                else:
                    print(f"Python: Не удалось удалить алгоритм ID {algorithm_id}. Возможно, есть выполнения или другие ограничения.")
                    return False # QML может показать сообщение пользователю
            except Exception as e:
                print(f"Python: Исключение при удалении алгоритма {algorithm_id}: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("Python: Ошибка - Нет подключения к БД SQLite.")
            return False

    @Slot(int, result=int)
    def duplicateAlgorithm(self, original_algorithm_id: int) -> int:
        """Создает копию алгоритма."""
        print(f"Python: QML отправил запрос на дублирование алгоритма ID {original_algorithm_id}.")
        
        if not isinstance(original_algorithm_id, int) or original_algorithm_id <= 0:
            print(f"Python: Ошибка - Некорректный ID оригинального алгоритма: {original_algorithm_id}")
            return -1

        if self.database_manager:
            try:
                new_algorithm_id = self.database_manager.duplicate_algorithm(original_algorithm_id)
                if new_algorithm_id != -1:
                    print(f"Python: Алгоритм ID {original_algorithm_id} успешно дублирован. Новый ID: {new_algorithm_id}")
                    return new_algorithm_id
                else:
                    print(f"Python: Не удалось дублировать алгоритм ID {original_algorithm_id}.")
                    return -1
            except Exception as e:
                print(f"Python: Исключение при дублировании алгоритма {original_algorithm_id}: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return -1
        else:
            print("Python: Ошибка - Нет подключения к БД SQLite.")
            return -1

    # --- СЛОТЫ ДЛЯ РАБОТЫ С ACTIONS ---

    @Slot(int, result=list)
    def getActionsByAlgorithmId(self, algorithm_id: int) -> list:
        """Возвращает список действий для заданного алгоритма."""
        try:
            if not isinstance(algorithm_id, int) or algorithm_id <= 0:
                print(f"Python: Ошибка - Некорректный ID алгоритма: {algorithm_id}")
                return []

            if self.database_manager:
                actions = self.database_manager.get_actions_by_algorithm_id(algorithm_id)
                print(f"Python: QML запросил действия для алгоритма ID {algorithm_id}. Найдено: {len(actions)}")
                result = []
                for action in actions:
                    if isinstance(action, dict):
                        result.append(action)
                    else:
                        result.append(dict(action))
                return result
            else:
                print("Python: Ошибка - Нет подключения к БД SQLite.")
                return []
        except Exception as e:
            print(f"Python: Ошибка при получении действий для алгоритма ID {algorithm_id}: {e}")
            import traceback
            traceback.print_exc()
            return []

    @Slot(int, result='QVariant')
    def getActionById(self, action_id: int) -> 'QVariant':
        """Возвращает данные действия по ID."""
        try:
            if not isinstance(action_id, int) or action_id <= 0:
                print(f"Python: Ошибка - Некорректный ID действия: {action_id}")
                return None

            if self.database_manager:
                action = self.database_manager.get_action_by_id(action_id)
                if action:
                    print(f"Python: QML запросил действие ID {action_id}.")
                    print(f"Python: action keys = {list(action.keys())}")
                    print(f"Python: action['technical_text'] = {action.get('technical_text')}")
                    return action
                else:
                    print(f"Python: Действие ID {action_id} не найдено.")
                    return None
            else:
                print("Python: Ошибка - Нет подключения к БД SQLite.")
                return None
        except Exception as e:
            print(f"Python: Ошибка при получении действия ID {action_id}: {e}")
            import traceback
            traceback.print_exc()
            return None

    @Slot('QVariant', result=int)
    def addAction(self, action_data: 'QVariant') -> int:
        """Добавляет новое действие."""
        print("Python: QML отправил запрос на добавление нового действия.")
        
        if hasattr(action_data, 'toVariant'):
            action_data = action_data.toVariant()
            print(f"Python: QJSValue (action_data) преобразован в: {action_data}")

        if not isinstance(action_data, dict):
            print(f"Python: Ошибка - action_data не является словарем. Получен тип: {type(action_data)}")
            return -1
        if not action_data:
            print("Python: Ошибка - action_data пуст.")
            return -1

        if self.database_manager:
            try:
                required_fields = ['algorithm_id', 'description']
                missing_fields = [field for field in required_fields if field not in action_data or not action_data[field]]
                if missing_fields:
                    print(f"Python: Ошибка - Отсутствуют обязательные поля: {missing_fields}")
                    return -1

                # Подготовка данных, включая преобразование INTERVAL из строки QML
                prepared_data = {}
                for key, value in action_data.items():
                    if key in ['algorithm_id', 'description', 'technical_text', 'contact_phones', 'report_materials']:
                        prepared_data[key] = str(value).strip() if value is not None else (None if key in ['contact_phones', 'report_materials'] else "")
                    elif key in ['start_offset', 'end_offset']:
                        # Ожидаем, что QML передаст строку вроде '2 days 3 hours' или '03:30:00'
                        # psycopg2 может автоматически преобразовать строку в INTERVAL, если поле в БД типа INTERVAL
                        # Но для надежности можно оставить как строку, БД сама преобразует
                        prepared_data[key] = value if value is not None else None
                
                # Особая обработка algorithm_id
                try:
                    prepared_data['algorithm_id'] = int(prepared_data['algorithm_id'])
                except (ValueError, TypeError):
                    print("Python: Ошибка - algorithm_id должен быть целым числом.")
                    return -1

                new_id = self.database_manager.create_action(prepared_data)
                if isinstance(new_id, int) and new_id > 0:
                    print(f"Python: Новое действие успешно добавлено с ID: {new_id}")
                    return new_id
                else:
                    print(f"Python: Менеджер БД вернул некорректный ID: {new_id}")
                    return -1
            except Exception as e:
                print(f"Python: Исключение при добавлении действия: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return -1
        else:
            print("Python: Ошибка - Нет подключения к БД SQLite.")
            return -1

    @Slot(int, 'QVariant', result=bool)
    def updateAction(self, action_id: int, action_data: 'QVariant') -> bool:
        """Обновляет существующее действие."""
        print(f"Python: QML отправил запрос на обновление действия ID {action_id}.")
        
        if hasattr(action_data, 'toVariant'):
            action_data = action_data.toVariant()
            print(f"Python: QJSValue (action_data) преобразован в: {action_data}")

        if not isinstance(action_data, dict):
            print(f"Python: Ошибка - action_data не является словарем. Получен тип: {type(action_data)}")
            return False
        if not action_data:
            print("Python: Ошибка - action_data пуст.")
            return False
        if not isinstance(action_id, int) or action_id <= 0:
            print(f"Python: Ошибка - Некорректный ID действия: {action_id}")
            return False

        if self.database_manager:
            try:
                # Подготовка данных (фильтрация разрешенных полей)
                allowed_fields = ['description', 'technical_text', 'start_offset', 'end_offset', 'contact_phones', 'report_materials']
                prepared_data = {}
                for key, value in action_data.items():
                    if key in allowed_fields:
                        if key in ['description', 'technical_text', 'contact_phones', 'report_materials']:
                            prepared_data[key] = str(value).strip() if value is not None else (None if key in ['contact_phones', 'report_materials'] else "")
                        elif key in ['start_offset', 'end_offset']:
                            # Аналогично добавлению
                            prepared_data[key] = value if value is not None else None

                if not prepared_data:
                    print("Python: Ошибка - Нет данных для обновления.")
                    return False

                success = self.database_manager.update_action(action_id, prepared_data)
                if success:
                    print(f"Python: Действие ID {action_id} успешно обновлено.")
                    return True
                else:
                    print(f"Python: Не удалось обновить действие ID {action_id}.")
                    return False
            except Exception as e:
                print(f"Python: Исключение при обновлении действия {action_id}: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("Python: Ошибка - Нет подключения к БД SQLite.")
            return False

    @Slot(int, result=bool)
    def deleteAction(self, action_id: int) -> bool:
        """Удаляет действие."""
        print(f"Python: QML отправил запрос на удаление действия ID {action_id}.")
        
        if not isinstance(action_id, int) or action_id <= 0:
            print(f"Python: Ошибка - Некорректный ID действия: {action_id}")
            return False

        if self.database_manager:
            try:
                success = self.database_manager.delete_action(action_id)
                if success:
                    print(f"Python: Действие ID {action_id} успешно удалено.")
                    return True
                else:
                    print(f"Python: Не удалось удалить действие ID {action_id}. Возможно, есть выполнения или другие ограничения.")
                    return False
            except Exception as e:
                print(f"Python: Исключение при удалении действия {action_id}: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("Python: Ошибка - Нет подключения к БД SQLite.")
            return False

    @Slot(int, result=int) # Для дублирования в том же алгоритме
    @Slot(int, int, result=int) # Для дублирования в другом алгоритме
    def duplicateAction(self, original_action_id: int, new_algorithm_id: int = None) -> int:
        """Создает копию действия."""
        print(f"Python: QML отправил запрос на дублирование действия ID {original_action_id} (новый алгоритм ID: {new_algorithm_id}).")
        
        if not isinstance(original_action_id, int) or original_action_id <= 0:
            print(f"Python: Ошибка - Некорректный ID оригинального действия: {original_action_id}")
            return -1

        if self.database_manager:
            try:
                # Передаем None как есть, если new_algorithm_id не передан или равен 0
                final_new_alg_id = new_algorithm_id if new_algorithm_id is not None and new_algorithm_id > 0 else None
                new_action_id = self.database_manager.duplicate_action(original_action_id, final_new_alg_id)
                if new_action_id != -1:
                    print(f"Python: Действие ID {original_action_id} успешно дублировано. Новый ID: {new_action_id}")
                    return new_action_id
                else:
                    print(f"Python: Не удалось дублировать действие ID {original_action_id}.")
                    return -1
            except Exception as e:
                print(f"Python: Исключение при дублировании действия {original_action_id}: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return -1
        else:
            print("Python: Ошибка - Нет подключения к БД SQLite.")
            return -1


    @Slot(int, result=bool)
    def moveAlgorithmUp(self, algorithm_id: int) -> bool:
        """
        Перемещает алгоритм вверх в списке.
        :param algorithm_id: ID алгоритма для перемещения.
        :return: True, если успешно, иначе False.
        """
        print(f"Python: QML отправил запрос на перемещение алгоритма ID {algorithm_id} вверх.")
        if not isinstance(algorithm_id, int) or algorithm_id <= 0:
            print(f"Python: Ошибка - Некорректный ID алгоритма: {algorithm_id}")
            return False

        if self.database_manager:
            try:
                success = self.database_manager.move_algorithm_up(algorithm_id)
                if success:
                    print(f"Python: Алгоритм ID {algorithm_id} успешно перемещен вверх.")
                    # Перезагружаем список алгоритмов в QML
                    self.algorithmsListChanged.emit()
                    return True
                else:
                    print(f"Python: Не удалось переместить алгоритм ID {algorithm_id} вверх.")
                    return False
            except Exception as e:
                print(f"Python: Исключение при перемещении алгоритма {algorithm_id} вверх: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("Python: Ошибка - Нет подключения к БД SQLite.")
            return False

    @Slot(int, result=bool)
    def moveAlgorithmDown(self, algorithm_id: int) -> bool:
        """
        Перемещает алгоритм вниз в списке.
        :param algorithm_id: ID алгоритма для перемещения.
        :return: True, если успешно, иначе False.
        """
        print(f"Python: QML отправил запрос на перемещение алгоритма ID {algorithm_id} вниз.")
        if not isinstance(algorithm_id, int) or algorithm_id <= 0:
            print(f"Python: Ошибка - Некорректный ID алгоритма: {algorithm_id}")
            return False

        if self.database_manager:
            try:
                success = self.database_manager.move_algorithm_down(algorithm_id)
                if success:
                    print(f"Python: Алгоритм ID {algorithm_id} успешно перемещен вниз.")
                    # Перезагружаем список алгоритмов в QML
                    self.algorithmsListChanged.emit()
                    return True
                else:
                    print(f"Python: Не удалось переместить алгоритм ID {algorithm_id} вниз.")
                    return False
            except Exception as e:
                print(f"Python: Исключение при перемещении алгоритма {algorithm_id} вниз: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("Python: Ошибка - Нет подключения к БД SQLite.")
            return False

    @Slot(str, result='QVariant') # Принимает строку даты, возвращает список
    def getExecutionsByDate(self, date_string: str) -> 'QVariant':
        """
        Возвращает список алгоритмов (algorithm_executions) за заданную дату.
        :param date_string: Дата в формате 'YYYY-MM-DD'.
        :return: Список словарей с данными execution'ов.
        """
        print(f"Python: QML запросил список execution'ов за дату '{date_string}'.")
        
        if not date_string:
            print("Python: Ошибка - date_string пуста.")
            return []
            
        if self.database_manager:
            try:
                # Вызываем метод из менеджера БД
                executions = self.database_manager.get_executions_by_date(date_string)
                if executions and isinstance(executions, list):
                    print(f"Python: Получен список {len(executions)} execution'ов за дату '{date_string}' из БД.")
                    # Возвращаем как есть, QML сам преобразует QVariantList в JS Array
                    return executions 
                else:
                    print(f"Python: Не найдено execution'ов за дату '{date_string}' или ошибка получения.")
                    return []
            except Exception as e:
                print(f"Python: Ошибка при получении execution'ов за дату '{date_string}': {e}")
                import traceback
                traceback.print_exc()
                return []
        else:
            print("Python: Ошибка - Нет подключения к БД SQLite.")
            return []

    # --- СЛОТЫ ДЛЯ РАБОТЫ С ЗАПУЩЕННЫМИ АЛГОРИТМАМИ (EXECUTIONS) ---

    @Slot(str, result='QVariant')
    def getActiveExecutionsByCategory(self, category: str) -> 'QVariant':
        """
        Слот для получения списка активных executions по категории из QML.
        """
        print(f"Python: QML запросил активные executions для категории '{category}'.")
        if self.database_manager:
            try:
                executions = self.database_manager.get_active_executions_by_category(category)
                # print(f"DEBUG: Executions from DB: {executions}")
                # QML ожидает список словарей (QVariantList of QVariantMap)
                return executions
            except Exception as e:
                print(f"Python: Ошибка в слоте getActiveExecutionsByCategory: {e}")
                import traceback
                traceback.print_exc()
                return [] # Возвращаем пустой список в случае ошибки
        else:
            print("Python: Ошибка - database_manager не инициализирован.")
            return []

    @Slot(int, result=bool)
    def stopAlgorithm(self, execution_id: int) -> bool:
        """
        Слот для остановки (завершения) execution из QML.
        Использует УЖЕ ВЫЧИСЛЕННОЕ местное время из ApplicationData.
        """
        print(f"Python: QML запросил остановку execution ID {execution_id}.")
        if self.database_manager:
            try:
                # --- ИЗМЕНЕНО: Используем УЖЕ ВЫЧИСЛЕННОЕ местное время ---
                # Получаем местную дату и время напрямую из свойств ApplicationData
                # Эти свойства обновляются таймером в update_time()
                local_date_str = self.localDate  # Формат "DD.MM.YYYY"
                local_time_str = self.localTime  # Формат "HH:MM:SS"
                print(f"Python: Используем УЖЕ ВЫЧИСЛЕННОЕ местное время из ApplicationData: дата={local_date_str}, время={local_time_str}")
                
                # Объединяем дату и время в строку формата 'YYYY-MM-DD HH:MM:SS'
                # Разбираем дату
                from datetime import datetime
                try:
                    date_parts = local_date_str.split('.')
                    day = int(date_parts[0])
                    month = int(date_parts[1])
                    year = int(date_parts[2])
                    # Разбираем время
                    time_parts = local_time_str.split(':')
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    seconds = int(time_parts[2])
                    
                    # Создаём объект datetime
                    local_now_dt = datetime(year, month, day, hours, minutes, seconds)
                    print(f"Python: Преобразовано в datetime.datetime: {local_now_dt}")
                except (ValueError, IndexError) as ve:
                    print(f"Python: Ошибка преобразования localDate/localTime в datetime: {ve}")
                    return False
                # --- ---
                
                print(f"Python: Местное время для завершения execution ID {execution_id}: {local_now_dt}")
                
                # Вызываем метод менеджера БД, передавая местное время
                success = self.database_manager.stop_algorithm(execution_id, local_now_dt)
                return success
            except Exception as e:
                print(f"Python: Ошибка в слоте stopAlgorithm: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("Python: Ошибка - database_manager не инициализирован.")
            return False

    @Slot('QVariant', result=bool) # Или result=int, если возвращаете ID
    def startAlgorithmExecution(self, execution_data: 'QVariant') -> bool: # Или int
        """
        Слот для запуска нового execution из QML.
        """
        print(f"Python: QML отправил запрос на запуск нового execution: {execution_data}")
        if hasattr(execution_data, 'toVariant'):
            execution_data = execution_data.toVariant()
            print(f"Python: QJSValue (execution_data) преобразован в: {execution_data}")

        if not isinstance(execution_data, dict):
            print(f"Python: Ошибка - execution_data не является словарем. Получен тип: {type(execution_data)}")
            return False # Или -1, если result=int

        if not execution_data:
            print("Python: Ошибка - execution_data пуст.")
            return False # Или -1

        if self.database_manager:
            try:
                # Подготовка данных
                algorithm_id = execution_data.get('algorithm_id')
                started_at_str = execution_data.get('started_at') # 'DD.MM.YYYY HH:MM:SS' - нужно преобразовать
                created_by_user_id = execution_data.get('created_by_user_id')
                notes = execution_data.get('notes')

                # ВАЖНО: Преобразовать started_at из 'DD.MM.YYYY HH:MM:SS' в 'YYYY-MM-DD HH:MM:SS'
                import datetime
                try:
                    input_format = "%d.%m.%Y %H:%M:%S"
                    parsed_datetime = datetime.datetime.strptime(started_at_str, input_format)
                    started_at_iso = parsed_datetime.isoformat(sep=' ') # 'YYYY-MM-DD HH:MM:SS'
                except ValueError as ve:
                    print(f"Python: Ошибка преобразования даты/времени '{started_at_str}': {ve}")
                    return False # Или -1

                print(f"Python: Подготовленные данные для запуска: algorithm_id={algorithm_id}, started_at={started_at_iso}, user_id={created_by_user_id}")

                # Вызов метода менеджера БД
                result = self.database_manager.start_algorithm_execution(algorithm_id, started_at_iso, created_by_user_id, notes)
                if isinstance(result, int) and result > 0:
                    print(f"Python: Execution успешно запущен с ID: {result}")
                    return True # или return result, если result=int
                else:
                    print(f"Python: Ошибка при запуске execution: {result}")
                    return False # или return -1
            except Exception as e:
                print(f"Python: Ошибка в слоте startAlgorithmExecution: {e}")
                import traceback
                traceback.print_exc()
                return False # или -1
        else:
            print("Python: Ошибка - database_manager не инициализирован.")
            return False # или -1

    @Slot(str, str, result='QVariant') # Принимает строку категории и строку даты
    def getCompletedExecutionsByCategoryAndDate(self, category: str, date_string: str) -> 'QVariant':
        """
        Слот для получения списка завершённых executions по категории и дате из QML.
        :param category: Категория алгоритмов.
        :param date_string: Дата в формате 'DD.MM.YYYY'.
        :return: Список словарей с данными execution'ов или пустой список.
        """
        print(f"Python: QML запросил завершённые executions для категории '{category}' и даты '{date_string}'.")
        if self.database_manager:
            try:
                # Вызов метода из PostgreSQLDatabaseManager
                executions_list = self.database_manager.get_completed_executions_by_category_and_date(category, date_string)
                print(f"Python: Найдено {len(executions_list) if isinstance(executions_list, list) else 'N/A'} завершённых executions.")
                # QML ожидает список словарей (QVariantList of QVariantMap)
                return executions_list if isinstance(executions_list, list) else []
            except Exception as e:
                print(f"Python: Ошибка в слоте getCompletedExecutionsByCategoryAndDate: {e}")
                import traceback
                traceback.print_exc()
                return []
        else:
            print("Python: Ошибка - database_manager не инициализирован.")
            return []

    @Slot(int, result='QVariant') # Указываем QVariant для QML
    def getExecutionById(self, execution_id: int):
        """
        QML Slot для получения данных execution'а по ID.
        Вызывает метод из PostgreSQLDatabaseManager.
        :param execution_id: ID execution'а.
        :return: Словарь с данными или None.
        """
        print(f"Python ApplicationData: Запрос данных execution ID {execution_id}")
        if self.database_manager: 
            execution_data = self.database_manager.get_algorithm_execution_by_id(execution_id)
            print(f"Python ApplicationData: Получены данные из БД для execution ID {execution_id}: {execution_data}")
            return execution_data # Возвращаем словарь или None
        else:
            print("Python ApplicationData: Менеджер PostgreSQL недоступен.")
            return None

    @Slot(int, result='QVariant') # Указываем QVariant для QML
    def getActionExecutionsByExecutionId(self, execution_id: int):
        """
        QML Slot для получения списка action_execution'ов по ID execution'а.
        Вызывает метод из PostgreSQLDatabaseManager и ДОБАВЛЯЕТ оперативные смещения.
        :param execution_id: ID execution'а.
        :return: Список словарей с данными action_execution'ов или None.
        """
        print(f"Python ApplicationData: Запрос списка action_execution'ов для execution ID {execution_id}")
        if self.database_manager: 
            action_executions_list = self.database_manager.get_action_executions_by_execution_id(execution_id)
            if not action_executions_list:
                print(f"Python ApplicationData: Список action_execution'ов пуст для execution ID {execution_id}.")
                return action_executions_list

            # --- НОВОЕ: Получаем данные execution'а, чтобы узнать его тип времени и время запуска ---
            execution_data = self.database_manager.get_algorithm_execution_by_id(execution_id)
            if not execution_data:
                print(f"Python ApplicationData: Не удалось получить данные execution ID {execution_id} для расчета смещений.")
                return action_executions_list

            execution_time_type = execution_data.get('snapshot_time_type', 'оперативное') # По умолчанию 'оперативное'
            execution_started_at_str = execution_data.get('started_at')
            if not execution_started_at_str:
                print(f"Python ApplicationData: В execution ID {execution_id} отсутствует started_at.")
                return action_executions_list

            # Преобразуем started_at в datetime
            try:
                from datetime import datetime
                execution_started_at = datetime.fromisoformat(execution_started_at_str.replace('Z', '+00:00'))
            except Exception as e:
                print(f"Python ApplicationData: Ошибка парсинга started_at '{execution_started_at_str}': {e}")
                return action_executions_list
            # --- ---

            # --- НОВОЕ: Обработка списка, если тип времени 'оперативное' ---
            if execution_time_type == 'оперативное':
                print(f"Python ApplicationData: Execution ID {execution_id} имеет тип времени 'оперативное'. Рассчитываем смещения...")
                for action in action_executions_list:
                    op_start_offset = ""
                    op_end_offset = ""

                    calculated_start_str = action.get('calculated_start_time')
                    calculated_end_str = action.get('calculated_end_time')

                    if calculated_start_str:
                        try:
                            calc_start_dt = datetime.fromisoformat(calculated_start_str.replace('Z', '+00:00'))
                            delta_start = calc_start_dt - execution_started_at
                            # Форматируем timedelta в dd:hh:mm:ss
                            total_seconds_start = int(delta_start.total_seconds())
                            is_negative_start = total_seconds_start < 0
                            abs_total_seconds_start = abs(total_seconds_start)
                            days_start = abs_total_seconds_start // 86400
                            remaining_seconds_start = abs_total_seconds_start % 86400
                            hours_start = remaining_seconds_start // 3600
                            remaining_seconds_start %= 3600
                            minutes_start = remaining_seconds_start // 60
                            seconds_start = remaining_seconds_start % 60
                            op_start_offset = f"Ч+{days_start:02d}:{hours_start:02d}:{minutes_start:02d}:{seconds_start:02d}"
                            if is_negative_start:
                                op_start_offset = op_start_offset.replace("Ч+", "Ч-")
                        except Exception as e:
                            print(f"Python ApplicationData: Ошибка расчета смещения начала для действия: {e}")

                    if calculated_end_str:
                        try:
                            calc_end_dt = datetime.fromisoformat(calculated_end_str.replace('Z', '+00:00'))
                            delta_end = calc_end_dt - execution_started_at
                            total_seconds_end = int(delta_end.total_seconds())
                            is_negative_end = total_seconds_end < 0
                            abs_total_seconds_end = abs(total_seconds_end)
                            days_end = abs_total_seconds_end // 86400
                            remaining_seconds_end = abs_total_seconds_end % 86400
                            hours_end = remaining_seconds_end // 3600
                            remaining_seconds_end %= 3600
                            minutes_end = remaining_seconds_end // 60
                            seconds_end = remaining_seconds_end % 60
                            op_end_offset = f"Ч+{days_end:02d}:{hours_end:02d}:{minutes_end:02d}:{seconds_end:02d}"
                            if is_negative_end:
                                op_end_offset = op_end_offset.replace("Ч+", "Ч-")
                        except Exception as e:
                            print(f"Python ApplicationData: Ошибка расчета смещения окончания для действия: {e}")

                    # Добавляем новые поля в словарь действия
                    action['operational_start_offset'] = op_start_offset
                    action['operational_end_offset'] = op_end_offset
                    print(f"Python ApplicationData: Действию добавлены смещения: start='{op_start_offset}', end='{op_end_offset}'")
            # --- ---

            print(f"Python ApplicationData: Обработан список из {len(action_executions_list)} action_execution'ов для execution ID {execution_id}.")
            return action_executions_list # Возвращаем обновленный список
        else:
            print("Python ApplicationData: Менеджер PostgreSQL недоступен.")
            return None

    # --- НОВЫЙ СЛОТ ДЛЯ ДОБАВЛЕНИЯ ACTION_EXECUTION ---
    @Slot(int, 'QVariant', result=bool) # <-- ВАЖНО: сигнатура
    def addActionExecution(self, execution_id: int, action_execution_: 'QVariant') -> bool: # <-- ИМЯ ПАРАМЕТРА С ПОДЧЁРКИВАНИЕМ
        """
        Добавляет новое action_execution к существующему execution.
        Вызывается из QML.
        :param execution_id: ID execution'а.
        :param action_execution_: Данные нового action_execution'а (QVariantMap из QML).
        :return: True, если успешно, иначе False.
        """
        # Сразу преобразуем QVariant в словарь Python
        # action_execution_ - это параметр функции, являющийся QVariant
        py_action_data = action_execution_.toVariant() # <-- Используем ПРАВИЛЬНОЕ имя параметра
        
        print(f"Python ApplicationData (из main.py): QML запросил добавление нового action_execution к execution ID {execution_id}. Преобразовано в: {py_action_data}")

        # 1. Проверки (опционально, но рекомендуется)
        if not isinstance(py_action_data, dict): # <-- Используем py_action_data
             print("Python ApplicationData: ОШИБКА - action_execution_.toVariant() не вернул словарь.")
             return False

        if not isinstance(execution_id, int) or execution_id <= 0:
            print(f"Python ApplicationData: Некорректный execution_id: {execution_id}")
            return False

        # 2. Вызвать метод менеджера БД
        # Предполагается, что у вас есть это свойство, созданное после входа в систему
        if self.database_manager: 
            try:
                # Передаем ИМЕННО преобразованный словарь
                success = self.database_manager.create_action_execution(execution_id, py_action_data) # <-- Используем py_action_data
                if success:
                    print(f"Python ApplicationData: Новое action_execution успешно добавлено к execution ID {execution_id}.")
                    return True
                else:
                    print(f"Python ApplicationData: Менеджер БД не смог добавить action_execution к execution ID {execution_id}.")
                    return False # Или возвращать строку с ошибкой от менеджера
            except Exception as e:
                print(f"Python ApplicationData: Исключение при добавлении action_execution к execution ID {execution_id}: {e}")
                import traceback
                traceback.print_exc() # Для вывода полной трассировки
                return False # Или возвращать строку с ошибкой
        else:
            print("Python ApplicationData: Ошибка - Нет подключения к БД SQLite.")
            return False
    # --- КОНЕЦ СЛОТА ---

    # --- НОВЫЙ СЛОТ ДЛЯ ПОЛУЧЕНИЯ ВРЕМЕНИ НАЧАЛА EXECUTION ---
    @Slot(int, result=str) # <-- ВАЖНО: сигнатура, возвращает строку
    def getExecutionStartedAt(self, execution_id: int) -> str:
        """
        Получает отформатированную строку started_at для execution по его ID.
        Используется для установки значений по умолчанию в диалогах редактирования action_execution.
        :param execution_id: ID execution'а.
        :return: Строка в формате 'dd.MM.yyyy HH:mm:ss' или пустая строка в случае ошибки.
        """
        logger.debug(f"Python ApplicationData: QML запросил started_at для execution ID {execution_id}.")

        if not isinstance(execution_id, int) or execution_id <= 0:
            logger.error(f"Python ApplicationData: Некорректный execution_id: {execution_id}")
            return ""

        if self.database_manager:
            try:
                # Предполагается, что у PostgreSQLDatabaseManager есть метод get_execution_by_id
                # который возвращает словарь с данными execution'а, включая started_at как datetime.datetime
                execution_data = self.database_manager.get_execution_by_id(execution_id)
                if execution_data and 'started_at' in execution_data and execution_data['started_at']:
                    started_at_dt = execution_data['started_at']
                    # Форматируем datetime в строку, понятную для UI
                    # Используем strftime для форматирования
                    formatted_time = started_at_dt.strftime('%d.%m.%Y %H:%M:%S')
                    logger.debug(f"Python ApplicationData: Получено и отформатировано started_at для execution ID {execution_id}: {formatted_time}")
                    return formatted_time
                else:
                    logger.warning(f"Python ApplicationData: Execution ID {execution_id} не найден или started_at отсутствует.")
                    return ""
            except Exception as e:
                logger.exception(f"Python ApplicationData: Исключение при получении started_at для execution ID {execution_id}: {e}")
                return ""
        else:
            logger.error("Python ApplicationData: Нет подключения к БД SQLite.")
            return ""
    # --- КОНЕЦ СЛОТА ---

    @Slot(int, int, result=bool)
    def updateExecutionResponsibleUser(self, execution_id: int, new_responsible_user_id: int) -> bool:
        """
        Обновляет ответственного пользователя для запущенного алгоритма (execution).
        Вызывается из QML.
        :param execution_id: ID execution'а.
        :param new_responsible_user_id: ID нового ответственного пользователя.
        :return: True, если успешно, иначе False.
        """
        print(f"Python ApplicationData: QML запросил обновление ответственного пользователя для execution ID {execution_id} на пользователя ID {new_responsible_user_id}.")

        if not isinstance(execution_id, int) or execution_id <= 0:
            print(f"Python ApplicationData: Некорректный execution_id: {execution_id}")
            return False

        if not isinstance(new_responsible_user_id, int) or new_responsible_user_id <= 0:
            print(f"Python ApplicationData: Некорректный ID нового ответственного пользователя: {new_responsible_user_id}")
            return False

        if self.database_manager:
            try:
                success = self.database_manager.update_execution_responsible_user(execution_id, new_responsible_user_id)
                if success:
                    print(f"Python ApplicationData: Ответственный пользователь для execution ID {execution_id} успешно обновлен на ID {new_responsible_user_id}.")
                    # Возможно, нужно обновить какие-то данные в интерфейсе
                    return True
                else:
                    print(f"Python ApplicationData: Не удалось обновить ответственного пользователя для execution ID {execution_id}.")
                    return False
            except Exception as e:
                print(f"Python ApplicationData: Исключение при обновлении ответственного пользователя для execution ID {execution_id}: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("Python ApplicationData: Менеджер БД не инициализирован.")
            return False

    @Slot(int, 'QVariant', result=bool)
    def updateActionExecution(self, action_execution_id: int, action_execution_data: 'QVariant') -> bool:
        """
        QML Slot для обновления action_execution.
        Вызывает метод из PostgreSQLDatabaseManager.
        :param action_execution_id: ID action_execution для обновления.
        :param action_execution_data: QVariantMap (словарь) с новыми данными.
        :return: True, если успешно, иначе False.
        """
        print(f"Python ApplicationData: Запрос на обновление action_execution ID {action_execution_id} с данными: {action_execution_data}")

        # Преобразование QVariantMap в обычный словарь Python
        if hasattr(action_execution_data, 'toVariant'):
            print("Python ApplicationData: Преобразование QVariantMap в словарь Python...")
            try:
                python_data = action_execution_data.toVariant()
                print(f"Python ApplicationData: Преобразованные данные: {python_data}")
            except Exception as e:
                print(f"Python ApplicationData: Ошибка преобразования QVariantMap: {e}")
                return False
        else:
            python_data = action_execution_data
            print(f"Python ApplicationData: Данные уже являются словарем Python: {python_data}")

        if not isinstance(python_data, dict):
            print(f"Python ApplicationData: Ошибка - action_execution_data не является словарем. Тип: {type(python_data)}")
            return False

        if not isinstance(action_execution_id, int) or action_execution_id <= 0:
            print(f"Python ApplicationData: Ошибка - некорректный action_execution_id: {action_execution_id}")
            return False

        if self.database_manager:
            try:
                # Если обновляется только поле notes, используем специализированный метод
                if len(python_data) == 1 and 'notes' in python_data:
                    success = self.database_manager.update_action_execution_notes(
                        action_execution_id,
                        python_data['notes'] if python_data['notes'] and python_data['notes'].strip() else None
                    )
                else:
                    # Используем общий метод для других случаев
                    success = self.database_manager.update_action_execution(action_execution_id, python_data)
                
                if success:
                    print(f"Python ApplicationData: Action execution ID {action_execution_id} успешно обновлён в БД.")
                    # Возможно, стоит эмитить сигнал для обновления UI, если это не делает QML самостоятельно
                    # self.actionExecutionUpdated.emit(action_execution_id)
                    return True
                else:
                    print(f"Python ApplicationData: Не удалось обновить action_execution ID {action_execution_id} в БД.")
                    return False
            except Exception as e:
                print(f"Python ApplicationData: Исключение при обновлении action_execution ID {action_execution_id}: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("Python ApplicationData: Менеджер PostgreSQL недоступен.")
            return False

    @Slot(int, result='QVariant') # Указываем QVariant для QML
    def getActionExecutionById(self, action_execution_id: int):
        """
        QML Slot для получения данных action_execution по ID.
        Вызывает метод из PostgreSQLDatabaseManager.
        :param action_execution_id: ID action_execution.
        :return: QVariant (словарь) с данными или None.
        """
        print(f"Python ApplicationData: Запрос данных action_execution ID {action_execution_id}")
        if not isinstance(action_execution_id, int) or action_execution_id <= 0:
            print(f"Python ApplicationData: Ошибка - некорректный action_execution_id: {action_execution_id}")
            return None

        if self.database_manager:
            action_execution_data = self.database_manager.get_action_execution_by_id(action_execution_id)
            print(f"Python ApplicationData: Получены данные из БД дл�� action_execution ID {action_execution_id}: {action_execution_data}")
            return action_execution_data # Возвращаем словарь ил������ None
        else:
            print("Python ApplicationData: Менеджер PostgreSQL недоступен.")
            return None

    @Slot(int, result=bool)
    def completeAllPendingActionsAutomatically(self, execution_id: int) -> bool:
        """
        Автоматически завершает все незавершённые действия в execution:
        - status = 'completed'
        - actual_end_time = calculated_end_time
        - notes: дополняет существующее примечание или устанавливает 'Завершено автоматически'
        """
        print(f"Python: Запрошено автоматическое завершение всех действий для execution ID {execution_id}")
        if not isinstance(execution_id, int) or execution_id <= 0:
            print("Python: Ошибка — некорректный execution_id")
            return False

        if not self.database_manager:
            print("Python: Ошибка — нет подключения к PostgreSQL")
            return False

        try:
            actions = self.database_manager.get_action_executions_by_execution_id(execution_id)
            if not actions:
                print("Python: Нет действий для завершения")
                return True

            updated_count = 0
            for action in actions:
                if action.get('status') != 'completed':
                    calculated_end = action.get('calculated_end_time')
                    if not calculated_end:
                        continue

                    # === ОБНОВЛЕНИЕ: Работа с примечаниями ===
                    existing_notes = action.get('notes') or ""
                    auto_note = "Завершено автоматически"
                    new_notes = auto_note
                    if existing_notes.strip():
                        # Если уже есть примечание — добавляем новую строку
                        new_notes = f"{existing_notes}\n\n{auto_note}"

                    # Преобразуем calculated_end_time в нужный формат
                    try:
                        dt = datetime.datetime.fromisoformat(calculated_end.replace('Z', '+00:00'))
                        actual_end_formatted = dt.strftime('%d.%m.%Y %H:%M:%S')
                    except Exception as e:
                        print(f"Python: Ошибка парсинга calculated_end_time '{calculated_end}': {e}")
                        continue

                    update_data = {
                        'actual_end_time': actual_end_formatted,
                        'reported_to': 'Авто',
                        'notes': new_notes
                    }

                    success = self.database_manager.update_action_execution(action['id'], update_data)
                    if success:
                        updated_count += 1
                    else:
                        print(f"Python: Не удалось обновить действие ID {action['id']}")

            print(f"Python: Автоматически завершено {updated_count} действий")
            return updated_count > 0

        except Exception as e:
            print(f"Python: Ошибка при автоматическом завершении действий: {e}")
            import traceback
            traceback.print_exc()
            return False

    @Slot(int, result='QVariantMap')
    def getActionExecutionStatsForPieChart(self, execution_id: int) -> dict:
        """
        Возвращает статистику по действиям execution'а для круговой диаграммы.
        :return: {
            "on_time": 5,
            "late": 2,
            "not_done": 3,
            "total": 10
        }
        """
        if not isinstance(execution_id, int) or execution_id <= 0:
            return {"on_time": 0, "late": 0, "not_done": 0, "total": 0}

        if not self.database_manager:
            return {"on_time": 0, "late": 0, "not_done": 0, "total": 0}

        try:
            actions = self.database_manager.get_action_executions_by_execution_id(execution_id)
            if not actions:
                return {"on_time": 0, "late": 0, "not_done": 0, "total": 0}

            on_time = 0
            late = 0
            not_done = 0

            for a in actions:
                status = a.get('status', 'pending')
                if status != 'completed':
                    not_done += 1
                else:
                    actual = a.get('actual_end_time')
                    planned = a.get('calculated_end_time')

                    if not actual or not planned:
                        not_done += 1
                        continue

                    try:
                        actual_dt = datetime.datetime.fromisoformat(actual)
                        planned_dt = datetime.datetime.fromisoformat(planned)
                    except Exception:
                        not_done += 1
                        continue

                    if actual_dt <= planned_dt:
                        on_time += 1
                    else:
                        late += 1

            total = len(actions)
            return {
                "on_time": on_time,
                "late": late,
                "not_done": not_done,
                "total": total
            }

        except Exception as e:
            print(f"Ошибка при расчёте статистики для execution {execution_id}: {e}")
            return {"on_time": 0, "late": 0, "not_done": 0, "total": 0}


    @Slot(int, str, result=bool)
    def updateActionExecutionNotes(self, action_execution_id: int, notes: str) -> bool:
        """
        Обновляет поле 'notes' у action_execution.
        """
        if not isinstance(action_execution_id, int) or action_execution_id <= 0:
            print("Python: Некорректный action_execution_id")
            return False
        if self.database_manager:
            try:
                # Используем специализированный метод для обновления только примечаний
                success = self.database_manager.update_action_execution_notes(
                    action_execution_id,
                    notes if notes.strip() else None
                )
                if success:
                    print(f"Python ApplicationData: Примечание для action_execution ID {action_execution_id} успешно обновлено в БД.")
                else:
                    print(f"Python ApplicationData: Не удалось обновить примечание для action_execution ID {action_execution_id} в БД.")
                return success
            except Exception as e:
                print(f"Python: Ошибка обновления примечаний: {e}")
                return False
        return False

    @Slot(int)
    def previewExecutionDetails(self, execution_id: int):
        """Открывает окно предпросмотра печати."""
        try:
            exec_data = self.database_manager.get_algorithm_execution_by_id(execution_id)
            actions = self.database_manager.get_action_executions_by_execution_id(execution_id)
            if not exec_data or not actions:
                print("Нет данных для предпросмотра")
                return

            html_content = self._generate_execution_html(exec_data, actions)
            doc = QTextDocument()
            doc.setHtml(html_content)

            from PySide6.QtPrintSupport import QPrintPreviewDialog
            from PySide6.QtGui import QPageLayout 
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageOrientation(QPageLayout.Landscape)
            preview = QPrintPreviewDialog(printer)

            # === РАСТЯГИВАЕМ НА ВЕСЬ ЭКРАН ===
            screen = QApplication.primaryScreen()
            preview.resize(screen.availableGeometry().size() * 0.9)
            preview.move(screen.availableGeometry().topLeft())

            preview.paintRequested.connect(lambda p: doc.print_(p))
            preview.exec()
        except Exception as e:
            print(f"Ошибка предпросмотра: {e}")
            traceback.print_exc()

    @Slot(int)
    def printExecutionDetails(self, execution_id: int):
        """Печатает напрямую (без предпросмотра)."""
        try:
            exec_data = self.database_manager.get_algorithm_execution_by_id(execution_id)
            actions = self.database_manager.get_action_executions_by_execution_id(execution_id)
            if not exec_data or not actions:
                print("Нет данных для печати")
                return

            html_content = self._generate_execution_html(exec_data, actions)
            doc = QTextDocument()
            doc.setHtml(html_content)

            printer = QPrinter()
            dialog = QPrintDialog(printer)
            if dialog.exec() == QPrintDialog.Accepted:
                doc.print_(printer)
        except Exception as e:
            print(f"Ошибка печати: {e}")
            traceback.print_exc()

    @Slot(str, str, result=bool)
    def verifyAdminPassword(self, login: str, password: str) -> bool:
        """
        Проверяет, совпадает ли переданный пароль с паролем указанного пользователя.
        Также проверяет, что пользователь является администратором.
        """
        try:
            if self.database_manager is None:
                print("Ошибка: database_manager не инициализирован.")
                return False

            conn = self.database_manager._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, login, password_hash, is_admin FROM users WHERE login = ? AND is_active = 1;",
                (login,)
            )
            row = cursor.fetchone()
            cursor.close()

            if row:
                user_id = row["id"]
                user_login = row["login"]
                stored_hash = row["password_hash"]
                is_admin = bool(row["is_admin"])

                print(f"Python verifyAdminPassword: Пользователь найден: ID={user_id}, логин={user_login}, is_admin={is_admin}")

                if not is_admin:
                    print(f"Пользователь '{login}' не является администратором (is_admin={is_admin}).")
                    return False

                result = check_password_hash(stored_hash, password)
                print(f"Python verifyAdminPassword: Проверка пароля: {'УСПЕХ' if result else 'НЕУДАЧА'}")
                return result
            else:
                print(f"Пользователь '{login}' не найден или неактивен.")
                return False

        except Exception as e:
            print(f"Ошибка при проверке пароля администратора: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _generate_execution_html(self, exec_data, actions) -> str:
        """Генерирует HTML-отчёт по выполнению с учётом настроек печати и корректной подписью."""
        import html
        import os
        from datetime import datetime
        import re

        def escape(s):
            return html.escape(str(s) if s is not None else "", quote=True)

        def fmt_dt(dt_str):
            if not dt_str:
                return ""
            try:
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                return dt.strftime("%d.%m.%Y %H:%M")
            except Exception:
                return str(dt_str)

        # === Настройки шрифта печати ===
        font_family = self._print_font_family or "Arial"
        font_size = max(8, min(24, int(self._print_font_size or 12)))
        font_style = self._print_font_style or "normal"

        font_weight = "bold" if font_style in ("bold", "bold_italic") else "normal"
        font_style_css = "italic" if font_style in ("italic", "bold_italic") else "normal"

        # === Данные заголовка ===
        title = escape(exec_data.get('snapshot_name', 'Без названия'))
        started_at_raw = exec_data.get('started_at')
        started_at = fmt_dt(started_at_raw)

        # === Подпись: парсинг ФИО и звания ===
        # 1. Название поста — из appData (SQLite)
        post_name = escape(self._post_name) if self._post_name else "Пост"

        # 2. Пытаемся взять звание из отдельного поля (если сохранено при запуске)
        rank = escape(exec_data.get('created_by_rank', ''))

        # 3. Полное отображаемое имя (сохранено при запуске)
        full_display = exec_data.get('created_by_user_display_name', '').strip()

        # 4. Если звание не сохранено отдельно — извлекаем его из full_display
        if not rank and full_display:
            # Пример: "ст. лейтенант Иванов И.И." → звание = "ст. лейтенант"
            # Ищем первую часть до фамилии (предполагаем, что фамилия начинается с заглавной буквы)
            # Простой способ: всё до первой заглавной буквы, за которой следует строчная (начало фамилии)
            match = re.match(r'^([^\w]*[А-Яа-яёЁ\s]+?)\s+([А-Я][а-яё]+)', full_display)
            if match:
                rank = escape(match.group(1).strip())
                fio_part = full_display[len(rank):].strip()
            else:
                # Если не удалось распарсить — считаем, что всё — ФИО, звание пустое
                fio_part = full_display
        else:
            fio_part = full_display

        # 5. Очищаем ФИО от возможного дублирующего звания
        if fio_part.startswith(rank):
            fio_part = fio_part[len(rank):].strip()

        # 6. Если ФИО пустое — используем заглушку
        full_name = escape(fio_part) if fio_part else "—"

        current_year = datetime.now().strftime("%Y")

        # === Статистика ===
        total = len(actions)
        completed = sum(1 for a in actions if a.get('status') == 'completed')
        on_time = 0
        for a in actions:
            if a.get('status') == 'completed':
                try:
                    actual = datetime.fromisoformat(a.get('actual_end_time', '').replace('Z', '+00:00'))
                    planned = datetime.fromisoformat(a.get('calculated_end_time', '').replace('Z', '+00:00'))
                    if actual <= planned:
                        on_time += 1
                except Exception:
                    pass

        pct_completed = round(100 * completed / total, 1) if total > 0 else 0
        pct_on_time = round(100 * on_time / total, 1) if total > 0 else 0

        # === Формирование строк таблицы ===
        rows = []
        for i, a in enumerate(actions, 1):
            desc = escape(a.get('snapshot_description', ''))
            start = fmt_dt(a.get('calculated_start_time'))
            end = fmt_dt(a.get('calculated_end_time'))
            phones = escape(a.get('snapshot_contact_phones', ''))

            materials_html = ""
            materials = a.get('snapshot_report_materials')
            if materials:
                for line in str(materials).splitlines():
                    path = line.strip()
                    if path:
                        filename = os.path.basename(path)
                        materials_html += f'<a href="{html.escape(path)}">{html.escape(filename)}</a><br>'

            status = a.get('status', '')
            if status == 'completed':
                actual_end = fmt_dt(a.get('actual_end_time'))
                execution_text = f"Выполнено<br>{actual_end}"
            else:
                execution_text = "Не выполнено"

            rows.append(f"""
            <tr>
                <td>{i}</td>
                <td>{desc}</td>
                <td>{start}</td>
                <td>{end}</td>
                <td>{phones}</td>
                <td>{materials_html}</td>
                <td>{execution_text}</td>
            </tr>
            """)

        # === Генерация HTML ===
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Отчёт по выполнению</title>
            <style>
                body {{
                    font-family: "{font_family}", Arial, sans-serif;
                    font-size: {font_size}pt;
                    font-weight: {font_weight};
                    font-style: {font_style_css};
                    line-height: 1.4;
                    margin: 20px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: {font_size + 4}pt;
                    font-weight: bold;
                }}
                .start-date {{
                    margin-top: 8px;
                    font-size: {font_size}pt;
                }}
                table {{
                    width: 100%;
                    table-layout: fixed;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                colgroup col {{ }}
                th, td {{
                    border: 1px solid #000;
                    padding: 6px;
                    vertical-align: top;
                    text-align: left;
                    word-wrap: break-word;
                }}
                th {{
                    background-color: #f0f0f0;
                    font-weight: bold;
                }}
                tr:nth-child(even) {{ background-color: #fafafa; }}
                .summary {{
                    margin-top: 20px;
                    font-weight: bold;
                    font-size: {font_size}pt;
                }}
                .signature-block {{
                    margin-top: 40px;
                    font-size: {font_size}pt;
                }}
                .signature-line-left {{
                    text-align: left;
                    margin: 4px 0;
                }}
                .signature-line-right {{
                    text-align: right;
                    margin: 4px 0;
                }}
                a {{ color: #0066cc; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <div class="start-date">Начало: {started_at}</div>
            </div>

            <table>
                <colgroup>
                    <col style="width: 5%;">
                    <col style="width: 30%;">
                    <col style="width: 10%;">
                    <col style="width: 10%;">
                    <col style="width: 12%;">
                    <col style="width: 15%;">
                    <col style="width: 18%;">
                </colgroup>
                <thead>
                    <tr>
                        <th>№</th>
                        <th>Выполняемое мероприятие</th>
                        <th>Начало</th>
                        <th>Окончание</th>
                        <th>Телефоны для взаимодействия</th>
                        <th>Отчётный материал</th>
                        <th>Выполнение</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>

            <div class="summary">
                Итого: из {total} задач выполнено {completed} ({pct_completed}%), своевременно — {on_time} ({pct_on_time}%)
            </div>

            <div class="signature-block">
                <div class="signature-line-left">{post_name}</div>
                <div class="signature-line-left">{rank}</div>
                <div class="signature-line-right">{full_name}</div>
                <div class="signature-line-left">«____»  _________________ {current_year} г.</div>
            </div>
        </body>
        </html>
        """
        return html_content

    def minimize_window(self):
        if self.window:
            self.window.showMinimized()
            print("Окно минимизировано") # Для отладки

    def maximize_window(self):
        if self.window:
            self.window.showMaximized()
            print("Окно развернуто") # Для отладки

    def on_tray_icon_activated(self, reason):
        """Обработчик клика по иконке в трее."""
        if reason == QSystemTrayIcon.Trigger or reason == QSystemTrayIcon.DoubleClick: # Левый клик или двойной клик
            self.restore_window()
        # elif reason == QSystemTrayIcon.Context: # Правый клик - меню показывается автоматически
            # pass

    def quit_app(self):
        print("Выход из приложения") # Для отладки
        # Скрываем иконку трея перед выходом
        if self.tray_icon:
            self.tray_icon.hide()
        self.app.quit()

    def _start_notification_timer(self):
        """Инициализирует и запускает таймер для проверки дедлайнов действий,
        а также загружает звуковые эффекты.
        QSystemTrayIcon больше не используется для визуальных уведомлений."""
        if not self.database_manager:
            print("Python: Предупреждение - database_manager не инициализирован, уведомления не запускаются.")
            return

        # Инициализация таймера проверки дедлайнов
        self._notification_timer = QTimer()
        self._notification_timer.timeout.connect(self._check_action_deadlines)
        # Проверяем раз в 30 секунд (30000 миллисекунд)
        self._notification_timer.start(10000) # 10 секунд
        print("Python: Таймер проверки дедлайнов действий запущен (30 секунд).")

        # Инициализация QSoundEffect для звуков
        try:
            from PySide6.QtCore import QUrl # Импорт внутри блока, если не импортирован глобально
            self._sound_approaching = QSoundEffect(self)
            # Укажите путь к вашему WAV файлу для "приближается"
            # Убедитесь, что файл существует и путь указан правильно
            sound_path_approaching = "sounds/soon.wav" # <-- Укажите реальный путь
            if os.path.exists(sound_path_approaching):
                self._sound_approaching.setSource(QUrl.fromLocalFile(sound_path_approaching))
                self._sound_approaching.setLoopCount(1)
                print(f"Python: Звук уведомления 'приближается' загружен из {sound_path_approaching}.")
            else:
                print(f"Python: Файл звука 'приближается' не найден: {sound_path_approaching}")
                self._sound_approaching = None # Отключаем воспроизведение
        except Exception as e:
            print(f"Python: Ошибка при загрузке звука 'приближается': {e}")
            self._sound_approaching = None # Отключаем воспроизведение, если ошибка

        try:
            self._sound_overdue = QSoundEffect(self)
            # Укажите путь к вашему WAV файлу для "просрочено"
            # Убедитесь, что файл существует и путь указан правильно
            sound_path_overdue = "sounds/time_out.wav" # <-- Укажите реальный путь
            if os.path.exists(sound_path_overdue):
                self._sound_overdue.setSource(QUrl.fromLocalFile(sound_path_overdue))
                self._sound_overdue.setLoopCount(1)
                print(f"Python: Звук уведомления 'просрочено' загружен из {sound_path_overdue}.")
            else:
                print(f"Python: Файл звука 'просрочено' не найден: {sound_path_overdue}")
                self._sound_overdue = None # Отключаем воспроизведение

        except Exception as e:
            print(f"Python: Ошибка при загрузке звука 'просрочено': {e}")
            self._sound_overdue = None # Отключаем воспроизведение, если ошибка
    # --- Конец метода _start_notification_timer ---

    def _check_action_deadlines(self):
        """Проверяет дедлайны действий и отправляет уведомления."""
        if not self.database_manager:
            print("Python: _check_action_deadlines - database_manager не инициализирован.")
            return # Нечего проверять без БД

        # Получаем текущее МЕСТНОЕ время из appData (строки)
        # Нужно преобразовать строку времени и даты в объект datetime
        current_time_str = self._local_time # "HH:MM:SS"
        current_date_str = self._local_date # "DD.MM.YYYY"
        try:
            # Формат даты "DD.MM.YYYY HH:MM:SS"
            local_now_str = f"{current_date_str} {current_time_str}"
            local_now_dt = datetime.datetime.strptime(local_now_str, "%d.%m.%Y %H:%M:%S")
            print(f"Python: Проверка дедлайнов. Текущее местное время: {local_now_dt}")
        except ValueError as e:
            print(f"Python: Ошибка преобразования местного времени: {e}")
            return # Не удалось получить корректное время, пропускаем проверку

        # Определяем порог для "приближается" (5 минут)
        reminder_threshold = datetime.timedelta(minutes=5)

        # Загружаем активные action_executions для активных algorithm_executions
        try:
            active_actions = self.database_manager.get_active_action_executions_with_details()
        except Exception as e:
            print(f"Python: Ошибка при получении активных действий для проверки дедлайнов: {e}")
            import traceback
            traceback.print_exc()
            return

        for action in active_actions:
            action_exec_id = action.get('id')
            execution_id = action.get('execution_id')
            calculated_end_time_value = action.get('calculated_end_time')
            calculated_start_time_value = action.get('calculated_start_time')
            action_status = action.get('status')
            execution_status = action.get('execution_status')
            action_description = action.get('snapshot_description', 'Действие без описания')
            algorithm_name = action.get('snapshot_name', 'Неизвестный алгоритм')

            # Получаем множество типов уведомлений, которые уже были показаны для этого действия
            notified_types = self._notified_action_executions.get(action_exec_id, set())

            # Пропускаем, если статус действия не pending или in_progress
            if action_status not in ['pending', 'in_progress']:
                print(f"Python: Пропуск action_execution ID {action_exec_id} - статус '{action_status}', не pending/in_progress.")
                continue

            # Пропускаем, если статус выполнения алгоритма не active
            if execution_status != 'active':
                print(f"Python: Пропуск action_execution ID {action_exec_id} - статус алгоритма '{execution_status}', не active.")
                continue

            # Преобразуем calculated_start_time и calculated_end_time в datetime
            action_start_dt = None
            action_end_dt = None

            # === Преобразование времени начала ===
            if calculated_start_time_value is not None:
                try:
                    if isinstance(calculated_start_time_value, datetime.datetime):
                        action_start_dt = calculated_start_time_value
                    elif isinstance(calculated_start_time_value, str):
                        try:
                            action_start_dt = datetime.datetime.strptime(calculated_start_time_value, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            try:
                                action_start_dt = datetime.datetime.fromisoformat(calculated_start_time_value.replace('Z', '+00:00'))
                            except ValueError:
                                print(f"Python: Не удается распознать формат calculated_start_time для action_execution ID {action_exec_id}")
                                action_start_dt = None
                except Exception as e:
                    print(f"Python: Ошибка преобразования calculated_start_time для action_execution ID {action_exec_id}: {e}")

            # === Преобразование времени окончания ===
            if calculated_end_time_value is not None:
                try:
                    if isinstance(calculated_end_time_value, datetime.datetime):
                        action_end_dt = calculated_end_time_value
                    elif isinstance(calculated_end_time_value, str):
                        try:
                            action_end_dt = datetime.datetime.strptime(calculated_end_time_value, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            try:
                                action_end_dt = datetime.datetime.fromisoformat(calculated_end_time_value.replace('Z', '+00:00'))
                            except ValueError:
                                print(f"Python: Не удается распознать формат calculated_end_time для action_execution ID {action_exec_id}")
                                action_end_dt = None
                except Exception as e:
                    print(f"Python: Ошибка преобразования calculated_end_time для action_execution ID {action_exec_id}: {e}")

            # Вычисляем длительность действия
            action_duration = None
            if action_start_dt and action_end_dt:
                action_duration = action_end_dt - action_start_dt

            print(f"Python: Проверка action_execution ID {action_exec_id} (exec {execution_id}), начало: {action_start_dt}, окончание: {action_end_dt}, длительность: {action_duration}, статус: {action_status}")

            # === 1. ПРОВЕРКА: Время начала действия (зеленое уведомление, когда действие уже началось) ===
            if action_start_dt and action_start_dt <= local_now_dt:
                if "Начало действия" not in notified_types:
                    print(f"Python: Обнаружено НАЧАЛО действия ID {action_exec_id} (execution {execution_id}), начало: {action_start_dt}.")
                    # Отправляем уведомление о начале действия
                    self._send_notification(action_exec_id, execution_id, algorithm_name, "Начало действия", action_description, action_start_dt)
                    # Воспроизводим звук
                    self._play_notification_sound("approaching")
                    # Добавляем тип уведомления в множество уведомленных
                    if action_exec_id not in self._notified_action_executions:
                        self._notified_action_executions[action_exec_id] = set()
                    self._notified_action_executions[action_exec_id].add("Начало действия")
                    print(f"Python: Добавлено action_execution ID {action_exec_id} в список уведомлений (начало действия).")
                else:
                    print(f"Python: Пропуск - уведомление о начале действия уже было показано для ID {action_exec_id}.")

            # === 2. ПРОВЕРКА: Время истекло (красное уведомление) ===
            if action_end_dt and action_end_dt < local_now_dt:
                if "Время истекло" not in notified_types:
                    print(f"Python: Обнаружено ПРОСРОЧЕННОЕ действие ID {action_exec_id} (execution {execution_id}).")
                    # Отправляем уведомление
                    self._send_notification(action_exec_id, execution_id, algorithm_name, "Время истекло", action_description, action_end_dt)
                    # Воспроизводим звук
                    self._play_notification_sound("overdue")
                    # Добавляем тип уведомления в множество уведомленных
                    if action_exec_id not in self._notified_action_executions:
                        self._notified_action_executions[action_exec_id] = set()
                    self._notified_action_executions[action_exec_id].add("Время истекло")
                    print(f"Python: Добавлено action_execution ID {action_exec_id} в список уведомлений (время истекло).")
                else:
                    print(f"Python: Пропуск - уведомление об истечении времени уже было показано для ID {action_exec_id}.")

            # === 3. ПРОВЕРКА: Осталось 5 минут до окончания (желтое уведомление, только если длительность > 5 минут) ===
            # Проверяем, что длительность действия больше 5 минут
            if action_duration and action_duration > reminder_threshold:
                # Проверяем, приближается ли время окончания (в течение 5 минут)
                if action_end_dt and local_now_dt <= action_end_dt <= (local_now_dt + reminder_threshold):
                    if "Осталось 5 минут" not in notified_types:
                        print(f"Python: Обнаружено ПРИБЛИЖАЮЩЕЕСЯ ОКОНЧАНИЕ действия ID {action_exec_id} (execution {execution_id}), окончание: {action_end_dt}.")
                        # Отправляем уведомление
                        self._send_notification(action_exec_id, execution_id, algorithm_name, "Осталось 5 минут", action_description, action_end_dt)
                        # Воспроизводим звук
                        self._play_notification_sound("approaching")
                        # Добавляем тип уведомления в множество уведомленных
                        if action_exec_id not in self._notified_action_executions:
                            self._notified_action_executions[action_exec_id] = set()
                        self._notified_action_executions[action_exec_id].add("Осталось 5 минут")
                        print(f"Python: Добавлено action_execution ID {action_exec_id} в список уведомлений (осталось 5 минут).")
                    else:
                        print(f"Python: Пропуск - уведомление об окончании уже было показано для ID {action_exec_id}.")
            else:
                if action_duration:
                    print(f"Python: Пропуск проверки окончания для action_execution ID {action_exec_id} - длительность действия ({action_duration}) <= 5 минут.")

        print("Python: Проверка дедлайнов завершена.")
    # --- Конец метода _check_action_deadlines ---

    def _send_notification(self, action_exec_id: int, execution_id: int, algorithm_name: str, status_type: str, description: str, calculated_time: datetime.datetime):
        """Отправляет визуальное уведомление через NotificationContainerWidget."""
        # Проверяем внутреннюю переменную настройки '_use_persistent_reminders'
        use_reminders = getattr(self, '_use_persistent_reminders', False)
        if not use_reminders:
            print(f"Python: Уведомление '{status_type}' для action_execution {action_exec_id} подавлено (уведомления отключены).")
            return # Уведомления отключены

        # --- Формирование заголовка и сообщения ---
        title = f"Уведомление о действии ({status_type})"
        formatted_time = calculated_time.strftime("%d.%m.%Y %H:%M:%S")

        # --- СОКРАЩЕНИЕ ТЕКСТА ---
        max_algorithm_name_length = 40 # Максимальная длина названия алгоритма
        max_description_length = 120    # Максимальная длина описания действия

        truncated_algorithm_name = algorithm_name if len(algorithm_name) <= max_algorithm_name_length else algorithm_name[:max_algorithm_name_length-3] + "..."
        truncated_description = description if len(description) <= max_description_length else description[:max_description_length-3] + "..."
        # --- ---

        # --- Определяем тип сообщения и цвет в зависимости от статуса ---
        if status_type == "Начало действия":
            message = f"Алгоритм: {truncated_algorithm_name}\nМероприятие: {truncated_description}\nВремя начала: {formatted_time}"
            icon_type = "Success"  # Зеленое уведомление
        elif status_type == "Осталось 5 минут":
            message = f"Алгоритм: {truncated_algorithm_name}\nМероприятие: {truncated_description}\nОсталось времени: 5 минут"
            icon_type = "Warning"  # Желтое уведомление
        elif status_type == "Время истекло":
            message = f"Алгоритм: {truncated_algorithm_name}\nМероприятие: {truncated_description}\nВремя истекло: {formatted_time}"
            icon_type = "Error"  # Красное уведомление
        else:
            message = f"Алгоритм: {truncated_algorithm_name}\nМероприятие: {truncated_description}\nВремя: {formatted_time}"
            icon_type = "Information"  # Информационное уведомление
        # --- ---

        # Отправляем уведомление в контейнер
        try:
            # Используем ОДИН экземпляр контейнера
            self.notification_container.add_notification(
                title=title,
                message=message,
                icon_type=icon_type,
                duration_ms=200000 # 10 секунд, например
            )
            print(f"Python: Добавлено визуальное уведомление в контейнер: {status_type} - {truncated_description[:50]}... (Алгоритм: {truncated_algorithm_name[:30]}..., Время: {formatted_time})")

        except Exception as e:
            print(f"Python: Ошибка при добавлении уведомления в контейнер: {e}")
            import traceback
            traceback.print_exc()


    def _play_notification_sound(self, status_type: str):
        """Воспроизводит звук уведомления."""
        # Проверяем внутреннюю переменную настройки '_sound_enabled'
        # Используем getattr с дефолтным значением False, если атрибут не существует
        sound_enabled = getattr(self, '_sound_enabled', False)
        if not sound_enabled:
            print(f"Python: Звук для '{status_type}' подавлен (звук отключен).")
            return # Звук отключен

        # Выбираем QSoundEffect в зависимости от типа уведомления
        sound_effect = None
        if status_type == "approaching" and self._sound_approaching:
            sound_effect = self._sound_approaching
        elif status_type == "overdue" and self._sound_overdue:
            sound_effect = self._sound_overdue

        if sound_effect:
            # Проверяем, играет ли уже этот звук, чтобы избежать наложения
            if sound_effect.isPlaying():
                 print(f"Python: Звук для '{status_type}' не воспроизводится - предыдущий звук еще играет.")
                 return # Не запускаем новый, если предыдущий ещё играет
            # Воспроизводим звук
            sound_effect.play()
            print(f"Python: Воспроизведён звук уведомления: {status_type}")
        else:
            print(f"Python: Звуковой файл для '{status_type}' не загружен, отключен или не существует.")
    # --- Конец метода _play_notification_sound ---

    @Slot()
    def quitApp(self):
        """
        Завершает работу приложения.
        """
        print("Python ApplicationData: Запрошено завершение приложения.")
        try:
            # Закрываем соединение с БД, если оно открыто
            if hasattr(self, 'database_manager') and self.database_manager:
                # Закрываем соединение, если оно реализовано в менеджере
                if hasattr(self.database_manager, 'close_connection'):
                    self.database_manager.close_connection()
                print("Python ApplicationData: Соединение с БД закрыто.")
            
            # Закрываем иконку в трее, если она есть
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.hide()
                print("Python ApplicationData: Иконка в трее скрыта.")
            
            # Завершаем приложение
            if hasattr(self, 'app') and self.app:
                self.app.quit()
                print("Python ApplicationData: Приложение завершено через app.quit().")
            else:
                import sys
                print("Python ApplicationData: Приложение завершено через sys.exit().")
                sys.exit(0)
        except Exception as e:
            print(f"Python ApplicationData: Ошибка при завершении приложения: {e}")
            import sys
            sys.exit(1)

    # --- НОВЫЕ МЕТОДЫ ДЛЯ РАБОТЫ С ОТНОСИТЕЛЬНЫМ ВРЕМЕНЕМ ---
    
    @Slot(int, 'QVariant', result=bool)
    def addRelativeTimeActionExecution(self, execution_id: int, action_execution_data: 'QVariant') -> bool:
        """
        Добавляет новое action_execution с относительным временем к существующему execution.
        Вычисляет абсолютное время на основе времени запуска алгоритма и относительных сдвигов.
        Вызывается из QML.
        :param execution_id: ID execution'а.
        :param action_execution_data: Данные нового action_execution'а (QVariantMap из QML).
        :return: True, если успешно, иначе False.
        """
        # Преобразуем QVariant в словарь Python
        py_action_data = action_execution_data.toVariant()
        
        print(f"Python ApplicationData: QML запросил добавление action_execution с относительным временем к execution ID {execution_id}. Данные: {py_action_data}")

        # Проверки
        if not isinstance(py_action_data, dict):
            print("Python ApplicationData: ОШИБКА - action_execution_data не является словарем.")
            return False

        if not isinstance(execution_id, int) or execution_id <= 0:
            print(f"Python ApplicationData: Некорректный execution_id: {execution_id}")
            return False

        # Получаем время запуска алгоритма
        if not self.database_manager:
            print("Python ApplicationData: Ошибка - Нет подключения к БД.")
            return False

        try:
            # Используем правильный метод для получения информации о выполнении алгоритма
            execution_info = self.database_manager.get_algorithm_execution_by_id(execution_id)
            if not execution_info or 'started_at' not in execution_info:
                print(f"Python ApplicationData: Не найдено время запуска для execution ID {execution_id}")
                return False
            
            start_time = execution_info['started_at']
            if isinstance(start_time, str):
                # Преобразуем строку в datetime объект
                start_time = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            
            # Вычисляем абсолютное время начала и окончания на основе относительных сдвигов
            # Получаем относительные значения из данных
            start_days = int(py_action_data.get('relative_start_days', 0))
            start_hours = int(py_action_data.get('relative_start_hours', 0))
            start_minutes = int(py_action_data.get('relative_start_minutes', 0))
            start_seconds = int(py_action_data.get('relative_start_seconds', 0))
            
            end_days = int(py_action_data.get('relative_end_days', 0))
            end_hours = int(py_action_data.get('relative_end_hours', 0))
            end_minutes = int(py_action_data.get('relative_end_minutes', 0))
            end_seconds = int(py_action_data.get('relative_end_seconds', 0))

            # Вычисляем абсолютные даты
            calculated_start_time = start_time + datetime.timedelta(
                days=start_days,
                hours=start_hours,
                minutes=start_minutes,
                seconds=start_seconds
            )
            
            calculated_end_time = start_time + datetime.timedelta(
                days=end_days,
                hours=end_hours,
                minutes=end_minutes,
                seconds=end_seconds
            )

            # Подготовим данные для сохранения в БД
            # Заменяем относительные значения на абсолютные
            db_action_data = py_action_data.copy()
            db_action_data['calculated_start_time'] = calculated_start_time.strftime('%Y-%m-%dT%H:%M:%S')
            db_action_data['calculated_end_time'] = calculated_end_time.strftime('%Y-%m-%dT%H:%M:%S')
            
            # Удаляем относительные поля, так как они не хранятся в БД
            relative_fields = [
                'relative_start_days', 'relative_start_hours', 'relative_start_minutes', 'relative_start_seconds',
                'relative_end_days', 'relative_end_hours', 'relative_end_minutes', 'relative_end_seconds'
            ]
            for field in relative_fields:
                if field in db_action_data:
                    del db_action_data[field]

            # Вызываем метод напрямую из database_manager, передавая ему подготовленные данные
            if self.database_manager:
                try:
                    success = self.database_manager.create_action_execution(execution_id, db_action_data)
                    if success:
                        print(f"Python ApplicationData: Новое action_execution с относительным временем успешно добавлено к execution ID {execution_id}.")
                        return True
                    else:
                        print(f"Python ApplicationData: Менеджер БД не смог добавить action_execution к execution ID {execution_id}.")
                        return False
                except Exception as e:
                    print(f"Python ApplicationData: Исключение при добавлении action_execution к execution ID {execution_id} через database_manager: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            else:
                print("Python ApplicationData: Ошибка - Нет подключения к БД SQLite.")
                return False
            
        except Exception as e:
            print(f"Python ApplicationData: Исключение при добавлении action_execution с относительным временем: {e}")
            import traceback
            traceback.print_exc()
            return False

    @Slot(int, 'QVariant', result=bool)
    def updateRelativeTimeActionExecution(self, action_execution_id: int, action_execution_data: 'QVariant') -> bool:
        """
        Обновляет action_execution с относительным временем.
        Вычисляет абсолютное время на основе времени запуска алгоритма и относительных сдвигов.
        :param action_execution_id: ID action_execution для обновления.
        :param action_execution_data: QVariantMap (словарь) с новыми данными.
        :return: True, если успешно, иначе False.
        """
        print(f"Python ApplicationData: Запрос на обновление action_execution с относительным временем ID {action_execution_id} с данными: {action_execution_data}")

        # Преобразование QVariantMap в обычный словарь Python
        if hasattr(action_execution_data, 'toVariant'):
            python_data = action_execution_data.toVariant()
        else:
            python_data = action_execution_data

        if not isinstance(python_data, dict):
            print(f"Python ApplicationData: Ошибка - action_execution_data не является словарем. Тип: {type(python_data)}")
            return False

        if not isinstance(action_execution_id, int) or action_execution_id <= 0:
            print(f"Python ApplicationData: Ошибка - некорректный action_execution_id: {action_execution_id}")
            return False

        # Получаем информацию о текущем action_execution и связанном execution
        if not self.database_manager:
            print("Python ApplicationData: Менеджер БД не инициализирован.")
            return False

        try:
            # Получаем информацию о текущем action_execution
            current_action = self.database_manager.get_action_execution_by_id(action_execution_id)
            if not current_action:
                print(f"Python ApplicationData: Action execution ID {action_execution_id} не найден.")
                return False

            # Получаем execution_id из текущего action_execution
            execution_id = current_action['execution_id']

            # Получаем время запуска алгоритма
            execution_info = self.database_manager.get_algorithm_execution_by_id(execution_id)
            if not execution_info or 'started_at' not in execution_info:
                print(f"Python ApplicationData: Не найдено время запуска для execution ID {execution_id}")
                return False

            start_time = execution_info['started_at']
            if isinstance(start_time, str):
                # Преобразуем строку в datetime объект
                start_time = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))

            # Вычисляем абсолютное время начала и окончания на основе относительных сдвигов
            start_days = int(python_data.get('relative_start_days', 0))
            start_hours = int(python_data.get('relative_start_hours', 0))
            start_minutes = int(python_data.get('relative_start_minutes', 0))
            start_seconds = int(python_data.get('relative_start_seconds', 0))

            end_days = int(python_data.get('relative_end_days', 0))
            end_hours = int(python_data.get('relative_end_hours', 0))
            end_minutes = int(python_data.get('relative_end_minutes', 0))
            end_seconds = int(python_data.get('relative_end_seconds', 0))

            # Вычисляем абсолютные даты
            calculated_start_time = start_time + datetime.timedelta(
                days=start_days,
                hours=start_hours,
                minutes=start_minutes,
                seconds=start_seconds
            )

            calculated_end_time = start_time + datetime.timedelta(
                days=end_days,
                hours=end_hours,
                minutes=end_minutes,
                seconds=end_seconds
            )

            # Подготовим данные для обновления в БД
            # Заменяем относительные значения на абсолютные
            db_action_data = python_data.copy()
            db_action_data['calculated_start_time'] = calculated_start_time.strftime('%Y-%m-%dT%H:%M:%S')
            db_action_data['calculated_end_time'] = calculated_end_time.strftime('%Y-%m-%dT%H:%M:%S')

            # Удаляем относительные поля, так как они не хранятся в БД
            relative_fields = [
                'relative_start_days', 'relative_start_hours', 'relative_start_minutes', 'relative_start_seconds',
                'relative_end_days', 'relative_end_hours', 'relative_end_minutes', 'relative_end_seconds'
            ]
            for field in relative_fields:
                if field in db_action_data:
                    del db_action_data[field]

            # Вызываем метод напрямую из database_manager, передавая ему подготовленные данные
            if self.database_manager:
                try:
                    success = self.database_manager.update_action_execution(action_execution_id, db_action_data)
                    if success:
                        print(f"Python ApplicationData: Action_execution с относительным временем ID {action_execution_id} успешно обновлено.")
                        return True
                    else:
                        print(f"Python ApplicationData: Менеджер БД не смог обновить action_execution ID {action_execution_id}.")
                        return False
                except Exception as e:
                    print(f"Python ApplicationData: Исключение при обновлении action_execution ID {action_execution_id} через database_manager: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            else:
                print("Python ApplicationData: Ошибка - Нет подключения к БД SQLite.")
                return False

        except Exception as e:
            print(f"Python ApplicationData: Исключение при обновлении action_execution с относительным временем ID {action_execution_id}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False


    # ========================================================================
    # СЛОТЫ ДЛЯ РАБОТЫ С ОРГАНИЗАЦИЯМИ (QML)
    # ========================================================================

    @Slot(result='QVariant')
    def getAllOrganizations(self):
        """Получить все организации для QML."""
        if self.database_manager:
            try:
                result = self.database_manager.get_all_organizations()
                print(f"Python ApplicationData: getAllOrganizations вернул: {result}")
                print(f"Python ApplicationData: Тип результата: {type(result)}")
                if result:
                    print(f"Python ApplicationData: Тип первого элемента: {type(result[0])}")
                    print(f"Python ApplicationData: Первый элемент: {result[0]}")
                return result
            except Exception as e:
                print(f"Python ApplicationData: Ошибка при получении организаций: {e}")
                import traceback
                traceback.print_exc()
                return []
        else:
            print("Python ApplicationData: Менеджер БД не инициализирован.")
            return []

    @Slot('QVariant', result='QVariant')
    def createOrganization(self, org_data: 'QVariant'):
        """Создать организацию. Возвращает ID новой записи или 0 при ошибке."""
        py_data = org_data.toVariant() if hasattr(org_data, 'toVariant') else org_data
        if self.database_manager:
            try:
                return self.database_manager.create_organization(py_data)
            except Exception as e:
                print(f"Python ApplicationData: Ошибка при создании организации: {e}")
                return 0
        return 0

    @Slot(int, 'QVariant', result=bool)
    def updateOrganization(self, org_id: int, org_data: 'QVariant') -> bool:
        """Обновить организацию."""
        py_data = org_data.toVariant() if hasattr(org_data, 'toVariant') else org_data
        if self.database_manager:
            try:
                return self.database_manager.update_organization(org_id, py_data)
            except Exception as e:
                print(f"Python ApplicationData: Ошибка при обновлении организации: {e}")
                return False
        return False

    @Slot(int, result=bool)
    def deleteOrganization(self, org_id: int) -> bool:
        """Удалить организацию."""
        if self.database_manager:
            try:
                return self.database_manager.delete_organization(org_id)
            except Exception as e:
                print(f"Python ApplicationData: Ошибка при удалении организации: {e}")
                return False
        return False

    @Slot(int, result='QVariant')
    def getOrganizationReferenceFiles(self, org_id: int):
        """Получить справочные файлы организации."""
        if self.database_manager:
            try:
                return self.database_manager.get_organization_reference_files(org_id)
            except Exception as e:
                print(f"Python ApplicationData: Ошибка при получении файлов: {e}")
                return []
        return []

    @Slot(int, str, str, result=bool)
    def addOrganizationReferenceFile(self, org_id: int, file_path: str, file_type: str = 'other') -> bool:
        """Добавить справочный файл к организации."""
        if self.database_manager:
            try:
                return self.database_manager.add_organization_reference_file(org_id, file_path, file_type)
            except Exception as e:
                print(f"Python ApplicationData: Ошибка при добавлении файла: {e}")
                return False
        return False

    @Slot(int, result=bool)
    def deleteOrganizationReferenceFile(self, file_id: int) -> bool:
        """Удалить справочный файл организации (только запись в БД)."""
        if self.database_manager:
            try:
                return self.database_manager.delete_organization_reference_file(file_id)
            except Exception as e:
                print(f"Python ApplicationData: Ошибка при удалении файла: {e}")
                return False
        return False

    @Slot(int, result=bool)
    def deleteOrganizationReferenceFileWithPhysicalFile(self, file_id: int) -> bool:
        """Удалить справочный файл организации И физический файл с диска."""
        import os
        if self.database_manager:
            try:
                files = self.database_manager.get_organization_reference_files_by_id(file_id)
                if files and len(files) > 0:
                    file_path = files[0].get('file_path', '')
                    db_success = self.database_manager.delete_organization_reference_file(file_id)
                    if db_success and file_path:
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                print(f"Python ApplicationData: Файл удалён с диска: {file_path}")
                                return True
                            except OSError as e:
                                print(f"Python ApplicationData: Ошибка при удалении файла с диска: {e}")
                                return True
                        else:
                            print(f"Python ApplicationData: Файл не найден на диске: {file_path}")
                            return True
                    return db_success
                else:
                    print(f"Python ApplicationData: Файл с ID {file_id} не найден в БД.")
                    return False
            except Exception as e:
                print(f"Python ApplicationData: Ошибка при удалении файла с диска: {e}")
                return False
        return False

    @Slot(int, result='QVariant')
    def getOrganizationsForActionExecution(self, action_execution_id: int):
        """Получить организации, привязанные к действию."""
        if self.database_manager:
            try:
                orgs = self.database_manager.get_organizations_for_action_execution(action_execution_id)
                result = []
                for org in orgs:
                    files = self.database_manager.get_organization_reference_files(org['id'])
                    org_with_files = dict(org)
                    org_with_files['reference_files'] = files
                    result.append(org_with_files)
                return result
            except Exception as e:
                print(f"Python ApplicationData: Ошибка при получении организаций: {e}")
                return []
        return []

    @Slot(result='QVariant')
    def getAllOrganizationsWithReferenceFiles(self):
        """Получить ВСЕ организации с привязанными к ним справочными файлами."""
        if self.database_manager:
            try:
                # 1. Получаем все организации
                orgs = self.database_manager.get_all_organizations()
                result = []
                
                # 2. Для каждой организации подгружаем файлы
                for org in orgs:
                    org_with_files = dict(org) # Копируем данные организации
                    # Получаем файлы и добавляем их в словарь организации
                    files = self.database_manager.get_organization_reference_files(org['id'])
                    org_with_files['reference_files'] = files 
                    result.append(org_with_files)
                    
                return result
            except Exception as e:
                print(f"Python ApplicationData: Ошибка при получении списка всех организаций: {e}")
                return []
        return []


    @Slot(int, str, result=bool)
    def updateActionExecutionStatus(self, action_execution_id: int, new_status: str) -> bool:
        """Обновить статус выполнения действия."""
        if self.database_manager:
            try:
                return self.database_manager.update_action_execution_status(action_execution_id, new_status)
            except Exception as e:
                print(f"Python ApplicationData: Ошибка при обновлении статуса: {e}")
                return False
        return False

    @Slot(int, str, result=bool)
    def updateActionExecutionReportedTo(self, action_execution_id: int, reported_to: str) -> bool:
        """Обновить поле 'Кому доложено' для действия."""
        if self.database_manager:
            try:
                return self.database_manager.update_action_execution_reported_to(action_execution_id, reported_to)
            except Exception as e:
                print(f"Python ApplicationData: Ошибка при обновлении reported_to: {e}")
                return False
        return False

    @Slot(int, str, result=bool)
    def addActionExecutionReportMaterial(self, action_execution_id: int, material_path: str) -> bool:
        """Добавить отчётный материал к действию."""
        if self.database_manager:
            try:
                return self.database_manager.append_action_execution_report_material(action_execution_id, material_path)
            except Exception as e:
                print(f"Python ApplicationData: Ошибка при добавлении отчётного материала: {e}")
                return False
        return False

    @Slot(int, int, result=bool)
    def deleteActionExecutionReportMaterial(self, action_execution_id: int, material_index: int) -> bool:
        """Удалить отчётный материал по индексу."""
        if self.database_manager:
            try:
                return self.database_manager.delete_action_execution_report_material(action_execution_id, material_index)
            except Exception as e:
                print(f"Python ApplicationData: Ошибка при удалении отчётного материала: {e}")
                return False
        return False


def on_qml_loaded(obj, url):
    if obj and url.fileName() == "main.qml":
        print("QML main.qml загружен. Устанавливаем соединения сигналов...")
        # obj - это корневой объект ApplicationWindow из main.qml
        # Подключаем сигнал mainScreenRequested к функции QML switchToMainScreen
        # и loginScreenRequested к функции QML switchToLoginScreen
        data_context.mainScreenRequested.connect(obj.switchToMainScreen)
        data_context.loginScreenRequested.connect(obj.switchToLoginScreen)
        print("Соединения сигналов установлены.")



# --- ТОЧКА ВХОДА В ПРИЛОЖЕНИЕ ---
if __name__ == "__main__":
    # --- Используем QApplication для поддержки QSystemTrayIcon ---
    app = QApplication(sys.argv)
    # ВАЖНО: Не завершать приложение при закрытии последнего окна
    app.setQuitOnLastWindowClosed(False)

    app.setWindowIcon(QIcon('emblem.ico'))

    # --- СОЗДАЕМ экземпляр менеджера ЛОКАЛЬНОЙ КОНФИГУРАЦИИ (SQLite) ---
    sqlite_config_manager = SQLiteConfigManager()
    print("Python: SQLiteConfigManager инициализирован.")
    # --- ---

    # --- Сначала создаем engine ---
    engine = QQmlApplicationEngine()

    # --- Затем создаем ApplicationData, ПЕРЕДАВАЯ app, engine и db_manager ---
    # Обратите внимание на добавленный аргумент db_manager
    data_context = ApplicationData(app, engine, sqlite_config_manager) # <-- Добавлен sqlite_config_manager
    
    # --- Регистрация контекста для QML ---
    engine.rootContext().setContextProperty("appData", data_context)

    engine.objectCreated.connect(on_qml_loaded)

    # --- Загрузка QML файла ---
    qml_file = Path(__file__).parent / "ui" / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        sys.exit(-1)

    # --- П��ДКЛЮЧАЕМ ОЧИСТКУ ПРИ ЗАВЕРШЕНИИ ПРИЛОЖЕНИЯ ---
    # Подключаем сигнал aboutToQuit к методу уничтожения контейнера у data_context
    # Lambda используется для захвата ссылки на data_context в момент подключения
    app.aboutToQuit.connect(lambda dc=data_context: dc.notification_container.deleteLater() if hasattr(dc, 'notification_container') else None)
    # --- ---

    sys.exit(app.exec())
