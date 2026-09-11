"""Optional recovery projection; authoritative records remain unchanged."""


def compact_resume(packet: dict) -> dict:
    return {
        **packet,
        "experiments": [
            {
                key: value
                for key, value in row.items()
                if key not in ("command_json", "environment_json")
            }
            for row in packet["experiments"]
        ],
        "specifications": [
            {key: value for key, value in row.items() if key != "bundle_json"}
            for row in packet["specifications"]
        ],
        "context_projection": {
            "mode": "compact",
            "omitted_fields": {
                "experiments": ["command_json", "environment_json"],
                "specifications": ["bundle_json"],
            },
            "full_recovery": "resume (without --compact)",
            "execution_details": (
                "experiment list; registered execution_artifact_id resolves through artifact list"
            ),
            "specification_details": (
                "spec list; artifact_id and narrative_artifact_id resolve through artifact list"
            ),
            "meaning": (
                "No records were deleted or reclassified. "
                "Read exact receipts before evaluating empirical proof."
            ),
        },
    }
