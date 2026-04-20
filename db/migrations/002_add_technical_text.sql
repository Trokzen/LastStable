-- Миграция 002: Добавление поля technical_text для действий
-- Применять к существующей базе данных SQLite

-- Добавляем поле technical_text в таблицу actions
ALTER TABLE actions ADD COLUMN technical_text TEXT;

-- Добавляем поле snapshot_technical_text в таблицу action_executions
ALTER TABLE action_executions ADD COLUMN snapshot_technical_text TEXT;
