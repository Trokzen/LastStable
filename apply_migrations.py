#!/usr/bin/env python3
"""
Скрипт для применения миграций к существующей базе данных SQLite.
Запускать из корневой директории проекта: python apply_migrations.py
"""

import sqlite3
import os
from pathlib import Path

DB_PATH = "duty_app.db"
MIGRATIONS_DIR = "db/migrations"


def apply_migration(conn, migration_file):
    """Применить один файл миграции."""
    print(f"Применение миграции: {migration_file}")
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    cursor = conn.cursor()
    try:
        conn.executescript(sql)
        conn.commit()
        print(f"  ✓ Миграция {os.path.basename(migration_file)} успешно применена.")
        return True
    except sqlite3.Error as e:
        print(f"  ✗ Ошибка при применении миграции: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()


def main():
    db_path = Path(DB_PATH)
    if not db_path.exists():
        print(f"База данных не найдена: {db_path}")
        return
    
    print(f"Подключение к базе данных: {db_path}")
    conn = sqlite3.connect(str(db_path))
    
    # Проверка, существуют ли уже таблицы
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='organizations';")
    if cursor.fetchone():
        print("Таблица 'organizations' уже существует. Пропуск миграции.")
    else:
        print("Таблица 'organizations' не найдена. Применение миграций...")
        
        # Получаем список файлов миграций
        migrations = sorted(Path(MIGRATIONS_DIR).glob("*.sql"))
        if not migrations:
            print("Файлы миграций не найдены.")
            return
        
        for migration_file in migrations:
            apply_migration(conn, str(migration_file))
    
    cursor.close()
    conn.close()
    print("Готово!")


if __name__ == "__main__":
    main()
