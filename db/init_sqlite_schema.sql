-- db/init_sqlite_schema.sql
-- Схема базы данных для SQLite, соответствующая PostgreSQL-схеме
-- Обновлено: реализованы связи 1:N для организаций и файлов в шаблонах и исполнениях

-- 1. Создание таблицы пользователей (должностных лиц)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,              -- Уникальный идентификатор пользователя
    login TEXT UNIQUE NOT NULL,                        -- Уникальное имя для входа в систему
    password_hash TEXT NOT NULL,                       -- Хэш пароля пользователя для безопасной аутентификации
    rank TEXT,                                         -- Звание пользователя (например, "лейтенант")
    last_name TEXT,                                    -- Фамилия пользователя
    first_name TEXT,                                   -- Имя пользователя
    middle_name TEXT,                                  -- Отчество пользователя
    phone TEXT,                                        -- Контактный телефон пользователя
    is_active INTEGER DEFAULT 1,                       -- Флаг активности пользователя (может ли входить в систему) 1=TRUE, 0=FALSE
    is_admin INTEGER DEFAULT 0,                        -- Флаг администратора (имеет ли права администратора) 1=TRUE, 0=FALSE
    created_at TEXT DEFAULT (datetime('now', 'localtime')), -- Дата и время создания записи пользователя
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))  -- Дата и время последнего обновления записи пользователя
);

-- 2. Создание таблицы настроек поста
CREATE TABLE IF NOT EXISTS post_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),             -- Уникальный идентификатор записи настроек (ограничен одной записью)
    workplace_name TEXT,                               -- Название рабочего места (например, "Рабочее место дежурного")
    post_number TEXT,                                  -- Номер поста (например, "1")
    post_name TEXT,                                    -- Название поста (например, "Дежурство по части")
    use_persistent_reminders INTEGER DEFAULT 1,        -- Флаг использования настойчивых напоминаний 1=TRUE, 0=FALSE
    sound_enabled INTEGER DEFAULT 1,                   -- Флаг включения звуковых сигналов 1=TRUE, 0=FALSE
    custom_datetime TEXT,                              -- Пользовательская дата и время (для коррекции времени системы)
    background_image_path TEXT,                        -- Путь к фоновому изображению/эмблеме
    font_family TEXT DEFAULT 'Arial',                  -- Название шрифта интерфейса
    font_size INTEGER DEFAULT 12,                      -- Размер шрифта интерфейса
    background_color TEXT DEFAULT '#ecf0f1',           -- Цвет фонового оформления
    current_officer_id INTEGER,                        -- ID текущего дежурного
    print_font_family TEXT DEFAULT 'Arial',            -- Название шрифта для печати
    print_font_size INTEGER DEFAULT 12,                -- Размер шрифта для печати
    custom_time_label TEXT DEFAULT 'Местное время',    -- Метка для местного времени
    custom_time_offset_seconds INTEGER DEFAULT 0,      -- Смещение местного времени в секундах
    show_moscow_time INTEGER DEFAULT 1,                -- Показывать московское время 1=TRUE, 0=FALSE
    moscow_time_offset_seconds INTEGER DEFAULT 0       -- Смещение московского времени в секундах
);

-- === АЛГОРИТМЫ И ДЕЙСТВИЯ (ШАБЛОНЫ) ===

-- Таблица для хранения алгоритмов
CREATE TABLE IF NOT EXISTS algorithms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,              -- Уникальный идентификатор алгоритма
    name TEXT NOT NULL,                                -- Наименование алгоритма (например, "Алгоритм реагирования на пожар")
    category TEXT NOT NULL, -- Категория алгоритма (проверка будет в приложении)
    time_type TEXT NOT NULL, -- Тип времени выполнения алгоритма (проверка будет в приложении)
    description TEXT,                                  -- Описание алгоритма
    sort_order INTEGER DEFAULT 0,                     -- Порядковый номер для сортировки алгоритмов в списке
    created_at TEXT DEFAULT (datetime('now', 'localtime')), -- Дата и время создания записи алгоритма
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))  -- Дата и время последнего обновления записи алгоритма
    CHECK (category IN ('повседневная деятельность', 'боевая готовность', 'противодействие терроризму', 'кризисные ситуации')),
    CHECK (time_type IN ('оперативное', 'астрономическое'))
);

