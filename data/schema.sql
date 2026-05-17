-- FitFlow SQLite schema
-- Источник данных: Working-in-IT/agentic-analytics-workshop (синтетический датасет)

-- events: 107 185 событий за период данных
CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    event_name TEXT NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    platform TEXT,
    properties JSON
);
CREATE INDEX idx_events_user ON events(user_id);
CREATE INDEX idx_events_name ON events(event_name);
CREATE INDEX idx_events_timestamp ON events(event_timestamp);

-- feedback: 1224 отзыва за период данных (351 из них nps_survey)
CREATE TABLE feedback (
    feedback_id TEXT PRIMARY KEY,
    user_id TEXT,
    feedback_date DATE NOT NULL,
    channel TEXT NOT NULL,
    rating INTEGER,
    text TEXT,
    platform TEXT
);
CREATE INDEX idx_feedback_channel ON feedback(channel);
