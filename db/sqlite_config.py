# db/sqlite_config.py
import sqlite3
import os
from pathlib import Path
# Для шифрования пароля
import base64
# Для хранения настроек приложения
import json
from typing import Optional, Dict, Any, List
import logging

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class SQLiteConfigManager:
    """Класс для управления локальной конфигурацией приложения в SQLite.
    Хранит параметры подключения к PostgreSQL и настройки приложения.
    """
    DB_FILENAME = "local_config.db"
    # Простой XOR-ключ (в реальном приложении следует использовать более сложный метод)
    XOR_KEY = b"my_simple_key_for_xor_encryption_12345"

    def __init__(self, config_path=None):
        """Инициализирует менеджер локальной конфигурации.
        :param config_path: Путь к файлу SQLite конфига.
                           Если None, используется путь по умолчанию (папка проекта/db/).
        """
        if config_path is None:
            # Хорошей практикой является хранение конфигов в подкаталоге проекта
            project_db_dir = Path(__file__).parent
            self.config_path = project_db_dir / self.DB_FILENAME
        else:
            self.config_path = Path(config_path)
        print(f"Путь к локальному конфигу SQLite: {self.config_path}")
        self._init_db()

    def _get_connection(self):
        """Создает и возвращает соединение с локальной БД SQLite."""
        conn = sqlite3.connect(str(self.config_path))
        conn.row_factory = sqlite3.Row  # Позволяет обращаться к колонкам по имени
        return conn

    def _init_db(self):
        """Инициализирует локальную базу данных SQLite."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # - Таблица параметров подключения к PostgreSQL -
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pg_connection (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                dbname TEXT NOT NULL,
                user TEXT NOT NULL,
                encrypted_password TEXT -- Храним зашифрованный пароль
            )
        ''')

        # Вставляем "заглушку" подключения, если запись отсутствует
        cursor.execute("SELECT COUNT(*) FROM pg_connection WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            # Вставляем запись с пустыми значениями по умолчанию
            cursor.execute('''
                INSERT INTO pg_connection (id, host, port, dbname, user, encrypted_password)
                VALUES (1, '', 5432, '', '', '')
            ''')
            print("Вставлена заглушка конфигурации подключения к PG.")

        # - Таблица настроек приложения -
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                workplace_name TEXT DEFAULT 'Рабочее место дежурного',
                post_number TEXT DEFAULT '1',
                post_name TEXT DEFAULT 'Дежурство по части',
                use_persistent_reminders INTEGER DEFAULT 1, -- 1=True, 0=False
                sound_enabled INTEGER DEFAULT 1, -- 1=True, 0=False
                custom_datetime TEXT DEFAULT NULL, -- ISO формат или NULL
                background_image_path TEXT DEFAULT NULL,
                font_family TEXT DEFAULT 'Arial',
                font_size INTEGER DEFAULT 12,
                background_color TEXT DEFAULT '#ecf0f1',
                current_officer_id INTEGER DEFAULT NULL, -- ID текущего дежурного
                settings_password_hash TEXT DEFAULT NULL, -- Хэш пароля настроек
                print_font_family TEXT DEFAULT 'Arial',
                print_font_size INTEGER DEFAULT 12,
                -- --- НОВЫЕ ПОЛЯ ДЛЯ ВРЕМЕНИ ---
                custom_time_label TEXT DEFAULT 'Местное время',
                custom_time_offset_seconds INTEGER DEFAULT 0, -- Смещение местного времени в секундах
                show_moscow_time INTEGER DEFAULT 1, -- 1=True, 0=False
                moscow_time_offset_seconds INTEGER DEFAULT 0 -- Смещение московского времени в секундах
                -- --- ---
            )
        ''')

        # --- МИГРАЦИЯ: Добавление новых колонок, если они отсутствуют ---
        # Это необходимо для обновления существующих БД
        # Получаем информацию о существующих колонках
        cursor.execute("PRAGMA table_info(app_settings)")
        existing_columns = [info[1] for info in cursor.fetchall()] # info[1] это имя колонки

        # Список новых колонок и их определения
        new_columns = {
            'custom_time_label': "TEXT DEFAULT 'Местное время'",
            'custom_time_offset_seconds': "INTEGER DEFAULT 0",
            'show_moscow_time': "INTEGER DEFAULT 1",
            'moscow_time_offset_seconds': "INTEGER DEFAULT 0",
            'font_style': "TEXT DEFAULT 'normal'",
            'print_font_style': "TEXT DEFAULT 'normal'"
        }

        # Проверяем и добавляем каждую новую колонку, если её нет
        for col_name, col_definition in new_columns.items():
            if col_name not in existing_columns:
                try:
                    # Используем f-string для формирования команды ALTER TABLE
                    # ВНИМАНИЕ: Имя таблицы и имя колонки НЕЛЬЗЯ подставлять через параметры в execute,
                    # только значения. Здесь имена фиксированы и безопасны.
                    alter_sql = f"ALTER TABLE app_settings ADD COLUMN {col_name} {col_definition}"
                    cursor.execute(alter_sql)
                    print(f"Миграция БД: Добавлена колонка '{col_name}' в таблицу 'app_settings'.")
                except sqlite3.Error as e:
                    print(f"Ошибка миграции БД при добавлении колонки '{col_name}': {e}. Возможно, колонка уже существует или имя некорректно.")
        # --- Конец миграции ---

        # Проверка и вставка начальных данных для настроек приложения
        cursor.execute("SELECT COUNT(*) FROM app_settings WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO app_settings (
                    id, 
                    workplace_name, 
                    post_number, 
                    post_name, 
                    print_font_family, 
                    print_font_size,
                    custom_time_label,
                    custom_time_offset_seconds,
                    show_moscow_time,
                    moscow_time_offset_seconds
                )
                VALUES (
                    1, 
                    'Рабочее место дежурного', 
                    '1', 
                    'Дежурство по части', 
                    'Arial', 
                    12,
                    'Местное время',
                    0,
                    1,
                    0
                )
            ''')
            print("Вставлена запись настроек приложения по умолчанию.")

        conn.commit()
        conn.close()
        print("Локальная БД конфигурации SQLite инициализирована.")

    # - Методы для работы с подключением к PostgreSQL -
    def get_connection_config(self) -> Optional[Dict[str, Any]]:
        """Получает конфигурацию подключения к PostgreSQL из локальной БД SQLite.
        :return: Словарь с параметрами подключения или None.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT host, port, dbname, user, encrypted_password FROM pg_connection WHERE id = 1")
            row = cursor.fetchone()
            conn.close()
            if row:
                config = dict(row)
                # Расшифровываем пароль
                config['password'] = self._xor_decrypt(config.pop('encrypted_password'))
                return config
            return None
        except sqlite3.Error as e:
            logger.error(f"Ошибка БД SQLite при получении конфигурации подключения к PG: {e}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка при получении конфигурации подключения к PG из SQLite: {e}")
            return None

    def save_connection_config(self, host, port, dbname, user, password):
        """Сохраняет конфигурацию подключения к PostgreSQL в локальной БД SQLite.
        :param host: Хост PostgreSQL.
        :param port: Порт PostgreSQL.
        :param dbname: Имя базы данных.
        :param user: Имя пользователя.
        :param password: Пароль (будет зашифрован).
        """
        encrypted_password = self._xor_encrypt(password)
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE pg_connection
            SET host = ?, port = ?, dbname = ?, user = ?, encrypted_password = ?
            WHERE id = 1
        ''', (host, port, dbname, user, encrypted_password))
        conn.commit()
        conn.close()
        print("Конфигурация подключения к PostgreSQL сохранена (пароль зашифрован).")

    # - Методы для работы с настройками приложения -
    def get_app_settings(self) -> Optional[Dict[str, Any]]:
        """Получает настройки приложения из локальной БД SQLite.
        :return: Словарь с настройками приложения или None.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM app_settings WHERE id = 1")
            row = cursor.fetchone()
            # Получаем названия колонок
            colnames = [desc[0] for desc in cursor.description]
            conn.close()
            
            if row:
                # Создаем словарь из результата
                settings_dict = dict(zip(colnames, row))
                logger.debug(f"Настройки приложения загружены из SQLite: { {k:v for k,v in settings_dict.items() if k != 'settings_password_hash'} }") # Лог без пароля
                return settings_dict
            else:
                logger.warning("Запись настроек приложения (id=1) не найдена в SQLite.")
                return None
        except sqlite3.Error as e:
            logger.error(f"Ошибка БД SQLite при получении настроек приложения: {e}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка при получении настроек приложения из SQLite: {e}")
            return None

    def update_app_settings(self, settings_data: Dict[str, Any]) -> bool:
        """Обновляет настройки приложения в локальной БД SQLite.
        :param settings_data: Словарь с новыми значениями настроек.
        :return: True, если успешно, иначе False.
        """
        if not settings_data:
            logger.warning("Попытка обновления настроек приложения с пустыми данными.")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Формируем SQL-запрос динамически, исключая 'id'
            # Это безопасно, так как ключи берутся из нашего кода, а не из пользовательского ввода
            fields_to_update = [key for key in settings_data.keys() if key != 'id']
            if not fields_to_update:
                 logger.warning("Нет полей для обновления в настройках приложения.")
                 return False

            set_clause = ", ".join([f"{key} = ?" for key in fields_to_update])
            values = [settings_data[key] for key in fields_to_update]
            values.append(1) # id = 1
            
            sql_query = f"UPDATE app_settings SET {set_clause} WHERE id = ?;"
            
            logger.debug(f"Выполнение SQL обновления настроек приложения: {cursor.mogrify(sql_query, values) if hasattr(cursor, 'mogrify') else sql_query}")
            cursor.execute(sql_query, values)
            conn.commit()
            
            rows_affected = cursor.rowcount
            conn.close()
            
            if rows_affected > 0:
                logger.info("Настройки приложения успешно обновлены в SQLite.")
                return True
            else:
                logger.warning("Не удалось обновить настройки приложения в SQLite (запись не найдена или данные не изменились).")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"Ошибка БД SQLite при обновлении настроек приложения: {e}")
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Неизвестная ошибка при обновлении настроек приложения в SQLite: {e}")
            if conn:
                conn.rollback()
            return False

    # - Вспомогательные методы для шифрования -
    def _xor_encrypt(self, plaintext: str) -> str:
        """Простое XOR-шифрование строки."""
        if not plaintext:
            return ""
        plaintext_bytes = plaintext.encode('utf-8')
        # Ключ повторяется или обрезается до длины текста
        key_cycle = (self.XOR_KEY * (len(plaintext_bytes) // len(self.XOR_KEY) + 1))[:len(plaintext_bytes)]
        encrypted_bytes = bytes([b ^ k for b, k in zip(plaintext_bytes, key_cycle)])
        # Кодируем в base64 для хранения в текстовом поле БД
        return base64.b64encode(encrypted_bytes).decode('utf-8')

    def _xor_decrypt(self, ciphertext: str) -> str:
        """Простое XOR-дешифрование строки."""
        if not ciphertext:
            return ""
        try:
            ciphertext_bytes = base64.b64decode(ciphertext.encode('utf-8'))
            key_cycle = (self.XOR_KEY * (len(ciphertext_bytes) // len(self.XOR_KEY) + 1))[:len(ciphertext_bytes)]
            decrypted_bytes = bytes([b ^ k for b, k in zip(ciphertext_bytes, key_cycle)])
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            print(f"Ошибка дешифрования: {e}")
            return "" # Возвращаем пустую строку в случае ошибки

# - Пример использования (для тестирования модуля отдельно) -
if __name__ == "__main__":
    config_manager = SQLiteConfigManager()
    config = config_manager.get_connection_config()
    print("Текущая конфигурация подключения к PG:", config)
    app_settings = config_manager.get_app_settings()
    print("Текущие настройки приложения:", app_settings)
    # Пример сохранения настроек приложения
    # config_manager.update_app_settings()
    # print("Настройки приложения обновлены.")