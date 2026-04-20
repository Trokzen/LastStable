#!/usr/bin/env python3
"""
Скрипт для применения конкретной миграции 003.
"""

import sqlite3
from pathlib import Path

DB_PATH = "duty_app.db"
MIGRATION_FILE = "db/migrations/003_add_image_file_type.sql"


def main():
    db_path = Path(DB_PATH)
    if not db_path.exists():
        print(f"База данных не найдена: {db_path}")
        return

    print(f"Подключение к базе данных: {db_path}")
    conn = sqlite3.connect(str(db_path))
    
    # Проверяем текущую схему
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='organization_reference_files';")
    result = cursor.fetchone()
    if result:
        print("Текущая схема таблицы:")
        print(result[0])
        print()
    
    # Применяем миграцию
    print("Применение миграции 003...")
    with open(MIGRATION_FILE, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    try:
        conn.executescript(sql)
        conn.commit()
        print("✓ Миграция успешно применена!")
        
        # Проверяем новую схему
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='organization_reference_files';")
        result = cursor.fetchone()
        if result:
            print("Новая схема таблицы:")
            print(result[0])
    except sqlite3.Error as e:
        print(f"✗ Ошибка: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        print("Готово!")


if __name__ == "__main__":
    main()
