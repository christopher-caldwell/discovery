CREATE TABLE jobs (
    id INTEGER PRIMARY KEY,
    payload TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending'
        CHECK (state IN ('pending', 'done'))
);

CREATE TABLE outbox (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    event_key TEXT NOT NULL UNIQUE,
    processed_at TEXT,
    attempts INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE synthetic_effects (
    id INTEGER PRIMARY KEY,
    event_key TEXT NOT NULL,
    payload TEXT NOT NULL
);
