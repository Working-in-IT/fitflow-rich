-- FitFlow SQLite schema
-- Источник данных: Working-in-IT/agentic-analytics-workshop (синтетический датасет)

-- events: 107 185 событий за период данных
CREATE TABLE events (
    event_id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,                 -- формат U<5 цифр>, напр. U00001
    event_name TEXT NOT NULL,
    event_timestamp TEXT NOT NULL,          -- ISO-8601 с T: 2025-01-01T06:45:46
    platform TEXT,                          -- ios / android / web
    properties TEXT                         -- JSON-строка (см. data/README.md)
);
CREATE INDEX idx_events_user ON events(user_id);
CREATE INDEX idx_events_name ON events(event_name);
CREATE INDEX idx_events_timestamp ON events(event_timestamp);

-- feedback: 1224 отзыва за период данных (351 из них nps_survey)
-- Note: feedback_id >= 1000000 — synthetic seed для воркшопа (см. data/README.md)
CREATE TABLE feedback (
    feedback_id INTEGER PRIMARY KEY,
    user_id TEXT,                           -- формат U<5 цифр>, может быть NULL
    feedback_date TEXT NOT NULL,            -- YYYY-MM-DD
    channel TEXT NOT NULL,                  -- nps_survey / google_play_review / app_store_review / in_app_feedback / support_ticket
    rating INTEGER,                          -- 1-5 для рейтинговых каналов, NULL иначе
    text TEXT,                               -- на русском
    platform TEXT                            -- ios / android / web
);
CREATE INDEX idx_feedback_channel ON feedback(channel);
