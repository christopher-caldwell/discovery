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