-- Таблица для хранения действий внутри алгоритмов
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,              -- Уникальный идентификатор действия
    algorithm_id INTEGER NOT NULL,                     -- Ссылка на родительский алгоритм
    description TEXT NOT NULL,                         -- Описание действия
    technical_text TEXT,                               -- Технический текст порядка выполнения
    start_offset TEXT,                                 -- Относительное время начала действия (смещение от начала алгоритма) в формате строки
    end_offset TEXT,                                   -- Относительное время окончания действия (смещение от начала алгоритма) в формате строки
    contact_phones TEXT,                               -- Телефоны для связи, связанные с этим действием
    report_materials TEXT,                             -- Пути или ссылки на отчетные материалы
    created_at TEXT DEFAULT (datetime('now', 'localtime')), -- Дата и время создания записи действия
    updated_at TEXT DEFAULT (datetime('now', 'localtime')), -- Дата и время последнего обновления записи действия
    FOREIGN KEY (algorithm_id) REFERENCES algorithms(id) ON DELETE CASCADE
);

-- Таблица для хранения запущенных/выполняемых экземпляров алгоритмов
CREATE TABLE IF NOT EXISTS algorithm_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,              -- Уникальный идентификатор экземпляра выполнения алгоритма
    algorithm_id INTEGER,                              -- Ссылка на исходный алгоритм (может быть NULL)
    -- ПОЛЯ ДЛЯ SNAPSHOT'А ДАННЫХ АЛГОРИТМА НА МОМЕНТ ЗАПУСКА
    snapshot_name TEXT NOT NULL,                       -- Копия name алгоритма на момент запуска
    snapshot_category TEXT NOT NULL,                   -- Копия category алгоритма на момент запуска
    snapshot_time_type TEXT NOT NULL,                  -- Копия time_type алгоритма на момент запуска
    snapshot_description TEXT,                         -- Копия description алгоритма на момент запуска
    started_at TEXT,                                   -- Фактическое время начала выполнения экземпляра
    completed_at TEXT,                                 -- Фактическое время завершения выполнения экземпляра
    status TEXT DEFAULT 'active', -- Статус выполнения экземпляра (проверка будет в приложении)
    -- ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ НА МОМЕНТ ЗАПУСКА
    created_by_user_id INTEGER,                        -- ID пользователя на момент запуска (для трассировки, может быть NULL если пользователь удален)
    created_by_user_display_name TEXT,                 -- Отображаемое имя пользователя на момент запуска (Фамилия И.О.)
    created_at TEXT DEFAULT (datetime('now', 'localtime')), -- Дата и время создания записи выполнения
    updated_at TEXT DEFAULT (datetime('now', 'localtime')), -- Дата и время последнего обновления записи выполнения
    FOREIGN KEY (algorithm_id) REFERENCES algorithms(id) ON DELETE CASCADE,
    CHECK (status IN ('active', 'completed', 'cancelled'))
);

-- Таблица для хранения выполнения действий в рамках запущенного алгоритма
CREATE TABLE IF NOT EXISTS action_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,              -- Уникальный идентификатор выполнения действия
    execution_id INTEGER NOT NULL,                     -- Ссылка на экземпляр выполнения алгоритма
    -- ПОЛЯ ДЛЯ SNAPSHOT'А СТАТИЧЕСКИХ ДАННЫХ ДЕЙСТВИЯ НА МОМЕНТ ПЛАНИРОВАНИЯ
    snapshot_description TEXT NOT NULL,                -- Копия description действия на момент планирования
    snapshot_technical_text TEXT,                      -- Копия technical_text действия на момент планирования
    snapshot_contact_phones TEXT,                      -- Копия contact_phones действия на момент планирования
    snapshot_report_materials TEXT,                    -- Копия report_materials действия на момент планирования
    -- РАССЧИТАННЫЕ АБСОЛЮТНЫЕ ВРЕМЕНА (вместо snapshot_*_offset шаблона действия)
    calculated_start_time TEXT,                        -- Рассчитанное (планируемое) АБСОЛЮТНОЕ время начала действия
    calculated_end_time TEXT,                          -- Рассчитанное (планируемое) АБСОЛЮТНОЕ время окончания действия
    -- ФАКТИЧЕСКИЕ ВРЕМЕНА ВЫПОЛНЕНИЯ
    actual_end_time TEXT,                              -- Фактическое время окончания выполнения действия (ОБЯЗАТЕЛЬНО)
    status TEXT DEFAULT 'pending', -- Статус выполнения действия (проверка будет в приложении)
    reported_to TEXT,                                  -- Информация о том, кому было доложено о выполнении действия
    notes TEXT,                                        -- Дополнительные заметки по выполнению действия
    created_at TEXT DEFAULT (datetime('now', 'localtime')), -- Дата и время создания записи выполнения действия
    updated_at TEXT DEFAULT (datetime('now', 'localtime')), -- Дата и время последнего обновления записи выполнения действия
    FOREIGN KEY (execution_id) REFERENCES algorithm_executions(id) ON DELETE CASCADE,
    CHECK (status IN ('pending', 'in_progress', 'completed', 'skipped'))
);

