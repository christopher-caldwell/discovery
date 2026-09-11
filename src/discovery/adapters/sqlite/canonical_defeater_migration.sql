CREATE TABLE defeater_check (
    defeater_id INTEGER NOT NULL REFERENCES defeater(defeater_id),
    adversarial_check_id INTEGER NOT NULL REFERENCES adversarial_check(adversarial_check_id),
    link_reason TEXT NOT NULL CHECK(length(trim(link_reason)) > 0),
    linked_by_actor_id INTEGER NOT NULL REFERENCES actor(actor_id),
    dt_created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (defeater_id, adversarial_check_id)
) STRICT, WITHOUT ROWID;
CREATE INDEX idx_defeater_check_check ON defeater_check(adversarial_check_id, defeater_id);
INSERT INTO defeater_check
    (defeater_id, adversarial_check_id, link_reason, linked_by_actor_id, dt_created)
SELECT defeater_id, adversarial_check_id, 'Original owning check', created_by_actor_id, dt_created
FROM defeater;
CREATE TABLE conclusion_assessment (
    assessment_id INTEGER PRIMARY KEY,
    assessment_uuid TEXT NOT NULL UNIQUE,
    created_by_actor_id INTEGER NOT NULL REFERENCES actor(actor_id),
    phase_revision_id INTEGER NOT NULL REFERENCES phase_revision(phase_revision_id),
    snapshot_sha256 TEXT NOT NULL,
    assessment_json TEXT NOT NULL CHECK(json_valid(assessment_json)),
    dt_created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
) STRICT;
PRAGMA user_version = 6;
