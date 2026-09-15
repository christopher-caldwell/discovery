ALTER TABLE assumption ADD COLUMN scope TEXT NOT NULL DEFAULT '';
ALTER TABLE assumption ADD COLUMN invalidation_condition TEXT NOT NULL DEFAULT '';

ALTER TABLE research_surface ADD COLUMN addition_reason TEXT NOT NULL DEFAULT '';

ALTER TABLE question_respondent ADD COLUMN created_by_actor_id INTEGER
    REFERENCES actor(actor_id);
ALTER TABLE question_respondent ADD COLUMN identity_status TEXT NOT NULL DEFAULT 'known'
    CHECK(identity_status IN ('known','unknown'));

ALTER TABLE claim ADD COLUMN verification_method TEXT NOT NULL DEFAULT 'inspection'
    CHECK(verification_method IN
        ('inspection','analysis','authoritative_record','test','experiment'));
ALTER TABLE claim ADD COLUMN verification_availability TEXT NOT NULL DEFAULT 'unavailable'
    CHECK(verification_availability IN ('available','unavailable','inaccessible'));
ALTER TABLE claim ADD COLUMN verification_rationale TEXT NOT NULL
    DEFAULT 'Schema 7 migration: the historical verification method was not recorded';
ALTER TABLE claim ADD COLUMN verification_limitations TEXT NOT NULL
    DEFAULT 'Reclassify verification explicitly before relying on this claim';

CREATE TABLE assumption_claim (
    assumption_id INTEGER NOT NULL REFERENCES assumption(assumption_id),
    claim_id INTEGER NOT NULL REFERENCES claim(claim_id),
    dependency_reason TEXT NOT NULL CHECK(length(trim(dependency_reason)) > 0),
    linked_by_actor_id INTEGER NOT NULL REFERENCES actor(actor_id),
    dt_created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (assumption_id, claim_id)
) STRICT, WITHOUT ROWID;
CREATE INDEX idx_assumption_claim_claim ON assumption_claim(claim_id, assumption_id);

CREATE TABLE assumption_decision (
    assumption_id INTEGER NOT NULL REFERENCES assumption(assumption_id),
    technical_decision_id INTEGER NOT NULL REFERENCES technical_decision(technical_decision_id),
    dependency_reason TEXT NOT NULL CHECK(length(trim(dependency_reason)) > 0),
    linked_by_actor_id INTEGER NOT NULL REFERENCES actor(actor_id),
    dt_created TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (assumption_id, technical_decision_id)
) STRICT, WITHOUT ROWID;
CREATE INDEX idx_assumption_decision_decision
    ON assumption_decision(technical_decision_id, assumption_id);

PRAGMA user_version = 7;