-- === ИНДЕКСЫ (АЛГОРИТМЫ И ДЕЙСТВИЯ) ===

-- Индекс для ускорения поиска действий по алгоритму
CREATE INDEX IF NOT EXISTS idx_actions_algorithm_id ON actions(algorithm_id);

-- Индексы для оптимизации запросов логов
CREATE INDEX IF NOT EXISTS idx_algorithm_executions_algorithm_id ON algorithm_executions(algorithm_id);
CREATE INDEX IF NOT EXISTS idx_algorithm_executions_status ON algorithm_executions(status);
CREATE INDEX IF NOT EXISTS idx_action_executions_execution_id ON action_executions(execution_id);
CREATE INDEX IF NOT EXISTS idx_action_executions_status ON action_executions(status);

-- НОВЫЙ ИНДЕКС: Для сортировки алгоритмов
CREATE INDEX IF NOT EXISTS idx_algorithms_sort_order ON algorithms(sort_order);

-- === НАЧАЛЬНЫЕ ДАННЫЕ ===

-- Вставка начальных настроек поста
INSERT OR IGNORE INTO post_settings (
    id, workplace_name, post_number, post_name, print_font_family, print_font_size,
    custom_time_label, custom_time_offset_seconds, show_moscow_time, moscow_time_offset_seconds,
    use_persistent_reminders, sound_enabled
) VALUES (
    1, 'Рабочее место дежурного', '1', 'Дежурство по части', 'Arial', 12,
    'Местное время', 0, 1, 0, 1, 1
);

-- Вставка начального администратора
INSERT OR IGNORE INTO users (
    login, password_hash, rank, last_name, first_name, middle_name, is_admin
) VALUES (
    'admin',
    'scrypt:32768:8:1$Atn4MrMt5x0I1XQr$a9f9efc8c59fdf784156004ace3717466af3e871cc9f4ee6a07ec72dc7319196fd741dde5d3458b21731c92e57fcc833eec0141a746d46237816dc016ef76475',
    'Администратор', 'Админов', 'Админ', 'Админович', 1
);

-- === МЕРОПРИЯТИЯ ===

-- Таблица для хранения шаблонов мероприятий
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,              -- Уникальный идентификатор мероприятия
    name TEXT NOT NULL,                                -- Наименование мероприятия
    description TEXT,                                  -- Описание мероприятия
    recurrence_rule TEXT,                              -- Правило повторения в формате JSON (гибкий формат)
    start_time TEXT,                                   -- Время начала мероприятия (относительно начала дня) в формате HH:MM
    end_time TEXT,                                     -- Время окончания мероприятия (относительно начала дня) в формате HH:MM
    notification_offset TEXT,                          -- Интервал времени для напоминания до начала (например, '1 hour')
    responsible_user_id INTEGER,                       -- Ответственный за мероприятие
    report_materials TEXT,                             -- Отчетный материал
    created_at TEXT DEFAULT (datetime('now', 'localtime')), -- Дата и время создания записи мероприятия
    updated_at TEXT DEFAULT (datetime('now', 'localtime')), -- Дата и время последнего обновления записи мероприятия
    FOREIGN KEY (responsible_user_id) REFERENCES users(id)
);

