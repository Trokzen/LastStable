-- Миграция 003: Добавление типа файла 'image' для справочных материалов организаций
-- Дата: 2026-04-15

-- В SQLite нельзя изменить CHECK ограничение напрямую, нужно пересоздать таблицу
-- Создаем новую таблицу с обновленным ограничением
CREATE TABLE IF NOT EXISTS organization_reference_files_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT DEFAULT 'other',
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    CHECK (file_type IN ('word', 'excel', 'pdf', 'image', 'other'))
);

-- Копируем данные из старой таблицы
INSERT INTO organization_reference_files_new (id, organization_id, file_path, file_type, created_at)
SELECT id, organization_id, file_path, file_type, created_at FROM organization_reference_files;

-- Удаляем старую таблицу
DROP TABLE IF EXISTS organization_reference_files;

-- Переименовываем новую таблицу
ALTER TABLE organization_reference_files_new RENAME TO organization_reference_files;

-- Воссоздаем индекс
CREATE INDEX IF NOT EXISTS idx_org_ref_files_organization_id ON organization_reference_files(organization_id);
