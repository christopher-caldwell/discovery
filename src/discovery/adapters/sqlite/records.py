"""Internal SQL helpers, not a public table CRUD interface."""

import sqlite3

from discovery.domain.encoding import uid
from discovery.domain.errors import require

ENTITIES = {
    "strategy": ("implementation_strategy", "ST"),
    "decision": ("technical_decision", "D"),
    "obligation": ("proof_obligation", "PO"),
    "experiment": ("experiment", "EXP"),
    "challenge": ("adversarial_check", "CH"),
    "defeater": ("defeater", "DEF"),
    "spec": ("technical_spec_revision", "SPEC"),
    "requirement": ("technical_requirement", "REQ"),
    "group": ("investigation_group", "G"),
    "agent": ("agent_run", "AR"),
    "finding": ("investigator_finding", "F"),
    "lead": ("lead", "LEAD"),
    "method": ("research_method", "M"),
    "evidence": ("evidence", "E"),
    "claim": ("claim", "C"),
    "argument": ("argument", "ARG"),
    "source": ("source_repository", "SRC"),
    "question": ("clarification_question", "Q"),
    "need": ("research_need", "RN"),
    "lane": ("research_lane", "L"),
    "surface": ("research_surface", "S"),
    "artifact": ("artifact", "A"),
    "activity": ("research_activity", "RA"),
    "review": ("agent_run", "AR"),
}


def insert(con: sqlite3.Connection, table: str, **values: object) -> int:
    keys = ",".join(values)
    marks = ",".join("?" for _ in values)
    return con.execute(
        f"INSERT INTO {table} ({keys}) VALUES ({marks})", tuple(values.values())
    ).lastrowid


def entity(con: sqlite3.Connection, kind: str, **values: object) -> dict:
    table, prefix = ENTITIES[kind]
    identifier = uid()
    numeric = insert(con, table, **{table + "_uuid": identifier}, **values)
    return {"id": numeric, "uuid": identifier, "ref": f"{prefix}-{numeric:03d}"}


def resolve(con: sqlite3.Connection, kind: str, ref: str) -> dict:
    table, prefix = ENTITIES[kind]
    require(
        isinstance(ref, str) and ref.strip(), "INVALID_ARGUMENT", f"A {kind} reference is required."
    )
    if ref.startswith(prefix + "-") and ref[len(prefix) + 1 :].isdigit():
        field, value = table + "_id", int(ref[len(prefix) + 1 :])
    else:
        field, value = table + "_uuid", ref
    row = con.execute(f"SELECT * FROM {table} WHERE {field} = ?", (value,)).fetchone()
    require(row is not None, "ENTITY_NOT_FOUND", f"Unknown {kind}: {ref}")
    return dict(row)