-- Таблица для хранения экземпляров мероприятий (Occurrences)
CREATE TABLE IF NOT EXISTS event_occurrences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,              -- Уникальный идентификатор экземпляра мероприятия
    event_id INTEGER NOT NULL,                         -- Ссылка на шаблон мероприятия
    calculated_start_datetime TEXT,                    -- Рассчитанная (планируемая) АБСОЛЮТНАЯ дата и время начала
    calculated_end_datetime TEXT,                      -- Рассчитанная (планируемая) АБСОЛЮТНАЯ дата и время окончания
    actual_start_datetime TEXT,                        -- Фактическая дата и время начала выполнения
    actual_end_datetime TEXT,                          -- Фактическая дата и время окончания выполнения
    status TEXT DEFAULT 'pending', -- Статус выполнения (проверка будет в приложении)
    notes TEXT,                                        -- Примечания к выполнению
    performed_by_user_id INTEGER,                      -- Пользователь, выполнивший мероприятие
    created_at TEXT DEFAULT (datetime('now', 'localtime')), -- Дата и время создания записи экземпляра
    updated_at TEXT DEFAULT (datetime('now', 'localtime')), -- Дата и время последнего обновления записи экземпляра
    FOREIGN KEY (event_id) REFERENCES events(id),
    CHECK (status IN ('pending', 'in_progress', 'completed', 'missed', 'cancelled'))
);

-- === ИНДЕКСЫ ДЛЯ МЕРОПРИЯТИЙ ===
CREATE INDEX IF NOT EXISTS idx_events_responsible_user_id ON events(responsible_user_id);
CREATE INDEX IF NOT EXISTS idx_event_occurrences_event_id ON event_occurrences(event_id);
CREATE INDEX IF NOT EXISTS idx_event_occurrences_calculated_start_datetime ON event_occurrences(calculated_start_datetime);
CREATE INDEX IF NOT EXISTS idx_event_occurrences_status ON event_occurrences(status);

-- === ОРГАНИЗАЦИИ И ФАЙЛЫ (ШАБЛОНЫ: 1:N ЦЕПОЧКА) ===
-- actions (1) -> organizations (N) -> organization_files (N)

-- Таблица организаций, привязанных к конкретному шаблону действия
CREATE TABLE IF NOT EXISTS organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id INTEGER NOT NULL,                      -- Связь один-ко-многим: организация принадлежит одному действию
    name TEXT NOT NULL,
    phone TEXT,
    contact_person TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (action_id) REFERENCES actions(id) ON DELETE CASCADE
);

-- Таблица справочных материалов организаций
CREATE TABLE IF NOT EXISTS organization_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER NOT NULL,                -- Связь один-ко-многим: файл принадлежит одной организации
    file_path TEXT NOT NULL,
    file_type TEXT DEFAULT 'other',
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    CHECK (file_type IN ('word', 'excel', 'pdf', 'image', 'other'))
);

-- === ОРГАНИЗАЦИИ И ФАЙЛЫ (ИСПОЛНЕНИЕ: 1:N ЦЕПОЧКА) ===
-- action_executions (1) -> exec_organizations (N) -> exec_organization_files (N)
-- Дублирует структуру шаблонов для хранения снимков/фактических данных на момент выполнения

CREATE TABLE IF NOT EXISTS exec_organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_execution_id INTEGER NOT NULL,            -- Связь один-ко-многим: организация привязана к выполнению действия
    name TEXT NOT NULL,
    phone TEXT,
    contact_person TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (action_execution_id) REFERENCES action_executions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exec_organization_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exec_organization_id INTEGER NOT NULL,           -- Связь один-ко-многим: файл привязан к организации в рамках выполнения
    file_path TEXT NOT NULL,
    file_type TEXT DEFAULT 'other',
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (exec_organization_id) REFERENCES exec_organizations(id) ON DELETE CASCADE,
    CHECK (file_type IN ('word', 'excel', 'pdf', 'image', 'other'))
);

-- === ИНДЕКСЫ ДЛЯ ОРГАНИЗАЦИЙ И ФАЙЛОВ ===
CREATE INDEX IF NOT EXISTS idx_organizations_action_id ON organizations(action_id);
CREATE INDEX IF NOT EXISTS idx_org_files_organization_id ON organization_files(organization_id);
CREATE INDEX IF NOT EXISTS idx_exec_organizations_action_execution_id ON exec_organizations(action_execution_id);
CREATE INDEX IF NOT EXISTS idx_exec_org_files_exec_organization_id ON exec_organization_files(exec_organization_id);