-- Миграция 001: Добавление таблиц для организаций и справочных материалов
-- Применять к существующей базе данных SQLite

-- Таблица для хранения справочника организаций
CREATE TABLE IF NOT EXISTS organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    contact_person TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);

-- Таблица для связи организаций с действиями (многие-ко-многим)
CREATE TABLE IF NOT EXISTS action_execution_organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_execution_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (action_execution_id) REFERENCES action_executions(id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

-- Таблица для хранения справочных материалов организаций
CREATE TABLE IF NOT EXISTS organization_reference_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT DEFAULT 'other',
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    CHECK (file_type IN ('word', 'excel', 'pdf', 'image', 'other'))
);

-- Индексы для ускорения поиска
CREATE INDEX IF NOT EXISTS idx_ae_orgs_action_execution_id ON action_execution_organizations(action_execution_id);
CREATE INDEX IF NOT EXISTS idx_ae_orgs_organization_id ON action_execution_organizations(organization_id);
CREATE INDEX IF NOT EXISTS idx_org_ref_files_organization_id ON organization_reference_files(organization_id);
