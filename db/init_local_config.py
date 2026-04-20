# db/init_local_config.py
import os
import sys
# --- Добавляем родительскую директорию в путь поиска модулей ---
# Это нужно, потому что скрипт теперь внутри пакета 'db'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# ---

from db.sqlite_config import SQLiteConfigManager # Импорт теперь корректен

if __name__ == "__main__":
    # Создаем экземпляр менеджера. Файл будет создан в папке 'db'.
    config_manager = SQLiteConfigManager()
    config_path = config_manager.config_path
    print(f"Файл конфигурации будет создан по пути: {config_path}")
    print(f"Абсолютный путь: {config_path.absolute()}")

    # --- Остальная логика остается той же ---
    existing_config = config_manager.get_connection_config()
    if existing_config:
        print("Найдена существующая конфигурация:")
        safe_config = {k: v for k, v in existing_config.items() if k != 'password'}
        print(safe_config)
        overwrite = input("Перезаписать? (y/N): ")
        if overwrite.lower() != 'y':
            print("Выход без изменений.")
            exit()
    else:
        print("Существующая конфигурация не найдена. Создаем новую.")

    # --- Введите здесь свои реальные параметры подключения к PostgreSQL ---
    HOST = "localhost"
    PORT = 5432
    DBNAME = "algodch_db"
    USER = "postgres"
    PASSWORD = "123" # <<<=== УКАЖИТЕ ВАШ ПАРОЛЬ
    # ---------------------------------------------------------------------

    print("\nСохраняем новую конфигурацию подключения к PostgreSQL...")
    print(f"  Хост: {HOST}")
    print(f"  Порт: {PORT}")
    print(f"  База: {DBNAME}")
    print(f"  Пользователь: {USER}")

    try:
        config_manager.save_connection_config(
            host=HOST,
            port=PORT,
            dbname=DBNAME,
            user=USER,
            password=PASSWORD
        )
        print("Конфигурация успешно сохранена.")

        saved_config = config_manager.get_connection_config()
        if saved_config:
            print("\nПроверка сохраненной конфигурации (без пароля):")
            safe_saved_config = {k: v for k, v in saved_config.items() if k != 'password'}
            print(safe_saved_config)
            print("Готово.")
        else:
            print("\nОшибка: Не удалось получить сохраненную конфигурацию.")

    except Exception as e:
        print(f"Ошибка при сохранении конфигурации: {e}")

    print("\nТеперь файл local_config.db должен существовать в папке проекта/db/.")
