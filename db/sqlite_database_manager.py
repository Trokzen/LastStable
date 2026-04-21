# db/sqlite_database_manager.py
import sqlite3
from typing import Optional, Dict, Any, List
import logging
import datetime
from werkzeug.security import check_password_hash, generate_password_hash

# Настройка логирования для отладки
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Или DEBUG для более подробного лога

class SQLiteDatabaseManager:
    """
    Класс для управления подключением к базе данных SQLite
    и выполнения запросов, связанных с основной логикой приложения.
    """
    
    def __init__(self, db_path: str):
        """
        Инициализирует менеджер БД SQLite.
        :param db_path: Путь к файлу базы данных SQLite.
        """
        self.db_path = db_path
        self.connection = None
        logger.info(f"SQLiteDatabaseManager инициализирован. Путь к БД: {self.db_path}")
        
        # Инициализируем базу данных
        self._init_db()

    def _get_connection(self):
        """
        Создает и возвращает новое подключение к БД.
        """
        try:
            logger.debug(f"Попытка подключения к SQLite: {self.db_path}")

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Позволяет обращаться к колонкам по имени

            # ВАЖНО: Включаем поддержку внешних ключей в SQLite
            conn.execute("PRAGMA foreign_keys = ON;")
            logger.debug("Поддержка внешних ключей включена.")

            logger.debug("Соединение sqlite3 создано.")

            return conn
        except sqlite3.Error as e:
            logger.error(f"Ошибка подключения к SQLite: {e}")
            raise
        except Exception as e: # Ловим любые другие исключения
            logger.error(f"Неизвестная ошибка при подключении к SQLite: {type(e).__name__}: {e}")
            raise

    def _init_db(self):
        """Инициализирует базу данных SQLite, создавая таблицы, если они не существуют."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # ВАЖНО: Убедимся, что поддержка внешних ключей включена перед созданием таблиц
        cursor.execute("PRAGMA foreign_keys = ON;")
        logger.debug("Поддержка внешних ключей включена при инициализации БД.")

        # Читаем SQL-скрипт из файла и выполняем его
        import os
        import sys

        # Определяем путь к файлу в зависимости от того, запущено ли приложение как скрипт или exe
        if getattr(sys, 'frozen', False):
            # Приложение запущено как exe — используем _MEIPASS (стандартный способ PyInstaller)
            base_path = sys._MEIPASS
            schema_path = os.path.join(base_path, 'db', 'init_sqlite_schema.sql')
        else:
            # Приложение запущено как скрипт
            script_dir = os.path.dirname(os.path.abspath(__file__))
            schema_path = os.path.join(script_dir, 'init_sqlite_schema.sql')

        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Выполняем скрипт
        cursor.executescript(sql_script)

        # --- МИГРАЦИЯ: Добавляем missing колонки если их нет ---
        cursor.execute("PRAGMA table_info(actions)")
        existing_columns = [info[1] for info in cursor.fetchall()]

        if 'technical_text' not in existing_columns:
            try:
                cursor.execute("ALTER TABLE actions ADD COLUMN technical_text TEXT;")
                logger.info("Миграция: добавлена колонка technical_text в actions.")
            except sqlite3.Error as e:
                logger.warning(f"Миграция: не удалось добавить technical_text: {e}")

        if 'snapshot_technical_text' not in existing_columns:
            try:
                cursor.execute("ALTER TABLE action_executions ADD COLUMN snapshot_technical_text TEXT;")
                logger.info("Миграция: добавлена колонка snapshot_technical_text в action_executions.")
            except sqlite3.Error as e:
                logger.warning(f"Миграция: не удалось добавить snapshot_technical_text: {e}")
        # --- Конец миграции ---

        conn.commit()
        conn.close()
        logger.info("База данных SQLite инициализирована.")

    def close_connection(self):
        """Закрывает подключение к БД."""
        if self.connection:
            self.connection.close()
            logger.info("Подключение к SQLite закрыто.")
            self.connection = None

    def test_connection(self) -> bool:
        """
        Тестирует подключение к БД.
        :return: True, если подключение успешно, иначе False.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Простой запрос для проверки подключения
            cursor.execute('SELECT 1;')
            test_result = cursor.fetchone()

            cursor.close()
            conn.close()  # Закрываем соединение после использования

            if test_result:
                logger.info("Тест подключения к SQLite успешен.")
                return True
            else:
                logger.error("Тест подключения к SQLite не удался: не удалось выполнить простой запрос.")
                return False

        except Exception as e:
            logger.error(f"Тест подключения к SQLite не удался: {e}")
            return False

    def authenticate_user(self, login: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Аутентифицирует пользователя по логину и паролю.
        :param login: Логин пользователя.
        :param password: Введенный пароль (в открытом виде).
        :return: Словарь с данными пользователя, если аутентификация успешна, иначе None.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, login, password_hash, rank, last_name, first_name, middle_name, is_admin FROM users WHERE login = ? AND is_active = 1;",
                (login,)
            )
            user_record = cursor.fetchone()
            cursor.close()

            if user_record:
                # user_record[2] - это password_hash из запроса
                stored_hash = user_record[2]
                # Проверяем, соответствует ли введенный пароль хэшу с помощью Werkzeug
                if check_password_hash(stored_hash, password):
                    logger.info(f"Пользователь '{login}' успешно аутентифицирован.")
                    # Возвращаем данные пользователя (без хэша пароля)
                    return {
                        'id': user_record[0],
                        'login': user_record[1],
                        'rank': user_record[3],
                        'last_name': user_record[4],
                        'first_name': user_record[5],
                        'middle_name': user_record[6],
                        'is_admin': bool(user_record[7])
                    }
                else:
                    logger.warning(f"Неверный пароль для пользователя '{login}'.")
            else:
                logger.warning(f"Пользователь '{login}' не найден или неактивен.")
            return None
        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при аутентификации пользователя '{login}': {e}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка при аутентификации пользователя '{login}': {e}")
            return None

    # --- Методы для работы с данными (реализации) ---

    def get_settings(self) -> Optional[Dict[str, Any]]:
        """Получает настройки приложения из БД."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM post_settings WHERE id = 1;")
            row = cursor.fetchone()
            # Получаем названия колонок
            colnames = [desc[0] for desc in cursor.description]
            cursor.close()

            if row:
                # Создаем словарь из результата
                settings_dict = dict(zip(colnames, row))
                logger.debug(f"Настройки загружены из БД: {settings_dict}")
                return settings_dict
            else:
                logger.warning("Запись настроек (id=1) не найдена в БД.")
                return None
        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при получении настроек: {e}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка при получении настроек: {e}")
            return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Получает список всех пользователей (активных и неактивных), отсортированных по званию, фамилии, имени, отчеству.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            # Убираем WHERE is_active = TRUE, чтобы получить всех пользователей
            cursor.execute(
                "SELECT id, login, rank, last_name, first_name, middle_name, phone, is_active, is_admin FROM users ORDER BY rank ASC, last_name ASC, first_name ASC, middle_name ASC;"
            )
            rows = cursor.fetchall()
            # Получаем названия колонок
            colnames = [desc[0] for desc in cursor.description]
            cursor.close()

            # Преобразуем список кортежей в список словарей
            users_list = [dict(zip(colnames, row)) for row in rows]
            logger.debug(f"Получен список {len(users_list)} всех пользователей из БД (отсортирован по званию, фамилии, имени, отчеству).")
            return users_list
        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при получении списка всех пользователей: {e}")
            return []
        except Exception as e:
            logger.error(f"Неизвестная ошибка при получении списка всех пользователей: {e}")
            return []

    # --- Добавим заглушку для будущего метода обновления настроек ---
    def update_settings(self, settings_data: Dict[str, Any]) -> bool:
        """
        Обновляет настройки приложения в БД.
        :param settings_data: Словарь с новыми значениями настроек.
        :return: True, если успешно, иначе False.
        """
        if not settings_data:
            logger.warning("Попытка обновления настроек с пустыми данными.")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Формируем SQL-запрос динамически, исключая 'id'
            # Это безопасно, так как ключи берутся из нашего кода, а не из пользовательского ввода
            fields_to_update = [key for key in settings_data.keys() if key != 'id']
            if not fields_to_update:
                 logger.warning("Нет полей для обновления в настройках.")
                 return False

            set_clause = ", ".join([f"{key} = ?" for key in fields_to_update])
            values = [settings_data[key] for key in fields_to_update]
            values.append(1) # id = 1

            sql_query = f"UPDATE post_settings SET {set_clause} WHERE id = ?;"

            logger.debug(f"Выполнение SQL обновления настроек: {sql_query} с параметрами {values}")
            cursor.execute(sql_query, values)
            conn.commit()

            rows_affected = cursor.rowcount
            cursor.close()

            if rows_affected > 0:
                logger.info(f"Настройки успешно обновлены в БД. Затронуто строк: {rows_affected}.")
                return True
            else:
                logger.warning("Не удалось обновить настройки (запись не найдена или данные не изменились).")
                return False

        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при обновлении настроек: {e}")
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Неизвестная ошибка при обновлении настроек: {e}")
            if conn:
                conn.rollback()
            return False

        # --- НОВЫЕ МЕТОДЫ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ (ДОЛЖНОСТНЫМИ ЛИЦАМИ) ---

    def create_user(self, user_data: Dict[str, Any]) -> int:
        """
        Создает нового пользователя (должностного лица) в БД.
        :param user_data: Словарь с данными нового пользователя.
                         Должен содержать ключи: rank, last_name, first_name, login.
                         Может содержать: middle_name, phone, is_active, is_admin, new_password.
        :return: ID нового пользователя, если успешно, иначе -1.
        """
        if not user_data:
            logger.warning("Попытка создания пользователя с пустыми данными.")
            return -1

        required_fields = ['rank', 'last_name', 'first_name', 'login'] # <-- Обновлено: добавлен 'login'
        missing_fields = [field for field in required_fields if not user_data.get(field)]
        if missing_fields:
            logger.error(f"Отсутствуют обязательные поля для создания пользователя: {missing_fields}")
            return -1

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # --- Подготовка полей и значений для INSERT ---
            # Определяем поля, которые будут вставлены
            # --- ОБНОВЛЕНО: Добавлены 'login' и 'password_hash' ---
            allowed_fields = ['rank', 'last_name', 'first_name', 'middle_name', 'phone', 'is_active', 'is_admin', 'login', 'password_hash']
            # --- ---
            fields = [field for field in allowed_fields if field in user_data or field == 'password_hash'] # Всегда включаем password_hash, если есть new_password

            # Создаем список ? плейсхолдеров
            placeholders = ['?'] * len(fields)

            # Формируем значения для вставки, обрабатывая типы данных
            values = []
            for field in fields:
                val = user_data.get(field)
                # Обработка булевых полей
                if field in ['is_active', 'is_admin']:
                    # Преобразуем в Python boolean (1/0 для SQLite)
                    values.append(1 if val else 0)
                # --- ДОБАВЛЕНО: Обработка логина и пароля ---
                elif field == 'login':
                     # Логин должен быть строкой
                     values.append(str(val).strip() if val is not None else None)
                elif field == 'password_hash':
                     # password_hash генерируется из new_password
                     new_pass = user_data.get('new_password')
                     if new_pass:
                         # Генерируем хэш с использованием Werkzeug
                         values.append(generate_password_hash(str(new_pass)))
                     else:
                         # Если пароль не задан, вставляем NULL
                         values.append(None)
                # --- ---
                else: # rank, last_name, first_name, middle_name, phone
                    # Для текстовых полей None -> NULL, пустые строки -> NULL
                    processed_val = val if val is not None else None
                    if isinstance(processed_val, str) and processed_val == "":
                         processed_val = None
                    values.append(processed_val)

            # --- Формирование и выполнение SQL-запроса ---
            columns_str = ', '.join(fields)
            placeholders_str = ', '.join(placeholders)
            # Используем RETURNING id для получения ID нового пользователя (в SQLite используем lastrowid)
            sql_query = f"INSERT INTO users ({columns_str}) VALUES ({placeholders_str});"

            logger.debug(f"Выполнение SQL создания пользователя: {sql_query} с параметрами {values}")
            cursor.execute(sql_query, values)
            new_id = cursor.lastrowid
            conn.commit()
            cursor.close()

            if new_id:
                logger.info(f"Новый пользователь успешно создан с ID: {new_id}")
                return new_id
            else:
                logger.error("Не удалось получить ID нового пользователя после вставки.")
                return -1

        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при создании пользователя: {e}")
            if conn:
                conn.rollback()
            return -1
        except Exception as e:
            logger.error(f"Неизвестная ошибка при создании пользователя: {e}")
            if conn:
                conn.rollback()
            return -1

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """
        Обновляет данные существующего пользователя (должностного лица) в БД.
        :param user_id: ID пользователя для обновления.
        :param user_data: Словарь с новыми данными пользователя.
                         Может содержать: rank, last_name, first_name, middle_name, phone, is_active, is_admin, login, new_password.
        :return: True, если успешно, иначе False.
        """
        if not user_data:
            logger.warning("Попытка обновления пользователя с пустыми данными.")
            return False

        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Некорректный ID пользователя для обновления.")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # --- Подготовка полей и значений для UPDATE ---
            # Определяем поля, которые разрешено обновлять
            # --- ОБНОВЛЕНО: Добавлены 'login' и 'password_hash' ---
            allowed_fields = ['rank', 'last_name', 'first_name', 'middle_name', 'phone', 'is_active', 'is_admin', 'login', 'password_hash']
            # --- ---

            # Фильтруем только те поля, которые присутствуют в user_data
            fields_to_update = [field for field in allowed_fields if field in user_data]

            # Особая обработка для password_hash: оно обновляется только если передан new_password
            if 'new_password' in user_data and user_data['new_password']:
                 # Добавляем password_hash в список обновляемых полей, если его еще нет
                 if 'password_hash' not in fields_to_update:
                     fields_to_update.append('password_hash')
            else:
                 # Если new_password пуст или не передан, исключаем password_hash из обновления
                 if 'password_hash' in fields_to_update:
                     fields_to_update.remove('password_hash')

            if not fields_to_update:
                logger.warning("Нет полей для обновления.")
                return False

            # Формируем SET часть запроса и список значений
            set_clauses = []
            values = []
            for field in fields_to_update:
                val = user_data.get(field)
                # Обработка типов данных
                if field in ['is_active', 'is_admin']:
                    # Преобразуем в Python boolean (1/0 для SQLite)
                    values.append(1 if val else 0)
                # --- ДОБАВЛЕНО: Обработка логина и пароля ---
                elif field == 'login':
                     # Логин должен быть строкой
                     values.append(str(val).strip() if val is not None else None)
                elif field == 'password_hash':
                     # password_hash генерируется из new_password
                     new_pass = user_data.get('new_password')
                     if new_pass:
                         # Генерируем хэш с использованием Werkzeug
                         values.append(generate_password_hash(str(new_pass)))
                     else:
                         # Это не должно произойти, так как мы фильтровали выше, но на всякий случай
                         logger.warning("Попытка установить password_hash без new_password.")
                         values.append(None) # Или continue?
                # --- ---
                else: # rank, last_name, first_name, middle_name, phone
                    # Обработка текстовых полей: пустая строка -> None -> NULL
                    processed_val = val if val is not None else None
                    if isinstance(processed_val, str) and processed_val == "":
                         processed_val = None
                    values.append(processed_val)

                set_clauses.append(f"{field} = ?")

            # Добавляем user_id в конец списка значений для WHERE
            values.append(user_id)

            # --- Формирование и выполнение SQL-запроса ---
            set_clause_str = ', '.join(set_clauses)
            sql_query = f"UPDATE users SET {set_clause_str} WHERE id = ?;"

            logger.debug(f"Выполнение SQL обновления пользователя {user_id}: {sql_query} с параметрами {values}")
            cursor.execute(sql_query, values)
            conn.commit()

            rows_affected = cursor.rowcount
            cursor.close()

            if rows_affected > 0:
                logger.info(f"Пользователь с ID {user_id} успешно обновлен. Затронуто строк: {rows_affected}.")
                return True
            else:
                logger.warning(f"Не удалось обновить пользователя с ID {user_id} (запись не найдена или данные не изменились).")
                return False

        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при обновлении пользователя {user_id}: {e}")
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Неизвестная ошибка при обновлении пользователя {user_id}: {e}")
            if conn:
                conn.rollback()
            return False

    def delete_user(self, user_id: int) -> bool:
        """
        Полностью удаляет пользователя (должностное лицо) из БД.
        ЗАЩИТА: Пользователь с логином 'admin' не может быть удален.
        :param user_id: ID пользователя для удаления.
        :return: True, если успешно, иначе False.
        """
        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Некорректный ID пользователя для удаления.")
            return False

        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # --- ПРОВЕРКА: Не пытаемся ли мы удалить admin ---
            cursor.execute("SELECT login, is_admin FROM users WHERE id = ?;", (user_id,))
            user_row = cursor.fetchone()

            if user_row and user_row['login'] == 'admin':
                logger.warning("Попытка удаления пользователя 'admin' заблокирована!")
                cursor.close()
                conn.close()
                return False

            # --- Формирование и выполнение SQL-запроса на удаление ---
            sql_query = f"DELETE FROM users WHERE id = ?;"

            logger.debug(f"Выполнение SQL удаления пользователя {user_id}: {sql_query} с параметром {user_id}")
            cursor.execute(sql_query, (user_id,))
            conn.commit()

            rows_affected = cursor.rowcount
            cursor.close()

            if rows_affected > 0:
                logger.info(f"Пользователь с ID {user_id} успешно удален из БД. Затронуто строк: {rows_affected}.")
                return True
            else:
                logger.warning(f"Не удалось удалить пользователя с ID {user_id} (запись не найдена).")
                return False

        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при удалении пользователя {user_id}: {e}")
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Неизвестная ошибка при удалении пользователя {user_id}: {e}")
            if conn:
                conn.rollback()
            return False

    def get_duty_officer_by_id(self, officer_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает данные должностного лица по его ID.
        :param officer_id: ID пользователя.
        :return: Словарь с данными или None.
        """
        if not isinstance(officer_id, int) or officer_id <= 0:
            logger.warning("Некорректный ID пользователя для получения.")
            return None

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE id = ? AND is_active = 1;", # Можно убрать is_active = 1, если хотите получать всех
                (officer_id,)
            )
            row = cursor.fetchone()
            # Получаем названия колонок
            colnames = [desc[0] for desc in cursor.description]
            cursor.close()

            if row:
                # Создаем словарь из результата
                officer_dict = dict(zip(colnames, row))
                logger.debug(f"Получены данные должностного лица по ID {officer_id}: {officer_dict}")
                return officer_dict
            else:
                logger.warning(f"Должностное лицо с ID {officer_id} не найдено (или неактивно).")
                return None
        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при получении данных должностного лица по ID {officer_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка при получении данных должностного лица по ID {officer_id}: {e}")
            return None

    def set_current_duty_officer(self, officer_id: int) -> bool:
        """
        Устанавливает выбранного дежурного в настройках приложения.
        :param officer_id: ID нового дежурного.
        :return: True, если успешно, иначе False.
        """
        if not isinstance(officer_id, int):
            logger.error("Некорректный тип ID дежурного. Ожидался int.")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # --- Обновляем настройки, устанавливая current_officer_id ---
            # Предполагается, что в таблице post_settings есть запись с id=1
            sql_query = f"UPDATE post_settings SET current_officer_id = ? WHERE id = 1;"

            logger.debug(f"Выполнение SQL установки текущего дежурного: {sql_query} с параметром {officer_id}")
            cursor.execute(sql_query, (officer_id,))
            conn.commit()

            rows_affected = cursor.rowcount
            cursor.close()

            if rows_affected > 0:
                logger.info(f"Текущий дежурный успешно установлен в настройках: ID {officer_id}")
                return True
            else:
                logger.warning(f"Не удалось установить текущего дежурного: запись post_settings (id=1) не найдена или ID {officer_id} не изменился.")
                return False

        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при установке текущего дежурного ID {officer_id}: {e}")
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Неизвестная ошибка при установке текущего дежурного ID {officer_id}: {e}")
            if conn:
                conn.rollback()
            return False

        # --- МЕТОДЫ ДЛЯ РАБОТЫ С ALGORITHMS ---

    def get_all_algorithms(self) -> List[Dict[str, Any]]:
        """
        Получает список всех алгоритмов, отсортированных по sort_order.
        :return: Список словарей с данными алгоритмов.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, category, time_type, description, created_at, updated_at FROM algorithms ORDER BY sort_order ASC;"
            )
            rows = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]
            cursor.close()
            algorithms_list = [dict(zip(colnames, row)) for row in rows]
            logger.debug(f"Получен список {len(algorithms_list)} алгоритмов из БД.")
            return algorithms_list
        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при получении списка алгоритмов: {e}")
            return []
        except Exception as e:
            logger.error(f"Неизвестная ошибка при получении списка алгоритмов: {e}")
            return []

    def create_algorithm(self, algorithm_data: Dict[str, Any]) -> int:
        """
        Создает новый алгоритм в БД.

        :param algorithm_data: Словарь с данными нового алгоритма.
                               Должен содержать ключи: name, category, time_type.
                               Может содержать: description.
        :return: ID нового алгоритма, если успешно, иначе -1.
        """
        if not algorithm_data:
            print("SQLiteDatabaseManager: Попытка создания алгоритма с пустыми данными.")
            return -1

        required_fields = ['name', 'category', 'time_type']
        missing_fields = [field for field in required_fields if not algorithm_data.get(field)]
        if missing_fields:
            print(f"SQLiteDatabaseManager: Отсутствуют обязательные поля для создания алгоритма: {missing_fields}")
            return -1

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # --- Подготовка данных для вставки ---
            # Разрешенные поля для вставки
            allowed_fields = ['name', 'category', 'time_type', 'description']
            # Подготавливаем словарь только с разрешенными полями
            prepared_data = {}
            for key, value in algorithm_data.items():
                if key in allowed_fields:
                    if key in ['name', 'category', 'time_type']:
                        prepared_data[key] = str(value).strip() if value is not None else ""
                    else:  # description
                        prepared_data[key] = str(value).strip() if value is not None else ""

            if not prepared_data:
                print("SQLiteDatabaseManager: Нет данных для вставки.")
                return -1

            # --- Формирование SQL-запроса ---
            columns = list(prepared_data.keys())
            placeholders = ['?'] * len(columns)
            columns_str = ', '.join(columns)
            placeholders_str = ', '.join(placeholders)
            values = list(prepared_data.values())

            sql_query = f"""
                INSERT INTO algorithms ({columns_str})
                VALUES ({placeholders_str});
            """

            print(f"SQLiteDatabaseManager: Выполнение SQL создания алгоритма: {sql_query} с параметрами {values}")
            cursor.execute(sql_query, values)
            new_id = cursor.lastrowid

            if new_id:
                # --- НОВОЕ: Установка уникального sort_order ---
                print(f"SQLiteDatabaseManager: Новый алгоритм создан с ID: {new_id}. Установка уникального sort_order...")
                # Получаем максимальный существующий sort_order
                cursor.execute("SELECT COALESCE(MAX(sort_order), 0) FROM algorithms;")
                max_sort_order_row = cursor.fetchone()
                max_sort_order = max_sort_order_row[0] if max_sort_order_row else 0
                new_sort_order = max_sort_order + 1
                print(f"SQLiteDatabaseManager: Максимальный sort_order: {max_sort_order}. Новый sort_order для ID {new_id}: {new_sort_order}")
                # Обновляем sort_order для нового алгоритма
                cursor.execute("UPDATE algorithms SET sort_order = ? WHERE id = ?;", (new_sort_order, new_id))

                conn.commit()
                print(f"SQLiteDatabaseManager: Алгоритм ID {new_id} успешно создан и sort_order установлен на {new_sort_order}.")
                cursor.close()
                conn.close()
                return new_id
            else:
                print("SQLiteDatabaseManager: Не удалось получить ID нового алгоритма после вставки.")
                cursor.close()
                conn.close()
                return -1
        except sqlite3.Error as e:
            print(f"SQLiteDatabaseManager: Ошибка БД при создании алгоритма: {e}")
            import traceback
            traceback.print_exc()
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return -1
        except Exception as e:
            print(f"SQLiteDatabaseManager: Неизвестная ошибка при создании алгоритма: {e}")
            import traceback
            traceback.print_exc()
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return -1

    def update_algorithm(self, algorithm_id: int, algorithm_data: Dict[str, Any]) -> bool:
        """
        Обновляет данные существующего алгоритма в БД.
        :param algorithm_id: ID алгоритма для обновления.
        :param algorithm_data: Словарь с новыми данными алгоритма.
                               Может содержать: name, category, time_type, description.
        :return: True, если успешно, иначе False.
        """
        if not algorithm_data:
            logger.warning("Попытка обновления алгоритма с пустыми данными.")
            return False

        if not isinstance(algorithm_id, int) or algorithm_id <= 0:
            logger.error("Некорректный ID алгоритма для обновления.")
            return False

        # Проверка допустимых значений, если они переданы
        if 'category' in algorithm_data and algorithm_data['category'] not in ['повседневная деятельность', 'боевая готовность', 'противодействие терроризму', 'кризисные ситуации']:
             logger.error(f"Недопустимая категория: {algorithm_data['category']}")
             return False
        if 'time_type' in algorithm_data and algorithm_data['time_type'] not in ['оперативное', 'астрономическое']:
             logger.error(f"Недопустимый тип времени: {algorithm_data['time_type']}")
             return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            allowed_fields = ['name', 'category', 'time_type', 'description']
            fields_to_update = [field for field in allowed_fields if field in algorithm_data]

            if not fields_to_update:
                logger.warning("Нет полей для обновления алгоритма.")
                return False

            set_clauses = [f"{field} = ?" for field in fields_to_update]
            values = [algorithm_data[field] for field in fields_to_update]
            values.append(algorithm_id)

            set_clause_str = ', '.join(set_clauses)
            sql_query = f"UPDATE algorithms SET {set_clause_str} WHERE id = ?;"

            logger.debug(f"Выполнение SQL обновления алгоритма {algorithm_id}: {sql_query} с параметрами {values}")
            cursor.execute(sql_query, values)
            conn.commit()

            rows_affected = cursor.rowcount
            cursor.close()

            if rows_affected > 0:
                logger.info(f"Алгоритм с ID {algorithm_id} успешно обновлен. Затронуто строк: {rows_affected}.")
                return True
            else:
                logger.warning(f"Не удалось обновить алгоритм с ID {algorithm_id} (запись не найдена или данные не изменились).")
                return False

        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при обновлении алгоритма {algorithm_id}: {e}")
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Неизвестная ошибка при обновлении алгоритма {algorithm_id}: {e}")
            if conn:
                conn.rollback()
            return False

    def delete_algorithm(self, algorithm_id: int) -> bool:
        """
        Удаляет алгоритм и ВСЕ связанные с ним записи
        (actions, algorithm_executions, action_executions) благодаря ON DELETE CASCADE.

        :param algorithm_id: ID алгоритма для удаления.
        :return: True, если успешно, иначе False.
        """
        if not isinstance(algorithm_id, int) or algorithm_id <= 0:
            print(f"SQLiteDatabaseManager: Некорректный ID алгоритма: {algorithm_id}")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            print(f"SQLiteDatabaseManager: Удаление алгоритма ID {algorithm_id} и всех связанных записей (CASCADE)...")

            # Удаляем алгоритм - остальные таблицы обновлены с ON DELETE CASCADE
            query = "DELETE FROM algorithms WHERE id = ?;"
            cursor.execute(query, (algorithm_id,))
            rows_affected = cursor.rowcount

            if rows_affected > 0:
                conn.commit()
                print(f"SQLiteDatabaseManager: Алгоритм ID {algorithm_id} и все связанные записи успешно удалены. Затронуто строк: {rows_affected}.")
                cursor.close()
                conn.close()
                return True
            else:
                print(f"SQLiteDatabaseManager: Алгоритм ID {algorithm_id} не найден для удаления.")
                cursor.close()
                conn.close()
                return False
        except sqlite3.Error as e:
            print(f"SQLiteDatabaseManager: Ошибка БД при удалении алгоритма {algorithm_id}: {e}")
            import traceback
            traceback.print_exc()
            if 'conn' in locals():
                conn.close()
            return False
        except Exception as e:
            print(f"SQLiteDatabaseManager: Неизвестная ошибка при удалении алгоритма {algorithm_id}: {e}")
            import traceback
            traceback.print_exc()
            if 'conn' in locals():
                conn.close()
            return False

    def duplicate_algorithm(self, original_algorithm_id: int) -> int:
        """
        Создает копию существующего алгоритма и всех его действий.

        :param original_algorithm_id: ID оригинального алгоритма.
        :return: ID нового алгоритма, если успешно, иначе -1.
        """
        if not isinstance(original_algorithm_id, int) or original_algorithm_id <= 0:
            print(f"SQLiteDatabaseManager: Некорректный ID оригинального алгоритма: {original_algorithm_id}")
            return -1

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 1. Получаем данные оригинального алгоритма
            cursor.execute("""
                SELECT id, name, category, time_type, description
                FROM algorithms WHERE id = ?
            """, (original_algorithm_id,))
            original_algorithm_row = cursor.fetchone()
            if not original_algorithm_row:
                print(f"SQLiteDatabaseManager: Оригинальный алгоритм с ID {original_algorithm_id} не найден.")
                return -1

            # Преобразуем в словарь
            original_algorithm = {
                'id': original_algorithm_row[0],
                'name': original_algorithm_row[1],
                'category': original_algorithm_row[2],
                'time_type': original_algorithm_row[3],
                'description': original_algorithm_row[4]
            }

            print(f"SQLiteDatabaseManager: Найден оригинальный алгоритм ID {original_algorithm_id}: {original_algorithm['name']}")

            # 2. Формируем данные для нового алгоритма (с пометкой "копия")
            original_name = original_algorithm.get('name', 'Алгоритм')
            new_name = f"{original_name} (копия)"
            new_algorithm_data = {
                'name': new_name,
                'category': original_algorithm['category'],
                'time_type': original_algorithm['time_type'],
                'description': original_algorithm.get('description', '')
            }

            # 3. Создаем новый алгоритм в БД
            new_algorithm_id = self.create_algorithm(new_algorithm_data)
            if isinstance(new_algorithm_id, int) and new_algorithm_id > 0:
                print(f"SQLiteDatabaseManager: Алгоритм ID {original_algorithm_id} успешно дублирован. Новый ID: {new_algorithm_id}")

                # 4. Дублируем действия оригинального алгоритма
                cursor.execute("""
                    SELECT id, description, technical_text, start_offset, end_offset, contact_phones, report_materials
                    FROM actions WHERE algorithm_id = ? ORDER BY start_offset
                """, (original_algorithm_id,))
                original_actions_rows = cursor.fetchall()

                # Преобразуем в список словарей
                original_actions = []
                for action_row in original_actions_rows:
                    action_dict = {
                        'id': action_row[0],
                        'description': action_row[1],
                        'technical_text': action_row[2],
                        'start_offset': action_row[3],
                        'end_offset': action_row[4],
                        'contact_phones': action_row[5],
                        'report_materials': action_row[6]
                    }
                    original_actions.append(action_dict)

                actions_duplicated_count = 0
                for original_action in original_actions:
                    print(f"SQLiteDatabaseManager: Дублирование действия ID {original_action['id']}...")

                    # Формируем данные для нового действия
                    new_action_data = {
                        'algorithm_id': new_algorithm_id, # <-- ВАЖНО: Новый algorithm_id
                        'description': original_action.get('description', ''),
                        'technical_text': original_action.get('technical_text', ''),
                        'start_offset': original_action.get('start_offset'),
                        'end_offset': original_action.get('end_offset'),
                        'contact_phones': original_action.get('contact_phones'),
                        'report_materials': original_action.get('report_materials')
                    }

                    # Создаем копию действия в БД
                    new_action_id = self.create_action(new_action_data)
                    if isinstance(new_action_id, int) and new_action_id > 0:
                        print(f"SQLiteDatabaseManager: Действие ID {original_action['id']} дублировано как ID {new_action_id} для нового алгоритма {new_algorithm_id}.")
                        actions_duplicated_count += 1
                    else:
                        print(f"SQLiteDatabaseManager: Не удалось дублировать действие ID {original_action['id']} для алгоритма {new_algorithm_id}.")

                print(f"SQLiteDatabaseManager: Для нового алгоритма ID {new_algorithm_id} дублировано {actions_duplicated_count} из {len(original_actions)} действий.")
                cursor.close()
                conn.close()
                return new_algorithm_id
            else:
                print(f"SQLiteDatabaseManager: Ошибка при создании нового алгоритма (копии). Результат create_algorithm: {new_algorithm_id}")
                cursor.close()
                conn.close()
                return -1
        except sqlite3.Error as e:
            print(f"SQLiteDatabaseManager: Ошибка БД при дублировании алгоритма {original_algorithm_id}: {e}")
            import traceback
            traceback.print_exc()
            if 'conn' in locals():
                conn.close()
            return -1
        except Exception as e:
            print(f"SQLiteDatabaseManager: Неизвестная ошибка при дублировании алгоритма {original_algorithm_id}: {e}")
            import traceback
            traceback.print_exc()
            if 'conn' in locals():
                conn.close()
            return -1

    # --- МЕТОДЫ ДЛЯ РАБОТЫ С ACTIONS ---

    def get_actions_by_algorithm_id(self, algorithm_id: int) -> List[Dict[str, Any]]:
        """
        Получает список всех действий для заданного алгоритма, отсортированных по времени начала (start_offset).
        Поддерживает сортировку как по числовым значениям (секунды), так и по формату времени (HH:MM:SS).
        :param algorithm_id: ID алгоритма.
        :return: Список словарей с данными действий.
        """
        if not isinstance(algorithm_id, int) or algorithm_id <= 0:
            logger.warning("Некорректный ID алгоритма для получения действий.")
            return []

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, algorithm_id, description, technical_text, start_offset, end_offset, contact_phones, report_materials, created_at, updated_at "
                "FROM actions "
                "WHERE algorithm_id = ? "
                "ORDER BY "
                "CASE "
                "WHEN start_offset LIKE '% %:__:__' THEN "
                "  CASE "
                "    WHEN start_offset LIKE '____-__-__T__:__:__%' THEN "
                "      substr(start_offset, 1, 4) * 31536000 + substr(start_offset, 6, 2) * 2678400 + substr(start_offset, 9, 2) * 86400 + substr(start_offset, 12, 2) * 3600 + substr(start_offset, 15, 2) * 60 + substr(start_offset, 18, 2) "
                "    ELSE "
                "      CAST(substr(start_offset, 1, instr(start_offset, ' ') - 1) AS INTEGER) * 86400 + "
                "      substr(substr(start_offset, instr(start_offset, ' ') + 1), 1, 2) * 3600 + "
                "      substr(substr(start_offset, instr(start_offset, ' ') + 1), 4, 2) * 60 + "
                "      substr(substr(start_offset, instr(start_offset, ' ') + 1), 7, 2) "
                "  END "
                "WHEN start_offset LIKE '__:__:__' THEN substr(start_offset, 1, 2) * 3600 + substr(start_offset, 4, 2) * 60 + substr(start_offset, 7, 2) "
                "ELSE CAST(COALESCE(start_offset, '0') AS INTEGER) "
                "END ASC, "
                "id ASC;",
                (algorithm_id,)
            )
            rows = cursor.fetchall()
            # Получаем названия колонок
            colnames = [desc[0] for desc in cursor.description]
            cursor.close()

            # Преобразование timedelta в строки (для совместимости с PostgreSQL версией)
            actions_list = []
            for row in rows:
                # Создаем словарь из строки результата
                action_dict = dict(zip(colnames, row))

                # Для SQLite start_offset и end_offset - это строки, преобразуем их при необходимости
                for time_field in ['start_offset', 'end_offset']:
                    if action_dict[time_field] is None:
                         action_dict[time_field] = "" # или None
                         logger.debug(f"{time_field} был None, преобразован в пустую строку")
                    else:
                        # оставляем как есть или преобразуем в строку принудительно
                        action_dict[time_field] = str(action_dict[time_field])

                actions_list.append(action_dict)

            logger.debug(f"Получен список {len(actions_list)} действий для алгоритма ID {algorithm_id}.")
            return actions_list
        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при получении списка действий для алгоритма {algorithm_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Неизвестная ошибка при получении списка действий для алгоритма {algorithm_id}: {e}")
            import traceback
            traceback.print_exc() # Для более детального лога ошибок
            return []

    def get_action_by_id(self, action_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает данные действия по его ID.
        :param action_id: ID действия.
        :return: Словарь с данными действия или None.
        """
        if not isinstance(action_id, int) or action_id <= 0:
            logger.warning("Некорректный ID действия для получения.")
            return None

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, algorithm_id, description, technical_text, start_offset, end_offset, contact_phones, report_materials FROM actions WHERE id = ?;",
                (action_id,)
            )
            row = cursor.fetchone()
            colnames = [desc[0] for desc in cursor.description]
            cursor.close()

            if row:
                action_dict = dict(zip(colnames, row))
                logger.debug(f"Получены данные действия по ID {action_id}: {action_dict}")
                return action_dict
            else:
                logger.warning(f"Действие с ID {action_id} не найдено.")
                return None
        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при получении данных действия по ID {action_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка при получении данных действия по ID {action_id}: {e}")
            return None

    def _convert_time_string_to_interval(self, time_str: str) -> str:
        """
        Преобразует строку времени различных форматов в единый формат для SQLite.
        Поддерживаемые форматы:
        - 'dd:hh:mm:ss' (например, '1:02:30:45')
        - 'hh:mm:ss' (например, '02:30:45')
        - 'dd hh:mm:ss' (например, '1 02:30:45')
        - 'dd:hh mm:ss' (например, '0:0 02:00:00')
        :param time_str: Строка времени.
        :return: Форматированная строка для SQLite или исходная строка, если формат не распознан.
        """
        if not time_str:
            return '00:00:00'

        import re

        # Проверяем формат dd:hh mm:ss (например, '0:0 02:00:00')
        # Это означает 'days:hours minutes:seconds:seconds' - но это не логично
        # На самом деле формат '0:0 02:00:00' означает 'days:hours hours:minutes:seconds'
        # где '0:0' это дни:часы, а '02:00:00' это часы:минуты:секунды
        # Но это тоже не логично. Правильнее интерпретировать как 'days:hours space hours:minutes:seconds'
        # Формат '0:0 02:00:00' скорее всего означает 'days:hours offset space hours:minutes:seconds'
        # Но судя по всему, это формат 'days:hours space hours:minutes:seconds' где первые '0:0' - это дни:часы, а вторая часть '02:00:00' - это часы:минуты:секунды
        # Правильная интерпретация: '0:0 02:00:00' -> 0 дней, 0 часов, 02:00:00 (часы:минуты:секунды)
        # Но это тоже не логично. Скорее всего это 'days:hours space hours:minutes:seconds' -> '0:0 02:00:00' -> 0 дней, 0 часов, 02:00:00
        # Нужно понять, как QML формирует этот формат
        # Судя по описанию, формат '0:0 02:00:00' может означать 'days:hours space hours:minutes:seconds'
        # Но это неоднозначно. Попробуем интерпретировать как 'days:hours offset space hours:minutes:seconds'
        # где '0:0' - это дни:часы, а '02:00:00' - это смещение в формате hours:minutes:seconds
        # Но это тоже неоднозначно. Попробуем другой подход:
        # '0:0 02:00:00' -> 'days:hours space hours:minutes:seconds' -> 'days=0, hours=0, time=02:00:00'
        # Это значит, что это 0 дней, 0 часов, и смещение 02:00:00 (2 часа 0 минут 0 секунд)
        # Но это тоже не логично. Правильнее интерпретировать как '0 days, 0 hours, 02:00:00' -> '0 02:00:00'
        # Попробуем так: '0:0 02:00:00' -> '0 days, 0 hours offset, 02:00:00 time' -> '0 02:00:00'
        # Это означает 0 дней и 02:00:00 времени (0 часов, 2 минуты, 0 секунд)? Нет, это 2 часа, 0 минут, 0 секунд
        # Правильная интерпретация: '0:0 02:00:00' -> '0 days, 0 hours' + '02:00:00' -> '0 02:00:00'
        # где '0:0' означает 0 дней и 0 часов, а '02:00:00' - это смещение в формате HH:MM:SS
        # Но это все равно неоднозначно. Давайте посмотрим на примеры:
        # '0:0 02:00:00' -> '0 days, 0 hours offset, 02:00:00 time' -> '0 02:00:00'
        # '0:0 48:00:00' -> '0 days, 0 hours offset, 48:00:00 time' -> '0 48:00:00'
        # Это означает, что формат 'days:hours offset HH:MM:SS' -> 'days HH:MM:SS'
        # где 'days:hours' - это дни и часы, а 'HH:MM:SS' - это смещение
        # Но это не логично. Скорее всего, формат '0:0 02:00:00' означает 'days:hours space HH:MM:SS'
        # где '0:0' - это дни:часы, а '02:00:00' - это HH:MM:SS
        # Но это тоже не логично. Правильнее интерпретировать как '0 days, 0 hours, 02:00:00 offset'
        # Давайте просто разберем строку: '0:0 02:00:00' -> ['0:0', '02:00:00'] -> разделим по пробелу
        # part1 = '0:0', part2 = '02:00:00'
        # part1: '0:0' -> days=0, hours=0
        # part2: '02:00:00' -> hours=02, minutes=00, seconds=00
        # Итого: 0 дней, 0 часов, 02:00:00 -> результат '0 02:00:00'
        # Это логично!

        match_parts = re.match(r'(\d+):(\d+)\s+(\d{2}):(\d{2}):(\d{2})', time_str)
        if match_parts:
            days, hours, h, m, s = match_parts.groups()
            days_int = int(days)
            hours_int = int(hours)  # Это часы из '0:0'
            h_int = int(h)  # Это часы из '02:00:00'
            m_int = int(m)  # Это минуты
            s_int = int(s)  # Это секунды

            # Теперь нужно понять, что из этого использовать
            # Если '0:0 02:00:00' означает 0 дней, 0 часов, и смещение 02:00:00
            # То результат должен быть '0 02:00:00' (0 дней, 02:00:00)
            # Но в формате SQLite это будет '0 02:00:00'
            # Где 0 - это дни, а 02:00:00 - это время
            # Но это не совсем корректно, потому что 02:00:00 - это 2 часа, а не дни
            # Правильнее будет: если '0:0 02:00:00', то это 0 дней, и смещение 02:00:00
            # Результат: '0 02:00:00' (0 дней и 02:00:00)

            # Возвращаем в формате 'dd hh:mm:ss'
            return f"{days_int} {h_int:02d}:{m_int:02d}:{s_int:02d}"

        # Проверяем формат dd hh:mm:ss (например, '1 02:30:45')
        match_dd_space_hh_mm_ss = re.fullmatch(r'(\d+)\s+(\d{2}):(\d{2}):(\d{2})', time_str)
        if match_dd_space_hh_mm_ss:
            days, hours, minutes, seconds = match_dd_space_hh_mm_ss.groups()
            days_int = int(days)
            hours_int = int(hours)
            minutes_int = int(minutes)
            seconds_int = int(seconds)

            # Возвращаем в формате 'dd hh:mm:ss'
            return f"{days_int} {hours_int:02d}:{minutes_int:02d}:{seconds_int:02d}"

        # Проверяем формат dd:hh:mm:ss (например, '1:02:30:45')
        match_dd_hh_mm_ss = re.fullmatch(r'(\d+):(\d{1,2}):(\d{1,2}):(\d{1,2})', time_str)
        if match_dd_hh_mm_ss:
            days, hours, minutes, seconds = match_dd_hh_mm_ss.groups()
            days_int = int(days)
            hours_int = int(hours)
            minutes_int = int(minutes)
            seconds_int = int(seconds)

            # Возвращаем в формате 'dd hh:mm:ss'
            return f"{days_int} {hours_int:02d}:{minutes_int:02d}:{seconds_int:02d}"

        # Проверяем формат hh:mm:ss (например, '02:30:45')
        match_hh_mm_ss = re.fullmatch(r'(\d{1,2}):(\d{1,2}):(\d{1,2})', time_str)
        if match_hh_mm_ss:
            hours, minutes, seconds = match_hh_mm_ss.groups()
            # Возвращаем в формате HH:MM:SS
            return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

        # Если формат не распознан, возвращаем исходную строку
        logger.warning(f"Нер��спознанный формат времени '{time_str}'. Передаю как есть.")
        return time_str

    def create_action(self, action_data: Dict[str, Any]) -> int:
        """
        Создает новое действие в БД.
        :param action_data: Словарь с данными нового действия.
                             Должен содержать ключи: algorithm_id, description.
                             Может содержать: start_offset, end_offset, contact_phones, report_materials.
        :return: ID нового действия, если успешно, иначе -1.
        """
        # ... (проверки на существование action_data и обязательных полей) ...
        if not action_data:
            logger.warning("П��������пытка создания действия с пустыми данными.")
            return -1

        required_fields = ['algorithm_id', 'description']
        missing_fields = [field for field in required_fields if not action_data.get(field)]
        if missing_fields:
            logger.error(f"Отсутствуют обязательные поля для создания действия: {missing_fields}")
            return -1
        # ... (остальные проверки) ...

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # --- ИЗМЕНЕНО: Подготовка полей и значений с преобразованием времени ---
            # Определяем поля, которые будут встав��ены
            # Поддержка snapshot_technical_text из QML
            if 'snapshot_technical_text' in action_data and 'technical_text' not in action_data:
                action_data['technical_text'] = action_data.pop('snapshot_technical_text')

            allowed_fields = ['algorithm_id', 'description', 'technical_text', 'start_offset', 'end_offset', 'contact_phones', 'report_materials']
            fields = [field for field in allowed_fields if field in action_data]

            # Создаем спи��ок ? плейсхолдеров
            placeholders = ['?'] * len(fields)

            # Формируем значения для вставки, обрабатывая типы данных
            values = []
            for field in fields:
                val = action_data.get(field)
                # --- ДОБАВЛЕНО: Преобразование времени ---
                if field in ['start_offset', 'end_offset']:
                    # Преобразуем строку времени в формат, подходящий для SQLite
                    formatted_interval = self._convert_time_string_to_interval(str(val) if val is not None else "")
                    values.append(formatted_interval) # Передаем преобразованную строку
                    logger.debug(f"Преобразовано {field} из '{val}' в '{formatted_interval}'")
                # --- ---
                else: # algorithm_id, description, contact_phones, report_materials
                    # Для текстовых полей None -> NULL, пустые строки -> NULL
                    processed_val = val if val is not None else None
                    if isinstance(processed_val, str) and processed_val == "":
                         processed_val = None
                    values.append(processed_val)

            if not fields:
                logger.error("Нет корректных полей для вставки.")
                return -1
            # --- ---

            # ... (формирование и выполнение SQL-запроса) ...

            columns_str = ', '.join(fields)
            placeholders_str = ', '.join(placeholders)
            # Используем lastrowid для получения ID нового действия
            sql_query = f"INSERT INTO actions ({columns_str}) VALUES ({placeholders_str});"

            logger.debug(f"Выполнение SQL создания действия: {sql_query}")
            logger.debug(f"Значения для вставки: {values}")
            cursor.execute(sql_query, values)
            new_id = cursor.lastrowid
            conn.commit()
            cursor.close()

            if new_id:
                # Проверка: считываем обратно technical_text
                if 'technical_text' in action_data:
                    conn2 = self._get_connection()
                    c2 = conn2.cursor()
                    c2.execute("SELECT technical_text FROM actions WHERE id = ?", (new_id,))
                    r = c2.fetchone()
                    c2.close()
                    logger.info(f"Проверка: после вставки technical_text для ID {new_id} = {repr(r[0] if r else 'N/A')}")

            if new_id:
                logger.info(f"Новое действие успешно создано с ID: {new_id}")
                return new_id
            else:
                logger.error("Не удалось получить ID нового действия после вставки.")
                return -1

        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при создании действия: {e}")
            if conn:
                conn.rollback()
            return -1
        except Exception as e:
            logger.error(f"Неизвестная ошибка при создании действия: {e}")
            if conn:
                conn.rollback()
            return -1

    def update_action(self, action_id: int, action_data: Dict[str, Any]) -> bool:
        """
        Обновляет данные существующего действия в БД.
        :param action_id: ID действия для обновления.
        :param action_data: Словарь с новыми данными действия.
                            Может содержать: algorithm_id, description, start_offset, end_offset,
                                           contact_phones, report_materials.
        :return: True, если успешно, иначе False.
        """
        # ... (проверки на существование action_data и action_id) ...
        if not action_data:
            logger.warning("Попытка обновления действия с пустыми данными.")
            return False

        if not isinstance(action_id, int) or action_id <= 0:
            logger.error("Некорректный ID действия для обновления.")
            return False
        # ... (остальные проверки) ...

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # --- ИЗМЕНЕНО: Подготовка данных с преобразованием времени ---
            # Фильтруем и готовим только разрешенные поля
            allowed_fields = ['algorithm_id', 'description', 'technical_text', 'start_offset', 'end_offset', 'contact_phones', 'report_materials']
            fields_to_update = [field for field in allowed_fields if field in action_data]

            print(f"DEBUG update_action: action_data keys = {list(action_data.keys())}")
            print(f"DEBUG update_action: allowed_fields = {allowed_fields}")
            print(f"DEBUG update_action: fields_to_update = {fields_to_update}")

            if not fields_to_update:
                logger.warning("Нет полей для обновления действия.")
                return False

            set_clauses = []
            values = []
            for field in fields_to_update:
                val = action_data.get(field)
                # --- ДОБАВЛЕНО: Преобразование времени ---
                if field in ['start_offset', 'end_offset']:
                    # Преобразуем строку времени в формат, подходящий для SQLite
                    formatted_interval = self._convert_time_string_to_interval(str(val) if val is not None else "")
                    values.append(formatted_interval) # Передаем преобразованную строку
                    logger.debug(f"Преобразовано {field} из '{val}' в '{formatted_interval}'")
                # --- ---
                else: # algorithm_id, description, contact_phones, report_materials
                    # Обработка текстовых полей: пустая строка -> None -> NULL
                    processed_val = val if val is not None else None
                    if isinstance(processed_val, str) and processed_val == "":
                         processed_val = None
                    values.append(processed_val)

                set_clauses.append(f"{field} = ?")

            # Добавляем action_id в конец списка значений для WHERE
            values.append(action_id)
            # --- ---

            # ... (формирование и выполнение SQL-запроса) ...

            set_clause_str = ', '.join(set_clauses)
            sql_query = f"UPDATE actions SET {set_clause_str} WHERE id = ?;"

            logger.debug(f"Выполнение SQL обновления действия {action_id}: {sql_query} с параметрами {values}")
            print(f"DEBUG UPDATE action {action_id}: SQL = {sql_query}")
            print(f"DEBUG UPDATE action {action_id}: VALUES = {values}")
            cursor.execute(sql_query, values)
            conn.commit()

            rows_affected = cursor.rowcount
            cursor.close()

            if rows_affected > 0:
                logger.info(f"Действие с ID {action_id} успешно обновлено. Затронуто строк: {rows_affected}.")
                return True
            else:
                logger.warning(f"Не удалось обновить действие с ID {action_id} (запись не найдена или данные не изменились).")
                return False

        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при обновлении действия {action_id}: {e}")
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Неизвестная ошибка при обновлении действия {action_id}: {e}")
            if conn:
                conn.rollback()
            return False

    def delete_action(self, action_id: int) -> bool:
        """
        Удаляет действие из БД.
        :param action_id: ID действия для удаления.
        :return: True, если успешно, иначе False.
        """
        if not isinstance(action_id, int) or action_id <= 0:
            logger.error("Некорректный ID действия для удаления.")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            sql_query = f"DELETE FROM actions WHERE id = ?;"

            logger.debug(f"Выполнение SQL удаления действия {action_id}: {sql_query} с параметром {action_id}")
            cursor.execute(sql_query, (action_id,))
            conn.commit()

            rows_affected = cursor.rowcount
            cursor.close()

            if rows_affected > 0:
                logger.info(f"Действие с ID {action_id} успешно удалено из БД. Затронуто строк: {rows_affected}.")
                return True
            else:
                logger.warning(f"Не удалось удалить действие с ID {action_id} (запись не найдена).")
                return False

        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при удалении действия {action_id}: {e}")
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Неизвестная ошибка при удалении действия {action_id}: {e}")
            if conn:
                conn.rollback()
            return False

    def duplicate_action(self, original_action_id: int, new_algorithm_id: int = None) -> int:
        """
        Создает копию существующего действия.
        :param original_action_id: ID оригинального действия.
        :param new_algorithm_id: ID алгоритма для новой копии (если None, используется ID оригинального алгоритма).
        :return: ID нового действия, если успешно, иначе -1.
        """
        original_action = self.get_action_by_id(original_action_id)
        if not original_action:
            logger.error(f"Не удалось найти оригинальное действие с ID {original_action_id} для дублирования.")
            return -1

        new_action_data = {
            'algorithm_id': new_algorithm_id if new_algorithm_id is not None else original_action['algorithm_id'],
            'description': original_action['description'],
            'technical_text': original_action.get('technical_text', ''),
            'start_offset': original_action.get('start_offset'),
            'end_offset': original_action.get('end_offset'),
            'contact_phones': original_action.get('contact_phones'),
            'report_materials': original_action.get('report_materials')
        }

        new_action_id = self.create_action(new_action_data)

        if new_action_id != -1:
            logger.info(f"Действие ID {original_action_id} успешно дублировано. Новый ID: {new_action_id}")
        else:
            logger.error(f"Ошибка при дублировании действия ID {original_action_id}.")

        return new_action_id
        
    def move_algorithm_up(self, algorithm_id: int) -> bool:
        """
        Перемещает алгоритм вверх в списке (уменьшает sort_order на 1).
        :param algorithm_id: ID алгоритма для перемещения.
        :return: True, если успешно, иначе False.
        """
        if not isinstance(algorithm_id, int) or algorithm_id <= 0:
            logger.error("Некорректный ID алгоритма для перемещения вверх.")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 1. Получаем текущий sort_order алгоритма
            cursor.execute(
                "SELECT sort_order FROM algorithms WHERE id = ?;",
                (algorithm_id,)
            )
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Алгоритм ID {algorithm_id} не найден для перемещения вверх.")
                return False

            current_sort_order = row[0]
            logger.debug(f"Текущий sort_order алгоритма {algorithm_id}: {current_sort_order}")

            # 2. Найдем алгоритм с sort_order на 1 меньше
            cursor.execute(
                "SELECT id, sort_order FROM algorithms WHERE sort_order = ?;",
                (current_sort_order - 1,)
            )
            swap_candidate = cursor.fetchone()

            if swap_candidate:
                # 3a. Если такой алгоритм есть, меняем их sort_order местами
                swap_algorithm_id, swap_sort_order = swap_candidate
                logger.debug(f"Найден алгоритм {swap_algorithm_id} с sort_order={swap_sort_order} для обмена.")

                # Начинаем транзакцию
                cursor.execute("BEGIN;")

                # Обновляем sort_order у текущего алгоритма
                cursor.execute(
                    "UPDATE algorithms SET sort_order = ? WHERE id = ?;",
                    (swap_sort_order, algorithm_id)
                )
                # Обновляем sort_order у алгоритма, с которым меняемся
                cursor.execute(
                    "UPDATE algorithms SET sort_order = ? WHERE id = ?;",
                    (current_sort_order, swap_algorithm_id)
                )

                conn.commit()
                cursor.close()
                logger.info(f"Алгоритм ID {algorithm_id} успешно перемещен вверх (sort_order: {current_sort_order} -> {swap_sort_order}). Алгоритм ID {swap_algorithm_id} перемещен вниз (sort_order: {swap_sort_order} -> {current_sort_order}).")
                return True
            else:
                # 3b. Если алгоритма с sort_order-1 нет, просто уменьшаем sort_order текущего
                logger.debug(f"Алгоритм с sort_order={current_sort_order - 1} не найден. Уменьшаем sort_order текущего алгоритма.")
                cursor.execute(
                    "UPDATE algorithms SET sort_order = sort_order - 1 WHERE id = ?;",
                    (algorithm_id,)
                )
                conn.commit()
                cursor.close()
                logger.info(f"Алгоритм ID {algorithm_id} успешно перемещен вверх (sort_order уменьшен на 1).")
                return True

        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при перемещении алгоритма {algorithm_id} вверх: {e}")
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Неизвестная ошибка при перемещении алгоритма {algorithm_id} вверх: {e}")
            if conn:
                conn.rollback()
            return False

    def move_algorithm_down(self, algorithm_id: int) -> bool:
        """
        Перемещает алгоритм вниз в списке (увеличивает sort_order на 1).
        :param algorithm_id: ID алгоритма для перемещения.
        :return: True, если успешно, иначе False.
        """
        if not isinstance(algorithm_id, int) or algorithm_id <= 0:
            logger.error("Некорректный ID алгоритма для перемещения вниз.")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 1. Получаем текущий sort_order алгоритма
            cursor.execute(
                "SELECT sort_order FROM algorithms WHERE id = ?;",
                (algorithm_id,)
            )
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Алгоритм ID {algorithm_id} не найден для перемещения вниз.")
                return False

            current_sort_order = row[0]
            logger.debug(f"Текущий sort_order алгоритма {algorithm_id}: {current_sort_order}")

            # 2. Найдем алгоритм с sort_order на 1 больше
            cursor.execute(
                "SELECT id, sort_order FROM algorithms WHERE sort_order = ?;",
                (current_sort_order + 1,)
            )
            swap_candidate = cursor.fetchone()

            if swap_candidate:
                # 3a. Если такой алгоритм есть, меняем их sort_order местами
                swap_algorithm_id, swap_sort_order = swap_candidate
                logger.debug(f"Найден алгоритм {swap_algorithm_id} с sort_order={swap_sort_order} для обмена.")

                # Начинаем транзакцию
                cursor.execute("BEGIN;")

                # Обновляем sort_order у текущего алгоритма
                cursor.execute(
                    "UPDATE algorithms SET sort_order = ? WHERE id = ?;",
                    (swap_sort_order, algorithm_id)
                )
                # Обновляем sort_order у алгоритма, с которым меняемся
                cursor.execute(
                    "UPDATE algorithms SET sort_order = ? WHERE id = ?;",
                    (current_sort_order, swap_algorithm_id)
                )

                conn.commit()
                cursor.close()
                logger.info(f"Алгоритм ID {algorithm_id} успешно перемещен вниз (sort_order: {current_sort_order} -> {swap_sort_order}). Алгоритм ID {swap_algorithm_id} перемещен вверх (sort_order: {swap_sort_order} -> {current_sort_order}).")
                return True
            else:
                # 3b. Если алгоритма с sort_order+1 нет, просто увеличиваем sort_order текущего
                logger.debug(f"Алгоритм с sort_order={current_sort_order + 1} не найден. Увеличиваем sort_order текущего алгоритма.")
                cursor.execute(
                    "UPDATE algorithms SET sort_order = sort_order + 1 WHERE id = ?;",
                    (algorithm_id,)
                )
                conn.commit()
                cursor.close()
                logger.info(f"Алгоритм ID {algorithm_id} успешно перемещен вниз (sort_order увеличен на 1).")
                return True

        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при перемещении алгоритма {algorithm_id} вниз: {e}")
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.error(f"Неизвестная ошибка при перемещении алгоритма {algorithm_id} вниз: {e}")
            if conn:
                conn.rollback()
            return False

    def get_executions_by_date(self, date_string: str) -> List[Dict[str, Any]]:
        """
        Получает список ВСЕХ выполнений алгоритмов (algorithm_executions) за заданную дату.
        Включает активные, завершенные и отмененные.
        :param date_string: Дата в формате 'YYYY-MM-DD'.
        :return: Список словарей с данными execution'ов.
        """
        if not date_string:
            logger.warning("Некорректная дата для получения execution'ов.")
            return []

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # SQL-запрос БЕЗ фильтрации по status
            # Используем substr для извлечения даты из timestamp
            sql_query = """
            SELECT
                ae.id,
                ae.algorithm_id,
                a.name AS algorithm_name,
                ae.started_at,
                substr(ae.started_at, 1, 19) AS started_at_display,
                ae.completed_at,
                CASE
                    WHEN ae.completed_at IS NOT NULL THEN substr(ae.completed_at, 1, 19)
                    ELSE NULL
                END AS completed_at_display,
                ae.status,
                ae.created_by_user_id,
                COALESCE(u.last_name || ' ' || u.first_name || ' ' || u.middle_name, 'Неизвестен') AS created_by_user_display_name
            FROM algorithm_executions ae
            JOIN algorithms a ON ae.algorithm_id = a.id
            LEFT JOIN users u ON ae.created_by_user_id = u.id
            WHERE substr(ae.started_at, 1, 10) = ?
            ORDER BY ae.started_at DESC;
            """

            logger.debug(f"Выполнение SQL получения ВСЕХ execution'ов за дату '{date_string}': {sql_query} с параметром {date_string}")
            cursor.execute(sql_query, (date_string,))
            rows = cursor.fetchall()
            # Получаем названия колонок
            colnames = [desc[0] for desc in cursor.description]
            cursor.close()

            # Преобразуем список кортежей в список словарей
            executions_list = [dict(zip(colnames, row)) for row in rows]
            logger.info(f"Получен список {len(executions_list)} ВСЕХ execution'ов за дату '{date_string}' из БД.")
            return executions_list

        except sqlite3.Error as e:
            logger.error(f"Ошибка БД при получении ВСЕХ execution'ов за дату '{date_string}': {e}")
            return []
        except Exception as e:
            logger.error(f"Неизвестная ошибка при получении ВСЕХ execution'ов за дату '{date_string}': {e}")
            import traceback
            traceback.print_exc()
            return []

    # --- МЕТОДЫ ДЛЯ РАБОТЫ С ЗАПУЩЕННЫМИ АЛГОРИТМАМИ (EXECUTIONS) ---

    def get_active_executions_by_category(self, category: str) -> list:
        """
        Получает список активных (status = 'active') запущенных алгоритмов (executions)
        для заданной категории (snapshot_category).

        :param category: Категория алгоритмов (например, "повседневная деятельность").
        :return: Список словарей с данными executions.
        """
        try:
            conn = self._get_connection()
            with conn:
                cursor = conn.cursor()
                # Запрос к таблице algorithm_executions, фильтруем по snapshot_category и status
                query = """
                    SELECT
                        id,
                        algorithm_id, -- Ссылка на оригинальный алгоритм
                        snapshot_name AS algorithm_name, -- Имя из snapshot'а
                        snapshot_category AS category, -- Категория из snapshot'а
                        started_at,
                        substr(started_at, 1, 19) AS started_at_display, -- <-- НОВОЕ: Отформатированное значение
                        completed_at,
                        status,
                        created_by_user_id, -- ID пользователя на момент запуска
                        created_by_user_display_name -- Отображаемое имя на момент запуска
                    FROM algorithm_executions
                    WHERE snapshot_category = ? AND status = 'active'
                    ORDER BY started_at DESC; -- Сортируем по времени запуска, например
                """
                cursor.execute(query, (category,))
                rows = cursor.fetchall()

                # Преобразуем результаты в список словарей
                executions = [dict(row) for row in rows]
                print(f"SQLiteDatabaseManager: Найдено {len(executions)} активных executions для категории '{category}'.")
                return executions
        except sqlite3.Error as e:
            print(f"SQLiteDatabaseManager: Ошибка при получении активных executions для категории '{category}': {e}")
            import traceback
            traceback.print_exc()
            return []
        except Exception as e:
            print(f"SQLiteDatabaseManager: Неизвестная ошибка при получении активных executions: {e}")
            import traceback
            traceback.print_exc()
            return []

    def stop_algorithm(self, execution_id: int, local_completed_at_dt: datetime.datetime) -> bool:
        """
        Останавливает (меняет статус на 'completed') запущенный алгоритм (execution) по его ID.
        Также устанавливает статус 'skipped' для всех незавершённых action_executions.
        Устанавливает completed_at в переданное местное время.

        :param execution_id: ID execution'а для остановки.
        :param local_completed_at_dt: Объект datetime.datetime, представляющий местное время завершения.
        :return: True, если успешно, иначе False.
        """
        if not isinstance(execution_id, int) or execution_id <= 0:
            print(f"SQLiteDatabaseManager: Некорректный ID execution: {execution_id}")
            return False

        # --- ДОБАВЛЕНО: Проверка типа local_completed_at_dt ---
        if not isinstance(local_completed_at_dt, datetime.datetime):
             print(f"SQLiteDatabaseManager: Ошибка - local_completed_at_dt должен быть datetime.datetime, а не {type(local_completed_at_dt)}.")
             return False
        # ---

        try:
            conn = self._get_connection()
            with conn:
                cursor = conn.cursor()
                
                # --- ИЗМЕНЕНО: Используем переданное local_completed_at_dt ---
                # 1. Обновляем статус и время завершения algorithm_execution
                query_algorithm = """
                    UPDATE algorithm_executions
                    SET status = 'completed', completed_at = ?, updated_at = datetime('now', 'localtime')
                    WHERE id = ? AND status = 'active'; -- Обновляем только если статус был 'active'
                """
                # Преобразуем datetime в строку для SQLite
                completed_at_str = local_completed_at_dt.strftime('%Y-%m-%d %H:%M:%S')
                # Передаём completed_at_str как параметр в запрос
                cursor.execute(query_algorithm, (completed_at_str, execution_id))
                rows_affected_algorithm = cursor.rowcount

                if rows_affected_algorithm > 0:
                    print(f"SQLiteDatabaseManager: Execution ID {execution_id} успешно остановлен. Время завершения: {completed_at_str}")

                    # --- НОВОЕ: Обновляем статусы action_executions ---
                    # 2. Находим все action_executions для этого execution_id, которые ещё не завершены
                    query_select_actions = """
                        SELECT id, status, actual_end_time
                        FROM action_executions
                        WHERE execution_id = ? AND status != 'completed'
                    """
                    cursor.execute(query_select_actions, (execution_id,))
                    uncompleted_actions = cursor.fetchall()

                    if uncompleted_actions:
                        print(f"SQLiteDatabaseManager: Найдено {len(uncompleted_actions)} незавершённых action_executions для execution ID {execution_id}. Устанавливаем им статус 'skipped'.")

                        # 3. Обновляем статус и actual_end_time для каждого из них
                        action_ids_to_skip = [action[0] for action in uncompleted_actions]
                        
                        # Создаем строку с плейсхолдерами для IN (?, ?, ...)
                        placeholders = ','.join(['?' for _ in action_ids_to_skip])

                        query_update_actions = f"""
                            UPDATE action_executions
                            SET status = 'skipped', actual_end_time = ?, updated_at = datetime('now', 'localtime')
                            WHERE id IN ({placeholders})
                        """
                        # Передаём completed_at_str как время завершения для всех пропущенных действий
                        params = [completed_at_str] + action_ids_to_skip
                        cursor.execute(query_update_actions, params)
                        rows_affected_actions = cursor.rowcount
                        print(f"SQLiteDatabaseManager: Обновлено {rows_affected_actions} action_executions на статус 'skipped'.")
                    else:
                        print(f"SQLiteDatabaseManager: Для execution ID {execution_id} нет незавершённых action_executions. Пропуск обновления действий.")
                    # ---

                    return True
                else:
                    print(f"SQLiteDatabaseManager: Execution ID {execution_id} не найден или уже был остановлен.")
                    return False
        except sqlite3.Error as e:
            print(f"SQLiteDatabaseManager: Ошибка при остановке execution ID {execution_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"SQLiteDatabaseManager: Неизвестная ошибка при остановке execution ID {execution_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    # --- МЕТОД ДЛЯ ЗАПУСКА АЛГОРИТМА (ПРИМЕР) ---
    def start_algorithm_execution(self, algorithm_id: int, started_at_str: str, created_by_user_id: int, notes: str = None) -> int:
        """
        Создает новый экземпляр выполнения алгоритма (algorithm_execution).
        Также создает экземпляры действий (action_executions) на основе оригинальных действий алгоритма.
        Логика расчета времени зависит от time_type оригинального алгоритма.
        """
        try:
            conn = self._get_connection()
            with conn:
                cursor = conn.cursor()
                
                # 1. Получить оригинальный алгоритм и его действия
                cursor.execute("""
                    SELECT id, name, category, time_type, description
                    FROM algorithms WHERE id = ?
                """, (algorithm_id,))
                algorithm_row = cursor.fetchone()
                if not algorithm_row:
                    print(f"SQLiteDatabaseManager: Алгоритм с ID {algorithm_id} не найден.")
                    return -1

                original_algorithm = {
                    'id': algorithm_row[0],
                    'name': algorithm_row[1],
                    'category': algorithm_row[2],
                    'time_type': algorithm_row[3], # <-- ВАЖНО
                    'description': algorithm_row[4]
                }
                algorithm_time_type = original_algorithm['time_type'] # <-- Сохраняем тип времени
                print(f"SQLiteDatabaseManager: Запуск алгоритма ID {algorithm_id} с time_type '{algorithm_time_type}'.")

                cursor.execute("""
                    SELECT id, description, technical_text, start_offset, end_offset, contact_phones, report_materials
                    FROM actions WHERE algorithm_id = ? ORDER BY start_offset
                """, (algorithm_id,))
                original_actions_raw = cursor.fetchall()
                # Преобразуем в список словарей
                original_actions = []
                for action_row in original_actions_raw:
                    action_dict = {
                        'id': action_row[0],
                        'description': action_row[1],
                        'technical_text': action_row[2],
                        'start_offset': action_row[3],
                        'end_offset': action_row[4],
                        'contact_phones': action_row[5],
                        'report_materials': action_row[6]
                    }
                    original_actions.append(action_dict)
                print(f"SQLiteDatabaseManager: Получено {len(original_actions)} действий для алгоритма {algorithm_id}.")

                # 2. Получить информацию о пользователе на момент запуска
                cursor.execute("""
                    SELECT rank, last_name, first_name, middle_name
                    FROM users WHERE id = ?
                """, (created_by_user_id,))
                user_row = cursor.fetchone()
                if not user_row:
                     print(f"SQLiteDatabaseManager: Пользователь с ID {created_by_user_id} не найден для execution.")
                     return -1
                # Преобразуем в словарь
                user_data = {
                    'rank': user_row[0],
                    'last_name': user_row[1],
                    'first_name': user_row[2],
                    'middle_name': user_row[3]
                }
                display_name = f"{user_data['rank']} {user_data['last_name']} {user_data['first_name'][0]}.{user_data['middle_name'][0]+'.' if user_data['middle_name'] else ''}"

                # 3. Вставить новый algorithm_execution (snapshot)
                cursor.execute("""
                    INSERT INTO algorithm_executions (
                        algorithm_id,
                        snapshot_name, snapshot_category, snapshot_time_type, snapshot_description,
                        started_at,
                        created_by_user_id, created_by_user_display_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    original_algorithm['id'],
                    original_algorithm['name'], original_algorithm['category'], original_algorithm['time_type'], original_algorithm['description'],
                    started_at_str, # 'YYYY-MM-DD HH:MM:SS' или объект datetime
                    created_by_user_id, display_name
                ))
                new_execution_id = cursor.lastrowid
                print(f"SQLiteDatabaseManager: Создан новый execution ID {new_execution_id} для алгоритма {algorithm_id}.")

                # 4. Вставить action_executions (snapshot'ы действий)
                # Рассчитываем абсолютные времена на основе started_at и смещений
                import datetime
                started_at_dt = datetime.datetime.fromisoformat(started_at_str.replace(' ', 'T'))
                print(f"SQLiteDatabaseManager: Абсолютное время запуска алгоритма: {started_at_dt}.")

                for action in original_actions:
                    calculated_start_time = None
                    calculated_end_time = None

                    # --- ИЗМЕНЕНО: Логика в зависимости от time_type ---
                    if action['start_offset'] is not None:
                        if algorithm_time_type == 'астрономическое':
                            # --- ЛОГИКА ДЛЯ АСТРОНОМИЧЕСКОГО ---
                            print(f"SQLiteDatabaseManager: Рассчитываем calculated_start_time для астрономического времени действия ID {action['id']}.")
                            start_date_only = started_at_dt.date()

                            # Преобразуем строку смещения в формат, подходящий для расчета
                            offset_str = action['start_offset']
                            # Формат может быть 'dd hh:mm:ss' или 'hh:mm:ss'
                            import re
                            match = re.match(r'(\d+)\s+(\d{2}):(\d{2}):(\d{2})', offset_str) if ' ' in offset_str else re.match(r'(\d{2}):(\d{2}):(\d{2})', offset_str)

                            if match:
                                if ' ' in offset_str:  # Формат 'dd hh:mm:ss'
                                    days, hours, minutes, seconds = map(int, match.groups())
                                else:  # Формат 'hh:mm:ss'
                                    hours, minutes, seconds = map(int, match.groups())
                                    days = 0

                                # Создаем timedelta
                                offset_timedelta = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

                                # Добавляем дни к дате запуска, а время суток берем из смещения
                                calculated_start_time = datetime.datetime.combine(
                                    start_date_only + datetime.timedelta(days=days),
                                    datetime.time(hour=hours, minute=minutes, second=seconds)
                                )
                                print(f"SQLiteDatabaseManager:   Результат calculated_start_time: {calculated_start_time}")
                            else:
                                print(f"SQLiteDatabaseManager: Ошибка - не удается распознать формат start_offset '{offset_str}'. Устанавливаю None.")
                                calculated_start_time = None
                        else:
                            # --- ЛОГИКА ДЛЯ ОПЕРАТИВНОГО ---
                            print(f"SQLiteDatabaseManager: Рассчитываем calculated_start_time для оперативного времени действия ID {action['id']}.")
                            # Преобразуем строку смещения в timedelta
                            offset_str = action['start_offset']
                            import re
                            # Поддерживаем оба формата: 'hh:mm:ss' и 'dd hh:mm:ss'
                            match = re.match(r'(\d{2}):(\d{2}):(\d{2})', offset_str)  # Формат 'hh:mm:ss'
                            if not match:
                                match = re.match(r'(\d+)\s+(\d{2}):(\d{2}):(\d{2})', offset_str)  # Формат 'dd hh:mm:ss'
                                if match:
                                    # Формат 'dd hh:mm:ss' - извлекаем дни, часы, минуты, секунды
                                    days, hours, minutes, seconds = map(int, match.groups())
                                    offset_timedelta = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
                                    calculated_start_time = started_at_dt + offset_timedelta
                                    print(f"SQLiteDatabaseManager:   started_at_dt ({started_at_dt}) + offset ({offset_timedelta}) = {calculated_start_time}")
                                else:
                                    print(f"SQLiteDatabaseManager: Ошибка - не удается распознать формат start_offset '{offset_str}'. Устанавливаю None.")
                                    calculated_start_time = None
                            else:
                                # Формат 'hh:mm:ss' - извлекаем часы, минуты, секунды
                                hours, minutes, seconds = map(int, match.groups())
                                offset_timedelta = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
                                calculated_start_time = started_at_dt + offset_timedelta
                                print(f"SQLiteDatabaseManager:   started_at_dt ({started_at_dt}) + offset ({offset_timedelta}) = {calculated_start_time}")
                    # --- ---
                    if action['end_offset'] is not None:
                        if algorithm_time_type == 'астрономическое':
                            # --- ЛОГИКА ДЛЯ АСТРОНОМИЧЕСКОГО ---
                            print(f"SQLiteDatabaseManager: Рассчитываем calculated_end_time для астрономического времени действия ID {action['id']}.")
                            start_date_only = started_at_dt.date()

                            # Преобразуем строку смещения в формат, подходящий для расчета
                            offset_str = action['end_offset']
                            # Формат может быть 'dd hh:mm:ss' или 'hh:mm:ss'
                            import re
                            match = re.match(r'(\d+)\s+(\d{2}):(\d{2}):(\d{2})', offset_str) if ' ' in offset_str else re.match(r'(\d{2}):(\d{2}):(\d{2})', offset_str)

                            if match:
                                if ' ' in offset_str:  # Формат 'dd hh:mm:ss'
                                    days, hours, minutes, seconds = map(int, match.groups())
                                else:  # Формат 'hh:mm:ss'
                                    hours, minutes, seconds = map(int, match.groups())
                                    days = 0

                                # Создаем timedelta
                                offset_timedelta = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

                                # Добавляем дни к дате запуска, а время суток берем из смещения
                                calculated_end_time = datetime.datetime.combine(
                                    start_date_only + datetime.timedelta(days=days),
                                    datetime.time(hour=hours, minute=minutes, second=seconds)
                                )
                                print(f"SQLiteDatabaseManager:   Результат calculated_end_time: {calculated_end_time}")
                            else:
                                print(f"SQLiteDatabaseManager: Ошибка - не удается распознать формат end_offset '{offset_str}'. Устанавливаю None.")
                                calculated_end_time = None
                        else:
                            # --- ЛОГИКА ДЛЯ ОПЕРАТИВНОГО ---
                            print(f"SQLiteDatabaseManager: Рассчитываем calculated_end_time для оперативного времени действия ID {action['id']}.")
                            # Преобразуем строку смещения в timedelta
                            offset_str = action['end_offset']
                            import re
                            # Поддерживаем оба формата: 'hh:mm:ss' и 'dd hh:mm:ss'
                            match = re.match(r'(\d{2}):(\d{2}):(\d{2})', offset_str)  # Формат 'hh:mm:ss'
                            if not match:
                                match = re.match(r'(\d+)\s+(\d{2}):(\d{2}):(\d{2})', offset_str)  # Формат 'dd hh:mm:ss'
                                if match:
                                    # Формат 'dd hh:mm:ss' - извлекаем дни, часы, минуты, секунды
                                    days, hours, minutes, seconds = map(int, match.groups())
                                    offset_timedelta = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
                                    calculated_end_time = started_at_dt + offset_timedelta
                                    print(f"SQLiteDatabaseManager:   started_at_dt ({started_at_dt}) + offset ({offset_timedelta}) = {calculated_end_time}")
                                else:
                                    print(f"SQLiteDatabaseManager: Ошибка - не удается распознать формат end_offset '{offset_str}'. Устанавливаю None.")
                                    calculated_end_time = None
                            else:
                                # Формат 'hh:mm:ss' - извлекаем часы, минуты, секунды
                                hours, minutes, seconds = map(int, match.groups())
                                offset_timedelta = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
                                calculated_end_time = started_at_dt + offset_timedelta
                                print(f"SQLiteDatabaseManager:   started_at_dt ({started_at_dt}) + offset ({offset_timedelta}) = {calculated_end_time}")

                    cursor.execute("""
                        INSERT INTO action_executions (
                            execution_id,
                            snapshot_description, snapshot_technical_text, snapshot_contact_phones, snapshot_report_materials,
                            calculated_start_time, calculated_end_time
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        new_execution_id,
                        action['description'], action.get('technical_text'), action['contact_phones'], action['report_materials'],
                        calculated_start_time.isoformat() if calculated_start_time else None,
                        calculated_end_time.isoformat() if calculated_end_time else None
                    ))
                    print(f"SQLiteDatabaseManager: Создан action_execution для действия ID {action['id']} (start: {calculated_start_time}, end: {calculated_end_time}).")
                print(f"SQLiteDatabaseManager: Созданы {len(original_actions)} action_executions для execution ID {new_execution_id}.")

                print(f"SQLiteDatabaseManager: Транзакция завершена успешно. Новый execution ID: {new_execution_id}")
                return new_execution_id

        except sqlite3.Error as e:
           conn.rollback()  # Добавляем откат транзакции при ошибке
           print(f"SQLiteDatabaseManager: Ошибка при запуске execution для алгоритма {algorithm_id}: {e}")
           import traceback
           traceback.print_exc()
           return -1
        except Exception as e:
           print(f"SQLiteDatabaseManager: Неизвестная ошибка при запуске execution для алгоритма {algorithm_id}: {e}")
           import traceback
           traceback.print_exc()
           return -1
        except Exception as e:
            print(f"SQLiteDatabaseManager: Неизвестная ошибка при запуске execution для алгоритма {algorithm_id}: {e}")
            import traceback
            traceback.print_exc()
            return -1

    def get_completed_executions_by_category_and_date(self, category: str, date_string: str) -> List[Dict[str, Any]]:
        """
        Получает список завершённых (status = 'completed' или 'cancelled')
        выполнений алгоритмов (algorithm_executions) за заданную дату и категорию.
        Включает время начала и окончания в отформатированном виде.

        :param category: Категория алгоритмов (snapshot_category).
        :param date_string: Дата в формате 'DD.MM.YYYY'.
        :return: Список словарей с данными execution'ов.
        """
        if not category or not date_string:
            print("SQLiteDatabaseManager: Категория или дата не заданы.")
            return []

        try:
            # Преобразуем дату из DD.MM.YYYY в объект date для SQL
            from datetime import datetime
            target_date = datetime.strptime(date_string, '%d.%m.%Y').date()
            target_date_iso = target_date.isoformat() # 'YYYY-MM-DD'

            print(f"SQLiteDatabaseManager: Поиск завершённых executions категории '{category}' за дату {target_date_iso}.")

            conn = self._get_connection()
            with conn:
                cursor = conn.cursor()
                
                # SQL-запрос
                sql_query = """
                    SELECT
                        ae.id,
                        ae.algorithm_id,
                        ae.snapshot_name AS algorithm_name,
                        ae.snapshot_category AS category,
                        ae.started_at,
                        substr(ae.started_at, 1, 19) AS started_at_display,
                        ae.completed_at,
                        CASE
                            WHEN ae.completed_at IS NOT NULL THEN substr(ae.completed_at, 1, 19)
                            ELSE NULL
                        END AS completed_at_display,
                        ae.status,
                        ae.created_by_user_id,
                        ae.created_by_user_display_name
                    FROM algorithm_executions ae
                    WHERE ae.snapshot_category = ? 
                    AND ae.status IN ('completed', 'cancelled')
                    AND substr(ae.completed_at, 1, 10) = ?
                    ORDER BY ae.completed_at DESC;
                """
                cursor.execute(sql_query, (category, target_date_iso))
                rows = cursor.fetchall()

                # Преобразуем результаты в список словарей
                executions = [dict(row) for row in rows]
                print(f"SQLiteDatabaseManager: Найдено {len(executions)} завершённых executions.")
                return executions

        except sqlite3.Error as e:
            print(f"SQLiteDatabaseManager: Ошибка БД при получении завершённых executions: {e}")
            import traceback
            traceback.print_exc()
            return []
        except ValueError as ve:
            print(f"SQLiteDatabaseManager: Ошибка преобразования даты '{date_string}': {ve}")
            return []
        except Exception as e:
            print(f"SQLiteDatabaseManager: Неизвестная ошибка: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_algorithm_execution_by_id(self, execution_id: int) -> dict:
        """
        Получает данные конкретного экземпляра выполнения алгоритма (execution) по его ID.
        Включает информацию о пользователе, создавшем execution, на момент запуска.
        :param execution_id: ID execution'а.
        :return: Словарь с данными execution'а или None, если не найден.
        """
        try:
            conn = self._get_connection()
            with conn:
                cursor = conn.cursor()
                
                # SQL-запрос для получения данных execution'а и имени пользователя
                # Используем LEFT JOIN, чтобы получить данные даже если пользователь был удалён
                # В этом случае created_by_user_display_name будет NULL
                sql_query = """
                    SELECT
                        ae.id,
                        ae.algorithm_id,
                        ae.snapshot_name,
                        ae.snapshot_category,
                        ae.snapshot_time_type,
                        ae.snapshot_description,
                        ae.started_at,
                        ae.completed_at,
                        ae.status,
                        ae.created_by_user_id,
                        ae.created_by_user_display_name, -- Имя, сохранённое на момент запуска
                        ae.created_at,
                        ae.updated_at
                    FROM algorithm_executions ae
                    WHERE ae.id = ?
                """
                cursor.execute(sql_query, (execution_id,))
                row = cursor.fetchone()

                if row:
                    # Преобразуем результат в словарь
                    execution_data = {
                        'id': row[0],
                        'algorithm_id': row[1],
                        'snapshot_name': row[2],
                        'snapshot_category': row[3],
                        'snapshot_time_type': row[4],
                        'snapshot_description': row[5],
                        'started_at': row[6] if row[6] else None, # Оставляем строку как есть
                        'completed_at': row[7] if row[7] else None,
                        'status': row[8],
                        'created_by_user_id': row[9],
                        'created_by_user_display_name': row[10],
                        'created_at': row[11] if row[11] else None,
                        'updated_at': row[12] if row[12] else None,
                    }
                    logger.info(f"SQLiteDatabaseManager: Получены данные execution ID {execution_id}.")
                    return execution_data
                else:
                    logger.warning(f"SQLiteDatabaseManager: Execution с ID {execution_id} не найден.")
                    return None

        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка при получении execution ID {execution_id}: {e}")
            print(f"SQLiteDatabaseManager: Ошибка при получении execution ID {execution_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"SQLiteDatabaseManager: Неизвестная ошибка при получении execution ID {execution_id}: {e}")
            print(f"SQLiteDatabaseManager: Неизвестная ошибка при получении execution ID {execution_id}: {e}")
            return None

    def get_action_executions_by_execution_id(self, execution_id: int) -> list:
        """
        Получает список всех выполнений действий (action_execution'ов) для конкретного execution'а.
        Результат сортируется по calculated_start_time.
        :param execution_id: ID execution'а.
        :return: Список словарей с данными action_execution'ов или пустой список, если не найдены.
                 Возвращает None в случае ошибки.
        """
        try:
            conn = self._get_connection()
            with conn:
                cursor = conn.cursor()
                
                # SQL-запрос для получения данных action_execution'ов
                # Сортировка по calculated_start_time
                sql_query = """
                    SELECT
                        ae.id,
                        ae.execution_id,
                        ae.snapshot_description,
                        ae.snapshot_technical_text,
                        ae.snapshot_contact_phones,
                        ae.snapshot_report_materials,
                        ae.calculated_start_time,
                        ae.calculated_end_time,
                        ae.actual_end_time,
                        ae.status,
                        ae.reported_to,
                        ae.notes,
                        ae.created_at,
                        ae.updated_at
                    FROM action_executions ae
                    WHERE ae.execution_id = ?
                    ORDER BY
                        ae.calculated_start_time ASC,
                        ae.calculated_end_time ASC,
                        ae.id ASC
                """
                cursor.execute(sql_query, (execution_id,))
                rows = cursor.fetchall()

                # Получаем названия колонок
                colnames = [desc[0] for desc in cursor.description]

                action_executions_list = []
                for row in rows:
                    # Создаем словарь из строки результата
                    action_exec_dict = dict(zip(colnames, row))
                    # В SQLite даты хранятся как строки, оставляем как есть
                    action_executions_list.append(action_exec_dict)

                logger.info(f"SQLiteDatabaseManager: Получено {len(action_executions_list)} action_execution'ов для execution ID {execution_id}.")
                return action_executions_list

        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка при получении action_execution'ов для execution ID {execution_id}: {e}")
            print(f"SQLiteDatabaseManager: Ошибка при получении action_execution'ов для execution ID {execution_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"SQLiteDatabaseManager: Неизвестная ошибка при получении action_execution'ов для execution ID {execution_id}: {e}")
            print(f"SQLiteDatabaseManager: Неизвестная ошибка при получении action_execution'ов для execution ID {execution_id}: {e}")
            return None
    def create_action_execution(self, execution_id: int, action_execution_data: dict) -> bool:
        """
        Создает новое action_execution, связанное с execution_id.
        :param execution_id: ID execution'а.
        :param action_execution_data: Данные нового action_execution'а.
                                     Ожидается словарь с ключами, соответствующими полям в БД.
        :return: True, если успешно, иначе False.
        """
        logger.debug(f"SQLiteDatabaseManager: create_action_execution called with execution_id={execution_id}, data={action_execution_data}")

        if not isinstance(execution_id, int) or execution_id <= 0:
            logger.error("SQLiteDatabaseManager: Некорректный execution_id.")
            return False

        if not isinstance(action_execution_data, dict):
            logger.error("SQLiteDatabaseManager: action_execution_data должно быть словарем.")
            return False

        # --- 1. Подготовить данные для вставки ---
        # Определяем разрешенные поля (те, которые реально существуют в БД)
        allowed_fields_in_db = {
            'snapshot_description',
            'snapshot_technical_text',
            'calculated_start_time',      # ← используем calculated как факт
            'calculated_end_time',
            'snapshot_contact_phones',
            'snapshot_report_materials',
            'reported_to',
            'notes'
        }

        # Создаем копию данных, содержащую только разрешенные поля
        prepared_data = {k: v for k, v in action_execution_data.items() if k in allowed_fields_in_db}
        logger.debug(f"SQLiteDatabaseManager: Подготовленные данные (до преобразования времени): {prepared_data}")

        # Добавляем execution_id
        prepared_data['execution_id'] = execution_id
        # --- ---

        # --- 2. Обработка абсолю��ных дат/времени ---
        # Обрабатываем все возможные поля времени, включая calculated_*, actual_*, и другие
        # Предполагаем, что они могут содержать строки в формате 'dd.MM.yyyy HH:mm:ss' или пустые/None.
        # Нужно преобразовать их в формат, подходящий для SQLite.

        def parse_datetime_string(datetime_str: str) -> str | None:
            """Вспомогательная функция для парсинга строки даты/времени."""
            if not datetime_str or not isinstance(datetime_str, str):
                return None
            datetime_str = datetime_str.strip()
            if not datetime_str:
                return None
            try:
                parsed_dt = datetime.datetime.strptime(datetime_str, "%d.%m.%Y %H:%M:%S")
                logger.debug(f"SQLiteDatabaseManager: Строка '{datetime_str}' успешно преобразована в datetime: {parsed_dt}")
                # Преобразуем обратно в строку в формате ISO с T для SQLite (для согласованности с оригинальными действиями)
                return parsed_dt.isoformat('T')
            except ValueError as e:
                logger.warning(f"SQLiteDatabaseManager: Неверный формат строки даты/времени '{datetime_str}': {e}")
                return None # Или поднять исключение, если это критично

        # Преобразуем 'actual_start_time'
        if 'actual_start_time' in prepared_data:
            start_time_str = prepared_data['actual_start_time']
            prepared_data['actual_start_time'] = parse_datetime_string(start_time_str)
            # Если значение None, в БД пойдет NULL

        # Преобразуем 'actual_end_time'
        if 'actual_end_time' in prepared_data:
            end_time_str = prepared_data['actual_end_time']
            prepared_data['actual_end_time'] = parse_datetime_string(end_time_str)
            # Если значение None, в БД пойдет NULL

        # --- НОВОЕ: Обработка calculated_start_time и calculated_end_time ---
        # Эти поля могут передаваться из QML при добавлении новых действий
        if 'calculated_start_time' in prepared_data:
            calc_start_str = prepared_data['calculated_start_time']
            # Проверяем, не в нужном ли формате уже находится строка (ISO формат)
            if calc_start_str and isinstance(calc_start_str, str) and ':' in calc_start_str and ('-' in calc_start_str or 'T' in calc_start_str):
                # Если уже в формате YYYY-MM-DD HH:MM:SS или YYYY-MM-DDTHH:MM:SS, оставляем как есть
                pass
            else:
                # Преобразуем из формата dd.mm.yyyy HH:MM:SS в ISO формат с T
                prepared_data['calculated_start_time'] = parse_datetime_string(calc_start_str)

        if 'calculated_end_time' in prepared_data:
            calc_end_str = prepared_data['calculated_end_time']
            # Проверяем, не в нужном ли формате уже находится строка (ISO формат)
            if calc_end_str and isinstance(calc_end_str, str) and ':' in calc_end_str and ('-' in calc_end_str or 'T' in calc_end_str):
                # Если уже в формате YYYY-MM-DD HH:MM:SS или YYYY-MM-DDTHH:MM:SS, оставляем как есть
                pass
            else:
                # Преобразуем из формата dd.mm.yyyy HH:MM:SS в ISO формат с T
                prepared_data['calculated_end_time'] = parse_datetime_string(calc_end_str)
        # --- ---

        logger.debug(f"SQLiteDatabaseManager: Подготовленные данные (после преобразования времени): {prepared_data}")
        # --- ---

        # --- 3. Подготовить SQL-запрос ---
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Проверяем, существует ли execution_id
            cursor.execute(
                "SELECT 1 FROM algorithm_executions WHERE id = ?;", (execution_id,)
            )
            if not cursor.fetchone():
                 logger.error(f"SQLiteDatabaseManager: Execution ID {execution_id} не существует.")
                 cursor.close()
                 conn.close()
                 return False

            # Подготавливаем список колонок и значений
            columns = list(prepared_data.keys())
            values = [prepared_data[col] for col in columns] # Список значений, включая datetime или None

            # Создаем SQL-строки для запроса
            columns_str = ', '.join(columns)
            placeholders_str = ', '.join(['?'] * len(values)) # ? для всех значений, включая datetime

            sql_query = f"""
                INSERT INTO action_executions ({columns_str})
                VALUES ({placeholders_str});
            """

            logger.debug(f"SQLiteDatabaseManager: Выполняем SQL: {sql_query} с параметрами {values}")
            cursor.execute(sql_query, values)
            conn.commit()
            new_action_id = cursor.lastrowid

            if new_action_id:
                logger.info(f"SQLiteDatabaseManager: Новое action_execution (ID: {new_action_id}) добавлено для execution ID {execution_id}.")
                cursor.close()
                conn.close()
                return True
            else:
                logger.error(f"SQLiteDatabaseManager: Не удалось получить ID нового action_execution для execution ID {execution_id}.")
                cursor.close()
                conn.close()
                return False

        except sqlite3.IntegrityError as e:
             # Это может быть ошибка нарушения внешнего ключа (execution_id не существует)
             logger.error(f"SQLiteDatabaseManager: Ошибка целостности БД при добавлении action_execution для execution ID {execution_id}: {e}")
             return False
        except sqlite3.Error as e: # Ловим более общие ошибки sqlite3
             logger.error(f"SQLiteDatabaseManager: Ошибка БД sqlite3 при добавлении action_execution для execution ID {execution_id}: {e}")
             return False
        except Exception as e:
             logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при добавлении action_execution для execution ID {execution_id}: {e}")
             return False
        # --- ---


    def update_action_execution(self, action_execution_id: int, action_execution_data: dict) -> bool:
        """
        Обновляет существующее action_execution.
        :param action_execution_id: ID action_execution'а.
        :param action_execution_data: Данные для обновления.
        :return: True, если успешно, иначе False.
        """

        # --- 1. Подготовить данные для обновления ---
        # Определяем разрешенные поля (те, которые реально существуют в ТАБЛИЦЕ action_executions)
        allowed_fields_in_db = {
            'snapshot_description',
            'snapshot_technical_text',
            'calculated_start_time',
            'calculated_end_time',
            'actual_end_time',      # <-- Поле для фактического времени окончания
            'reported_to',          # <-- Поле для "Кому доложено"
            'notes',                # <-- Поле для "Примечания"
            'snapshot_contact_phones',
            'snapshot_report_materials' # Обычно не меняется (это копия из шаблона)
        }

        # Создаем копию данных, содержащую только разрешенные поля
        # Также фильтруем None значения, если БД не принимает NULL для каких-то полей
        prepared_data = {}
        for k, v in action_execution_data.items():
            if k in allowed_fields_in_db:
                # Преобразуем пустую строку в None для полей, которые должны быть NULL, если пустые
                if v == "":
                    prepared_data[k] = None
                else:
                    prepared_data[k] = v

        logger.debug(f"SQLiteDatabaseManager: Подготовленные данные для обновления (до преобразования времени): {prepared_data}")
        # --- ---

        # --- 2. Обработка абсолютных дат/времени (только для actual_end_time) ---
        def parse_datetime_string(datetime_str: str) -> str | None:
            """Вспомогательная функция для парсинга строки даты/времени."""
            if not datetime_str or not isinstance(datetime_str, str):
                return None
            datetime_str = datetime_str.strip()
            if not datetime_str:
                return None
            try:
                parsed_dt = datetime.datetime.strptime(datetime_str, "%d.%m.%Y %H:%M:%S")
                logger.debug(f"SQLiteDatabaseManager: Строка '{datetime_str}' успешно преобразована в datetime: {parsed_dt}")
                # Преобразуем обратно в строку в формате ISO с T для SQLite (для согласованности с оригинальными действиями)
                return parsed_dt.isoformat('T')
            except ValueError as e:
                logger.warning(f"SQLiteDatabaseManager: Неверный формат строки даты/времени '{datetime_str}': {e}")
                return None

        # Преобразуем 'actual_end_time', если оно присутствует
        actual_end_time_str = None
        if 'actual_end_time' in prepared_data:
            end_time_str = prepared_data['actual_end_time']
            actual_end_time_str = parse_datetime_string(end_time_str)
            if actual_end_time_str:
                prepared_data['actual_end_time'] = actual_end_time_str
            else:
                # Есл�� строка времени некорректна, удал��ем её из prepared_data
                logger.warning(f"SQLiteDatabaseManager: Невоз��ожно разобрать actual_end_time '{end_time_str}'. Поле будет пропущено.")
                prepared_data.pop('actual_end_time', None)
                actual_end_time_str = None # Убедимся, что dt тоже None, есл�� строка неверна

        # --- ---

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Проверяем, существует ли action_execution_id
            cursor.execute(
                "SELECT id, execution_id, calculated_start_time, calculated_end_time, status FROM action_executions WHERE id = ?;",
                (action_execution_id,)
            )
            row = cursor.fetchone()
            if not row:
                logger.error(f"SQLiteDatabaseManager: Action_execution ID {action_execution_id} не существует.")
                return False

            original_execution_data = {
                'id': row[0],
                'execution_id': row[1],
                'calculated_start_time': row[2],
                'calculated_end_time': row[3],
                'status': row[4]
            }
            logger.debug(f"SQLiteDatabaseManager: Найден action_execution для обновления: {original_execution_data}")

            # --- Проверка: actual_end_time не раньше calculated_start_time ---
            if actual_end_time_str and original_execution_data.get('calculated_start_time'):
                # Преобразуем строки в datetime для сравнения
                try:
                    # Поддерживаем оба формата: 'YYYY-MM-DD HH:MM:SS' и 'YYYY-MM-DDTHH:MM:SS'
                    calc_start_str = original_execution_data['calculated_start_time']
                    if calc_start_str and 'T' in calc_start_str:
                        calc_start_dt = datetime.datetime.fromisoformat(calc_start_str.replace('Z', '+00:00'))
                    else:
                        calc_start_dt = datetime.datetime.strptime(calc_start_str, "%Y-%m-%d %H:%M:%S")

                    # Поддерживаем оба формата: 'YYYY-MM-DD HH:MM:SS' и 'YYYY-MM-DDTHH:MM:SS'
                    if actual_end_time_str and 'T' in actual_end_time_str:
                        actual_end_dt = datetime.datetime.fromisoformat(actual_end_time_str.replace('Z', '+00:00'))
                    else:
                        actual_end_dt = datetime.datetime.strptime(actual_end_time_str, "%Y-%m-%d %H:%M:%S")

                    if actual_end_dt < calc_start_dt:
                        logger.error(f"SQLiteDatabaseManager: actual_end_time ({actual_end_dt}) не может быть раньше calculated_start_time ({calc_start_dt}) для action_execution ID {action_execution_id}.")
                        cursor.close()
                        conn.close()
                        return False
                except ValueError as ve:
                    logger.error(f"SQLiteDatabaseManager: Ошибка преобразования дат для проверки: {ve}")
                    cursor.close()
                    conn.close()
                    return False
            # --- ---

                # --- Определение нового статуса ---
                new_status = None
                if actual_end_time_str is not None:
                    # Если передано actual_end_time, статус должен стать 'completed'
                    new_status = 'completed'
                    prepared_data['status'] = new_status # Добавляем статус в подготовленные данные
                    logger.debug(f"SQLiteDatabaseManager: Установлен статус 'completed' для action_execution ID {action_execution_id} на основе actual_end_time.")
                # Если actual_end_time не передан, статус не изменяем, оставляем как есть
                # --- ---

                # --- Подготовка SQL-запроса ---
                if not prepared_data:
                    logger.info("SQLiteDatabaseManager: Нет данных для обновления (после фильтрации и преобразований).")
                    # Если нет данных для обновления, возвращаем True (ничего обновлять не нужно)
                    cursor.close()
                    conn.close()
                    return True

                # Подготавливаем SET часть запроса
                set_clauses = []
                values = []
                for key, value in prepared_data.items():
                    # Пропускаем None значения, если поле не поддерживает NULL (в SQLite большинство полей по умолчанию поддерживают NULL)
                    # Но для безопасности можно пропустить
                    if value is not None or key in ['actual_end_time', 'reported_to', 'notes']:  # Уточните, какие поля могут быть NULL
                        set_clauses.append(f"{key} = ?")
                        values.append(value) # Добавляем значение (datetime, строка, None и т.д.)

                # Если нет полей для обновления, возвращаем True (ничего обновлять не нужно)
                if not set_clauses:
                    logger.info("SQLiteDatabaseManager: Нет полей для обновления.")
                    cursor.close()
                    conn.close()
                    return True

                # Добавляем action_execution_id в конец списка значений для WHERE
                values.append(action_execution_id)

                set_clause_str = ", ".join(set_clauses)
                # Обновляем updated_at автоматически
                sql_query = f"""
                    UPDATE action_executions
                    SET {set_clause_str}, updated_at = datetime('now', 'localtime')
                    WHERE id = ?;
                """

                logger.debug(f"SQLiteDatabaseManager: Выполняем SQL UPDATE: {sql_query} с параметрами {values}")
                cursor.execute(sql_query, values)
                conn.commit()
                logger.info(f"SQLiteDatabaseManager: Запрос UPDATE выполнен для action_execution с ID {action_execution_id}.")

                cursor.close()
                conn.close()

                # Возвращаем True, если запрос выполнился успешно (независимо от количества затронутых строк)
                return True

        except sqlite3.IntegrityError as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка целостности БД при обновлении action_execution ID {action_execution_id}: {e}")
            if 'conn' in locals():
                conn.close()
            return False
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка БД sqlite3 при обновлении action_execution ID {action_execution_id}: {e}")
            if 'conn' in locals():
                conn.close()
            return False
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при обновлении action_execution ID {action_execution_id}: {e}")
            if 'conn' in locals():
                conn.close()
            return False
        # --- ---



    def update_action_execution_status(self, action_execution_id: int, new_status: str) -> bool:
        """Обновляет только статус action_execution."""
        if not isinstance(action_execution_id, int) or action_execution_id <= 0:
            logger.error("Некорректный ID action_execution для обновления статуса.")
            return False
        
        valid_statuses = ['pending', 'in_progress', 'completed', 'skipped']
        if new_status not in valid_statuses:
            logger.error(f"Недопустимый статус: {new_status}. Допустимые: {valid_statuses}")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE action_executions SET status = ?, updated_at = datetime('now', 'localtime') WHERE id = ?;",
                (new_status, action_execution_id)
            )
            conn.commit()
            affected = cursor.rowcount
            cursor.close()
            conn.close()
            logger.info(f"SQLiteDatabaseManager: Статус action_execution ID {action_execution_id} обновлен на '{new_status}'. Затронуто строк: {affected}")
            return affected > 0
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка БД при обновлении статуса action_execution ID {action_execution_id}: {e}")
            return False
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при обновлении статуса action_execution ID {action_execution_id}: {e}")
            return False

    def get_action_execution_by_id(self, action_execution_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает данные конкретного выполнения действия (action_execution) по его ID.
        :param action_execution_id: ID action_execution.
        :return: Словарь с данными action_execution или None.
        """
        if not isinstance(action_execution_id, int) or action_execution_id <= 0:
            logger.error(f"SQLiteDatabaseManager: Некорректный action_execution_id: {action_execution_id}")
            return None

        try:
            conn = self._get_connection()
            with conn:
                cursor = conn.cursor()
                
                # Запрос включает все нужные поля, включая snapshot и calculated/actual
                query = """
                SELECT
                    id,
                    execution_id,
                    snapshot_description,
                    snapshot_contact_phones,
                    snapshot_report_materials,
                    calculated_start_time,
                    calculated_end_time,
                    actual_end_time,
                    status,
                    reported_to,
                    notes
                FROM action_executions
                WHERE id = ?;
                """
                cursor.execute(query, (action_execution_id,))
                row = cursor.fetchone()

                if row:
                    # Преобразуем результат в словарь
                    result_dict = {
                        'id': row[0],
                        'execution_id': row[1],
                        'snapshot_description': row[2],
                        'snapshot_contact_phones': row[3],
                        'snapshot_report_materials': row[4],
                        'calculated_start_time': row[5],
                        'calculated_end_time': row[6],
                        'actual_end_time': row[7],
                        'status': row[8],
                        'reported_to': row[9],
                        'notes': row[10]
                    }

                    # В SQLite даты хранятся как строки, оставляем как есть
                    logger.debug(f"SQLiteDatabaseManager: Получены (и преобразованы) данные action_execution ID {action_execution_id}: {result_dict}")
                    return result_dict
                else:
                    logger.warning(f"SQLiteDatabaseManager: Action execution ID {action_execution_id} не найден.")
                    return None

        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка БД при получении action_execution ID {action_execution_id}: {e}")
            return None
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при получении action_execution ID {action_execution_id}: {e}")
            return None

    def update_execution_responsible_user(self, execution_id: int, new_responsible_user_id: int) -> bool:
        """
        Обновляет ответственного пользователя для запущенного алгоритма (execution).
        :param execution_id: ID execution'а.
        :param new_responsible_user_id: ID нового ответственного пользователя.
        :return: True, если успешно, иначе False.
        """
        if not isinstance(execution_id, int) or execution_id <= 0:
            logger.error(f"SQLiteDatabaseManager: Некорректный execution_id: {execution_id}")
            return False

        if not isinstance(new_responsible_user_id, int) or new_responsible_user_id <= 0:
            logger.error(f"SQLiteDatabaseManager: Некорректный ID нового ответственного пользователя: {new_responsible_user_id}")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Проверим, существует ли пользователь с указанным ID
            cursor.execute("SELECT id, rank, last_name, first_name, middle_name FROM users WHERE id = ? AND is_active = 1;", (new_responsible_user_id,))
            user_row = cursor.fetchone()
            if not user_row:
                logger.error(f"SQLiteDatabaseManager: Пользователь с ID {new_responsible_user_id} не найден или неактивен.")
                cursor.close()
                conn.close()
                return False

            # Формируем отображаемое имя пользователя
            _, rank, last_name, first_name, middle_name = user_row
            display_name = f"{rank} {last_name} {first_name[0]}."
            if middle_name:
                display_name += f"{middle_name[0]}."

            # Обновляем execution: ID пользователя и его отображаемое имя
            update_query = """
                UPDATE algorithm_executions
                SET created_by_user_id = ?, created_by_user_display_name = ?, updated_at = datetime('now', 'localtime')
                WHERE id = ?;
            """
            cursor.execute(update_query, (new_responsible_user_id, display_name, execution_id))
            rows_affected = cursor.rowcount

            if rows_affected > 0:
                conn.commit()
                logger.info(f"SQLiteDatabaseManager: Ответственный пользователь для execution ID {execution_id} успешно обновлен на ID {new_responsible_user_id} ({display_name}).")
                cursor.close()
                conn.close()
                return True
            else:
                logger.warning(f"SQLiteDatabaseManager: Execution ID {execution_id} не найден для обновления ответственного пользователя.")
                cursor.close()
                conn.close()
                return False

        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка БД при обновлении ответственного пользователя для execution ID {execution_id}: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при обновлении ответственного пользователя для execution ID {execution_id}: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False

    def get_active_action_executions_with_details(self) -> list:
        """
        Получает список активных action_executions вместе с деталями execution'а.

        Возвращает список словарей:
        [
            {
                'id': int, # ID action_execution
                'execution_id': int, # ID связанного algorithm_execution
                'calculated_start_time': str, # Время начала в формате строки
                'calculated_end_time': str, # Время окончания в формате строки
                'status': str, # Статус action_execution ('pending', 'in_progress', ...)
                'snapshot_description': str, # Описание действия
                'execution_status': str # Статус algorithm_execution ('active', 'completed', ...)
            },
            ...
        ]
        """
        query = """
        SELECT
            ae.id,
            ae.execution_id,
            ae.calculated_start_time,
            ae.calculated_end_time,
            ae.status,
            ae.snapshot_description,
            exec.status AS execution_status,
            exec.snapshot_name
        FROM action_executions ae
        JOIN algorithm_executions exec ON ae.execution_id = exec.id
        WHERE exec.status = 'active' -- Только активные выполнения алгоритмов
        AND ae.status IN ('pending', 'in_progress'); -- Только активные действия
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            # Преобразуем результаты в список словарей
            results = []
            for row in rows:
                result_dict = {
                    'id': row[0],
                    'execution_id': row[1],
                    'calculated_start_time': row[2],
                    'calculated_end_time': row[3],
                    'status': row[4],
                    'snapshot_description': row[5],
                    'execution_status': row[6],
                    'snapshot_name': row[7]
                }
                results.append(result_dict)
            cursor.close()
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Ошибка при получении активных действий с деталями: {e}")
            import traceback
            traceback.print_exc()
            return []
    # --- Конец метода get_active_action_executions_with_details ---

    def update_action_execution_notes(self, action_execution_id: int, notes: str) -> bool:
        """
        Обновляет только поле 'notes' у action_execution.
        :param action_execution_id: ID action_execution'а.
        :param notes: Новое значение примечания.
        :return: True, если успешно, иначе False.
        """
        if not isinstance(action_execution_id, int) or action_execution_id <= 0:
            logger.error(f"SQLiteDatabaseManager: Некорректный action_execution_id: {action_execution_id}")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Проверяем, существует ли action_execution_id
            cursor.execute(
                "SELECT id FROM action_executions WHERE id = ?;",
                (action_execution_id,)
            )
            row = cursor.fetchone()
            if not row:
                logger.error(f"SQLiteDatabaseManager: Action_execution ID {action_execution_id} не существует.")
                cursor.close()
                conn.close()
                return False

            # Обновляем только поле notes
            notes_value = notes if notes and notes.strip() else None
            cursor.execute(
                "UPDATE action_executions SET notes = ?, updated_at = datetime('now', 'localtime') WHERE id = ?;",
                (notes_value, action_execution_id)
            )

            conn.commit()
            affected_rows = cursor.rowcount
            logger.info(f"SQLiteDatabaseManager: Обновлено {affected_rows} записей action_execution с ID {action_execution_id} (только поле notes).")

            cursor.close()
            conn.close()

            # Возвращаем True, если обновление прошло успешно (независимо от количества затронутых строк)
            return True

        except sqlite3.IntegrityError as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка целостности БД при обновлении примечания для action_execution ID {action_execution_id}: {e}")
            if 'conn' in locals():
                conn.close()
            return False
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка БД sqlite3 при обновлении примечания для action_execution ID {action_execution_id}: {e}")
            if 'conn' in locals():
                conn.close()
            return False
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при обновлении примечания для action_execution ID {action_execution_id}: {e}")
            if 'conn' in locals():
                conn.close()
            return False

    def update_action_execution_reported_to(self, action_execution_id: int, reported_to: str) -> bool:
        """
        Обновляет поле 'reported_to' (Кому доложено) у action_execution.
        :param action_execution_id: ID action_execution'а.
        :param reported_to: Новое значение.
        :return: True, если успешно, иначе False.
        """
        if not isinstance(action_execution_id, int) or action_execution_id <= 0:
            logger.error(f"SQLiteDatabaseManager: Некорректный action_execution_id: {action_execution_id}")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM action_executions WHERE id = ?;", (action_execution_id,))
            if not cursor.fetchone():
                logger.error(f"SQLiteDatabaseManager: Action_execution ID {action_execution_id} не существует.")
                cursor.close()
                conn.close()
                return False

            reported_value = reported_to if reported_to and reported_to.strip() else None
            cursor.execute(
                "UPDATE action_executions SET reported_to = ?, updated_at = datetime('now', 'localtime') WHERE id = ?;",
                (reported_value, action_execution_id)
            )
            conn.commit()
            affected = cursor.rowcount
            logger.info(f"SQLiteDatabaseManager: Обновлено reported_to для action_execution ID {action_execution_id}. Строк: {affected}.")
            cursor.close()
            conn.close()
            return True

        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка БД при обновлении reported_to: {e}")
            if 'conn' in locals():
                conn.close()
            return False
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при обновлении reported_to: {e}")
            if 'conn' in locals():
                conn.close()
            return False

    def append_action_execution_report_material(self, action_execution_id: int, material_path: str) -> bool:
        """
        Добавляет путь к отчётному материалу в action_execution (дополняет существующие).
        :param action_execution_id: ID action_execution'а.
        :param material_path: Путь к файлу материала.
        :return: True, если успешно, иначе False.
        """
        if not isinstance(action_execution_id, int) or action_execution_id <= 0:
            logger.error(f"SQLiteDatabaseManager: Некорректный action_execution_id: {action_execution_id}")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Получаем текущие материалы
            cursor.execute(
                "SELECT snapshot_report_materials FROM action_executions WHERE id = ?;",
                (action_execution_id,)
            )
            row = cursor.fetchone()
            if not row:
                logger.error(f"SQLiteDatabaseManager: Action_execution ID {action_execution_id} не существует.")
                cursor.close()
                conn.close()
                return False

            current_materials = row[0] or ""
            if current_materials:
                new_materials = current_materials + "\n" + material_path
            else:
                new_materials = material_path

            cursor.execute(
                "UPDATE action_executions SET snapshot_report_materials = ?, updated_at = datetime('now', 'localtime') WHERE id = ?;",
                (new_materials, action_execution_id)
            )
            conn.commit()
            logger.info(f"SQLiteDatabaseManager: Добавлен отчётный материал для action_execution ID {action_execution_id}.")
            cursor.close()
            conn.close()
            return True

        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка БД при добавлении отчётного материала: {e}")
            if 'conn' in locals():
                conn.close()
            return False
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при добавлении отчётного материала: {e}")
            if 'conn' in locals():
                conn.close()
            return False

    def delete_action_execution_report_material(self, action_execution_id: int, material_index: int) -> bool:
        """
        Удаляет отчётный материал по индексу (строка в snapshot_report_materials).
        :param action_execution_id: ID action_execution'а.
        :param material_index: Индекс строки для удаления (0-based).
        :return: True, если успешно, иначе False.
        """
        if not isinstance(action_execution_id, int) or action_execution_id <= 0:
            logger.error(f"SQLiteDatabaseManager: Некорректный action_execution_id: {action_execution_id}")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT snapshot_report_materials FROM action_executions WHERE id = ?;",
                (action_execution_id,)
            )
            row = cursor.fetchone()
            if not row:
                cursor.close()
                conn.close()
                return False

            current_materials = row[0] or ""
            lines = [line for line in current_materials.split("\n") if line.strip()]
            if material_index < 0 or material_index >= len(lines):
                cursor.close()
                conn.close()
                return False

            lines.pop(material_index)
            new_materials = "\n".join(lines) if lines else None

            cursor.execute(
                "UPDATE action_executions SET snapshot_report_materials = ?, updated_at = datetime('now', 'localtime') WHERE id = ?;",
                (new_materials, action_execution_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True

        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка БД при удалении отчётного материала: {e}")
            if 'conn' in locals():
                conn.close()
            return False
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при удалении отчётного материала: {e}")
            if 'conn' in locals():
                conn.close()
            return False

    # ========================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С ОРГАНИЗАЦИЯМИ (ШАБЛОНЫ ДЕЙСТВИЙ)
    # ========================================================================

    def get_all_organizations(self) -> list:
        """Получить ВСЕ организации (для обратной совместимости)."""
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM organizations ORDER BY name;")
            rows = cursor.fetchall()
            organizations = [dict(row) for row in rows]
            cursor.close()
            conn.close()
            logger.info(f"SQLiteDatabaseManager: Получено {len(organizations)} организаций (все).")
            return organizations
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка при получении всех организаций: {e}")
            return []
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при получении всех организаций: {e}")
            return []

    def get_organizations_for_action(self, action_id: int) -> list:
        """Получить все организации, привязанные к конкретному действию (шаблону)."""
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM organizations WHERE action_id = ? ORDER BY name;", (action_id,))
            rows = cursor.fetchall()
            organizations = [dict(row) for row in rows]
            cursor.close()
            conn.close()
            logger.info(f"SQLiteDatabaseManager: Получено {len(organizations)} организаций для действия ID {action_id}.")
            return organizations
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка при получении организаций для действия ID {action_id}: {e}")
            return []
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при получении организаций для действия ID {action_id}: {e}")
            return []

    def create_organization_for_action(self, action_id: int, org_data: dict) -> int:
        """Создать новую организацию для конкретного действия. Возвращает ID новой записи или 0 при ошибке."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO organizations (action_id, name, phone, contact_person, notes) VALUES (?, ?, ?, ?, ?);",
                (
                    action_id,
                    org_data.get('name', ''),
                    org_data.get('phone', None),
                    org_data.get('contact_person', None),
                    org_data.get('notes', None)
                )
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.close()
            conn.close()
            logger.info(f"SQLiteDatabaseManager: Создана организация с ID {new_id} для действия ID {action_id}.")
            return new_id
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка при создании организации для действия ID {action_id}: {e}")
            return 0
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при создании организации для действия ID {action_id}: {e}")
            return 0

    def create_organization(self, org_data: dict) -> int:
        """Создать организацию (для обратной совместимости). Требует action_id в org_data."""
        action_id = org_data.get('action_id', 0)
        if not action_id:
            logger.error("SQLiteDatabaseManager: create_organization требует action_id в org_data.")
            return 0
        return self.create_organization_for_action(action_id, org_data)

    def update_organization(self, org_id: int, org_data: dict) -> bool:
        """Обновить данные организации."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE organizations SET name = ?, phone = ?, contact_person = ?, notes = ?, updated_at = datetime('now', 'localtime') WHERE id = ?;",
                (
                    org_data.get('name', ''),
                    org_data.get('phone', None),
                    org_data.get('contact_person', None),
                    org_data.get('notes', None),
                    org_id
                )
            )
            conn.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            conn.close()
            logger.info(f"SQLiteDatabaseManager: Обновлено {affected_rows} записей организации с ID {org_id}.")
            return affected_rows > 0
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка при обновлении организации: {e}")
            return False
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при обновлении организации: {e}")
            return False

    def delete_organization(self, org_id: int) -> bool:
        """Удалить организацию."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM organizations WHERE id = ?;", (org_id,))
            conn.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            conn.close()
            logger.info(f"SQLiteDatabaseManager: Удалено {affected_rows} организаций с ID {org_id}.")
            return affected_rows > 0
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка при удалении организации: {e}")
            return False
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при удалении организации: {e}")
            return False

    def get_organization_by_id(self, org_id: int) -> dict | None:
        """Получить организацию по ID."""
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM organizations WHERE id = ?;", (org_id,))
            row = cursor.fetchone()
            result = dict(row) if row else None
            cursor.close()
            conn.close()
            return result
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка при получении организации по ID {org_id}: {e}")
            return None
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при получении организации по ID {org_id}: {e}")
            return None

    # ========================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С СПРАВОЧНЫМИ ФАЙЛАМИ ОРГАНИЗАЦИЙ (ШАБЛОНЫ ДЕЙСТВИЙ)
    # ========================================================================

    def get_organization_reference_files(self, org_id: int) -> list:
        """Получить все справочные файлы организации."""
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM organization_files WHERE organization_id = ? ORDER BY file_type, file_path;", (org_id,))
            rows = cursor.fetchall()
            files = [dict(row) for row in rows]
            cursor.close()
            conn.close()
            logger.info(f"SQLiteDatabaseManager: Получено {len(files)} файлов для организации ID {org_id}.")
            return files
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка при получении файлов для организации ID {org_id}: {e}")
            return []
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при получении файлов для организации ID {org_id}: {e}")
            return []

    def get_organization_reference_files_by_id(self, file_id: int) -> list:
        """Получить справочный файл по ID."""
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM organization_files WHERE id = ?;", (file_id,))
            row = cursor.fetchone()
            files = [dict(row)] if row else []
            cursor.close()
            conn.close()
            return files
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка при получении файла по ID {file_id}: {e}")
            return []
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при получении файла по ID {file_id}: {e}")
            return []

    def add_organization_reference_file(self, org_id: int, file_path: str, file_type: str = 'other') -> bool:
        """Добавить справочный файл к организации."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO organization_files (organization_id, file_path, file_type) VALUES (?, ?, ?);",
                (org_id, file_path, file_type)
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.close()
            conn.close()
            logger.info(f"SQLiteDatabaseManager: Добавлен файл с ID {new_id} для организации ID {org_id}.")
            return new_id > 0
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка при добавлении файла для организации ID {org_id}: {e}")
            return False
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при добавлении файла для организации ID {org_id}: {e}")
            return False

    def delete_organization_reference_file(self, file_id: int) -> bool:
        """Удалить справочный файл организации."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM organization_files WHERE id = ?;", (file_id,))
            conn.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            conn.close()
            logger.info(f"SQLiteDatabaseManager: Удалено {affected_rows} файлов с ID {file_id}.")
            return affected_rows > 0
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка при удалении файла ID {file_id}: {e}")
            return False
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при удалении файла ID {file_id}: {e}")
            return False

    # ========================================================================
    # МЕТОДЫ ДЛЯ СВЯЗИ ОРГАНИЗАЦИЙ С ДЕЙСТВИЯМИ (ИСПОЛНЕНИЯ)
    # ========================================================================

    def get_organizations_for_action_execution(self, action_execution_id: int) -> list:
        """Получить все организации, привязанные к выполнению действия."""
        try:
            conn = self._get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT eo.*
                FROM exec_organizations eo
                WHERE eo.action_execution_id = ?
                ORDER BY eo.name;
            """, (action_execution_id,))
            rows = cursor.fetchall()
            organizations = [dict(row) for row in rows]
            cursor.close()
            conn.close()
            logger.info(f"SQLiteDatabaseManager: Получено {len(organizations)} организаций для выполнения действия ID {action_execution_id}.")
            return organizations
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка при получении организаций для выполнения действия ID {action_execution_id}: {e}")
            return []
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при получении организаций для выполнения действия ID {action_execution_id}: {e}")
            return []

    def add_organization_to_action_execution(self, action_execution_id: int, org_data: dict) -> int:
        """Создать организацию для выполнения действия. Возвращает ID новой записи или 0 при ошибке."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO exec_organizations (action_execution_id, name, phone, contact_person, notes) VALUES (?, ?, ?, ?, ?);",
                (
                    action_execution_id,
                    org_data.get('name', ''),
                    org_data.get('phone', None),
                    org_data.get('contact_person', None),
                    org_data.get('notes', None)
                )
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.close()
            conn.close()
            logger.info(f"SQLiteDatabaseManager: Создана организация с ID {new_id} для выполнения действия ID {action_execution_id}.")
            return new_id
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка при создании организации для выполнения действия ID {action_execution_id}: {e}")
            return 0
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при создании организации для выполнения действия ID {action_execution_id}: {e}")
            return 0

    def remove_organization_from_action_execution(self, exec_org_id: int) -> bool:
        """Удалить организацию из выполнения действия."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM exec_organizations WHERE id = ?;",
                (exec_org_id,)
            )
            conn.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            conn.close()
            logger.info(f"SQLiteDatabaseManager: Удалено {affected_rows} организаций из выполнения действия.")
            return affected_rows > 0
        except sqlite3.Error as e:
            logger.error(f"SQLiteDatabaseManager: Ошибка при удалении организации из выполнения действия: {e}")
            return False
        except Exception as e:
            logger.exception(f"SQLiteDatabaseManager: Неизвестная ошибка при удалении организации из выполнения действия: {e}")
            return False
