CREATE TABLE actor (
      actor_id                                                  INTEGER                                         NOT NULL
    , actor_uuid                                                TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , actor_kind                                                TEXT                                            NOT NULL
    , display_name                                              TEXT                                            NOT NULL
    , provider_name                                             TEXT                                                NULL
    , model_name                                                TEXT                                                NULL
    , CONSTRAINT chk_actor_kind                                 CHECK (actor_kind IN ('human', 'model', 'system'))
    , PRIMARY KEY (actor_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_actor_uuid                              ON actor                                         (actor_uuid);
CREATE        INDEX idx_actor_kind                              ON actor                                         (actor_kind);


CREATE TABLE source_repository (
      source_repository_id                                      INTEGER                                         NOT NULL
    , source_repository_uuid                                    TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , repository_kind                                           TEXT                                            NOT NULL DEFAULT 'git'
    , repository_uri                                            TEXT                                            NOT NULL
    , repository_root                                           TEXT                                                NULL
    , baseline_revision                                         TEXT                                            NOT NULL
    , baseline_tree_hash                                        TEXT                                                NULL
    , baseline_status                                           TEXT                                            NOT NULL DEFAULT 'active'
    , drift_status                                              TEXT                                            NOT NULL DEFAULT 'current'
    , dt_last_checked                                           TEXT                                                NULL
    , drift_details                                             TEXT                                            NOT NULL DEFAULT ''
    , captured_by_actor_id                                      INTEGER                                         NOT NULL
    , CONSTRAINT chk_source_repository_kind                     CHECK (repository_kind IN ('git', 'filesystem'))
    , CONSTRAINT chk_source_repository_baseline_status           CHECK (baseline_status IN ('active', 'superseded'))
    , CONSTRAINT chk_source_repository_drift_status             CHECK (drift_status IN ('current', 'drifted'))
    , CONSTRAINT fk_source_repository_actor_id                  FOREIGN KEY (captured_by_actor_id)              REFERENCES actor (actor_id)
    , PRIMARY KEY (source_repository_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_source_repository_uuid                  ON source_repository                             (source_repository_uuid);
CREATE UNIQUE INDEX idx_source_repository_uri_revision          ON source_repository                             (repository_uri, baseline_revision);
CREATE UNIQUE INDEX idx_source_repository_active_uri            ON source_repository                             (repository_uri)
                                                                 WHERE baseline_status = 'active';
CREATE        INDEX idx_source_repository_actor_id              ON source_repository                             (captured_by_actor_id);
CREATE        INDEX idx_source_repository_drift_status          ON source_repository                             (drift_status);
CREATE        INDEX idx_source_repository_baseline_status       ON source_repository                             (baseline_status);


CREATE TABLE artifact (
      artifact_id                                               INTEGER                                         NOT NULL
    , artifact_uuid                                             TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , artifact_kind                                             TEXT                                            NOT NULL
    , artifact_sha256                                           TEXT                                            NOT NULL
    , media_type                                                TEXT                                            NOT NULL
    , byte_size                                                 INTEGER                                         NOT NULL
    , storage_path                                              TEXT                                            NOT NULL
    , origin_uri                                                TEXT                                                NULL
    , source_repository_id                                      INTEGER                                             NULL
    , source_revision                                           TEXT                                                NULL
    , source_locator                                            TEXT                                                NULL
    , captured_by_actor_id                                      INTEGER                                         NOT NULL
    , metadata_json                                             TEXT                                            NOT NULL DEFAULT '{}'
    , CONSTRAINT chk_artifact_byte_size                         CHECK (byte_size >= 0)
    , CONSTRAINT chk_artifact_sha256                            CHECK (length(artifact_sha256) = 64 AND artifact_sha256 NOT GLOB '*[^0-9a-f]*')
    , CONSTRAINT chk_artifact_metadata_json                     CHECK (json_valid(metadata_json))
    , CONSTRAINT fk_artifact_source_repository_id               FOREIGN KEY (source_repository_id)              REFERENCES source_repository (source_repository_id)
    , CONSTRAINT fk_artifact_actor_id                           FOREIGN KEY (captured_by_actor_id)              REFERENCES actor (actor_id)
    , PRIMARY KEY (artifact_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_artifact_uuid                           ON artifact                                      (artifact_uuid);
CREATE        INDEX idx_artifact_sha256                         ON artifact                                      (artifact_sha256);
CREATE        INDEX idx_artifact_source_revision                ON artifact                                      (source_repository_id, source_revision);
CREATE        INDEX idx_artifact_actor_id                       ON artifact                                      (captured_by_actor_id);


CREATE TABLE artifact_lineage (
      artifact_id                                               INTEGER                                         NOT NULL
    , parent_artifact_id                                        INTEGER                                         NOT NULL
    , relationship                                              TEXT                                            NOT NULL
    , CONSTRAINT chk_artifact_lineage_self                      CHECK (artifact_id <> parent_artifact_id)
    , CONSTRAINT fk_artifact_lineage_artifact_id                FOREIGN KEY (artifact_id)                      REFERENCES artifact (artifact_id)
    , CONSTRAINT fk_artifact_lineage_parent_artifact_id         FOREIGN KEY (parent_artifact_id)               REFERENCES artifact (artifact_id)
    , PRIMARY KEY (artifact_id, parent_artifact_id, relationship)
)
STRICT, WITHOUT ROWID
;
CREATE        INDEX idx_artifact_lineage_parent_artifact_id     ON artifact_lineage                             (parent_artifact_id, artifact_id);


CREATE TABLE discovery_run (
      discovery_run_id                                          INTEGER                                         NOT NULL
    , discovery_run_uuid                                        TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , run_title                                                 TEXT                                            NOT NULL
    , run_status                                                TEXT                                            NOT NULL DEFAULT 'active'
    , current_phase_no                                          INTEGER                                         NOT NULL DEFAULT 1
    , current_phase_revision_id                                 INTEGER                                             NULL
    , subagents_enabled                                         INTEGER                                         NOT NULL DEFAULT 0
    , subagent_mode                                             TEXT                                                NULL
    , input_artifact_id                                         INTEGER                                         NOT NULL
    , config_json                                               TEXT                                            NOT NULL DEFAULT '{}'
    , CONSTRAINT chk_discovery_run_status                       CHECK (run_status IN ('active', 'finalized', 'abandoned'))
    , CONSTRAINT chk_discovery_run_phase_no                     CHECK (current_phase_no BETWEEN 1 AND 4)
    , CONSTRAINT chk_discovery_run_subagents_enabled            CHECK (subagents_enabled IN (0, 1))
    , CONSTRAINT chk_discovery_run_subagent_mode                CHECK (
                                                                    (subagents_enabled = 0 AND subagent_mode IS NULL)
                                                                    OR
                                                                    (subagents_enabled = 1 AND subagent_mode IN ('partitioned', 'overlap'))
                                                                )
    , CONSTRAINT chk_discovery_run_config_json                  CHECK (json_valid(config_json))
    , CONSTRAINT fk_discovery_run_input_artifact_id             FOREIGN KEY (input_artifact_id)                REFERENCES artifact (artifact_id)
    , CONSTRAINT fk_discovery_run_current_phase_revision_id     FOREIGN KEY (current_phase_revision_id)         REFERENCES phase_revision (phase_revision_id)
    , PRIMARY KEY (discovery_run_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_discovery_run_uuid                      ON discovery_run                                 (discovery_run_uuid);
CREATE        INDEX idx_discovery_run_input_artifact_id         ON discovery_run                                 (input_artifact_id);
CREATE        INDEX idx_discovery_run_current_phase_revision    ON discovery_run                                 (current_phase_revision_id);
CREATE        INDEX idx_discovery_run_status                    ON discovery_run                                 (run_status);


CREATE TABLE phase_revision (
      phase_revision_id                                         INTEGER                                         NOT NULL
    , phase_revision_uuid                                       TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_completed                                              TEXT                                                NULL
    , phase_no                                                  INTEGER                                         NOT NULL
    , revision_no                                               INTEGER                                         NOT NULL
    , revision_status                                           TEXT                                            NOT NULL DEFAULT 'pending'
    , regression_reason                                         TEXT                                            NOT NULL DEFAULT ''
    , invalidated_by_phase_revision_id                          INTEGER                                             NULL
    , created_by_actor_id                                       INTEGER                                         NOT NULL
    , CONSTRAINT chk_phase_revision_phase_no                    CHECK (phase_no BETWEEN 1 AND 4)
    , CONSTRAINT chk_phase_revision_revision_no                 CHECK (revision_no >= 1)
    , CONSTRAINT chk_phase_revision_status                      CHECK (revision_status IN ('pending', 'active', 'completed', 'invalidated'))
    , CONSTRAINT chk_phase_revision_self                        CHECK (invalidated_by_phase_revision_id IS NULL OR invalidated_by_phase_revision_id <> phase_revision_id)
    , CONSTRAINT fk_phase_revision_invalidated_by               FOREIGN KEY (invalidated_by_phase_revision_id)   REFERENCES phase_revision (phase_revision_id)
    , CONSTRAINT fk_phase_revision_actor_id                     FOREIGN KEY (created_by_actor_id)               REFERENCES actor (actor_id)
    , PRIMARY KEY (phase_revision_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_phase_revision_uuid                     ON phase_revision                                (phase_revision_uuid);
CREATE UNIQUE INDEX idx_phase_revision_phase_revision           ON phase_revision                                (phase_no, revision_no);
CREATE UNIQUE INDEX idx_phase_revision_active                   ON phase_revision                                (revision_status)
                                                                 WHERE revision_status = 'active';
CREATE        INDEX idx_phase_revision_actor_id                 ON phase_revision                                (created_by_actor_id);
CREATE        INDEX idx_phase_revision_invalidated_by           ON phase_revision                                (invalidated_by_phase_revision_id);


CREATE TABLE clarification_question (
      clarification_question_id                                 INTEGER                                         NOT NULL
    , clarification_question_uuid                               TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , phase_revision_id                                         INTEGER                                         NOT NULL
    , question_text                                             TEXT                                            NOT NULL
    , is_blocking                                               INTEGER                                         NOT NULL DEFAULT 1
    , question_status                                           TEXT                                            NOT NULL DEFAULT 'open'
    , authority_category                                        TEXT                                            NOT NULL
    , authority_confidence                                      REAL                                            NOT NULL
    , authority_rationale                                       TEXT                                            NOT NULL
    , answer_text                                               TEXT                                                NULL
    , answered_by_actor_id                                      INTEGER                                             NULL
    , created_by_actor_id                                       INTEGER                                         NOT NULL
    , CONSTRAINT chk_clarification_question_blocking            CHECK (is_blocking IN (0, 1))
    , CONSTRAINT chk_clarification_question_status              CHECK (question_status IN ('open', 'answered', 'assumed', 'withdrawn'))
    , CONSTRAINT chk_clarification_question_confidence          CHECK (authority_confidence BETWEEN 0.0 AND 1.0)
    , CONSTRAINT fk_clarification_question_phase_revision_id    FOREIGN KEY (phase_revision_id)                REFERENCES phase_revision (phase_revision_id)
    , CONSTRAINT fk_clarification_question_answered_actor_id    FOREIGN KEY (answered_by_actor_id)             REFERENCES actor (actor_id)
    , CONSTRAINT fk_clarification_question_created_actor_id     FOREIGN KEY (created_by_actor_id)              REFERENCES actor (actor_id)
    , PRIMARY KEY (clarification_question_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_clarification_question_uuid             ON clarification_question                       (clarification_question_uuid);
CREATE        INDEX idx_clarification_question_phase_revision   ON clarification_question                       (phase_revision_id);
CREATE        INDEX idx_clarification_question_answered_actor   ON clarification_question                       (answered_by_actor_id);
CREATE        INDEX idx_clarification_question_created_actor    ON clarification_question                       (created_by_actor_id);
CREATE        INDEX idx_clarification_question_open_blocking    ON clarification_question                       (phase_revision_id, clarification_question_id)
                                                                 WHERE is_blocking = 1 AND question_status = 'open';


CREATE TABLE question_respondent (
      question_respondent_id                                    INTEGER                                         NOT NULL
    , question_respondent_uuid                                  TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , clarification_question_id                                 INTEGER                                         NOT NULL
    , respondent_rank                                           INTEGER                                         NOT NULL
    , respondent_kind                                           TEXT                                            NOT NULL
    , respondent_name                                           TEXT                                            NOT NULL
    , respondent_confidence                                     REAL                                            NOT NULL
    , rationale                                                 TEXT                                            NOT NULL
    , supporting_artifact_id                                    INTEGER                                             NULL
    , CONSTRAINT chk_question_respondent_rank                    CHECK (respondent_rank >= 1)
    , CONSTRAINT chk_question_respondent_kind                    CHECK (respondent_kind IN ('person', 'group', 'role'))
    , CONSTRAINT chk_question_respondent_confidence              CHECK (respondent_confidence BETWEEN 0.0 AND 1.0)
    , CONSTRAINT fk_question_respondent_question_id              FOREIGN KEY (clarification_question_id)        REFERENCES clarification_question (clarification_question_id)
    , CONSTRAINT fk_question_respondent_artifact_id              FOREIGN KEY (supporting_artifact_id)           REFERENCES artifact (artifact_id)
    , PRIMARY KEY (question_respondent_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_question_respondent_uuid                ON question_respondent                           (question_respondent_uuid);
CREATE UNIQUE INDEX idx_question_respondent_question_rank       ON question_respondent                           (clarification_question_id, respondent_rank);
CREATE        INDEX idx_question_respondent_artifact_id         ON question_respondent                           (supporting_artifact_id);


CREATE TABLE assumption (
      assumption_id                                             INTEGER                                         NOT NULL
    , assumption_uuid                                           TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , phase_revision_id                                         INTEGER                                         NOT NULL
    , clarification_question_id                                 INTEGER                                             NULL
    , assumption_text                                           TEXT                                            NOT NULL
    , impact                                                    TEXT                                            NOT NULL
    , assumption_status                                         TEXT                                            NOT NULL DEFAULT 'active'
    , justification                                             TEXT                                            NOT NULL
    , resolution_notes                                          TEXT                                            NOT NULL DEFAULT ''
    , created_by_actor_id                                       INTEGER                                         NOT NULL
    , CONSTRAINT chk_assumption_impact                          CHECK (impact IN ('contextual', 'material', 'critical'))
    , CONSTRAINT chk_assumption_status                          CHECK (assumption_status IN ('active', 'discharged', 'invalidated', 'superseded'))
    , CONSTRAINT fk_assumption_phase_revision_id                FOREIGN KEY (phase_revision_id)                REFERENCES phase_revision (phase_revision_id)
    , CONSTRAINT fk_assumption_question_id                      FOREIGN KEY (clarification_question_id)        REFERENCES clarification_question (clarification_question_id)
    , CONSTRAINT fk_assumption_actor_id                         FOREIGN KEY (created_by_actor_id)              REFERENCES actor (actor_id)
    , PRIMARY KEY (assumption_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_assumption_uuid                         ON assumption                                    (assumption_uuid);
CREATE        INDEX idx_assumption_phase_revision               ON assumption                                    (phase_revision_id);
CREATE        INDEX idx_assumption_question_id                  ON assumption                                    (clarification_question_id);
CREATE        INDEX idx_assumption_actor_id                     ON assumption                                    (created_by_actor_id);
CREATE        INDEX idx_assumption_active                       ON assumption                                    (phase_revision_id, impact)
                                                                 WHERE assumption_status = 'active';


CREATE TABLE research_need (
      research_need_id                                          INTEGER                                         NOT NULL
    , research_need_uuid                                        TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , phase_revision_id                                         INTEGER                                         NOT NULL
    , need_statement                                            TEXT                                            NOT NULL
    , why_it_matters                                            TEXT                                            NOT NULL
    , impact                                                    TEXT                                            NOT NULL
    , need_status                                               TEXT                                            NOT NULL DEFAULT 'open'
    , source_artifact_id                                        INTEGER                                             NULL
    , created_by_actor_id                                       INTEGER                                         NOT NULL
    , CONSTRAINT chk_research_need_impact                       CHECK (impact IN ('contextual', 'material', 'critical'))
    , CONSTRAINT chk_research_need_status                       CHECK (need_status IN ('open', 'covered', 'answered', 'superseded'))
    , CONSTRAINT fk_research_need_phase_revision_id             FOREIGN KEY (phase_revision_id)                REFERENCES phase_revision (phase_revision_id)
    , CONSTRAINT fk_research_need_source_artifact_id            FOREIGN KEY (source_artifact_id)               REFERENCES artifact (artifact_id)
    , CONSTRAINT fk_research_need_actor_id                      FOREIGN KEY (created_by_actor_id)              REFERENCES actor (actor_id)
    , PRIMARY KEY (research_need_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_research_need_uuid                      ON research_need                                 (research_need_uuid);
CREATE        INDEX idx_research_need_phase_revision            ON research_need                                 (phase_revision_id);
CREATE        INDEX idx_research_need_source_artifact           ON research_need                                 (source_artifact_id);
CREATE        INDEX idx_research_need_actor_id                  ON research_need                                 (created_by_actor_id);
CREATE        INDEX idx_research_need_open                      ON research_need                                 (phase_revision_id, impact)
                                                                 WHERE need_status = 'open';


CREATE TABLE research_lane (
      research_lane_id                                          INTEGER                                         NOT NULL
    , research_lane_uuid                                        TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , phase_revision_id                                         INTEGER                                         NOT NULL
    , parent_research_lane_id                                   INTEGER                                             NULL
    , lane_question                                             TEXT                                            NOT NULL
    , why_it_matters                                            TEXT                                            NOT NULL
    , impact                                                    TEXT                                            NOT NULL
    , scope                                                     TEXT                                            NOT NULL
    , out_of_scope                                              TEXT                                            NOT NULL DEFAULT ''
    , evidence_profile                                          TEXT                                            NOT NULL
    , lane_status                                               TEXT                                            NOT NULL DEFAULT 'planned'
    , closure_iteration                                         INTEGER                                         NOT NULL DEFAULT 0
    , created_by_actor_id                                       INTEGER                                         NOT NULL
    , CONSTRAINT chk_research_lane_impact                       CHECK (impact IN ('contextual', 'material', 'critical'))
    , CONSTRAINT chk_research_lane_status                       CHECK (lane_status IN ('planned', 'active', 'procedurally_exhausted', 'blocked', 'superseded'))
    , CONSTRAINT chk_research_lane_closure_iteration            CHECK (closure_iteration >= 0)
    , CONSTRAINT chk_research_lane_self                         CHECK (parent_research_lane_id IS NULL OR parent_research_lane_id <> research_lane_id)
    , CONSTRAINT fk_research_lane_phase_revision_id             FOREIGN KEY (phase_revision_id)                REFERENCES phase_revision (phase_revision_id)
    , CONSTRAINT fk_research_lane_parent_id                     FOREIGN KEY (parent_research_lane_id)          REFERENCES research_lane (research_lane_id)
    , CONSTRAINT fk_research_lane_actor_id                      FOREIGN KEY (created_by_actor_id)              REFERENCES actor (actor_id)
    , PRIMARY KEY (research_lane_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_research_lane_uuid                      ON research_lane                                 (research_lane_uuid);
CREATE        INDEX idx_research_lane_phase_revision            ON research_lane                                 (phase_revision_id);
CREATE        INDEX idx_research_lane_parent_id                 ON research_lane                                 (parent_research_lane_id);
CREATE        INDEX idx_research_lane_actor_id                  ON research_lane                                 (created_by_actor_id);
CREATE        INDEX idx_research_lane_active                    ON research_lane                                 (phase_revision_id, impact)
                                                                 WHERE lane_status IN ('planned', 'active', 'blocked');


CREATE TABLE research_lane_need (
      research_lane_id                                          INTEGER                                         NOT NULL
    , research_need_id                                          INTEGER                                         NOT NULL
    , CONSTRAINT fk_research_lane_need_lane_id                  FOREIGN KEY (research_lane_id)                 REFERENCES research_lane (research_lane_id)
    , CONSTRAINT fk_research_lane_need_need_id                  FOREIGN KEY (research_need_id)                 REFERENCES research_need (research_need_id)
    , PRIMARY KEY (research_lane_id, research_need_id)
)
STRICT, WITHOUT ROWID
;
CREATE        INDEX idx_research_lane_need_need_id              ON research_lane_need                            (research_need_id, research_lane_id);


CREATE TABLE research_lane_dependency (
      research_lane_id                                          INTEGER                                         NOT NULL
    , depends_on_research_lane_id                               INTEGER                                         NOT NULL
    , dependency_reason                                         TEXT                                            NOT NULL
    , CONSTRAINT chk_research_lane_dependency_self              CHECK (research_lane_id <> depends_on_research_lane_id)
    , CONSTRAINT fk_research_lane_dependency_lane_id            FOREIGN KEY (research_lane_id)                 REFERENCES research_lane (research_lane_id)
    , CONSTRAINT fk_research_lane_dependency_depends_on_id      FOREIGN KEY (depends_on_research_lane_id)      REFERENCES research_lane (research_lane_id)
    , PRIMARY KEY (research_lane_id, depends_on_research_lane_id)
)
STRICT, WITHOUT ROWID
;
CREATE        INDEX idx_research_lane_dependency_depends_on     ON research_lane_dependency                      (depends_on_research_lane_id, research_lane_id);


CREATE TABLE research_surface (
      research_surface_id                                       INTEGER                                         NOT NULL
    , research_surface_uuid                                     TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , phase_revision_id                                         INTEGER                                         NOT NULL
    , research_lane_id                                          INTEGER                                             NULL
    , surface_kind                                              TEXT                                            NOT NULL
    , surface_name                                              TEXT                                            NOT NULL
    , is_mandatory                                              INTEGER                                         NOT NULL DEFAULT 1
    , disposition                                               TEXT                                            NOT NULL DEFAULT 'pending'
    , disposition_reason                                        TEXT                                            NOT NULL DEFAULT ''
    , dt_dispositioned                                          TEXT                                                NULL
    , created_by_actor_id                                       INTEGER                                         NOT NULL
    , CONSTRAINT chk_research_surface_mandatory                 CHECK (is_mandatory IN (0, 1))
    , CONSTRAINT chk_research_surface_disposition               CHECK (disposition IN ('pending', 'searched', 'unavailable', 'inaccessible', 'not_applicable'))
    , CONSTRAINT fk_research_surface_phase_revision_id          FOREIGN KEY (phase_revision_id)                REFERENCES phase_revision (phase_revision_id)
    , CONSTRAINT fk_research_surface_lane_id                    FOREIGN KEY (research_lane_id)                 REFERENCES research_lane (research_lane_id)
    , CONSTRAINT fk_research_surface_actor_id                   FOREIGN KEY (created_by_actor_id)              REFERENCES actor (actor_id)
    , PRIMARY KEY (research_surface_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_research_surface_uuid                   ON research_surface                              (research_surface_uuid);
CREATE        INDEX idx_research_surface_phase_revision         ON research_surface                              (phase_revision_id);
CREATE        INDEX idx_research_surface_lane_id                ON research_surface                              (research_lane_id);
CREATE        INDEX idx_research_surface_actor_id               ON research_surface                              (created_by_actor_id);
CREATE        INDEX idx_research_surface_pending_mandatory      ON research_surface                              (phase_revision_id, research_lane_id, research_surface_id)
                                                                 WHERE is_mandatory = 1 AND disposition = 'pending';


CREATE TABLE research_method (
      research_method_id                                        INTEGER                                         NOT NULL
    , research_method_uuid                                      TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , research_lane_id                                          INTEGER                                         NOT NULL
    , method_category                                           TEXT                                            NOT NULL
    , method_name                                               TEXT                                            NOT NULL
    , iteration_no                                              INTEGER                                         NOT NULL DEFAULT 0
    , is_mandatory                                              INTEGER                                         NOT NULL DEFAULT 1
    , disposition                                               TEXT                                            NOT NULL DEFAULT 'pending'
    , disposition_reason                                        TEXT                                            NOT NULL DEFAULT ''
    , CONSTRAINT chk_research_method_category                   CHECK (method_category IN ('primary', 'closure'))
    , CONSTRAINT chk_research_method_iteration_no               CHECK (iteration_no >= 0)
    , CONSTRAINT chk_research_method_mandatory                  CHECK (is_mandatory IN (0, 1))
    , CONSTRAINT chk_research_method_disposition                CHECK (disposition IN ('pending', 'completed', 'unavailable', 'inaccessible', 'not_applicable'))
    , CONSTRAINT fk_research_method_lane_id                     FOREIGN KEY (research_lane_id)                 REFERENCES research_lane (research_lane_id)
    , PRIMARY KEY (research_method_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_research_method_uuid                    ON research_method                               (research_method_uuid);
CREATE UNIQUE INDEX idx_research_method_lane_name_iteration     ON research_method                               (research_lane_id, method_category, method_name, iteration_no);
CREATE        INDEX idx_research_method_pending_mandatory       ON research_method                               (research_lane_id, method_category, iteration_no)
                                                                 WHERE is_mandatory = 1 AND disposition = 'pending';


CREATE TABLE research_activity (
      research_activity_id                                      INTEGER                                         NOT NULL
    , research_activity_uuid                                    TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , research_lane_id                                          INTEGER                                             NULL
    , research_surface_id                                       INTEGER                                             NULL
    , research_method_id                                        INTEGER                                             NULL
    , agent_run_id                                              INTEGER                                             NULL
    , actor_id                                                  INTEGER                                         NOT NULL
    , activity_kind                                             TEXT                                            NOT NULL
    , query_or_action                                           TEXT                                            NOT NULL
    , result_summary                                            TEXT                                            NOT NULL
    , result_artifact_id                                        INTEGER                                             NULL
    , CONSTRAINT fk_research_activity_lane_id                   FOREIGN KEY (research_lane_id)                 REFERENCES research_lane (research_lane_id)
    , CONSTRAINT fk_research_activity_surface_id                FOREIGN KEY (research_surface_id)              REFERENCES research_surface (research_surface_id)
    , CONSTRAINT fk_research_activity_method_id                 FOREIGN KEY (research_method_id)               REFERENCES research_method (research_method_id)
    , CONSTRAINT fk_research_activity_agent_run_id              FOREIGN KEY (agent_run_id)                     REFERENCES agent_run (agent_run_id)
    , CONSTRAINT fk_research_activity_actor_id                  FOREIGN KEY (actor_id)                         REFERENCES actor (actor_id)
    , CONSTRAINT fk_research_activity_artifact_id               FOREIGN KEY (result_artifact_id)               REFERENCES artifact (artifact_id)
    , PRIMARY KEY (research_activity_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_research_activity_uuid                  ON research_activity                             (research_activity_uuid);
CREATE        INDEX idx_research_activity_lane_id               ON research_activity                             (research_lane_id);
CREATE        INDEX idx_research_activity_surface_id            ON research_activity                             (research_surface_id);
CREATE        INDEX idx_research_activity_method_id             ON research_activity                             (research_method_id);
CREATE        INDEX idx_research_activity_agent_run_id          ON research_activity                             (agent_run_id);
CREATE        INDEX idx_research_activity_actor_id              ON research_activity                             (actor_id);
CREATE        INDEX idx_research_activity_artifact_id           ON research_activity                             (result_artifact_id);


CREATE TABLE lead (
      lead_id                                                   INTEGER                                         NOT NULL
    , lead_uuid                                                 TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , research_lane_id                                          INTEGER                                         NOT NULL
    , source_research_activity_id                               INTEGER                                             NULL
    , child_research_lane_id                                    INTEGER                                             NULL
    , clarification_question_id                                 INTEGER                                             NULL
    , duplicate_of_lead_id                                      INTEGER                                             NULL
    , lead_description                                          TEXT                                            NOT NULL
    , impact                                                    TEXT                                            NOT NULL
    , lead_status                                               TEXT                                            NOT NULL DEFAULT 'pending'
    , disposition_reason                                        TEXT                                            NOT NULL DEFAULT ''
    , created_by_actor_id                                       INTEGER                                         NOT NULL
    , CONSTRAINT chk_lead_impact                                CHECK (impact IN ('contextual', 'material', 'critical'))
    , CONSTRAINT chk_lead_status                                CHECK (lead_status IN ('pending', 'investigated', 'irrelevant', 'duplicate', 'inaccessible', 'requires_human_input'))
    , CONSTRAINT chk_lead_self                                  CHECK (duplicate_of_lead_id IS NULL OR duplicate_of_lead_id <> lead_id)
    , CONSTRAINT fk_lead_lane_id                                FOREIGN KEY (research_lane_id)                 REFERENCES research_lane (research_lane_id)
    , CONSTRAINT fk_lead_activity_id                            FOREIGN KEY (source_research_activity_id)      REFERENCES research_activity (research_activity_id)
    , CONSTRAINT fk_lead_child_lane_id                          FOREIGN KEY (child_research_lane_id)           REFERENCES research_lane (research_lane_id)
    , CONSTRAINT fk_lead_question_id                            FOREIGN KEY (clarification_question_id)        REFERENCES clarification_question (clarification_question_id)
    , CONSTRAINT fk_lead_duplicate_id                           FOREIGN KEY (duplicate_of_lead_id)             REFERENCES lead (lead_id)
    , CONSTRAINT fk_lead_actor_id                               FOREIGN KEY (created_by_actor_id)              REFERENCES actor (actor_id)
    , PRIMARY KEY (lead_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_lead_uuid                               ON lead                                          (lead_uuid);
CREATE        INDEX idx_lead_lane_id                            ON lead                                          (research_lane_id);
CREATE        INDEX idx_lead_activity_id                        ON lead                                          (source_research_activity_id);
CREATE        INDEX idx_lead_child_lane_id                      ON lead                                          (child_research_lane_id);
CREATE        INDEX idx_lead_question_id                        ON lead                                          (clarification_question_id);
CREATE        INDEX idx_lead_duplicate_id                       ON lead                                          (duplicate_of_lead_id);
CREATE        INDEX idx_lead_actor_id                           ON lead                                          (created_by_actor_id);
CREATE        INDEX idx_lead_pending                            ON lead                                          (research_lane_id, impact, lead_id)
                                                                 WHERE lead_status = 'pending';


CREATE TABLE agent_run (
      agent_run_id                                              INTEGER                                         NOT NULL
    , agent_run_uuid                                            TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_started                                                TEXT                                                NULL
    , dt_completed                                              TEXT                                                NULL
    , phase_revision_id                                         INTEGER                                         NOT NULL
    , research_lane_id                                          INTEGER                                             NULL
    , actor_id                                                  INTEGER                                         NOT NULL
    , run_role                                                  TEXT                                            NOT NULL
    , overlap_group_uuid                                        TEXT                                                NULL
    , run_status                                                TEXT                                            NOT NULL DEFAULT 'pending'
    , run_outcome                                               TEXT                                                NULL
    , status_details                                            TEXT                                            NOT NULL DEFAULT ''
    , lease_token_sha256                                        TEXT                                                NULL
    , dt_lease_expires                                          TEXT                                                NULL
    , context_artifact_id                                       INTEGER                                             NULL
    , report_artifact_id                                        INTEGER                                             NULL
    , CONSTRAINT chk_agent_run_role                             CHECK (run_role IN ('primary', 'replica', 'semantic_verifier', 'reconciler', 'adversarial_challenger'))
    , CONSTRAINT chk_agent_run_status                           CHECK (run_status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
    , CONSTRAINT chk_agent_run_outcome                          CHECK (run_outcome IS NULL OR run_outcome IN ('passed', 'findings', 'no_findings', 'inconclusive'))
    , CONSTRAINT chk_agent_run_lease_hash                       CHECK (lease_token_sha256 IS NULL OR (length(lease_token_sha256) = 64 AND lease_token_sha256 NOT GLOB '*[^0-9a-f]*'))
    , CONSTRAINT chk_agent_run_lease_pair                       CHECK ((lease_token_sha256 IS NULL AND dt_lease_expires IS NULL) OR (lease_token_sha256 IS NOT NULL AND dt_lease_expires IS NOT NULL))
    , CONSTRAINT fk_agent_run_phase_revision_id                 FOREIGN KEY (phase_revision_id)                REFERENCES phase_revision (phase_revision_id)
    , CONSTRAINT fk_agent_run_lane_id                           FOREIGN KEY (research_lane_id)                 REFERENCES research_lane (research_lane_id)
    , CONSTRAINT fk_agent_run_actor_id                          FOREIGN KEY (actor_id)                         REFERENCES actor (actor_id)
    , CONSTRAINT fk_agent_run_context_artifact_id               FOREIGN KEY (context_artifact_id)              REFERENCES artifact (artifact_id)
    , CONSTRAINT fk_agent_run_report_artifact_id                FOREIGN KEY (report_artifact_id)               REFERENCES artifact (artifact_id)
    , PRIMARY KEY (agent_run_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_agent_run_uuid                          ON agent_run                                     (agent_run_uuid);
CREATE        INDEX idx_agent_run_phase_revision                ON agent_run                                     (phase_revision_id);
CREATE        INDEX idx_agent_run_lane_id                       ON agent_run                                     (research_lane_id);
CREATE        INDEX idx_agent_run_actor_id                      ON agent_run                                     (actor_id);
CREATE        INDEX idx_agent_run_context_artifact              ON agent_run                                     (context_artifact_id);
CREATE        INDEX idx_agent_run_report_artifact               ON agent_run                                     (report_artifact_id);
CREATE        INDEX idx_agent_run_overlap_group                 ON agent_run                                     (overlap_group_uuid, research_lane_id);
CREATE        INDEX idx_agent_run_incomplete                    ON agent_run                                     (phase_revision_id, research_lane_id, run_role)
                                                                 WHERE run_status IN ('pending', 'running');
CREATE        INDEX idx_agent_run_lease_expires                 ON agent_run                                     (dt_lease_expires)
                                                                 WHERE lease_token_sha256 IS NOT NULL;


CREATE TABLE evidence (
      evidence_id                                               INTEGER                                         NOT NULL
    , evidence_uuid                                             TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , research_lane_id                                          INTEGER                                             NULL
    , artifact_id                                               INTEGER                                         NOT NULL
    , evidence_kind                                             TEXT                                            NOT NULL
    , source_locator                                            TEXT                                            NOT NULL
    , observation                                               TEXT                                            NOT NULL
    , evidence_status                                           TEXT                                            NOT NULL DEFAULT 'active'
    , agent_run_id                                              INTEGER                                             NULL
    , extracted_by_actor_id                                     INTEGER                                         NOT NULL
    , superseded_by_evidence_id                                 INTEGER                                             NULL
    , CONSTRAINT chk_evidence_status                            CHECK (evidence_status IN ('active', 'retracted', 'superseded'))
    , CONSTRAINT chk_evidence_self                              CHECK (superseded_by_evidence_id IS NULL OR superseded_by_evidence_id <> evidence_id)
    , CONSTRAINT fk_evidence_lane_id                            FOREIGN KEY (research_lane_id)                 REFERENCES research_lane (research_lane_id)
    , CONSTRAINT fk_evidence_artifact_id                        FOREIGN KEY (artifact_id)                      REFERENCES artifact (artifact_id)
    , CONSTRAINT fk_evidence_agent_run_id                       FOREIGN KEY (agent_run_id)                     REFERENCES agent_run (agent_run_id)
    , CONSTRAINT fk_evidence_actor_id                           FOREIGN KEY (extracted_by_actor_id)            REFERENCES actor (actor_id)
    , CONSTRAINT fk_evidence_superseded_by                      FOREIGN KEY (superseded_by_evidence_id)        REFERENCES evidence (evidence_id)
    , PRIMARY KEY (evidence_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_evidence_uuid                           ON evidence                                      (evidence_uuid);
CREATE        INDEX idx_evidence_lane_id                        ON evidence                                      (research_lane_id);
CREATE        INDEX idx_evidence_artifact_id                    ON evidence                                      (artifact_id);
CREATE        INDEX idx_evidence_agent_run_id                   ON evidence                                      (agent_run_id);
CREATE        INDEX idx_evidence_actor_id                       ON evidence                                      (extracted_by_actor_id);
CREATE        INDEX idx_evidence_superseded_by                  ON evidence                                      (superseded_by_evidence_id);
CREATE        INDEX idx_evidence_active                         ON evidence                                      (research_lane_id, evidence_kind)
                                                                 WHERE evidence_status = 'active';


CREATE TABLE claim (
      claim_id                                                  INTEGER                                         NOT NULL
    , claim_uuid                                                TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , phase_revision_id                                         INTEGER                                         NOT NULL
    , research_lane_id                                          INTEGER                                             NULL
    , claim_kind                                                TEXT                                            NOT NULL
    , impact                                                    TEXT                                            NOT NULL
    , claim_statement                                           TEXT                                            NOT NULL
    , claim_status                                              TEXT                                            NOT NULL DEFAULT 'proposed'
    , is_canonical                                              INTEGER                                         NOT NULL DEFAULT 0
    , confidence                                                REAL                                                NULL
    , agent_run_id                                              INTEGER                                             NULL
    , created_by_actor_id                                       INTEGER                                         NOT NULL
    , superseded_by_claim_id                                    INTEGER                                             NULL
    , CONSTRAINT chk_claim_impact                               CHECK (impact IN ('contextual', 'material', 'critical'))
    , CONSTRAINT chk_claim_status                               CHECK (claim_status IN ('proposed', 'evidenced', 'admissible', 'contested', 'rejected', 'superseded', 'survived'))
    , CONSTRAINT chk_claim_canonical                            CHECK (is_canonical IN (0, 1))
    , CONSTRAINT chk_claim_confidence                           CHECK (confidence IS NULL OR confidence BETWEEN 0.0 AND 1.0)
    , CONSTRAINT chk_claim_self                                 CHECK (superseded_by_claim_id IS NULL OR superseded_by_claim_id <> claim_id)
    , CONSTRAINT fk_claim_phase_revision_id                    FOREIGN KEY (phase_revision_id)                REFERENCES phase_revision (phase_revision_id)
    , CONSTRAINT fk_claim_lane_id                              FOREIGN KEY (research_lane_id)                 REFERENCES research_lane (research_lane_id)
    , CONSTRAINT fk_claim_agent_run_id                         FOREIGN KEY (agent_run_id)                     REFERENCES agent_run (agent_run_id)
    , CONSTRAINT fk_claim_actor_id                             FOREIGN KEY (created_by_actor_id)              REFERENCES actor (actor_id)
    , CONSTRAINT fk_claim_superseded_by                        FOREIGN KEY (superseded_by_claim_id)           REFERENCES claim (claim_id)
    , PRIMARY KEY (claim_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_claim_uuid                              ON claim                                         (claim_uuid);
CREATE        INDEX idx_claim_phase_revision                    ON claim                                         (phase_revision_id);
CREATE        INDEX idx_claim_lane_id                           ON claim                                         (research_lane_id);
CREATE        INDEX idx_claim_agent_run_id                      ON claim                                         (agent_run_id);
CREATE        INDEX idx_claim_actor_id                          ON claim                                         (created_by_actor_id);
CREATE        INDEX idx_claim_superseded_by                     ON claim                                         (superseded_by_claim_id);
CREATE        INDEX idx_claim_status_impact_lane                ON claim                                         (claim_status, impact, research_lane_id);
CREATE        INDEX idx_claim_unresolved_material               ON claim                                         (research_lane_id, claim_id)
                                                                 WHERE impact IN ('material', 'critical') AND claim_status IN ('proposed', 'evidenced', 'contested');


CREATE TABLE argument (
      argument_id                                               INTEGER                                         NOT NULL
    , argument_uuid                                             TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , claim_id                                                  INTEGER                                         NOT NULL
    , argument_role                                             TEXT                                            NOT NULL
    , reasoning                                                 TEXT                                            NOT NULL
    , limitations                                               TEXT                                            NOT NULL DEFAULT ''
    , verification_status                                      TEXT                                            NOT NULL DEFAULT 'pending'
    , verified_by_actor_id                                      INTEGER                                             NULL
    , dt_verified                                               TEXT                                                NULL
    , agent_run_id                                              INTEGER                                             NULL
    , created_by_actor_id                                       INTEGER                                         NOT NULL
    , CONSTRAINT chk_argument_role                              CHECK (argument_role IN ('supports', 'refutes', 'qualifies'))
    , CONSTRAINT chk_argument_verification_status               CHECK (verification_status IN ('pending', 'passed', 'failed', 'inconclusive'))
    , CONSTRAINT fk_argument_claim_id                           FOREIGN KEY (claim_id)                         REFERENCES claim (claim_id)
    , CONSTRAINT fk_argument_verified_actor_id                  FOREIGN KEY (verified_by_actor_id)             REFERENCES actor (actor_id)
    , CONSTRAINT fk_argument_agent_run_id                       FOREIGN KEY (agent_run_id)                     REFERENCES agent_run (agent_run_id)
    , CONSTRAINT fk_argument_created_actor_id                   FOREIGN KEY (created_by_actor_id)              REFERENCES actor (actor_id)
    , PRIMARY KEY (argument_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_argument_uuid                           ON argument                                      (argument_uuid);
CREATE        INDEX idx_argument_claim_id                       ON argument                                      (claim_id);
CREATE        INDEX idx_argument_verified_actor_id              ON argument                                      (verified_by_actor_id);
CREATE        INDEX idx_argument_agent_run_id                   ON argument                                      (agent_run_id);
CREATE        INDEX idx_argument_created_actor_id               ON argument                                      (created_by_actor_id);
CREATE        INDEX idx_argument_pending_verification           ON argument                                      (claim_id, argument_role)
                                                                 WHERE verification_status = 'pending';


CREATE TABLE argument_evidence (
      argument_id                                               INTEGER                                         NOT NULL
    , evidence_id                                               INTEGER                                         NOT NULL
    , CONSTRAINT fk_argument_evidence_argument_id               FOREIGN KEY (argument_id)                     REFERENCES argument (argument_id)
    , CONSTRAINT fk_argument_evidence_evidence_id               FOREIGN KEY (evidence_id)                     REFERENCES evidence (evidence_id)
    , PRIMARY KEY (argument_id, evidence_id)
)
STRICT, WITHOUT ROWID
;
CREATE        INDEX idx_argument_evidence_evidence_id           ON argument_evidence                            (evidence_id, argument_id);


CREATE TABLE agent_claim_position (
      canonical_claim_id                                        INTEGER                                         NOT NULL
    , agent_run_id                                              INTEGER                                         NOT NULL
    , source_claim_id                                           INTEGER                                             NULL
    , position                                                  TEXT                                            NOT NULL
    , rationale                                                 TEXT                                            NOT NULL DEFAULT ''
    , CONSTRAINT chk_agent_claim_position                       CHECK (position IN ('support', 'refute', 'not_seen'))
    , CONSTRAINT chk_agent_claim_source                         CHECK (
                                                                    (position = 'not_seen' AND source_claim_id IS NULL)
                                                                    OR
                                                                    (position IN ('support', 'refute') AND source_claim_id IS NOT NULL)
                                                                )
    , CONSTRAINT fk_agent_claim_canonical_claim_id              FOREIGN KEY (canonical_claim_id)              REFERENCES claim (claim_id)
    , CONSTRAINT fk_agent_claim_agent_run_id                    FOREIGN KEY (agent_run_id)                    REFERENCES agent_run (agent_run_id)
    , CONSTRAINT fk_agent_claim_source_claim_id                 FOREIGN KEY (source_claim_id)                 REFERENCES claim (claim_id)
    , PRIMARY KEY (canonical_claim_id, agent_run_id)
)
STRICT, WITHOUT ROWID
;
CREATE        INDEX idx_agent_claim_position_agent_run          ON agent_claim_position                         (agent_run_id, canonical_claim_id);
CREATE        INDEX idx_agent_claim_position_source_claim       ON agent_claim_position                         (source_claim_id);


CREATE TABLE implementation_strategy (
      implementation_strategy_id                                INTEGER                                         NOT NULL
    , implementation_strategy_uuid                              TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , phase_revision_id                                         INTEGER                                         NOT NULL
    , strategy_name                                             TEXT                                            NOT NULL
    , strategy_description                                      TEXT                                            NOT NULL
    , strategy_status                                           TEXT                                            NOT NULL DEFAULT 'candidate'
    , created_by_actor_id                                       INTEGER                                         NOT NULL
    , CONSTRAINT chk_implementation_strategy_status             CHECK (strategy_status IN ('candidate', 'selected', 'rejected', 'superseded'))
    , CONSTRAINT fk_implementation_strategy_phase_revision_id   FOREIGN KEY (phase_revision_id)                REFERENCES phase_revision (phase_revision_id)
    , CONSTRAINT fk_implementation_strategy_actor_id            FOREIGN KEY (created_by_actor_id)              REFERENCES actor (actor_id)
    , PRIMARY KEY (implementation_strategy_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_implementation_strategy_uuid            ON implementation_strategy                       (implementation_strategy_uuid);
CREATE        INDEX idx_implementation_strategy_phase_revision  ON implementation_strategy                       (phase_revision_id);
CREATE        INDEX idx_implementation_strategy_actor_id        ON implementation_strategy                       (created_by_actor_id);
CREATE        INDEX idx_implementation_strategy_status          ON implementation_strategy                       (strategy_status);


CREATE TABLE technical_decision (
      technical_decision_id                                     INTEGER                                         NOT NULL
    , technical_decision_uuid                                   TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , phase_revision_id                                         INTEGER                                         NOT NULL
    , implementation_strategy_id                                INTEGER                                         NOT NULL
    , decision_statement                                        TEXT                                            NOT NULL
    , rationale                                                 TEXT                                            NOT NULL
    , impact                                                    TEXT                                            NOT NULL
    , decision_status                                           TEXT                                            NOT NULL DEFAULT 'proposed'
    , created_by_actor_id                                       INTEGER                                         NOT NULL
    , CONSTRAINT chk_technical_decision_impact                  CHECK (impact IN ('contextual', 'material', 'critical'))
    , CONSTRAINT chk_technical_decision_status                  CHECK (decision_status IN ('proposed', 'accepted', 'rejected', 'superseded'))
    , CONSTRAINT fk_technical_decision_phase_revision_id        FOREIGN KEY (phase_revision_id)                REFERENCES phase_revision (phase_revision_id)
    , CONSTRAINT fk_technical_decision_strategy_id              FOREIGN KEY (implementation_strategy_id)       REFERENCES implementation_strategy (implementation_strategy_id)
    , CONSTRAINT fk_technical_decision_actor_id                 FOREIGN KEY (created_by_actor_id)              REFERENCES actor (actor_id)
    , PRIMARY KEY (technical_decision_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_technical_decision_uuid                 ON technical_decision                            (technical_decision_uuid);
CREATE        INDEX idx_technical_decision_phase_revision       ON technical_decision                            (phase_revision_id);
CREATE        INDEX idx_technical_decision_strategy_id          ON technical_decision                            (implementation_strategy_id);
CREATE        INDEX idx_technical_decision_actor_id             ON technical_decision                            (created_by_actor_id);
CREATE        INDEX idx_technical_decision_status_impact        ON technical_decision                            (decision_status, impact);


CREATE TABLE technical_decision_claim (
      technical_decision_id                                     INTEGER                                         NOT NULL
    , claim_id                                                  INTEGER                                         NOT NULL
    , relationship                                              TEXT                                            NOT NULL
    , CONSTRAINT chk_technical_decision_claim_relationship      CHECK (relationship IN ('depends_on', 'supports', 'changes'))
    , CONSTRAINT fk_technical_decision_claim_decision_id        FOREIGN KEY (technical_decision_id)            REFERENCES technical_decision (technical_decision_id)
    , CONSTRAINT fk_technical_decision_claim_claim_id           FOREIGN KEY (claim_id)                         REFERENCES claim (claim_id)
    , PRIMARY KEY (technical_decision_id, claim_id, relationship)
)
STRICT, WITHOUT ROWID
;
CREATE        INDEX idx_technical_decision_claim_claim_id       ON technical_decision_claim                      (claim_id, technical_decision_id);


CREATE TABLE proof_obligation (
      proof_obligation_id                                       INTEGER                                         NOT NULL
    , proof_obligation_uuid                                     TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , technical_decision_id                                     INTEGER                                         NOT NULL
    , obligation_description                                    TEXT                                            NOT NULL
    , impact                                                    TEXT                                            NOT NULL
    , evidence_profile                                          TEXT                                            NOT NULL
    , obligation_status                                         TEXT                                            NOT NULL DEFAULT 'pending'
    , disposition_reason                                        TEXT                                            NOT NULL DEFAULT ''
    , CONSTRAINT chk_proof_obligation_impact                    CHECK (impact IN ('contextual', 'material', 'critical'))
    , CONSTRAINT chk_proof_obligation_status                    CHECK (obligation_status IN ('pending', 'satisfied', 'failed', 'blocked', 'not_applicable'))
    , CONSTRAINT fk_proof_obligation_decision_id                FOREIGN KEY (technical_decision_id)            REFERENCES technical_decision (technical_decision_id)
    , PRIMARY KEY (proof_obligation_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_proof_obligation_uuid                   ON proof_obligation                              (proof_obligation_uuid);
CREATE        INDEX idx_proof_obligation_decision_id            ON proof_obligation                              (technical_decision_id);
CREATE        INDEX idx_proof_obligation_pending                ON proof_obligation                              (technical_decision_id, impact, proof_obligation_id)
                                                                 WHERE obligation_status = 'pending';


CREATE TABLE proof_obligation_evidence (
      proof_obligation_id                                       INTEGER                                         NOT NULL
    , evidence_id                                               INTEGER                                         NOT NULL
    , relationship                                              TEXT                                            NOT NULL DEFAULT 'supports'
    , CONSTRAINT chk_proof_obligation_evidence_relationship     CHECK (relationship IN ('supports', 'qualifies'))
    , CONSTRAINT fk_proof_obligation_evidence_obligation_id     FOREIGN KEY (proof_obligation_id)              REFERENCES proof_obligation (proof_obligation_id)
    , CONSTRAINT fk_proof_obligation_evidence_evidence_id       FOREIGN KEY (evidence_id)                      REFERENCES evidence (evidence_id)
    , PRIMARY KEY (proof_obligation_id, evidence_id, relationship)
)
STRICT, WITHOUT ROWID
;
CREATE        INDEX idx_proof_obligation_evidence_evidence_id   ON proof_obligation_evidence                    (evidence_id, proof_obligation_id);


CREATE TABLE experiment (
      experiment_id                                             INTEGER                                         NOT NULL
    , experiment_uuid                                           TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , phase_revision_id                                         INTEGER                                         NOT NULL
    , technical_decision_id                                     INTEGER                                             NULL
    , experiment_name                                           TEXT                                            NOT NULL
    , hypothesis                                                TEXT                                            NOT NULL
    , procedure                                                 TEXT                                            NOT NULL
    , sandbox_kind                                              TEXT                                            NOT NULL
    , sandbox_path                                              TEXT                                                NULL
    , experiment_status                                         TEXT                                            NOT NULL DEFAULT 'planned'
    , result_summary                                            TEXT                                            NOT NULL DEFAULT ''
    , limitations                                               TEXT                                            NOT NULL DEFAULT ''
    , created_by_actor_id                                       INTEGER                                         NOT NULL
    , CONSTRAINT chk_experiment_sandbox_kind                    CHECK (sandbox_kind IN ('git_worktree', 'database_copy', 'command', 'other'))
    , CONSTRAINT chk_experiment_status                          CHECK (experiment_status IN ('planned', 'running', 'passed', 'failed', 'inconclusive', 'blocked'))
    , CONSTRAINT fk_experiment_phase_revision_id                FOREIGN KEY (phase_revision_id)                REFERENCES phase_revision (phase_revision_id)
    , CONSTRAINT fk_experiment_decision_id                      FOREIGN KEY (technical_decision_id)            REFERENCES technical_decision (technical_decision_id)
    , CONSTRAINT fk_experiment_actor_id                         FOREIGN KEY (created_by_actor_id)              REFERENCES actor (actor_id)
    , PRIMARY KEY (experiment_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_experiment_uuid                         ON experiment                                    (experiment_uuid);
CREATE        INDEX idx_experiment_phase_revision               ON experiment                                    (phase_revision_id);
CREATE        INDEX idx_experiment_decision_id                  ON experiment                                    (technical_decision_id);
CREATE        INDEX idx_experiment_actor_id                     ON experiment                                    (created_by_actor_id);
CREATE        INDEX idx_experiment_incomplete                   ON experiment                                    (phase_revision_id, technical_decision_id)
                                                                 WHERE experiment_status IN ('planned', 'running', 'inconclusive', 'blocked');


CREATE TABLE proof_obligation_experiment (
      proof_obligation_id                                       INTEGER                                         NOT NULL
    , experiment_id                                             INTEGER                                         NOT NULL
    , CONSTRAINT fk_proof_obligation_experiment_obligation_id   FOREIGN KEY (proof_obligation_id)              REFERENCES proof_obligation (proof_obligation_id)
    , CONSTRAINT fk_proof_obligation_experiment_experiment_id   FOREIGN KEY (experiment_id)                   REFERENCES experiment (experiment_id)
    , PRIMARY KEY (proof_obligation_id, experiment_id)
)
STRICT, WITHOUT ROWID
;
CREATE        INDEX idx_proof_obligation_experiment_experiment  ON proof_obligation_experiment                  (experiment_id, proof_obligation_id);


CREATE TABLE experiment_artifact (
      experiment_id                                             INTEGER                                         NOT NULL
    , artifact_id                                               INTEGER                                         NOT NULL
    , artifact_role                                             TEXT                                            NOT NULL
    , CONSTRAINT chk_experiment_artifact_role                   CHECK (artifact_role IN ('input', 'output', 'log', 'snapshot', 'patch'))
    , CONSTRAINT fk_experiment_artifact_experiment_id           FOREIGN KEY (experiment_id)                   REFERENCES experiment (experiment_id)
    , CONSTRAINT fk_experiment_artifact_artifact_id             FOREIGN KEY (artifact_id)                     REFERENCES artifact (artifact_id)
    , PRIMARY KEY (experiment_id, artifact_id, artifact_role)
)
STRICT, WITHOUT ROWID
;
CREATE        INDEX idx_experiment_artifact_artifact_id         ON experiment_artifact                          (artifact_id, experiment_id);


CREATE TABLE adversarial_check (
      adversarial_check_id                                      INTEGER                                         NOT NULL
    , adversarial_check_uuid                                    TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , phase_revision_id                                         INTEGER                                         NOT NULL
    , technical_spec_revision_id                                INTEGER                                         NOT NULL
    , check_category                                            TEXT                                            NOT NULL
    , check_name                                                TEXT                                            NOT NULL
    , scope                                                     TEXT                                            NOT NULL
    , is_mandatory                                              INTEGER                                         NOT NULL DEFAULT 1
    , check_status                                              TEXT                                            NOT NULL DEFAULT 'pending'
    , disposition_reason                                        TEXT                                            NOT NULL DEFAULT ''
    , report_artifact_id                                        INTEGER                                             NULL
    , completed_by_actor_id                                     INTEGER                                             NULL
    , created_by_actor_id                                       INTEGER                                         NOT NULL
    , CONSTRAINT chk_adversarial_check_mandatory                CHECK (is_mandatory IN (0, 1))
    , CONSTRAINT chk_adversarial_check_status                   CHECK (check_status IN ('pending', 'completed_no_finding', 'completed_findings', 'not_applicable', 'unavailable', 'inaccessible'))
    , CONSTRAINT fk_adversarial_check_phase_revision_id         FOREIGN KEY (phase_revision_id)                REFERENCES phase_revision (phase_revision_id)
    , CONSTRAINT fk_adversarial_check_spec_revision_id          FOREIGN KEY (technical_spec_revision_id)       REFERENCES technical_spec_revision (technical_spec_revision_id)
    , CONSTRAINT fk_adversarial_check_report_artifact_id        FOREIGN KEY (report_artifact_id)               REFERENCES artifact (artifact_id)
    , CONSTRAINT fk_adversarial_check_completed_actor_id        FOREIGN KEY (completed_by_actor_id)            REFERENCES actor (actor_id)
    , CONSTRAINT fk_adversarial_check_created_actor_id          FOREIGN KEY (created_by_actor_id)              REFERENCES actor (actor_id)
    , PRIMARY KEY (adversarial_check_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_adversarial_check_uuid                  ON adversarial_check                             (adversarial_check_uuid);
CREATE UNIQUE INDEX idx_adversarial_check_spec_category_name    ON adversarial_check                             (technical_spec_revision_id, check_category, check_name);
CREATE        INDEX idx_adversarial_check_phase_revision        ON adversarial_check                             (phase_revision_id);
CREATE        INDEX idx_adversarial_check_spec_revision         ON adversarial_check                             (technical_spec_revision_id);
CREATE        INDEX idx_adversarial_check_report_artifact       ON adversarial_check                             (report_artifact_id);
CREATE        INDEX idx_adversarial_check_pending_mandatory     ON adversarial_check                             (phase_revision_id, technical_spec_revision_id, adversarial_check_id)
                                                                 WHERE is_mandatory = 1 AND check_status = 'pending';


CREATE TABLE defeater (
      defeater_id                                               INTEGER                                         NOT NULL
    , defeater_uuid                                             TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , dt_modified                                               TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , phase_revision_id                                         INTEGER                                         NOT NULL
    , adversarial_check_id                                      INTEGER                                             NULL
    , challenge                                                 TEXT                                            NOT NULL
    , impact                                                    TEXT                                            NOT NULL
    , defeater_status                                           TEXT                                            NOT NULL DEFAULT 'open'
    , resolution                                                TEXT                                            NOT NULL DEFAULT ''
    , created_by_actor_id                                       INTEGER                                         NOT NULL
    , CONSTRAINT chk_defeater_impact                            CHECK (impact IN ('contextual', 'material', 'critical'))
    , CONSTRAINT chk_defeater_status                            CHECK (defeater_status IN ('open', 'defeated', 'confirmed', 'accepted', 'inconclusive', 'superseded'))
    , CONSTRAINT fk_defeater_phase_revision_id                  FOREIGN KEY (phase_revision_id)                REFERENCES phase_revision (phase_revision_id)
    , CONSTRAINT fk_defeater_adversarial_check_id               FOREIGN KEY (adversarial_check_id)             REFERENCES adversarial_check (adversarial_check_id)
    , CONSTRAINT fk_defeater_actor_id                           FOREIGN KEY (created_by_actor_id)              REFERENCES actor (actor_id)
    , PRIMARY KEY (defeater_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_defeater_uuid                           ON defeater                                      (defeater_uuid);
CREATE        INDEX idx_defeater_phase_revision                 ON defeater                                      (phase_revision_id);
CREATE        INDEX idx_defeater_adversarial_check_id           ON defeater                                      (adversarial_check_id);
CREATE        INDEX idx_defeater_actor_id                       ON defeater                                      (created_by_actor_id);
CREATE        INDEX idx_defeater_open_material                  ON defeater                                      (phase_revision_id, impact, defeater_id)
                                                                 WHERE defeater_status IN ('open', 'inconclusive') AND impact IN ('material', 'critical');


CREATE TABLE defeater_evidence (
      defeater_id                                               INTEGER                                         NOT NULL
    , evidence_id                                               INTEGER                                         NOT NULL
    , relationship                                              TEXT                                            NOT NULL
    , CONSTRAINT chk_defeater_evidence_relationship             CHECK (relationship IN ('supports_challenge', 'refutes_challenge', 'qualifies'))
    , CONSTRAINT fk_defeater_evidence_defeater_id               FOREIGN KEY (defeater_id)                     REFERENCES defeater (defeater_id)
    , CONSTRAINT fk_defeater_evidence_evidence_id               FOREIGN KEY (evidence_id)                     REFERENCES evidence (evidence_id)
    , PRIMARY KEY (defeater_id, evidence_id, relationship)
)
STRICT, WITHOUT ROWID
;
CREATE        INDEX idx_defeater_evidence_evidence_id           ON defeater_evidence                            (evidence_id, defeater_id);


CREATE TABLE defeater_claim (
      defeater_id                                               INTEGER                                         NOT NULL
    , claim_id                                                  INTEGER                                         NOT NULL
    , CONSTRAINT fk_defeater_claim_defeater_id                  FOREIGN KEY (defeater_id)                     REFERENCES defeater (defeater_id)
    , CONSTRAINT fk_defeater_claim_claim_id                     FOREIGN KEY (claim_id)                        REFERENCES claim (claim_id)
    , PRIMARY KEY (defeater_id, claim_id)
)
STRICT, WITHOUT ROWID
;
CREATE        INDEX idx_defeater_claim_claim_id                 ON defeater_claim                                (claim_id, defeater_id);


CREATE TABLE defeater_decision (
      defeater_id                                               INTEGER                                         NOT NULL
    , technical_decision_id                                     INTEGER                                         NOT NULL
    , CONSTRAINT fk_defeater_decision_defeater_id               FOREIGN KEY (defeater_id)                     REFERENCES defeater (defeater_id)
    , CONSTRAINT fk_defeater_decision_decision_id               FOREIGN KEY (technical_decision_id)           REFERENCES technical_decision (technical_decision_id)
    , PRIMARY KEY (defeater_id, technical_decision_id)
)
STRICT, WITHOUT ROWID
;
CREATE        INDEX idx_defeater_decision_decision_id           ON defeater_decision                             (technical_decision_id, defeater_id);


CREATE TABLE technical_spec_revision (
      technical_spec_revision_id                                INTEGER                                         NOT NULL
    , technical_spec_revision_uuid                              TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    , phase_revision_id                                         INTEGER                                         NOT NULL
    , revision_no                                               INTEGER                                         NOT NULL
    , spec_status                                               TEXT                                            NOT NULL DEFAULT 'draft'
    , artifact_id                                               INTEGER                                         NOT NULL
    , scoring_model                                             TEXT                                            NOT NULL
    , overall_assurance_score                                   INTEGER                                             NULL
    , created_by_actor_id                                       INTEGER                                         NOT NULL
    , CONSTRAINT chk_technical_spec_revision_no                 CHECK (revision_no >= 1)
    , CONSTRAINT chk_technical_spec_status                      CHECK (spec_status IN ('draft', 'reviewed', 'final', 'superseded'))
    , CONSTRAINT chk_technical_spec_overall_score               CHECK (overall_assurance_score IS NULL OR overall_assurance_score BETWEEN 0 AND 100)
    , CONSTRAINT fk_technical_spec_phase_revision_id            FOREIGN KEY (phase_revision_id)                REFERENCES phase_revision (phase_revision_id)
    , CONSTRAINT fk_technical_spec_artifact_id                  FOREIGN KEY (artifact_id)                      REFERENCES artifact (artifact_id)
    , CONSTRAINT fk_technical_spec_actor_id                     FOREIGN KEY (created_by_actor_id)              REFERENCES actor (actor_id)
    , PRIMARY KEY (technical_spec_revision_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_technical_spec_revision_uuid            ON technical_spec_revision                       (technical_spec_revision_uuid);
CREATE UNIQUE INDEX idx_technical_spec_revision_no              ON technical_spec_revision                       (revision_no);
CREATE UNIQUE INDEX idx_technical_spec_revision_final           ON technical_spec_revision                       (spec_status)
                                                                 WHERE spec_status = 'final';
CREATE        INDEX idx_technical_spec_phase_revision           ON technical_spec_revision                       (phase_revision_id);
CREATE        INDEX idx_technical_spec_artifact_id              ON technical_spec_revision                       (artifact_id);
CREATE        INDEX idx_technical_spec_actor_id                 ON technical_spec_revision                       (created_by_actor_id);


CREATE TABLE assurance_score (
      technical_spec_revision_id                                INTEGER                                         NOT NULL
    , assurance_dimension                                      TEXT                                            NOT NULL
    , assurance_score                                          INTEGER                                         NOT NULL
    , scoring_details_json                                     TEXT                                            NOT NULL DEFAULT '{}'
    , CONSTRAINT chk_assurance_score                            CHECK (assurance_score BETWEEN 0 AND 100)
    , CONSTRAINT chk_assurance_score_details_json               CHECK (json_valid(scoring_details_json))
    , CONSTRAINT fk_assurance_score_spec_revision_id            FOREIGN KEY (technical_spec_revision_id)       REFERENCES technical_spec_revision (technical_spec_revision_id)
    , PRIMARY KEY (technical_spec_revision_id, assurance_dimension)
)
STRICT, WITHOUT ROWID
;


CREATE TABLE event_log (
      event_log_id                                              INTEGER                                         NOT NULL
    , event_uuid                                                TEXT                                            NOT NULL
    , event_schema_version                                      INTEGER                                         NOT NULL DEFAULT 1
    , command_uuid                                              TEXT                                            NOT NULL
    , command_name                                              TEXT                                            NOT NULL
    , command_input_sha256                                      TEXT                                            NOT NULL
    , dt_created                                                TEXT                                            NOT NULL
    , actor_id                                                  INTEGER                                         NOT NULL
    , session_uuid                                              TEXT                                            NOT NULL
    , phase_revision_id                                         INTEGER                                             NULL
    , event_type                                                TEXT                                            NOT NULL
    , payload_json                                              TEXT                                            NOT NULL
    , previous_event_log_id                                     INTEGER                                             NULL
    , previous_event_hash                                       TEXT                                                NULL
    , event_hash                                                TEXT                                            NOT NULL
    , CONSTRAINT chk_event_log_schema_version                  CHECK (event_schema_version >= 1)
    , CONSTRAINT chk_event_log_command_input_sha256             CHECK (length(command_input_sha256) = 64 AND command_input_sha256 NOT GLOB '*[^0-9a-f]*')
    , CONSTRAINT chk_event_log_payload_json                     CHECK (json_valid(payload_json))
    , CONSTRAINT chk_event_log_previous_hash                    CHECK (previous_event_hash IS NULL OR (length(previous_event_hash) = 64 AND previous_event_hash NOT GLOB '*[^0-9a-f]*'))
    , CONSTRAINT chk_event_log_hash                             CHECK (length(event_hash) = 64 AND event_hash NOT GLOB '*[^0-9a-f]*')
    , CONSTRAINT chk_event_log_previous_pair                    CHECK (
                                                                    (previous_event_log_id IS NULL AND previous_event_hash IS NULL)
                                                                    OR
                                                                    (previous_event_log_id IS NOT NULL AND previous_event_hash IS NOT NULL)
                                                                )
    , CONSTRAINT chk_event_log_previous_id                      CHECK (previous_event_log_id IS NULL OR previous_event_log_id < event_log_id)
    , CONSTRAINT fk_event_log_actor_id                          FOREIGN KEY (actor_id)                         REFERENCES actor (actor_id)
    , CONSTRAINT fk_event_log_phase_revision_id                 FOREIGN KEY (phase_revision_id)                REFERENCES phase_revision (phase_revision_id)
    , CONSTRAINT fk_event_log_previous_event_id                 FOREIGN KEY (previous_event_log_id)            REFERENCES event_log (event_log_id)
    , PRIMARY KEY (event_log_id)
)
STRICT
;
CREATE UNIQUE INDEX idx_event_log_uuid                          ON event_log                                     (event_uuid);
CREATE UNIQUE INDEX idx_event_log_command_uuid                  ON event_log                                     (command_uuid);
CREATE UNIQUE INDEX idx_event_log_hash                          ON event_log                                     (event_hash);
CREATE UNIQUE INDEX idx_event_log_previous_event_id             ON event_log                                     (previous_event_log_id)
                                                                 WHERE previous_event_log_id IS NOT NULL;
CREATE UNIQUE INDEX idx_event_log_single_root                   ON event_log                                     ((1))
                                                                 WHERE previous_event_log_id IS NULL;
CREATE        INDEX idx_event_log_actor_id                      ON event_log                                     (actor_id);
CREATE        INDEX idx_event_log_phase_revision               ON event_log                                     (phase_revision_id, event_log_id);
CREATE        INDEX idx_event_log_event_type                    ON event_log                                     (event_type, event_log_id);
CREATE        INDEX idx_event_log_command_name                  ON event_log                                     (command_name, event_log_id);


CREATE TRIGGER validate_event_log_chain
    BEFORE INSERT ON event_log
    FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN NOT EXISTS (SELECT 1 FROM event_log)
             AND (NEW.previous_event_log_id IS NOT NULL OR NEW.previous_event_hash IS NOT NULL)
        THEN RAISE(ABORT, 'first event cannot reference a previous event')
        WHEN EXISTS (SELECT 1 FROM event_log)
             AND (NEW.previous_event_log_id IS NULL OR NEW.previous_event_hash IS NULL)
        THEN RAISE(ABORT, 'non-root event must reference the current event-log head')
        WHEN EXISTS (SELECT 1 FROM event_log)
             AND NEW.previous_event_log_id <> (SELECT event_log_id FROM event_log ORDER BY event_log_id DESC LIMIT 1)
        THEN RAISE(ABORT, 'event must append to the current event-log head')
        WHEN EXISTS (SELECT 1 FROM event_log)
             AND NEW.previous_event_hash <> (SELECT event_hash FROM event_log ORDER BY event_log_id DESC LIMIT 1)
        THEN RAISE(ABORT, 'previous_event_hash does not match the current event-log head')
    END;
END;


CREATE TRIGGER prevent_event_log_update
    BEFORE UPDATE ON event_log
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'event_log is append-only');
END;

CREATE TRIGGER prevent_event_log_delete
    BEFORE DELETE ON event_log
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'event_log is append-only');
END;

CREATE TRIGGER prevent_artifact_update
    BEFORE UPDATE ON artifact
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'artifact is immutable; create a new artifact instead');
END;

CREATE TRIGGER prevent_artifact_delete
    BEFORE DELETE ON artifact
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'artifact is immutable; retain historical evidence');
END;

CREATE TRIGGER prevent_research_activity_update
    BEFORE UPDATE ON research_activity
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'research_activity is append-only');
END;

CREATE TRIGGER prevent_research_activity_delete
    BEFORE DELETE ON research_activity
    FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'research_activity is append-only');
END;


CREATE UNIQUE INDEX idx_discovery_run_singleton ON discovery_run ((1));
CREATE TRIGGER prevent_policy_update BEFORE UPDATE OF config_json, input_artifact_id, discovery_run_uuid, subagents_enabled, subagent_mode ON discovery_run
BEGIN SELECT RAISE(ABORT, 'run policy and identity are immutable'); END;
ALTER TABLE research_lane ADD COLUMN closure_status TEXT NOT NULL DEFAULT 'none' CHECK (closure_status IN ('none','running','stale','completed'));
ALTER TABLE research_lane ADD COLUMN answer_text TEXT NOT NULL DEFAULT '';
ALTER TABLE research_lane ADD COLUMN limitations TEXT NOT NULL DEFAULT '';
ALTER TABLE research_lane ADD COLUMN answer_question_id INTEGER REFERENCES clarification_question(clarification_question_id);
ALTER TABLE research_need ADD COLUMN answer_text TEXT NOT NULL DEFAULT '';
ALTER TABLE argument ADD COLUMN counter_status TEXT NOT NULL DEFAULT 'open' CHECK (counter_status IN ('open','resolved'));
ALTER TABLE argument ADD COLUMN resolution_evidence_id INTEGER REFERENCES evidence(evidence_id);
ALTER TABLE argument ADD COLUMN resolution_reason TEXT NOT NULL DEFAULT '';
ALTER TABLE argument ADD COLUMN verification_artifact_id INTEGER REFERENCES artifact(artifact_id);
CREATE INDEX idx_argument_resolution_evidence ON argument (resolution_evidence_id);
CREATE INDEX idx_argument_verification_artifact ON argument (verification_artifact_id);
CREATE INDEX idx_lane_answer_question ON research_lane (answer_question_id);
DROP INDEX idx_source_repository_uri_revision;
CREATE INDEX idx_source_repository_uri_revision ON source_repository (repository_uri, baseline_revision);
PRAGMA user_version = 4;
ALTER TABLE technical_spec_revision ADD COLUMN structure_sha256 TEXT NOT NULL DEFAULT '';
ALTER TABLE technical_spec_revision ADD COLUMN narrative_artifact_id INTEGER REFERENCES artifact(artifact_id);
ALTER TABLE technical_spec_revision ADD COLUMN bundle_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(bundle_json));
ALTER TABLE experiment ADD COLUMN source_repository_id INTEGER REFERENCES source_repository(source_repository_id);
ALTER TABLE experiment ADD COLUMN execution_uuid TEXT;
ALTER TABLE experiment ADD COLUMN execution_artifact_id INTEGER REFERENCES artifact(artifact_id);
ALTER TABLE experiment ADD COLUMN execution_exit_code INTEGER;
ALTER TABLE experiment ADD COLUMN superseded_by_experiment_id INTEGER REFERENCES experiment(experiment_id);
ALTER TABLE experiment ADD COLUMN command_json TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(command_json));
ALTER TABLE experiment ADD COLUMN environment_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(environment_json));
ALTER TABLE defeater ADD COLUMN resolution_artifact_id INTEGER REFERENCES artifact(artifact_id);
ALTER TABLE defeater ADD COLUMN confirmed_phase_revision_id INTEGER REFERENCES phase_revision(phase_revision_id);
CREATE TABLE technical_requirement (
 technical_requirement_id INTEGER PRIMARY KEY,
 technical_requirement_uuid TEXT NOT NULL UNIQUE,
 technical_decision_id INTEGER NOT NULL REFERENCES technical_decision(technical_decision_id),
 research_need_id INTEGER NOT NULL REFERENCES research_need(research_need_id),
 requirement_text TEXT NOT NULL,
 acceptance_criteria TEXT NOT NULL,
 verification_plan TEXT NOT NULL,
 created_by_actor_id INTEGER NOT NULL REFERENCES actor(actor_id)
) STRICT;
CREATE TABLE investigation_group (
 investigation_group_id INTEGER PRIMARY KEY,
 investigation_group_uuid TEXT NOT NULL UNIQUE,
 phase_revision_id INTEGER NOT NULL REFERENCES phase_revision(phase_revision_id),
 research_lane_id INTEGER REFERENCES research_lane(research_lane_id),
 technical_spec_revision_id INTEGER REFERENCES technical_spec_revision(technical_spec_revision_id),
 requested_count INTEGER NOT NULL CHECK(requested_count BETWEEN 1 AND 8),
 group_status TEXT NOT NULL DEFAULT 'open' CHECK(group_status IN ('open','reconciled','superseded')),
 context_artifact_id INTEGER NOT NULL REFERENCES artifact(artifact_id),
 report_artifact_id INTEGER REFERENCES artifact(artifact_id),
 disposition_reason TEXT NOT NULL DEFAULT '',
 created_by_actor_id INTEGER NOT NULL REFERENCES actor(actor_id)
) STRICT;
ALTER TABLE agent_run ADD COLUMN investigation_group_id INTEGER REFERENCES investigation_group(investigation_group_id);
CREATE TABLE investigator_finding (
 investigator_finding_id INTEGER PRIMARY KEY,
 investigator_finding_uuid TEXT NOT NULL UNIQUE,
 agent_run_id INTEGER NOT NULL REFERENCES agent_run(agent_run_id),
 position TEXT NOT NULL CHECK(position IN ('support','refute','not_seen','unique')),
 finding_text TEXT NOT NULL,
 impact TEXT NOT NULL CHECK(impact IN ('contextual','material','critical')),
 claim_id INTEGER REFERENCES claim(claim_id),
 technical_decision_id INTEGER REFERENCES technical_decision(technical_decision_id),
 artifact_id INTEGER REFERENCES artifact(artifact_id),
 disposition TEXT NOT NULL DEFAULT 'pending' CHECK(disposition IN ('pending','imported','dismissed')),
 disposition_reason TEXT NOT NULL DEFAULT '',
 lead_id INTEGER REFERENCES lead(lead_id),
 defeater_id INTEGER REFERENCES defeater(defeater_id)
) STRICT;
PRAGMA user_version = 5;

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
