# db/generate_admin_hash.py
# Убедитесь, что установили Werkzeug: pip install Werkzeug

from werkzeug.security import generate_password_hash

def generate_hash(password: str) -> str:
    """Генерирует хэш пароля с использованием Werkzeug."""
    # generate_password_hash использует pbkdf2:sha256 по умолчанию
    # Можно указать метод и количество раундов: generate_password_hash(password, method='pbkdf2:sha256', salt_length=12)
    return generate_password_hash(password)

if __name__ == "__main__":
    default_password = "admin" # Пароль по умолчанию
    print(f"Генерация Werkzeug хэша для пароля по умолчанию: '{default_password}'")
    hash_str = generate_hash('123')
    print("Сгенерированный хэш:")
    print(hash_str)
    print("\nСкопируйте этот хэш и вставьте его в SQL-скрипт init_postgres_schema.sql")
    print("в строку INSERT INTO users ... вместо 'PLACEHOLDER_WERKZEUG_HASH_HERE'")
    print("\nПосле этого выполните SQL-скрипт в вашей базе данных PostgreSQL.")

# --- Как использовать ---
# 1. Убедитесь, что установлен Werkzeug: pip install Werkzeug
# 2. Запустите скрипт: python db/generate_admin_hash.py
# 3. Скопируйте выводимый хэш.
# 4. Вставьте его в init_postgres_schema.sql.
# 5. Выполните SQL-скрипт в вашей БД.