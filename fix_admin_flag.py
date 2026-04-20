# -*- coding: utf-8 -*-
"""Скрипт для установки флага администратора пользователю 'admin'."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import sqlite3

DB_PATH = 'duty_app.db'

print(f"Подключение к базе данных: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Проверяем текущее состояние
cursor.execute("SELECT id, login, is_admin FROM users WHERE login = 'admin';")
row = cursor.fetchone()
if row:
    print(f"Найден пользователь: ID={row[0]}, логин={row[1]}, is_admin={row[2]}")
    if row[2] == 0:
        cursor.execute("UPDATE users SET is_admin = 1 WHERE login = 'admin';")
        conn.commit()
        print("Флаг is_admin установлен в 1 (администратор).")
    else:
        print("Пользователь уже является администратором.")
else:
    print("Пользователь 'admin' не найден.")

# Проверяем результат
cursor.execute("SELECT id, login, is_admin FROM users WHERE login = 'admin';")
row = cursor.fetchone()
if row:
    print(f"Текущее состояние: ID={row[0]}, логин={row[1]}, is_admin={row[2]}")

conn.close()
print("Готово.")
