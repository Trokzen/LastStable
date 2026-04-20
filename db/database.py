# db/database.py
import sqlite3
import os
from pathlib import Path
# from PySide6.QtCore import QStandardPaths, QDir # Потребуется позже для определения пути

class DatabaseManager:
    """
    Класс для управления подключением к базе данных SQLite и выполнения запросов.
    """
    DB_FILENAME = "duty_app.db"

    def __init__(self, db_path=None):
        """
        Инициализирует менеджер БД.
        :param db_path: Путь к файлу БД. Если None, используется путь по умолчанию (рядом со скриптом).
        """
        if db_path is None:
            # Определяем путь к файлу БД рядом с этим скриптом (пока без QStandardPaths)
            self.db_path = Path(__file__).parent / self.DB_FILENAME
        else:
            self.db_path = Path(db_path)
        print(f"Путь к БД: {self.db_path}")
        self._init_db()

    def _get_connection(self):
        """Создает и возвращает соединение с БД."""
        # check_same_thread=False может потребоваться в многопоточных приложениях,
        # но для простоты пока можно опустить или оставить.
        conn = sqlite3.connect(str(self.db_path)) # str() для совместимости
        conn.row_factory = sqlite3.Row  # Позволяет обращаться к колонкам по имени
        return conn

    def _init_db(self):
        """Инициализирует базу данных, создавая таблицы, если они не существуют."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # --- Создание таблицы должностных лиц ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS duty_officers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rank TEXT NOT NULL,
                last_name TEXT NOT NULL,
                first_name TEXT NOT NULL,
                middle_name TEXT,
                phone TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        print("Таблица 'duty_officers' проверена/создана.")

        # --- Создание таблицы настроек (если планируете использовать) ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                workplace_name TEXT DEFAULT 'Рабочее место дежурного',
                post_number TEXT DEFAULT '1',
                post_name TEXT DEFAULT 'Дежурство по части',
                custom_datetime TEXT DEFAULT NULL,
                background_image_path TEXT DEFAULT NULL,
                font_family TEXT DEFAULT 'Arial',
                font_size INTEGER DEFAULT 12,
                background_color TEXT DEFAULT '#ecf0f1',
                sound_enabled INTEGER DEFAULT 1,
                persistent_reminders INTEGER DEFAULT 1,
                current_officer_id INTEGER DEFAULT NULL,
                settings_password_hash TEXT DEFAULT NULL -- Для хранения хэша пароля настроек
            )
        ''')
        # Проверка и вставка начальных данных для settings
        cursor.execute("SELECT COUNT(*) FROM settings WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO settings (id, workplace_name, post_number, post_name)
                VALUES (1, 'Рабочее место дежурного', '1', 'Дежурство по части')
            ''')
            print("Вставлена запись настроек по умолчанию.")

        conn.commit()
        conn.close()
        print("База данных инициализирована.")

    # --- Методы для работы с данными ---

    def get_settings(self):
        """Получает текущие настройки из БД."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM settings WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def update_settings(self, settings_dict):
        """
        Обновляет настройки в БД.
        :param settings_dict: Словарь с новыми значениями настроек.
        """
        if not settings_dict:
            return
        conn = self._get_connection()
        cursor = conn.cursor()
        columns = ', '.join([f"{key} = ?" for key in settings_dict.keys()])
        values = list(settings_dict.values())
        values.append(1) # id = 1
        sql = f"UPDATE settings SET {columns} WHERE id = ?"
        cursor.execute(sql, values)
        conn.commit()
        conn.close()
        print("Настройки обновлены.")

    # --- Методы для работы с должностными лицами ---

    def get_all_duty_officers(self, include_inactive=False):
        """
        Получает список всех должностных лиц.
        :param include_inactive: Если True, включает неактивных (is_active=0).
        :return: Список словарей с данными должностных лиц.
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            if include_inactive:
                cursor.execute("SELECT * FROM duty_officers ORDER BY last_name, first_name")
            else:
                cursor.execute("SELECT * FROM duty_officers WHERE is_active = 1 ORDER BY last_name, first_name")
            rows = cursor.fetchall()
            conn.close()
            # Преобразуем sqlite3.Row в словари
            result = [dict(row) for row in rows]
            print(f"DB Manager: Получен список из {len(result)} должностных лиц.")
            return result
        except sqlite3.Error as e:
            print(f"DB Manager: Ошибка SQLite при получении списка: {e}")
            if conn:
                conn.close()
            return []
        except Exception as e:
            print(f"DB Manager: Неизвестная ошибка при получении списка: {e}")
            import traceback
            traceback.print_exc()
            if conn:
                conn.close()
            return []

    def get_duty_officer_by_id(self, officer_id):
        """
        Получает данные должностного лица по его ID.
        :param officer_id: ID должностного лица.
        :return: Словарь с данными или None.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM duty_officers WHERE id = ?", (officer_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def add_duty_officer(self, officer_data):
        """
        Добавляет нового должностного лица.
        :param officer_data: Словарь с данными должностного лица.
                             Должен содержать ключи: rank, last_name, first_name.
                             Может содержать: middle_name, phone, is_active.
        :return: ID нового должностного лица или -1 в случае ошибки.
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            fields = []
            placeholders = []
            values = []
            for key, value in officer_data.items():
                if key in ['rank', 'last_name', 'first_name', 'middle_name', 'phone', 'is_active']:
                    fields.append(key)
                    placeholders.append('?')
                    # Обработка None для текстовых полей
                    values.append(value if value is not None else None)

            if not fields:
                print("Нет корректных полей для вставки.")
                return -1

            columns_str = ', '.join(fields)
            placeholders_str = ', '.join(placeholders)
            sql = f"INSERT INTO duty_officers ({columns_str}) VALUES ({placeholders_str})"

            cursor.execute(sql, values)
            new_id = cursor.lastrowid
            conn.commit()
            print(f"DB Manager: Добавлен должностной: ID {new_id}")
            return new_id
        except sqlite3.Error as e:
            print(f"DB Manager: Ошибка SQLite при добавлении должностного лица: {e}")
            if conn:
                conn.rollback()
            return -1
        except Exception as e:
            print(f"DB Manager: Неизвестная ошибка при добавлении должностного лица: {e}")
            if conn:
                conn.rollback()
            return -1
        finally:
            if conn:
                conn.close()

    def update_duty_officer(self, officer_id, officer_data):
        """
        Обновляет данные должностного лица.
        :param officer_id: ID должностного лица.
        :param officer_data: Словарь с новыми данными.
        """
        conn = None
        if not officer_data:
            return
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            fields = []
            values = []
            for key, value in officer_data.items():
                if key in ['rank', 'last_name', 'first_name', 'middle_name', 'phone', 'is_active']:
                    fields.append(f"{key} = ?")
                    values.append(value if value is not None else None)

            if not fields:
                print("Нет корректных полей для обновления.")
                return

            values.append(officer_id)
            columns_str = ', '.join(fields)
            sql = f"UPDATE duty_officers SET {columns_str} WHERE id = ?"
            cursor.execute(sql, values)
            conn.commit()
            print(f"DB Manager: Обновлен должностной: ID {officer_id}")
        except sqlite3.Error as e:
            print(f"DB Manager: Ошибка SQLite при обновлении должностного лица {officer_id}: {e}")
            if conn:
                conn.rollback()
        except Exception as e:
            print(f"DB Manager: Неизвестная ошибка при обновлении должностного лица {officer_id}: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    def delete_duty_officer(self, officer_id):
        """
        Удаляет должностное лицо по ID.
        :param officer_id: ID должностного лица.
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            # Физическое удаление. Можно заменить на is_active = 0.
            cursor.execute("DELETE FROM duty_officers WHERE id = ?", (officer_id,))
            conn.commit()
            print(f"DB Manager: Удален должностной: ID {officer_id}")
        except sqlite3.Error as e:
            print(f"DB Manager: Ошибка SQLite при удалении должностного лица {officer_id}: {e}")
            if conn:
                conn.rollback()
        except Exception as e:
            print(f"DB Manager: Неизвестная ошибка при удалении должностного лица {officer_id}: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    def set_current_duty_officer(self, officer_id):
        """
        Устанавливает выбранного дежурного в настройках.
        :param officer_id: ID нового дежурного (может быть None для сброса).
        """
        self.update_settings({'current_officer_id': officer_id})

    def get_current_duty_officer(self):
        """
        Получает текущего выбранного дежурного на основе настроек.
        :return: Словарь с данными дежурного или None.
        """
        settings = self.get_settings()
        officer_id = settings.get('current_officer_id') if settings else None
        if officer_id:
            return self.get_duty_officer_by_id(officer_id)
        return None
