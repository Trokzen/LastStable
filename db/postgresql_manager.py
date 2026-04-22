# db/postgresql_manager.py
import psycopg2
from psycopg2 import sql
import re
# from psycopg2.extras import RealDictCursor # Для получения результатов как dict
from werkzeug.security import check_password_hash, generate_password_hash
from typing import Optional, Dict, Any, List
import logging
import datetime
from psycopg2.extras import RealDictCursor

# Настройка логирования для отладки
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Или DEBUG для более подробного лога

class PostgreSQLDatabaseManager:
    """
    Класс для управления подключением к базе данных PostgreSQL
    и выполнения запросов, связанных с основной логикой приложения.
    Предполагается, что все объекты БД находятся в схеме 'app_schema'.
    """
    SCHEMA_NAME = 'app_schema' # Имя схемы

    def __init__(self, connection_config: Dict[str, Any]):
        """
        Инициализирует менеджер БД PostgreSQL.
        :param connection_config: Словарь с параметрами подключения
                                  (host, port, dbname, user, password).
        """
        self.connection_config = connection_config
        self.connection = None
        logger.info(f"PostgreSQLDatabaseManager инициализирован. Используется схема: {self.SCHEMA_NAME}")

    def _get_connection(self):
        """
        Создает и возвращает новое подключение к БД.
        В реальном приложении здесь должен быть пул соединений.
        """
        if self.connection is None or self.connection.closed:
            try:
                logger.debug(f"Попытка подключения к PostgreSQL с параметрами: host={self.connection_config['host']}, port={self.connection_config['port']}, dbname={self.connection_config['dbname']}, user={self.connection_config['user']}")
                
                # --- ДОБАВЛЕНО: Отладка значений параметров ---
                # Проверим типы и содержимое каждого параметра
                for key, value in self.connection_config.items():
                    logger.debug(f"  Параметр '{key}': тип={type(value)}, значение='{value}'")
                    # Проверим, нет ли скрытых символов
                    if isinstance(value, str):
                        logger.debug(f"    Длина строки: {len(value)}")
                        logger.debug(f"    Символы: {[ord(c) for c in value]}") # Коды символов
                # --- ---

                # --- ИЗМЕНЕНО: Используем тот же стиль вызова, что и в Flask ---
                # Вместо формирования DSN, передаем параметры напрямую
                # и добавляем client_encoding вручную после подключения
                self.connection = psycopg2.connect(
                    host=self.connection_config['host'],
                    port=self.connection_config['port'],
                    dbname=self.connection_config['dbname'],
                    user=self.connection_config['user'],
                    password=self.connection_config['password']
                )
                logger.debug("Соединение psycopg2 создано (параметры напрямую).")

                # --- ИЗМЕНЕНО: Устанавливаем кодировку после подключения ---
                try:
                    # Сначала проверим, что соединение активно
                    test_cursor = self.connection.cursor()
                    test_cursor.execute("SELECT 1;")
                    test_cursor.fetchone()
                    test_cursor.close()
                    logger.debug("Тестовый запрос после подключения успешен.")

                    self.connection.set_client_encoding('UTF8')
                    logger.info("Кодировка клиента установлена в UTF8 после подключения.")
                except psycopg2.Error as pe:
                    logger.error(f"Ошибка psycopg2 при установке кодировки или тестовом запросе: {pe}")
                    raise
                except Exception as e_set_enc:
                    logger.error(f"Неизвестная ошибка при установке кодировки или тестовом запросе: {e_set_enc}")
                    raise
                # --- ---
                
            except psycopg2.Error as e:
                logger.error(f"Ошибка подключения к PostgreSQL (psycopg2): {e}")
                # Логируем без использования e.diag, чтобы избежать UnicodeDecodeError
                self.connection = None
                raise
            except Exception as e: # Ловим любые другие исключения
                logger.error(f"Неизвестная ошибка при подключении к PostgreSQL: {type(e).__name__}: {e}")
                self.connection = None
                raise
        else:
            logger.debug("Используется существующее подключение к PostgreSQL.")

        return self.connection

    def close_connection(self):
        """Закрывает подключение к БД."""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("Подключение к PostgreSQL закрыто.")

    def test_connection(self) -> bool:
        """
        Тестирует подключение к БД.
        :return: True, если подключение успешно, иначе False.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # --- ИЗМЕНЕНО: Простой запрос вместо SELECT version() ---
            # cursor.execute('SELECT version();')
            # db_version = cursor.fetchone()
            cursor.execute('SELECT 1;') # Очень простой запрос
            test_result = cursor.fetchone()
            # --- ---
            
            # Проверяем, существует ли схема app_schema
            cursor.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s;",
                (self.SCHEMA_NAME,)
            )
            schema_exists = cursor.fetchone()
            
            cursor.close()
            
            # if db_version: # Старая проверка
            if test_result: # Новая проверка
                if schema_exists:
                    # logger.info(f"Тест подключения успешен. Версия БД: {db_version[0] if db_version else 'Неизвестно'}. Схема '{self.SCHEMA_NAME}' найдена.")
                    logger.info(f"Тест подключения успешен. Простой запрос выполнен. Схема '{self.SCHEMA_NAME}' найдена.") # Обновленное сообщение
                    return True
                else:
                    logger.warning(f"Тест подключения успешен, но схема '{self.SCHEMA_NAME}' не найдена.")
                    return False
            else:
                logger.error("Тест подключения не удался: не удалось выполнить простой запрос.")
                return False
                
        except Exception as e:
            logger.error(f"Тест подключения не удался: {e}")
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
            # Используем полное имя таблицы с указанием схемы
            cursor.execute(
                f"SELECT id, login, password_hash, rank, last_name, first_name, middle_name, is_admin FROM {self.SCHEMA_NAME}.users WHERE login = %s AND is_active = TRUE;",
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
                        'is_admin': user_record[7]
                    }
                else:
                    logger.warning(f"Неверный пароль для пользователя '{login}'.")
            else:
                logger.warning(f"Пользователь '{login}' не найден или неактивен.")
            return None
        except psycopg2.Error as e:
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
            # Используем полное имя таблицы с указанием схемы
            cursor.execute(f"SELECT * FROM {self.SCHEMA_NAME}.settings WHERE id = 1;")
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
        except psycopg2.Error as e:
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
                f"SELECT id, login, rank, last_name, first_name, middle_name, phone, is_active, is_admin FROM {self.SCHEMA_NAME}.users ORDER BY rank ASC, last_name ASC, first_name ASC, middle_name ASC;"
            )
            rows = cursor.fetchall()
            # Получаем названия колонок
            colnames = [desc[0] for desc in cursor.description]
            cursor.close()
            
            # Преобразуем список кортежей в список словарей
            users_list = [dict(zip(colnames, row)) for row in rows]
            logger.debug(f"Получен список {len(users_list)} всех пользователей из БД (отсортирован по званию, фамилии, имени, отчеству).")
            return users_list
        except psycopg2.Error as e:
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

            set_clause = ", ".join([f"{key} = %s" for key in fields_to_update])
            values = [settings_data[key] for key in fields_to_update]
            values.append(1) # id = 1
            
            sql_query = f"UPDATE {self.SCHEMA_NAME}.settings SET {set_clause} WHERE id = %s;"
            
            logger.debug(f"Выполнение SQL обновления настроек: {cursor.mogrify(sql_query, values)}")
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
                
        except psycopg2.Error as e:
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
        :param user_ Словарь с данными нового пользователя.
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
            
            # Создаем список %s плейсхолдеров
            placeholders = ['%s'] * len(fields)
            
            # Формируем значения для вставки, обрабатывая типы данных
            values = []
            for field in fields:
                val = user_data.get(field)
                # Обработка булевых полей
                if field in ['is_active', 'is_admin']:
                    # Преобразуем в Python boolean (True/False)
                    values.append(bool(val)) 
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
            # Используем RETURNING id для получения ID нового пользователя
            sql_query = f"INSERT INTO {self.SCHEMA_NAME}.users ({columns_str}) VALUES ({placeholders_str}) RETURNING id;"
            
            logger.debug(f"Выполнение SQL создания пользователя: {cursor.mogrify(sql_query, values)}")
            cursor.execute(sql_query, values)
            new_id_row = cursor.fetchone()
            new_id = new_id_row[0] if new_id_row else None
            conn.commit()
            cursor.close()
            
            if new_id:
                logger.info(f"Новый пользователь успешно создан с ID: {new_id}")
                return new_id
            else:
                logger.error("Не удалось получить ID нового пользователя после вставки.")
                return -1

        except psycopg2.Error as e:
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
        :param user_ Словарь с новыми данными пользователя.
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
                    # Преобразуем в Python boolean
                    values.append(bool(val))
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
                
                set_clauses.append(f"{field} = %s")

            # Добавляем user_id в конец списка значений для WHERE
            values.append(user_id)
            
            # --- Формирование и выполнение SQL-запроса ---
            set_clause_str = ', '.join(set_clauses)
            sql_query = f"UPDATE {self.SCHEMA_NAME}.users SET {set_clause_str} WHERE id = %s;"
            
            logger.debug(f"Выполнение SQL обновления пользователя {user_id}: {cursor.mogrify(sql_query, values)}")
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

        except psycopg2.Error as e:
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
        :param user_id: ID пользователя для удаления.
        :return: True, если успешно, иначе False.
        """
        if not isinstance(user_id, int) or user_id <= 0:
            logger.error("Некорректный ID пользователя для удаления.")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # --- Формирование и выполнение SQL-запроса на удаление ---
            sql_query = f"DELETE FROM {self.SCHEMA_NAME}.users WHERE id = %s;"
            
            logger.debug(f"Выполнение SQL удаления пользователя {user_id}: {cursor.mogrify(sql_query, (user_id,))}")
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

        except psycopg2.Error as e:
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
        :param officer_id: ID должностного лица.
        :return: Словарь с данными или None.
        """
        if not isinstance(officer_id, int) or officer_id <= 0:
            logger.warning("Некорректный ID пользователя для получения.")
            return None

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            # --- Используем полное имя таблицы с указанием схемы ---
            cursor.execute(
                f"SELECT * FROM {self.SCHEMA_NAME}.users WHERE id = %s AND is_active = TRUE;", # Можно убрать is_active = TRUE, если хотите получать всех
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
        except psycopg2.Error as e:
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
            # Предполагается, что в таблице settings есть запись с id=1
            sql_query = f"UPDATE {self.SCHEMA_NAME}.settings SET current_officer_id = %s WHERE id = 1;"
            
            logger.debug(f"Выполнение SQL установки текущего дежурного: {cursor.mogrify(sql_query, (officer_id,))}")
            cursor.execute(sql_query, (officer_id,))
            conn.commit()
            
            rows_affected = cursor.rowcount
            cursor.close()
            
            if rows_affected > 0:
                logger.info(f"Текущий дежурный успешно установлен в настройках: ID {officer_id}")
                return True
            else:
                logger.warning(f"Не удалось установить текущего дежурного: запись settings (id=1) не найдена или ID {officer_id} не изменился.")
                return False

        except psycopg2.Error as e:
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
        Получает список всех алгоритмов, отсортированных по названию.
        :return: Список словарей с данными алгоритмов.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT id, name, category, time_type, description, created_at, updated_at FROM {self.SCHEMA_NAME}.algorithms ORDER BY sort_order ASC;"
            )
            rows = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]
            cursor.close()
            algorithms_list = [dict(zip(colnames, row)) for row in rows]
            logger.debug(f"Получен список {len(algorithms_list)} алгоритмов из БД.")
            return algorithms_list
        except psycopg2.Error as e:
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
        if not self.connection:
            print("PostgreSQLDatabaseManager: Нет подключения к БД.")
            return -1

        if not algorithm_data:
            print("PostgreSQLDatabaseManager: Попытка создания алгоритма с пустыми данными.")
            return -1

        required_fields = ['name', 'category', 'time_type']
        missing_fields = [field for field in required_fields if not algorithm_data.get(field)]
        if missing_fields:
            print(f"PostgreSQLDatabaseManager: Отсутствуют обязательные поля для создания алгоритма: {missing_fields}")
            return -1

        try:
            with self.connection.cursor() as cursor:
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
                    print("PostgreSQLDatabaseManager: Нет данных для вставки.")
                    return -1

                # --- Формирование SQL-запроса ---
                columns = list(prepared_data.keys())
                placeholders = ['%s'] * len(columns)
                columns_str = ', '.join(columns)
                placeholders_str = ', '.join(placeholders)
                values = list(prepared_data.values())

                sql_query = f"""
                    INSERT INTO {self.SCHEMA_NAME}.algorithms ({columns_str})
                    VALUES ({placeholders_str})
                    RETURNING id;
                """
                print(f"PostgreSQLDatabaseManager: Выполнение SQL создания алгоритма: {cursor.mogrify(sql_query, values)}")
                cursor.execute(sql_query, values)
                new_id_row = cursor.fetchone()
                new_id = new_id_row[0] if new_id_row else None
                # --- ---

                if new_id:
                    # --- НОВОЕ: Установка уникального sort_order ---
                    print(f"PostgreSQLDatabaseManager: Новый алгоритм создан с ID: {new_id}. Установка уникального sort_order...")
                    # Получаем максимальный существующий sort_order
                    cursor.execute(f"SELECT COALESCE(MAX(sort_order), 0) FROM {self.SCHEMA_NAME}.algorithms;")
                    max_sort_order_row = cursor.fetchone()
                    max_sort_order = max_sort_order_row[0] if max_sort_order_row else 0
                    new_sort_order = max_sort_order + 1
                    print(f"PostgreSQLDatabaseManager: Максимальный sort_order: {max_sort_order}. Новый sort_order для ID {new_id}: {new_sort_order}")
                    # Обновляем sort_order для нового алгоритма
                    cursor.execute(f"UPDATE {self.SCHEMA_NAME}.algorithms SET sort_order = %s WHERE id = %s;", (new_sort_order, new_id))
                    # --- ---
                    self.connection.commit()
                    print(f"PostgreSQLDatabaseManager: Алгоритм ID {new_id} успешно создан и sort_order установлен на {new_sort_order}.")
                    return new_id
                else:
                    print("PostgreSQLDatabaseManager: Не удалось получить ID нового алгоритма после вставки.")
                    self.connection.rollback()
                    return -1
        except psycopg2.Error as e:
            print(f"PostgreSQLDatabaseManager: Ошибка БД при создании алгоритма: {e}")
            self.connection.rollback()
            import traceback
            traceback.print_exc()
            return -1
        except Exception as e:
            print(f"PostgreSQLDatabaseManager: Неизвестная ошибка при создании алгоритма: {e}")
            self.connection.rollback()
            import traceback
            traceback.print_exc()
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

            set_clauses = [f"{field} = %s" for field in fields_to_update]
            values = [algorithm_data[field] for field in fields_to_update]
            values.append(algorithm_id)
            
            set_clause_str = ', '.join(set_clauses)
            sql_query = f"UPDATE {self.SCHEMA_NAME}.algorithms SET {set_clause_str} WHERE id = %s;"
            
            logger.debug(f"Выполнение SQL обновления алгоритма {algorithm_id}: {cursor.mogrify(sql_query, values)}")
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

        except psycopg2.Error as e:
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
        if not self.connection:
            print("PostgreSQLDatabaseManager: Нет подключения к БД.")
            return False

        if not isinstance(algorithm_id, int) or algorithm_id <= 0:
            print(f"PostgreSQLDatabaseManager: Некорректный ID алгоритма: {algorithm_id}")
            return False

        try:
            with self.connection.cursor() as cursor:
                print(f"PostgreSQLDatabaseManager: Удаление алгоритма ID {algorithm_id} и всех связанных записей (CASCADE)...")
                # --- ИЗМЕНЕНО: Простое удаление с CASCADE ---
                query = f"DELETE FROM {self.SCHEMA_NAME}.algorithms WHERE id = %s;"
                # Предполагается, что ограничения внешних ключей для actions, algorithm_executions, action_executions
                # были созданы с ON DELETE CASCADE.
                cursor.execute(query, (algorithm_id,))
                rows_affected = cursor.rowcount
                self.connection.commit()

                if rows_affected > 0:
                    print(f"PostgreSQLDatabaseManager: Алгоритм ID {algorithm_id} и все связанные записи успешно удалены. Затронуто строк: {rows_affected}.")
                    return True
                else:
                    print(f"PostgreSQLDatabaseManager: Алгоритм ID {algorithm_id} не найден для удаления.")
                    return False
        except psycopg2.Error as e:
            print(f"PostgreSQLDatabaseManager: Ошибка БД при удалении алгоритма {algorithm_id}: {e}")
            self.connection.rollback()
            import traceback
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"PostgreSQLDatabaseManager: Неизвестная ошибка при удалении алгоритма {algorithm_id}: {e}")
            self.connection.rollback()
            import traceback
            traceback.print_exc()
            return False

# db/postgresql_manager.py

# ... (другие методы класса PostgreSQLDatabaseManager) ...

    def duplicate_algorithm(self, original_algorithm_id: int) -> int:
        """
        Создает копию существующего алгоритма и всех его действий, организаций и файлов организаций.

        :param original_algorithm_id: ID оригинального алгоритма.
        :return: ID нового алгоритма, если успешно, иначе -1.
        """
        if not self.connection:
            print("PostgreSQLDatabaseManager: Нет подключения к БД.")
            return -1

        if not isinstance(original_algorithm_id, int) or original_algorithm_id <= 0:
            print(f"PostgreSQLDatabaseManager: Некорректный ID оригинального алгоритма: {original_algorithm_id}")
            return -1

        try:
            with self.connection.cursor() as cursor:
                # 1. Получаем данные оригинального алгоритма
                cursor.execute("""
                    SELECT id, name, category, time_type, description
                    FROM {self.SCHEMA_NAME}.algorithms WHERE id = %s
                """.format(self=self), (original_algorithm_id,))
                original_algorithm_row = cursor.fetchone()
                if not original_algorithm_row:
                    print(f"PostgreSQLDatabaseManager: Оригинальный алгоритм с ID {original_algorithm_id} не найден.")
                    return -1

                original_algorithm = {
                    'id': original_algorithm_row[0],
                    'name': original_algorithm_row[1],
                    'category': original_algorithm_row[2],
                    'time_type': original_algorithm_row[3],
                    'description': original_algorithm_row[4]
                }
                print(f"PostgreSQLDatabaseManager: Найден оригинальный алгоритм ID {original_algorithm_id}: {original_algorithm['name']}")

                # 2. Формируем данные для нового алгоритма
                original_name = original_algorithm.get('name', 'Алгоритм')
                new_name = f"{original_name} (Копия)"
                new_algorithm_data = {
                    'name': new_name,
                    'category': original_algorithm['category'],
                    'time_type': original_algorithm['time_type'],
                    'description': original_algorithm.get('description', '')
                }

                # 3. Создаем новый алгоритм в БД
                print(f"PostgreSQLDatabaseManager: Создание нового алгоритма (копии) с данными: {new_algorithm_data}")
                new_algorithm_id = self.create_algorithm(new_algorithm_data)
                if isinstance(new_algorithm_id, int) and new_algorithm_id > 0:
                    print(f"PostgreSQLDatabaseManager: Алгоритм ID {original_algorithm_id} успешно дублирован. Новый ID: {new_algorithm_id}")
                    
                    # 4. Дублируем действия оригинального алгоритма
                    cursor.execute("""
                        SELECT id, description, technical_text, start_offset, end_offset, contact_phones, report_materials
                        FROM {self.SCHEMA_NAME}.actions WHERE algorithm_id = %s ORDER BY start_offset
                    """.format(self=self), (original_algorithm_id,))
                    original_actions_rows = cursor.fetchall()

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
                        print(f"PostgreSQLDatabaseManager: Дублирование действия ID {original_action['id']}...")
                        
                        new_action_data = {
                            'algorithm_id': new_algorithm_id,
                            'description': f"{original_action.get('description', '')} (Копия)",
                            'technical_text': original_action.get('technical_text', ''),
                            'start_offset': original_action.get('start_offset'),
                            'end_offset': original_action.get('end_offset'),
                            'contact_phones': original_action.get('contact_phones'),
                            'report_materials': original_action.get('report_materials')
                        }
                        
                        new_action_id = self.create_action(new_action_data)
                        if isinstance(new_action_id, int) and new_action_id > 0:
                            print(f"PostgreSQLDatabaseManager: Действие ID {original_action['id']} дублировано как ID {new_action_id} для нового алгоритма {new_algorithm_id}.")
                            actions_duplicated_count += 1
                            
                            # 5. Дублируем организации и файлы организаций для нового действия
                            self._duplicate_action_organizations_and_files(original_action['id'], new_action_id)
                        else:
                            print(f"PostgreSQLDatabaseManager: Не удалось дублировать действие ID {original_action['id']} для алгоритма {new_algorithm_id}.")
                    
                    print(f"PostgreSQLDatabaseManager: Для нового алгоритма ID {new_algorithm_id} дублировано {actions_duplicated_count} из {len(original_actions)} действий.")
                    self.connection.commit()
                    return new_algorithm_id
                else:
                    print(f"PostgreSQLDatabaseManager: Ошибка при создании нового алгоритма (копии). Результат create_algorithm: {new_algorithm_id}")
                    self.connection.rollback()
                    return -1
        except psycopg2.Error as e:
            print(f"PostgreSQLDatabaseManager: Ошибка БД при дублировании алгоритма {original_algorithm_id}: {e}")
            self.connection.rollback()
            import traceback
            traceback.print_exc()
            return -1
        except Exception as e:
            print(f"PostgreSQLDatabaseManager: Неизвестная ошибка при дублировании алгоритма {original_algorithm_id}: {e}")
            self.connection.rollback()
            import traceback
            traceback.print_exc()
            return -1

# ... (другие методы класса PostgreSQLDatabaseManager) ...


    # --- МЕТОДЫ ДЛЯ РАБОТЫ С ACTIONS ---

    def get_actions_by_algorithm_id(self, algorithm_id: int) -> List[Dict[str, Any]]:
        """
        Получает список всех действий для заданного алгоритма, отсортированных по start_offset.
        :param algorithm_id: ID алгоритма.
        :return: Список словарей с данными действий.
        """
        if not isinstance(algorithm_id, int) or algorithm_id <= 0:
            logger.warning("Некорректный ID алгоритма для получения действий.")
            return []

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            # Используем полное имя таблицы с указанием схемы
            cursor.execute(
                f"SELECT id, algorithm_id, description, start_offset, end_offset, contact_phones, report_materials, created_at, updated_at "
                f"FROM {self.SCHEMA_NAME}.actions "
                f"WHERE algorithm_id = %s "
                f"ORDER BY start_offset ASC, end_offset ASC, id ASC;",
                (algorithm_id,)
            )
            rows = cursor.fetchall()
            # Получаем названия колонок
            colnames = [desc[0] for desc in cursor.description]
            cursor.close()
            
            # --- ИЗМЕНЕНО: Преобразование timedelta в строки ---
            actions_list = []
            for row in rows:
                # Создаем словарь из строки результата
                action_dict = dict(zip(colnames, row))
                
                # Преобразуем start_offset и end_offset, если они являются timedelta
                for time_field in ['start_offset', 'end_offset']:
                    if isinstance(action_dict[time_field], datetime.timedelta):
                        # timedelta можно преобразовать в строку в формате, понятном QML
                        # Например, "1 day, 2:30:45" -> "1 day 02:30:45"
                        # Или можно использовать strftime, если нужно определенное форматирование
                        # Для простоты используем стандартное строковое представление
                        # action_dict[time_field] = str(action_dict[time_field]) 
                        # Или более контролируемый формат:
                        td = action_dict[time_field]
                        # Форматируем как "DD:HH:MM:SS"
                        days = td.days
                        hours, remainder = divmod(td.seconds, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        action_dict[time_field] = f"{days}:{hours:02d}:{minutes:02d}:{seconds:02d}"
                        logger.debug(f"Преобразован {time_field} из timedelta в строку: {action_dict[time_field]}")
                    elif action_dict[time_field] is None:
                         # Если значение NULL в БД, преобразуем в пустую строку или оставляем None
                         # В зависимости от вашей логики в QML
                         action_dict[time_field] = "" # или None
                         logger.debug(f"{time_field} был None, преобразован в пустую строку")
                    else:
                        # Если это уже строка (например, из интервала типа '1 hour 30 minutes'),
                        # оставляем как есть или преобразуем в строку принудительно
                        action_dict[time_field] = str(action_dict[time_field])
                        
                actions_list.append(action_dict)
            # --- ---
            
            logger.debug(f"Получен список {len(actions_list)} действий для алгоритма ID {algorithm_id}.")
            return actions_list
        except psycopg2.Error as e:
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
                f"SELECT id, algorithm_id, description, start_offset, end_offset, contact_phones, report_materials FROM {self.SCHEMA_NAME}.actions WHERE id = %s;",
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
        except psycopg2.Error as e:
            logger.error(f"Ошибка БД при получении данных действия по ID {action_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка при получении данных действия по ID {action_id}: {e}")
            return None

    def _convert_time_string_to_interval(self, time_str: str) -> str:
        """
        Преобразует строку времени формата 'dd:hh:mm:ss' или 'hh:mm:ss' 
        в формат INTERVAL PostgreSQL, например '1 day 02:30:45' или '02:30:45'.
        Также поддерж��вает 'dd:h:m:s' (без ведущих нулей).
        :param time_str: Строка времени.
        :return: Форматированная строка INTERVAL для PostgreSQL или исходная строка, если формат не распознан.
        """
        if not time_str:
            return '0 seconds' 

        # 1. Попробуем сначала формат dd:hh:mm:ss (с ведущими нулями или без)
        # Регулярное выражение для dd:hh:mm:ss или dd:h:m:s
        # \d+ - один или более цифр для дней
        # \d{1,2} - одна или две цифры для часов/минут/секунд
        match_dd_hh_mm_ss = re.fullmatch(r'(\d+):(\d{1,2}):(\d{1,2}):(\d{1,2})', time_str)
        if match_dd_hh_mm_ss:
            days, hours, minutes, seconds = match_dd_hh_mm_ss.groups()
            days_int = int(days)
            hours_int = int(hours)
            minutes_int = int(minutes)
            seconds_int = int(seconds)
            
            # Формируем строку для PostgreSQL
            interval_parts = []
            if days_int > 0:
                interval_parts.append(f"{days_int} day{'s' if days_int != 1 else ''}")
            
            # Форматируем время как HH:MM:SS с ведущими нулями
            time_part = f"{hours_int:02d}:{minutes_int:02d}:{seconds_int:02d}"
            interval_parts.append(time_part)
            
            return " ".join(interval_parts) # Например: "1 day 02:30:45"

        # 2. Попробуем формат hh:mm:ss (с ведущими нулями или без)
        # \d{1,2} - одна или две цифры
        match_hh_mm_ss = re.fullmatch(r'(\d{1,2}):(\d{1,2}):(\d{1,2})', time_str)
        if match_hh_mm_ss:
            hours, minutes, seconds = match_hh_mm_ss.groups()
            # Форматируем как HH:MM:SS с ведущими нулями, это должно быть понятно PostgreSQL
            return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}" 
            
        # Если формат не распознан, возвращаем исходную строку
        logger.warning(f"Нераспознанный формат времени '{time_str}'. Передаю как есть.")
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
            logger.warning("Попытка создания действия с пустыми данными.")
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
            # Определяем поля, которые будут вставлены
            allowed_fields = ['algorithm_id', 'description', 'technical_text', 'start_offset', 'end_offset', 'contact_phones', 'report_materials']
            fields = [field for field in allowed_fields if field in action_data]

            # Создаем список ? плейсхолдеров
            placeholders = ['%s'] * len(fields)
            
            # Формируем значения для вставки, обрабатывая типы данных
            values = []
            for field in fields:
                val = action_data.get(field)
                # --- ДОБАВЛЕНО: Преобразование времени ---
                if field in ['start_offset', 'end_offset']:
                    # Преобразуем строку времени в формат INTERVAL PostgreSQL
                    formatted_interval = self._convert_time_string_to_interval(str(val) if val is not None else "")
                    values.append(formatted_interval) # Передаем преобразованную строку
                    logger.debug(f"Преобразовано {field} из '{val}' в INTERVAL '{formatted_interval}'")
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
            # Используем RETURNING id для получения ID нового пользователя
            sql_query = f"INSERT INTO {self.SCHEMA_NAME}.actions ({columns_str}) VALUES ({placeholders_str}) RETURNING id;"
            
            logger.debug(f"Выполнение SQL создания действия: {cursor.mogrify(sql_query, values)}")
            cursor.execute(sql_query, values)
            new_id_row = cursor.fetchone()
            new_id = new_id_row[0] if new_id_row else None
            conn.commit()
            cursor.close()
            
            if new_id:
                logger.info(f"Новое действие успешно создано с ID: {new_id}")
                return new_id
            else:
                logger.error("Не удалось получить ID нового действия после вставки.")
                return -1

        except psycopg2.Error as e:
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
            
            if not fields_to_update:
                logger.warning("Нет полей для обновления действия.")
                return False

            set_clauses = []
            values = []
            for field in fields_to_update:
                val = action_data.get(field)
                # --- ДОБАВЛЕНО: Преобразование времени ---
                if field in ['start_offset', 'end_offset']:
                    # Преобразуем строку времени в формат INTERVAL PostgreSQL
                    formatted_interval = self._convert_time_string_to_interval(str(val) if val is not None else "")
                    values.append(formatted_interval) # Передаем преобразованную строку
                    logger.debug(f"Преобразовано {field} из '{val}' в INTERVAL '{formatted_interval}'")
                # --- ---
                else: # algorithm_id, description, contact_phones, report_materials
                    # Обработка текстовых полей: пустая строка -> None -> NULL
                    processed_val = val if val is not None else None
                    if isinstance(processed_val, str) and processed_val == "":
                         processed_val = None
                    values.append(processed_val)
                
                set_clauses.append(f"{field} = %s")

            # Добавляем action_id в конец списка значений для WHERE
            values.append(action_id)
            # --- ---

            # ... (формирование и выполнение SQL-запроса) ...
            
            set_clause_str = ', '.join(set_clauses)
            sql_query = f"UPDATE {self.SCHEMA_NAME}.actions SET {set_clause_str} WHERE id = %s;"
            
            logger.debug(f"Выполнение SQL обновления действия {action_id}: {cursor.mogrify(sql_query, values)}")
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

        except psycopg2.Error as e:
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

            sql_query = f"DELETE FROM {self.SCHEMA_NAME}.actions WHERE id = %s;"
            
            logger.debug(f"Выполнение SQL удаления действия {action_id}: {cursor.mogrify(sql_query, (action_id,))}")
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

        except psycopg2.IntegrityError as e:
            # Это может произойти, если есть action_executions
            logger.error(f"Ошибка целостности БД при удалении действия {action_id} (возможно, есть выполнения): {e}")
            if conn:
                conn.rollback()
            return False
        except psycopg2.Error as e:
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
            'description': f"{original_action['description']} (Копия)",
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
    # --- ---
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
                f"SELECT sort_order FROM {self.SCHEMA_NAME}.algorithms WHERE id = %s;",
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
                f"SELECT id, sort_order FROM {self.SCHEMA_NAME}.algorithms WHERE sort_order = %s;",
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
                    f"UPDATE {self.SCHEMA_NAME}.algorithms SET sort_order = %s WHERE id = %s;",
                    (swap_sort_order, algorithm_id)
                )
                # Обновляем sort_order у алгоритма, с которым меняемся
                cursor.execute(
                    f"UPDATE {self.SCHEMA_NAME}.algorithms SET sort_order = %s WHERE id = %s;",
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
                    f"UPDATE {self.SCHEMA_NAME}.algorithms SET sort_order = sort_order - 1 WHERE id = %s;",
                    (algorithm_id,)
                )
                conn.commit()
                cursor.close()
                logger.info(f"Алгоритм ID {algorithm_id} успешно перемещен вверх (sort_order уменьшен на 1).")
                return True

        except psycopg2.Error as e:
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
                f"SELECT sort_order FROM {self.SCHEMA_NAME}.algorithms WHERE id = %s;",
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
                f"SELECT id, sort_order FROM {self.SCHEMA_NAME}.algorithms WHERE sort_order = %s;",
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
                    f"UPDATE {self.SCHEMA_NAME}.algorithms SET sort_order = %s WHERE id = %s;",
                    (swap_sort_order, algorithm_id)
                )
                # Обновляем sort_order у алгоритма, с которым меняемся
                cursor.execute(
                    f"UPDATE {self.SCHEMA_NAME}.algorithms SET sort_order = %s WHERE id = %s;",
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
                    f"UPDATE {self.SCHEMA_NAME}.algorithms SET sort_order = sort_order + 1 WHERE id = %s;",
                    (algorithm_id,)
                )
                conn.commit()
                cursor.close()
                logger.info(f"Алгоритм ID {algorithm_id} успешно перемещен вниз (sort_order увеличен на 1).")
                return True

        except psycopg2.Error as e:
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
            
            # --- ИЗМЕНЕНО: SQL-запрос БЕЗ фильтрации по status ---
            # Используем CAST(started_at AS DATE) для извлечения даты из timestamp
            # LEFT JOIN users для получения имени ответственного, даже если пользователь удален
            sql_query = f"""
            SELECT 
                ae.id,
                ae.algorithm_id,
                a.name AS algorithm_name,
                ae.started_at,
                TO_CHAR(ae.started_at, 'DD.MM.YYYY HH24:MI:SS') AS started_at_display,
                ae.completed_at,
                CASE 
                    WHEN ae.completed_at IS NOT NULL THEN TO_CHAR(ae.completed_at, 'DD.MM.YYYY HH24:MI:SS')
                    ELSE NULL
                END AS completed_at_display,
                ae.status,
                ae.created_by_user_id,
                COALESCE(u.last_name || ' ' || u.first_name || ' ' || u.middle_name, 'Неизвестен') AS created_by_user_display_name
            FROM {self.SCHEMA_NAME}.algorithm_executions ae
            JOIN {self.SCHEMA_NAME}.algorithms a ON ae.algorithm_id = a.id
            LEFT JOIN {self.SCHEMA_NAME}.users u ON ae.created_by_user_id = u.id
            WHERE CAST(ae.started_at AS DATE) = %s
            ORDER BY ae.started_at DESC;
            """
            # --- ---
            
            logger.debug(f"Выполнение SQL получения ВСЕХ execution'ов за дату '{date_string}': {cursor.mogrify(sql_query, (date_string,))}")
            cursor.execute(sql_query, (date_string,))
            rows = cursor.fetchall()
            # Получаем названия колонок
            colnames = [desc[0] for desc in cursor.description]
            cursor.close()
            
            # Преобразуем список кортежей в список словарей
            executions_list = [dict(zip(colnames, row)) for row in rows]
            logger.info(f"Получен список {len(executions_list)} ВСЕХ execution'ов за дату '{date_string}' из БД.")
            return executions_list
            
        except psycopg2.Error as e:
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
        if not self.connection:
            print("PostgreSQLDatabaseManager: Нет подключения к БД.")
            return []

        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Запрос к таблице algorithm_executions, фильтруем по snapshot_category и status
                query = """
                    SELECT
                        id,
                        algorithm_id, -- Ссылка на оригинальный алгоритм
                        snapshot_name AS algorithm_name, -- Имя из snapshot'а
                        snapshot_category AS category, -- Категория из snapshot'а
                        started_at,
                        TO_CHAR(started_at, 'DD.MM.YYYY HH24:MI:SS') AS started_at_display, -- <-- НОВОЕ: Отформатированное значение
                        completed_at,
                        status,
                        created_by_user_id, -- ID пользователя на момент запуска
                        created_by_user_display_name -- Отображаемое имя на момент запуска
                    FROM app_schema.algorithm_executions
                    WHERE snapshot_category = %s AND status = 'active'
                    ORDER BY started_at DESC; -- Сортируем по времени запуска, например
                """
                cursor.execute(query, (category,))
                rows = cursor.fetchall()

                # Преобразуем результаты в список словарей
                executions = [dict(row) for row in rows]
                print(f"PostgreSQLDatabaseManager: Найдено {len(executions)} активных executions для категории '{category}'.")
                return executions
        except psycopg2.Error as e:
            print(f"PostgreSQLDatabaseManager: Ошибка при получении активных executions для категории '{category}': {e}")
            import traceback
            traceback.print_exc()
            return []
        except Exception as e:
            print(f"PostgreSQLDatabaseManager: Неизвестная ошибка при получении активных executions: {e}")
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
        if not self.connection:
            print("PostgreSQLDatabaseManager: Нет подключения к БД.")
            return False

        if not isinstance(execution_id, int) or execution_id <= 0:
            print(f"PostgreSQLDatabaseManager: Некорректный ID execution: {execution_id}")
            return False

        # --- ДОБАВЛЕНО: Проверка типа local_completed_at_dt ---
        if not isinstance(local_completed_at_dt, datetime.datetime):
             print(f"PostgreSQLDatabaseManager: Ошибка - local_completed_at_dt должен быть datetime.datetime, а не {type(local_completed_at_dt)}.")
             return False
        # --- ---

        try:
            with self.connection.cursor() as cursor:
                # --- ИЗМЕНЕНО: Используем переданное local_completed_at_dt ---
                # 1. Обновляем статус и время завершения algorithm_execution
                query_algorithm = """
                    UPDATE app_schema.algorithm_executions
                    SET status = 'completed', completed_at = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND status = 'active'; -- Обновляем только если статус был 'active'
                """
                # Передаём local_completed_at_dt как параметр в запрос
                cursor.execute(query_algorithm, (local_completed_at_dt, execution_id))
                rows_affected_algorithm = cursor.rowcount
                # --- ---
                
                if rows_affected_algorithm > 0:
                    print(f"PostgreSQLDatabaseManager: Execution ID {execution_id} успешно остановлен. Время завершения: {local_completed_at_dt}")
                    
                    # --- НОВОЕ: Обновляем статусы action_executions ---
                    # 2. Находим все action_executions для этого execution_id, которые ещё не завершены
                    query_select_actions = """
                        SELECT id, status, actual_end_time
                        FROM app_schema.action_executions
                        WHERE execution_id = %s AND status != 'completed'
                    """
                    cursor.execute(query_select_actions, (execution_id,))
                    uncompleted_actions = cursor.fetchall()
                    
                    if uncompleted_actions:
                        print(f"PostgreSQLDatabaseManager: Найдено {len(uncompleted_actions)} незавершённых action_executions для execution ID {execution_id}. Устанавливаем им статус 'skipped'.")
                        
                        # 3. Обновляем статус и actual_end_time для каждого из них
                        action_ids_to_skip = [action[0] for action in uncompleted_actions]
                        # Создаем строку с плейсхолдерами для IN (%s,%s,...)
                        placeholders = ','.join(['%s'] * len(action_ids_to_skip))
                        
                        query_update_actions = f"""
                            UPDATE app_schema.action_executions
                            SET status = 'skipped', actual_end_time = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id IN ({placeholders})
                        """
                        # Передаём local_completed_at_dt как время завершения для всех пропущенных действий
                        cursor.execute(query_update_actions, (local_completed_at_dt,) + tuple(action_ids_to_skip))
                        rows_affected_actions = cursor.rowcount
                        print(f"PostgreSQLDatabaseManager: Обновлено {rows_affected_actions} action_executions на статус 'skipped'.")
                    else:
                        print(f"PostgreSQLDatabaseManager: Для execution ID {execution_id} нет незавершённых action_executions. Пропуск обновления действий.")
                    # --- ---
                    
                    self.connection.commit()
                    return True
                else:
                    print(f"PostgreSQLDatabaseManager: Execution ID {execution_id} не найден или уже был остановлен.")
                    self.connection.rollback() # Откатываем, если ничего не изменилось
                    return False
        except psycopg2.Error as e:
            print(f"PostgreSQLDatabaseManager: Ошибка при остановке execution ID {execution_id}: {e}")
            self.connection.rollback()
            import traceback
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"PostgreSQLDatabaseManager: Неизвестная ошибка при остановке execution ID {execution_id}: {e}")
            self.connection.rollback()
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
        if not self.connection:
            print("PostgreSQLDatabaseManager: Нет подключения к БД.")
            return -1

        try:
            with self.connection.cursor() as cursor:
                # 1. Получить оригинальный алгоритм и его действия
                # --- ИЗМЕНЕНО: Получаем time_type ---
                cursor.execute("""
                    SELECT id, name, category, time_type, description
                    FROM app_schema.algorithms WHERE id = %s
                """, (algorithm_id,))
                algorithm_row = cursor.fetchone()
                # --- ---
                if not algorithm_row:
                    print(f"PostgreSQLDatabaseManager: Алгоритм с ID {algorithm_id} не найден.")
                    return -1

                # --- ИЗМЕНЕНО: Явное создание словаря и извлечение time_type ---
                original_algorithm = {
                    'id': algorithm_row[0],
                    'name': algorithm_row[1],
                    'category': algorithm_row[2],
                    'time_type': algorithm_row[3], # <-- ВАЖНО
                    'description': algorithm_row[4]
                }
                algorithm_time_type = original_algorithm['time_type'] # <-- Сохраняем тип времени
                print(f"PostgreSQLDatabaseManager: Запуск алгоритма ID {algorithm_id} с time_type '{algorithm_time_type}'.")
                # --- ---

                cursor.execute("""
                    SELECT id, description, start_offset, end_offset, contact_phones, report_materials
                    FROM app_schema.actions WHERE algorithm_id = %s ORDER BY start_offset
                """, (algorithm_id,))
                original_actions_raw = cursor.fetchall()
                # Преобразуем в список словарей
                original_actions = []
                for action_row in original_actions_raw:
                    action_dict = {
                        'id': action_row[0],
                        'description': action_row[1],
                        'start_offset': action_row[2], # Это будет timedelta или None
                        'end_offset': action_row[3],   # Это будет timedelta или None
                        'contact_phones': action_row[4],
                        'report_materials': action_row[5]
                    }
                    original_actions.append(action_dict)
                print(f"PostgreSQLDatabaseManager: Получено {len(original_actions)} действий для алгоритма {algorithm_id}.")

                # 2. Получить информацию о пользователе на момент запуска
                cursor.execute("""
                    SELECT rank, last_name, first_name, middle_name
                    FROM app_schema.users WHERE id = %s
                """, (created_by_user_id,))
                user_row = cursor.fetchone()
                if not user_row:
                     print(f"PostgreSQLDatabaseManager: Пользователь с ID {created_by_user_id} не найден для execution.")
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
                    INSERT INTO app_schema.algorithm_executions (
                        algorithm_id,
                        snapshot_name, snapshot_category, snapshot_time_type, snapshot_description,
                        started_at,
                        created_by_user_id, created_by_user_display_name
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    original_algorithm['id'],
                    original_algorithm['name'], original_algorithm['category'], original_algorithm['time_type'], original_algorithm['description'],
                    started_at_str, # 'YYYY-MM-DD HH:MM:SS' или объект datetime
                    created_by_user_id, display_name
                ))
                new_execution_id = cursor.fetchone()[0]
                print(f"PostgreSQLDatabaseManager: Создан новый execution ID {new_execution_id} для алгоритма {algorithm_id}.")

                # 4. Вставить action_executions (snapshot'ы действий)
                # Рассчитываем абсолютные времена на основе started_at и смещений
                import datetime
                started_at_dt = datetime.datetime.fromisoformat(started_at_str.replace(' ', 'T'))
                print(f"PostgreSQLDatabaseManager: Абсолютное время запуска алгоритма: {started_at_dt}.")

                for action in original_actions:
                    calculated_start_time = None
                    calculated_end_time = None
                    
                    # --- ИЗМЕНЕНО: Логика в зависимости от time_type ---
                    if action['start_offset'] is not None:
                        if algorithm_time_type == 'астрономическое':
                            # --- ЛОГИКА ДЛЯ АСТРОНОМИЧЕСКОГО (ИСПРАВЛЕНО) ---
                            print(f"PostgreSQLDatabaseManager: Рассчитываем calculated_start_time для астрономического времени действия ID {action['id']}.")
                            start_date_only = started_at_dt.date()
                            offset_timedelta_start = action['start_offset']
                            
                            if isinstance(offset_timedelta_start, datetime.timedelta):
                                # --- ИЗМЕНЕНО: Извлекаем "время суток" и дни ---
                                total_seconds = int(offset_timedelta_start.total_seconds())
                                seconds_in_day = 24 * 60 * 60 # 86400
                                
                                # Количество полных дней в смещении
                                days = total_seconds // seconds_in_day
                                # Остаток секунд для "времени суток"
                                total_seconds_in_day = total_seconds % seconds_in_day
                                
                                # Извлекаем часы, минуты, секунды из остатка
                                hours = total_seconds_in_day // 3600
                                minutes = (total_seconds_in_day % 3600) // 60
                                seconds = total_seconds_in_day % 60
                                # --- ---
                                
                                # Создаем новое datetime: дата_запуска + дни + время_из_смещения
                                # datetime.timedelta(days=days) корректно обработает переходы через месяцы/годы
                                calculated_start_time = datetime.datetime.combine(
                                    start_date_only,
                                    datetime.time(hour=hours, minute=minutes, second=seconds)
                                ) + datetime.timedelta(days=days)
                                print(f"PostgreSQLDatabaseManager:   Дата запуска: {start_date_only}, Дни: {days}, Время из смещения: {hours:02d}:{minutes:02d}:{seconds:02d}")
                                print(f"PostgreSQLDatabaseManager:   Результат calculated_start_time: {calculated_start_time}")
                            else:
                                print(f"PostgreSQLDatabaseManager: Ошибка - start_offset для действия {action['id']} не является timedelta: {type(offset_timedelta_start)}. Устанавливаю None.")
                                calculated_start_time = None
                            # --- ---
                        else:
                            # --- ЛОГИКА ДЛЯ ОПЕРАТИВНОГО ---
                            print(f"PostgreSQLDatabaseManager: Рассчитываем calculated_start_time для оперативного времени действия ID {action['id']}.")
                            calculated_start_time = started_at_dt + action['start_offset']
                            print(f"PostgreSQLDatabaseManager:   started_at_dt ({started_at_dt}) + start_offset ({action['start_offset']}) = {calculated_start_time}")
                            # --- ---
                    # --- ---
                    if action['end_offset'] is not None:
                        if algorithm_time_type == 'астрономическое':
                            # --- ЛОГИКА ДЛЯ АСТРОНОМИЧЕСКОГО (ИСПРАВЛЕНО) ---
                            print(f"PostgreSQLDatabaseManager: Рассчитываем calculated_end_time для астрономического времени действия ID {action['id']}.")
                            start_date_only = started_at_dt.date()
                            offset_timedelta_end = action['end_offset']
                            
                            if isinstance(offset_timedelta_end, datetime.timedelta):
                                # --- ИЗМЕНЕНО: Извлекаем "время суток" и дни ---
                                total_seconds = int(offset_timedelta_end.total_seconds())
                                seconds_in_day = 24 * 60 * 60 # 86400
                                
                                # Количество полных дней в смещении
                                days = total_seconds // seconds_in_day
                                # Остаток секунд для "времени суток"
                                total_seconds_in_day = total_seconds % seconds_in_day
                                
                                # Извлекаем часы, минуты, секунды из остатка
                                hours = total_seconds_in_day // 3600
                                minutes = (total_seconds_in_day % 3600) // 60
                                seconds = total_seconds_in_day % 60
                                # --- ---
                                
                                # Создаем новое datetime: дата_запуска + дни + время_из_смещения
                                # datetime.timedelta(days=days) корректно обработает переходы через месяцы/годы
                                calculated_end_time = datetime.datetime.combine(
                                    start_date_only,
                                    datetime.time(hour=hours, minute=minutes, second=seconds)
                                ) + datetime.timedelta(days=days)
                                print(f"PostgreSQLDatabaseManager:   Дата запуска: {start_date_only}, Дни: {days}, Время из смещения: {hours:02d}:{minutes:02d}:{seconds:02d}")
                                print(f"PostgreSQLDatabaseManager:   Результат calculated_end_time: {calculated_end_time}")
                            else:
                                print(f"PostgreSQLDatabaseManager: Ошибка - end_offset для действия {action['id']} не является timedelta: {type(offset_timedelta_end)}. Устанавливаю None.")
                                calculated_end_time = None
                            # --- ---
                        else:
                            # --- ЛОГИКА ДЛЯ ОПЕРАТИВНОГО ---
                            print(f"PostgreSQLDatabaseManager: Рассчитываем calculated_end_time для оперативного времени действия ID {action['id']}.")
                            calculated_end_time = started_at_dt + action['end_offset']
                            print(f"PostgreSQLDatabaseManager:   started_at_dt ({started_at_dt}) + end_offset ({action['end_offset']}) = {calculated_end_time}")
                            # --- ---

                    cursor.execute("""
                        INSERT INTO app_schema.action_executions (
                            execution_id,
                            snapshot_description, snapshot_contact_phones, snapshot_report_materials,
                            calculated_start_time, calculated_end_time
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        new_execution_id,
                        action['description'], action['contact_phones'], action['report_materials'],
                        calculated_start_time, calculated_end_time
                    ))
                    print(f"PostgreSQLDatabaseManager: Создан action_execution для действия ID {action['id']} (start: {calculated_start_time}, end: {calculated_end_time}).")
                print(f"PostgreSQLDatabaseManager: Созданы {len(original_actions)} action_executions для execution ID {new_execution_id}.")

                self.connection.commit()
                print(f"PostgreSQLDatabaseManager: Транзакция завершена успешно. Новый execution ID: {new_execution_id}")
                return new_execution_id

        except psycopg2.Error as e:
            print(f"PostgreSQLDatabaseManager: Ошибка при запуске execution для алгоритма {algorithm_id}: {e}")
            self.connection.rollback()
            import traceback
            traceback.print_exc()
            return -1
        except Exception as e:
            print(f"PostgreSQLDatabaseManager: Неизвестная ошибка при запуске execution для алгоритма {algorithm_id}: {e}")
            self.connection.rollback()
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
        if not self.connection:
            print("PostgreSQLDatabaseManager: Нет подключения к БД.")
            return []

        if not category or not date_string:
            print("PostgreSQLDatabaseManager: Категория или дата не заданы.")
            return []

        try:
            # Преобразуем дату из DD.MM.YYYY в объект date для SQL
            from datetime import datetime
            target_date = datetime.strptime(date_string, '%d.%m.%Y').date()
            target_date_iso = target_date.isoformat() # 'YYYY-MM-DD'

            print(f"PostgreSQLDatabaseManager: Поиск завершённых executions категории '{category}' за дату {target_date_iso}.")

            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # SQL-запрос
                sql_query = f"""
                    SELECT
                        ae.id,
                        ae.algorithm_id,
                        ae.snapshot_name AS algorithm_name,
                        ae.snapshot_category AS category,
                        ae.started_at,
                        TO_CHAR(ae.started_at, 'DD.MM.YYYY HH24:MI:SS') AS started_at_display,
                        ae.completed_at,
                        CASE
                            WHEN ae.completed_at IS NOT NULL THEN TO_CHAR(ae.completed_at, 'DD.MM.YYYY HH24:MI:SS')
                            ELSE NULL
                        END AS completed_at_display,
                        ae.status,
                        ae.created_by_user_id,
                        ae.created_by_user_display_name
                    FROM {self.SCHEMA_NAME}.algorithm_executions ae
                    WHERE ae.snapshot_category = %s
                    AND ae.status IN ('completed', 'cancelled')
                    AND CAST(ae.completed_at AS DATE) = %s
                    ORDER BY ae.completed_at DESC;
                """
                cursor.execute(sql_query, (category, target_date_iso))
                rows = cursor.fetchall()

                # Преобразуем результаты в список словарей
                executions = [dict(row) for row in rows]
                print(f"PostgreSQLDatabaseManager: Найдено {len(executions)} завершённых executions.")
                return executions

        except psycopg2.Error as e:
            print(f"PostgreSQLDatabaseManager: Ошибка БД при получении завершённых executions: {e}")
            import traceback
            traceback.print_exc()
            return []
        except ValueError as ve:
            print(f"PostgreSQLDatabaseManager: Ошибка преобразования даты '{date_string}': {ve}")
            return []
        except Exception as e:
            print(f"PostgreSQLDatabaseManager: Неизвестная ошибка: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_algorithm_execution_by_id(self, execution_id: int) -> dict:
        """
        Получает данные конкретного экземпляра выполнения алгоритма (execution) по его ID.
        Включает информацию о пользователе, создавшем execution, на момент запуска.
        ВНИМАНИЕ: Этот метод НЕ ДОЛЖЕН использовать ту же транзакцию, что и другие,
        которые могут быть "сломаны". Временно делаем rollback, чтобы изолировать ошибку.
        :param execution_id: ID execution'а.
        :return: Словарь с данными execution'а или None, если не найден.
        """
        if not self.connection:
            print("PostgreSQLDatabaseManager: Нет подключения к БД.")
            logger.error("PostgreSQLDatabaseManager: Нет подключения к БД.")
            return None

        try:
            # --- ВРЕМЕННОЕ РЕШЕНИЕ: Откатываем текущую транзакцию ---
            # Это сбросит состояние и позволит выполнить запрос "с чистого листа"
            # ВНИМАНИЕ: Это может повлиять на другие операции, ожидающие commit!
            # Используем только для диагностики.
            print(f"PostgreSQLDatabaseManager: [DEBUG] Выполняем rollback перед запросом execution ID {execution_id} для изоляции.")
            self.connection.rollback()
            # --- ---

            with self.connection.cursor() as cursor:
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
                        -- ae.notes, -- <-- УДАЛЕНО: Столбец 'notes' не существует в таблице algorithm_executions
                        ae.created_at,
                        ae.updated_at
                    FROM app_schema.algorithm_executions ae
                    WHERE ae.id = %s
                """
                cursor.execute(sql_query, (execution_id,))
                row = cursor.fetchone()

                if row:
                    # Преобразуем результат в словарь
                    # Порядок столбцов в SELECT должен соответствовать порядку в row
                    execution_data = {
                        'id': row[0],
                        'algorithm_id': row[1],
                        'snapshot_name': row[2],
                        'snapshot_category': row[3],
                        'snapshot_time_type': row[4],
                        'snapshot_description': row[5],
                        'started_at': row[6].isoformat() if row[6] else None, # Преобразуем datetime в строку
                        'completed_at': row[7].isoformat() if row[7] else None,
                        'status': row[8],
                        'created_by_user_id': row[9],
                        'created_by_user_display_name': row[10],
                        # 'notes': row[11], # <-- УДАЛЕНО: Соответствующий элемент в словаре тоже убираем
                        'created_at': row[11].isoformat() if row[11] else None, # Индекс сдвинулся на 1
                        'updated_at': row[12].isoformat() if row[12] else None, # Индекс сдвинулся на 1
                    }
                    logger.info(f"PostgreSQLDatabaseManager: Получены данные execution ID {execution_id}.")
                    return execution_data
                else:
                    logger.warning(f"PostgreSQLDatabaseManager: Execution с ID {execution_id} не найден.")
                    return None

        except psycopg2.Error as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка при получении execution ID {execution_id}: {e}")
            print(f"PostgreSQLDatabaseManager: Ошибка при получении execution ID {execution_id}: {e}")
            # self.connection.rollback() # Уже был выполнен выше, если ошибка произошла после него
            return None
        except Exception as e:
            logger.error(f"PostgreSQLDatabaseManager: Неизвестная ошибка при получении execution ID {execution_id}: {e}")
            print(f"PostgreSQLDatabaseManager: Неизвестная ошибка при получении execution ID {execution_id}: {e}")
            # self.connection.rollback() # Уже был выполнен выше, если ошибка произошла после него
            return None

    def get_action_executions_by_execution_id(self, execution_id: int) -> list:
        """
        Получает список всех выполнений действий (action_execution'ов) для конкретного execution'а.
        Результат сортируется по calculated_start_time.
        :param execution_id: ID execution'а.
        :return: Список словарей с данными action_execution'ов или пустой список, если не найдены.
                 Возвращает None в случае ошибки.
        """
        if not self.connection:
            print("PostgreSQLDatabaseManager: Нет подключения к БД.")
            logger.error("PostgreSQLDatabaseManager: Нет подключения к БД.")
            return None

        try:
            with self.connection.cursor() as cursor:
                # SQL-запрос для получения данных action_execution'ов
                # Сортировка по calculated_start_time
                sql_query = """
                    SELECT
                        ae.id,
                        ae.execution_id,
                        ae.snapshot_description,
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
                    FROM app_schema.action_executions ae
                    WHERE ae.execution_id = %s
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
                    # Преобразуем datetime в строку, если они не None
                    for time_field in ['calculated_start_time', 'calculated_end_time', 'actual_end_time', 'created_at', 'updated_at']:
                        if action_exec_dict.get(time_field):
                            action_exec_dict[time_field] = action_exec_dict[time_field].isoformat()
                    action_executions_list.append(action_exec_dict)

                logger.info(f"PostgreSQLDatabaseManager: Получено {len(action_executions_list)} action_execution'ов для execution ID {execution_id}.")
                return action_executions_list

        except psycopg2.Error as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка при получении action_execution'ов для execution ID {execution_id}: {e}")
            print(f"PostgreSQLDatabaseManager: Ошибка при получении action_execution'ов для execution ID {execution_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"PostgreSQLDatabaseManager: Неизвестная ошибка при получении action_execution'ов для execution ID {execution_id}: {e}")
            print(f"PostgreSQLDatabaseManager: Неизвестная ошибка при получении action_execution'ов для execution ID {execution_id}: {e}")
            return None


    # db/postgresql_manager.py
    # ... (импорты, logger, класс ...) ...

    def create_action_execution(self, execution_id: int, action_execution_data: dict) -> bool:
        """
        Создает новое action_execution, связанное с execution_id.
        :param execution_id: ID execution'а.
        :param action_execution_data: Данные нового action_execution'а.
                                     Ожидается словарь с ключами, соответствующими полям в БД.
        :return: True, если успешно, иначе False.
        """
        logger.debug(f"PostgreSQLDatabaseManager: create_action_execution called with execution_id={execution_id}, data={action_execution_data}")

        if not isinstance(execution_id, int) or execution_id <= 0:
            logger.error("PostgreSQLDatabaseManager: Некорректный execution_id.")
            return False

        if not isinstance(action_execution_data, dict):
            logger.error("PostgreSQLDatabaseManager: action_execution_data должно быть словарем.")
            return False

        # --- 1. Подготовить данные для вставки ---
        # Определяем разрешенные поля (те, которые реально существуют в БД)
        # Убедитесь, что этот список соответствует вашей схеме БД!
        # Например, если у вас нет поля 'actual_start_time', удалите его отсюда.
        allowed_fields_in_db = {
            'snapshot_description',
            'calculated_start_time',      # ← используем calculated как факт
            'calculated_end_time',
            'snapshot_contact_phones',
            'snapshot_report_materials',
            'reported_to',
            'notes'
        }
        
        # Создаем копию данных, содержащую только разрешенные поля
        prepared_data = {k: v for k, v in action_execution_data.items() if k in allowed_fields_in_db}
        logger.debug(f"PostgreSQLDatabaseManager: Подготовленные данные (до преобразования времени): {prepared_data}")
        
        # Добавляем execution_id
        prepared_data['execution_id'] = execution_id
        # --- ---

        # --- 2. Обработка абсолютных дат/времени ---
        # Предполагаем, что поля 'actual_start_time' и 'actual_end_time' содержат
        # строки в формате 'dd.MM.yyyy HH:mm:ss' или пустые/None.
        # Нужно преобразовать их в datetime.datetime Python'а.
        
        def parse_datetime_string(datetime_str: str) -> datetime.datetime | None:
            """Вспомогательная функция для парсинга строки даты/времени."""
            if not datetime_str or not isinstance(datetime_str, str):
                return None
            datetime_str = datetime_str.strip()
            if not datetime_str:
                return None
            try:
                # Пробуем распарсить строку в datetime
                # datetime.datetime.strptime("05.10.2025 14:30:00", "%d.%m.%Y %H:%M:%S")
                parsed_dt = datetime.datetime.strptime(datetime_str, "%d.%m.%Y %H:%M:%S")
                logger.debug(f"PostgreSQLDatabaseManager: Строка '{datetime_str}' успешно преобразована в datetime: {parsed_dt}")
                return parsed_dt
            except ValueError as e:
                logger.warning(f"PostgreSQLDatabaseManager: Неверный формат строки даты/времени '{datetime_str}': {e}")
                return None # Или поднять исключение, если это критично

        # Преобразуем 'actual_start_time'
        if 'actual_start_time' in prepared_data:
            start_time_str = prepared_data['actual_start_time']
            prepared_data['actual_start_time'] = parse_datetime_string(start_time_str)
            # Psycopg2 автоматически преобразует datetime.datetime в TIMESTAMP для PostgreSQL
            # Если значение None, в БД пойдет NULL

        # Преобразуем 'actual_end_time'
        if 'actual_end_time' in prepared_data:
            end_time_str = prepared_data['actual_end_time']
            prepared_data['actual_end_time'] = parse_datetime_string(end_time_str)
            # Psycopg2 автоматически преобразует datetime.datetime в TIMESTAMP для PostgreSQL
            # Если значение None, в БД пойдет NULL

        logger.debug(f"PostgreSQLDatabaseManager: Подготовленные данные (после преобразования времени): {prepared_data}")
        # --- ---

        # --- 3. Подготовить SQL-запрос ---
        try:
            with self._get_connection() as conn: # <-- Используем _get_connection (с подчеркиванием)
                with conn.cursor() as cursor:
                    # Проверяем, существует ли execution_id
                    cursor.execute(
                        f"SELECT 1 FROM {self.SCHEMA_NAME}.algorithm_executions WHERE id = %s;", (execution_id,)
                    )
                    if not cursor.fetchone():
                         logger.error(f"PostgreSQLDatabaseManager: Execution ID {execution_id} не существует.")
                         return False

                    # Подготавливаем список колонок и значений
                    columns = list(prepared_data.keys())
                    values = [prepared_data[col] for col in columns] # Список значений, включая datetime или None
                    
                    # Создаем SQL-строки для запроса
                    columns_str = ', '.join(columns)
                    placeholders_str = ', '.join(['%s'] * len(values)) # %s для всех значений, включая datetime
                    
                    sql_query = f"""
                        INSERT INTO {self.SCHEMA_NAME}.action_executions ({columns_str})
                        VALUES ({placeholders_str})
                        RETURNING id; -- Возвращаем ID нового action_execution
                    """

                    logger.debug(f"PostgreSQLDatabaseManager: Выполняем SQL: {cursor.mogrify(sql_query, values)}")
                    cursor.execute(sql_query, values)
                    new_action_id_row = cursor.fetchone()
                    new_action_id = new_action_id_row[0] if new_action_id_row else None
                    # conn.commit() вызывается автоматически при выходе из контекстного менеджера `with conn:`
                    if new_action_id:
                        logger.info(f"PostgreSQLDatabaseManager: Новое action_execution (ID: {new_action_id}) добавлено для execution ID {execution_id}.")
                        return True # Или return new_action_id, если хотите возвращать ID
                    else:
                        logger.error(f"PostgreSQLDatabaseManager: Не удалось получить ID нового action_execution для execution ID {execution_id}.")
                        return False

        except psycopg2.IntegrityError as e:
             # Это может быть ошибка нарушения внешнего ключа (execution_id не существует)
             # или уникальности (если такое возможно). Обычно IntegrityError.
             logger.error(f"PostgreSQLDatabaseManager: Ошибка целостности БД при добавлении action_execution для execution ID {execution_id}: {e}")
             # conn.rollback() вызывается автоматически при выходе из `with conn:` в случае исключения
             return False
        except psycopg2.Error as e: # Ловим более общие ошибки psycopg2
             logger.error(f"PostgreSQLDatabaseManager: Ошибка БД psycopg2 при добавлении action_execution для execution ID {execution_id}: {e}")
             # conn.rollback() вызывается автоматически
             return False
        except Exception as e:
             logger.exception(f"PostgreSQLDatabaseManager: Неизвестная ошибка при добавлении action_execution для execution ID {execution_id}: {e}")
             # conn.rollback() вызывается автоматически
             return False
        # --- ---

    def update_action_execution(self, action_execution_id: int, action_execution_data: dict) -> bool:
        """
        Обновляет существующее action_execution.
        :param action_execution_id: ID action_execution'а.
        :param action_execution_ Данные для обновления.
        :return: True, если успешно, иначе False.
        """

        # --- 1. Подготовить данные для обновления ---
        # Определяем разрешенные поля (те, которые реально существуют в ТАБЛИЦЕ action_executions)
        allowed_fields_in_db = {
            'actual_end_time',      # <-- Поле для фактического времени окончания
            'reported_to',          # <-- Поле для "Кому доложено"
            'notes',                # <-- Поле для "Примечания"
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

        logger.debug(f"PostgreSQLDatabaseManager: Подготовленные данные для обновления (до преобразования времени): {prepared_data}")
        # --- ---

        # --- 2. Обработка абсолютных дат/времени (только для actual_end_time) ---
        def parse_datetime_string(datetime_str: str) -> datetime.datetime | None:
            """Вспомогательная функция для парсинга строки даты/времени."""
            if not datetime_str or not isinstance(datetime_str, str):
                return None
            datetime_str = datetime_str.strip()
            if not datetime_str:
                return None
            try:
                parsed_dt = datetime.datetime.strptime(datetime_str, "%d.%m.%Y %H:%M:%S")
                logger.debug(f"PostgreSQLDatabaseManager: Строка '{datetime_str}' успешно преобразована в datetime: {parsed_dt}")
                return parsed_dt
            except ValueError as e:
                logger.warning(f"PostgreSQLDatabaseManager: Неверный формат строки даты/времени '{datetime_str}': {e}")
                return None

        # Преобразуем 'actual_end_time', если оно присутствует
        actual_end_time_dt = None
        if 'actual_end_time' in prepared_data:
            end_time_str = prepared_data['actual_end_time']
            actual_end_time_dt = parse_datetime_string(end_time_str)
            if actual_end_time_dt:
                prepared_data['actual_end_time'] = actual_end_time_dt
            else:
                # Если строка времени некорректна, удаляем её из prepared_data
                logger.warning(f"PostgreSQLDatabaseManager: Невозможно разобрать actual_end_time '{end_time_str}'. Поле будет пропущено.")
                prepared_data.pop('actual_end_time', None)
                actual_end_time_dt = None # Убедимся, что dt тоже None, если строка неверна

        # --- ---

        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor: # Используем RealDictCursor для именованных колонок
                    # Проверяем, существует ли action_execution_id
                    cursor.execute(
                        f"SELECT id, execution_id, calculated_start_time, calculated_end_time, status FROM {self.SCHEMA_NAME}.action_executions WHERE id = %s;",
                        (action_execution_id,)
                    )
                    row = cursor.fetchone()
                    if not row:
                        logger.error(f"PostgreSQLDatabaseManager: Action_execution ID {action_execution_id} не существует.")
                        return False

                    original_execution_data = dict(row) # Преобразуем в обычный словарь
                    logger.debug(f"PostgreSQLDatabaseManager: Найден action_execution для обновления: {original_execution_data}")

                    # --- Проверка: actual_end_time не раньше calculated_start_time ---
                    if actual_end_time_dt and original_execution_data.get('calculated_start_time'):
                        calc_start_dt = original_execution_data['calculated_start_time']
                        if actual_end_time_dt < calc_start_dt:
                            logger.error(f"PostgreSQLDatabaseManager: actual_end_time ({actual_end_time_dt}) не может быть раньше calculated_start_time ({calc_start_dt}) для action_execution ID {action_execution_id}.")
                            return False
                    # --- ---

                    # --- Определение нового статуса ---
                    new_status = None
                    if actual_end_time_dt is not None:
                        # Если передано actual_end_time, статус должен стать 'completed'
                        new_status = 'completed'
                        prepared_data['status'] = new_status # Добавляем статус в подготовленные данные
                        logger.debug(f"PostgreSQLDatabaseManager: Установлен статус 'completed' для action_execution ID {action_execution_id} на основе actual_end_time.")
                    # Если actual_end_time не передан, статус не изменяем, оставляем как есть
                    # (или можно предусмотреть явное указание статуса в action_execution_data, если нужно)
                    # --- ---

                    # --- Подготовка SQL-запроса ---
                    if not prepared_data:
                        logger.warning("PostgreSQLDatabaseManager: Нет данных для обновления (после фильтрации и преобразований).")
                        # Возможно, нужно вернуть True, если обновление без изменений считается успешным
                        # Но обычно возвращают True, только если что-то реально изменилось.
                        # В данном случае, если actual_end_time был None или невалиден, и других полей нет, возвращаем False
                        return False

                    # Подготавливаем SET часть запроса
                    set_clauses = []
                    values = []
                    for key, value in prepared_data.items():
                        set_clauses.append(f"{key} = %s")
                        values.append(value) # Добавляем значение (datetime, строка, None и т.д.)

                    # Добавляем action_execution_id в конец списка значений для WHERE
                    values.append(action_execution_id)

                    set_clause_str = ", ".join(set_clauses)
                    # Обновляем updated_at автоматически
                    sql_query = f"""
                        UPDATE {self.SCHEMA_NAME}.action_executions
                        SET {set_clause_str}, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s;
                    """

                    logger.debug(f"PostgreSQLDatabaseManager: Выполняем SQL UPDATE: {cursor.mogrify(sql_query, values)}")
                    cursor.execute(sql_query, values)
                    # conn.commit() вызывается автоматически
                    affected_rows = cursor.rowcount
                    logger.info(f"PostgreSQLDatabaseManager: Обновлено {affected_rows} записей action_execution с ID {action_execution_id}.")

                    # Возвращаем True, если одна строка была затронута
                    return affected_rows == 1

        except psycopg2.IntegrityError as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка целостности БД при обновлении action_execution ID {action_execution_id}: {e}")
            return False
        except psycopg2.Error as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка БД psycopg2 при обновлении action_execution ID {action_execution_id}: {e}")
            return False
        except Exception as e:
            logger.exception(f"PostgreSQLDatabaseManager: Неизвестная ошибка при обновлении action_execution ID {action_execution_id}: {e}")
            return False
        # --- ---



    def get_action_execution_by_id(self, action_execution_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает данные конкретного выполнения действия (action_execution) по его ID.
        :param action_execution_id: ID action_execution.
        :return: Словарь с данными action_execution или None.
        """
        if not isinstance(action_execution_id, int) or action_execution_id <= 0:
            logger.error(f"PostgreSQLDatabaseManager: Некорректный action_execution_id: {action_execution_id}")
            return None

        if not self.connection:
            print("PostgreSQLDatabaseManager: Нет подключения к БД.")
            logger.error("PostgreSQLDatabaseManager: Нет подключения к БД.")
            return None

        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Запрос включает все нужные поля, включая snapshot и calculated/actual
                query = f"""
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
                FROM {self.SCHEMA_NAME}.action_executions
                WHERE id = %s;
                """
                cursor.execute(query, (action_execution_id,))
                row = cursor.fetchone()

                if row:
                    # Преобразуем RealDictRow в словарь
                    result_dict = dict(row)
                    
                    # --- ИСПРАВЛЕНИЕ: Преобразование datetime в строки ---
                    # Это необходимо для корректной передачи данных в QML и избежания QVariant(PySide::PyObjectWrapper)
                    # Преобразуем конкретные поля, если они не None
                    datetime_fields = ['calculated_start_time', 'calculated_end_time', 'actual_end_time']
                    for field in datetime_fields:
                        if result_dict.get(field) is not None:
                            # Проверяем, является ли значение datetime объектом
                            if isinstance(result_dict[field], datetime.datetime):
                                # Преобразуем в строку в формате, удобном для QML
                                result_dict[field] = result_dict[field].strftime("%d.%m.%Y %H:%M:%S")
                            # Если значение уже строка (например, из-за предыдущих обработок), оставляем как есть
                            # Если значение имеет другой тип (вряд ли), оно останется как есть, и QML получит его как есть
                    # --- ---
                    
                    logger.debug(f"PostgreSQLDatabaseManager: Получены (и преобразованы) данные action_execution ID {action_execution_id}: {result_dict}")
                    return result_dict
                else:
                    logger.warning(f"PostgreSQLDatabaseManager: Action execution ID {action_execution_id} не найден.")
                    return None

        except psycopg2.Error as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка БД при получении action_execution ID {action_execution_id}: {e}")
            return None
        except Exception as e:
            logger.exception(f"PostgreSQLDatabaseManager: Неизвестная ошибка при получении action_execution ID {action_execution_id}: {e}")
            return None

    def get_active_action_executions_with_details(self) -> list:
        """
        Получает список активных action_executions вместе с деталями execution'а.

        Возвращает список словарей:
        [
            {
                'id': int, # ID action_execution
                'execution_id': int, # ID связанного algorithm_execution
                'calculated_start_time': datetime.datetime, # Объект datetime времени начала
                'calculated_end_time': datetime.datetime, # Объект datetime времени окончания
                'status': str, # Статус action_execution ('pending', 'in_progress', ...) - теперь без алиаса
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
            ae.status, -- Явно указываем ae.status, он будет 'status' в словаре Python
            ae.snapshot_description,
            exec.status AS execution_status,
            exec.snapshot_name -- <-- Добавляем snapshot_name из связанного execution
        FROM app_schema.action_executions ae
        JOIN app_schema.algorithm_executions exec ON ae.execution_id = exec.id
        WHERE exec.status = 'active' -- Только активные выполнения алгоритмов
        AND ae.status IN ('pending', 'in_progress'); -- Только активные действия
        """
        try:
            # Используем _get_connection для получения соединения
            with self._get_connection() as conn:
                # Создаем курсор из соединения, используя RealDictCursor
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    # rows уже будут списком RealDictRow, который можно напрямую конвертировать в dict
                    # Преобразуем в список словарей Python
                    results = [dict(row) for row in rows]
                    return results
        except Exception as e:
            logger.error(f"Ошибка при получении активных действий с деталями: {e}")
            import traceback
            traceback.print_exc()
            return []
    # --- Конец метода get_active_action_executions_with_details ---

    # ========================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С ОРГАНИЗАЦИЯМИ
    # ========================================================================

    def get_all_organizations(self) -> list:
        """Получить все организации из справочника."""
        try:
            conn = self._get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM app_schema.organizations ORDER BY name;")
                    rows = cursor.fetchall()
                    organizations = [dict(row) for row in rows]
                    logger.info(f"PostgreSQLDatabaseManager: Получено {len(organizations)} организаций.")
                    return organizations
        except Exception as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка при получении организаций: {e}")
            return []
        except Exception as e:
            logger.exception(f"PostgreSQLDatabaseManager: Неизвестная ошибка при получении организаций: {e}")
            return []

    def create_organization(self, org_data: dict) -> int:
        """Создать новую организацию. Возвращает ID или 0 при ошибке."""
        try:
            conn = self._get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO app_schema.organizations (name, phone, contact_person, notes) VALUES (%s, %s, %s, %s) RETURNING id;",
                        (
                            org_data.get('name', ''),
                            org_data.get('phone', None),
                            org_data.get('contact_person', None),
                            org_data.get('notes', None)
                        )
                    )
                    result = cursor.fetchone()
                    conn.commit()
                    new_id = result['id'] if result else 0
                    logger.info(f"PostgreSQLDatabaseManager: Создана организация с ID {new_id}.")
                    return new_id
        except Exception as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка при создании организации: {e}")
            if conn:
                conn.rollback()
            return 0
        except Exception as e:
            logger.exception(f"PostgreSQLDatabaseManager: Неизвестная ошибка при создании организации: {e}")
            if conn:
                conn.rollback()
            return 0

    def update_organization(self, org_id: int, org_data: dict) -> bool:
        """Обновить данные организации."""
        try:
            conn = self._get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE app_schema.organizations SET name = %s, phone = %s, contact_person = %s, notes = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s;",
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
                    logger.info(f"PostgreSQLDatabaseManager: Обновлено {affected_rows} записей организации с ID {org_id}.")
                    return affected_rows > 0
        except Exception as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка при обновлении организации: {e}")
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.exception(f"PostgreSQLDatabaseManager: Неизвестная ошибка при обновлении организации: {e}")
            if conn:
                conn.rollback()
            return False

    def delete_organization(self, org_id: int) -> bool:
        """Удалить организацию."""
        try:
            conn = self._get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM app_schema.organizations WHERE id = %s;", (org_id,))
                    conn.commit()
                    affected_rows = cursor.rowcount
                    logger.info(f"PostgreSQLDatabaseManager: Удалено {affected_rows} организаций с ID {org_id}.")
                    return affected_rows > 0
        except Exception as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка при удалении организации: {e}")
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.exception(f"PostgreSQLDatabaseManager: Неизвестная ошибка при удалении организации: {e}")
            if conn:
                conn.rollback()
            return False

    def get_organization_by_id(self, org_id: int) -> dict | None:
        """Получить организацию по ID."""
        try:
            conn = self._get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM app_schema.organizations WHERE id = %s;", (org_id,))
                    row = cursor.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка при получении организации по ID {org_id}: {e}")
            return None
        except Exception as e:
            logger.exception(f"PostgreSQLDatabaseManager: Неизвестная ошибка при получении организации по ID {org_id}: {e}")
            return None

    # ========================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С СПРАВОЧНЫМИ ФАЙЛАМИ ОРГАНИЗАЦИЙ
    # ========================================================================

    def get_organization_reference_files(self, org_id: int) -> list:
        """Получить все справочные файлы организации."""
        try:
            conn = self._get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM app_schema.organization_reference_files WHERE organization_id = %s ORDER BY file_type, file_path;",
                        (org_id,)
                    )
                    rows = cursor.fetchall()
                    files = [dict(row) for row in rows]
                    logger.info(f"PostgreSQLDatabaseManager: Получено {len(files)} файлов для организации ID {org_id}.")
                    return files
        except Exception as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка при получении файлов для организации ID {org_id}: {e}")
            return []
        except Exception as e:
            logger.exception(f"PostgreSQLDatabaseManager: Неизвестная ошибка при получении файлов для организации ID {org_id}: {e}")
            return []

    def add_organization_reference_file(self, org_id: int, file_path: str, file_type: str = 'other') -> int:
        """Добавить справочный файл к организации. Возвращает ID или 0 при ошибке."""
        try:
            conn = self._get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO app_schema.organization_reference_files (organization_id, file_path, file_type) VALUES (%s, %s, %s) RETURNING id;",
                        (org_id, file_path, file_type)
                    )
                    result = cursor.fetchone()
                    conn.commit()
                    new_id = result['id'] if result else 0
                    logger.info(f"PostgreSQLDatabaseManager: Добавлен файл с ID {new_id} для организации ID {org_id}.")
                    return new_id
        except Exception as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка при добавлении файла для организации ID {org_id}: {e}")
            if conn:
                conn.rollback()
            return 0
        except Exception as e:
            logger.exception(f"PostgreSQLDatabaseManager: Неизвестная ошибка при добавлении файла для организации ID {org_id}: {e}")
            if conn:
                conn.rollback()
            return 0

    def delete_organization_reference_file(self, file_id: int) -> bool:
        """Удалить справочный файл организации."""
        try:
            conn = self._get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM app_schema.organization_reference_files WHERE id = %s;", (file_id,))
                    conn.commit()
                    affected_rows = cursor.rowcount
                    logger.info(f"PostgreSQLDatabaseManager: Удалено {affected_rows} файлов с ID {file_id}.")
                    return affected_rows > 0
        except Exception as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка при удалении файла ID {file_id}: {e}")
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.exception(f"PostgreSQLDatabaseManager: Неизвестная ошибка при удалении файла ID {file_id}: {e}")
            if conn:
                conn.rollback()
            return False

    # ========================================================================
    # МЕТОДЫ ДЛЯ СВЯЗИ ОРГАНИЗАЦИЙ С ДЕЙСТВИЯМИ
    # ========================================================================

    def get_organizations_for_action_execution(self, action_execution_id: int) -> list:
        """Получить все организации, привязанные к действию."""
        try:
            conn = self._get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT o.*
                        FROM app_schema.organizations o
                        INNER JOIN app_schema.action_execution_organizations aeo ON o.id = aeo.organization_id
                        WHERE aeo.action_execution_id = %s
                        ORDER BY o.name;
                    """, (action_execution_id,))
                    rows = cursor.fetchall()
                    organizations = [dict(row) for row in rows]
                    logger.info(f"PostgreSQLDatabaseManager: Получено {len(organizations)} организаций для действия ID {action_execution_id}.")
                    return organizations
        except Exception as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка при получении организаций для действия ID {action_execution_id}: {e}")
            return []
        except Exception as e:
            logger.exception(f"PostgreSQLDatabaseManager: Неизвестная ошибка при получении организаций для действия ID {action_execution_id}: {e}")
            return []

    def add_organization_to_action_execution(self, action_execution_id: int, organization_id: int) -> int:
        """Привязать организацию к действию. Возвращает ID связи или 0 при ошибке."""
        try:
            conn = self._get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO app_schema.action_execution_organizations (action_execution_id, organization_id) VALUES (%s, %s) RETURNING id;",
                        (action_execution_id, organization_id)
                    )
                    result = cursor.fetchone()
                    conn.commit()
                    new_id = result['id'] if result else 0
                    logger.info(f"PostgreSQLDatabaseManager: Организация ID {organization_id} привязана к действию ID {action_execution_id}.")
                    return new_id
        except Exception as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка при привязке организации к действию: {e}")
            if conn:
                conn.rollback()
            return 0
        except Exception as e:
            logger.exception(f"PostgreSQLDatabaseManager: Неизвестная ошибка при привязке организации к действию: {e}")
            if conn:
                conn.rollback()
            return 0

    def remove_organization_from_action_execution(self, action_execution_id: int, organization_id: int) -> bool:
        """Отвязать организацию от действия."""
        try:
            conn = self._get_connection()
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM app_schema.action_execution_organizations WHERE action_execution_id = %s AND organization_id = %s;",
                        (action_execution_id, organization_id)
                    )
                    conn.commit()
                    affected_rows = cursor.rowcount
                    logger.info(f"PostgreSQLDatabaseManager: Отвязано {affected_rows} организаций от действия ID {action_execution_id}.")
                    return affected_rows > 0
        except Exception as e:
            logger.error(f"PostgreSQLDatabaseManager: Ошибка при отвязке организации от действия: {e}")
            if conn:
                conn.rollback()
            return False
        except Exception as e:
            logger.exception(f"PostgreSQLDatabaseManager: Неизвестная ошибка при отвязке организации от действия: {e}")
            if conn:
                conn.rollback()
            return False


# --- Пример использования (для тестирования модуля отдельно) ---
if __name__ == "__main__":
    # Для тестирования в standalone-режиме нужно получить конфиг из SQLite
    # from db.sqlite_config import SQLiteConfigManager
    # config_manager = SQLiteConfigManager()
    # connection_config = config_manager.get_connection_config()
    #
    # if connection_config:
    #     pg_manager = PostgreSQLDatabaseManager(connection_config)
    #     if pg_manager.test_connection():
    #         print("Подключение к PostgreSQL успешно!")
    #         # Попробуем аутентификацию (логин и пароль нужно знать)
    #         # user = pg_manager.authenticate_user("admin", "admin_password")
    #         # print("Результат аутентификации:", user)
    #         # settings = pg_manager.get_settings()
    #         # print("Настройки:", settings)
    #         # users = pg_manager.get_all_active_users()
    #         # print("Пользователи:", users)
    #     else:
    #         print("Не удалось подключиться к PostgreSQL или схема не найдена.")
    # else:
    #     print("Конфигурация подключения к PostgreSQL не найдена.")
    pass
