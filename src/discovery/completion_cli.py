"""Command grammar for design, experiments, and adversarial refinement."""

FAMILIES = {
    "agent": ["start", "reclaim", "heartbeat", "complete", "finding", "list"],
    "group": ["dispatch", "list", "reconcile", "supersede"],
    "finding": ["list", "reconcile"],
    "strategy": ["create", "list", "select", "reject"],
    "decision": ["create", "list", "accept", "reject"],
    "obligation": [
        "create",
        "list",
        "attach-evidence",
        "attach-experiment",
        "satisfy",
        "fail",
        "block",
        "not-applicable",
    ],
    "requirement": ["create", "list"],
    "experiment": ["plan", "list", "exec", "finish", "abort", "replace"],
    "challenge": ["initialize", "list", "complete"],
    "defeater": ["create", "list", "confirm", "defeat", "accept-contextual-risk"],
    "spec": ["draft", "revise", "list", "snapshot", "export"],
    "assurance": ["calculate"],
}


def arguments(cmd, name, text):
    family, action = name.split(".")
    if family not in FAMILIES or family in ("agent", "group", "finding"):
        return

    def option(key, **kwargs):
        cmd.add_argument("--" + key, required=True, type=text, **kwargs)

    if action in (
        "select",
        "reject",
        "accept",
        "attach-evidence",
        "attach-experiment",
        "satisfy",
        "fail",
        "block",
        "not-applicable",
        "exec",
        "finish",
        "abort",
        "replace",
        "complete",
        "confirm",
        "defeat",
        "accept-contextual-risk",
    ):
        cmd.add_argument("ref", type=text)
    if name == "strategy.create":
        option("name")
        option("description")
    if name == "decision.create":
        option("strategy")
        option("text")
        option("rationale")
        cmd.add_argument("--claim", dest="claims", action="append", required=True, type=text)
    if name == "requirement.create":
        for k in ("decision", "need", "text", "acceptance", "verification"):
            option(k)
    if name == "obligation.create":
        option("decision")
        option("text")
        option("profile", choices=["primary", "empirical"])
    if name in ("decision.create", "obligation.create", "defeater.create"):
        option("impact", choices=["contextual", "material", "critical"])
    if name in ("obligation.attach-evidence", "defeater.create", "defeater.defeat"):
        option("evidence-ref")
    if name == "obligation.attach-experiment":
        option("experiment")
    if name == "experiment.plan":
        for k in ("decision", "name", "hypothesis", "procedure"):
            option(k)
    if name == "experiment.exec":
        option("command", dest="command_json")
        cmd.add_argument("--timeout", type=int, default=60)
    if name == "experiment.replace":
        option("replacement")
    if name == "experiment.finish":
        option("outcome", choices=["passed", "failed", "inconclusive", "blocked"])
        option("conclusion")
        option("limitations")
    if name == "challenge.complete":
        option(
            "disposition",
            choices=[
                "completed_no_finding",
                "completed_findings",
                "not_applicable",
                "unavailable",
                "inaccessible",
            ],
        )
    if name == "defeater.create":
        option("check")
        option("text")
        cmd.add_argument("--claim", type=text)
        cmd.add_argument("--decision", type=text)
    if name in ("challenge.complete", "defeater.defeat"):
        option("report")
    if name in ("spec.draft", "spec.revise"):
        option("narrative")
    if action in (
        "select",
        "reject",
        "accept",
        "satisfy",
        "fail",
        "block",
        "not-applicable",
        "abort",
        "replace",
        "complete",
        "confirm",
        "defeat",
        "accept-contextual-risk",
    ):
        option("reason")


def agent_arguments(cmd, name, text):
    if name in (
        "agent.start",
        "agent.reclaim",
        "agent.heartbeat",
        "agent.complete",
        "agent.finding",
        "group.reconcile",
        "group.supersede",
        "finding.reconcile",
    ):
        cmd.add_argument("ref", type=text)
    if name == "group.dispatch":
        cmd.add_argument("--lane", type=text)
        cmd.add_argument("--count", type=int, required=True)
    if name in ("group.reconcile", "group.supersede", "finding.reconcile"):
        cmd.add_argument("--reason", type=text, required=True)
    if name in ("agent.complete", "group.reconcile", "agent.finding"):
        cmd.add_argument("--report", type=text, required=True)
    if name == "agent.complete":
        cmd.add_argument(
            "--outcome",
            choices=["passed", "findings", "no_findings", "inconclusive"],
            required=True,
        )
    if name == "agent.finding":
        cmd.add_argument(
            "--position", choices=["support", "refute", "not_seen", "unique"], required=True
        )
        cmd.add_argument("--text", type=text, required=True)
        cmd.add_argument("--impact", choices=["contextual", "material", "critical"], required=True)
        cmd.add_argument("--origin-uri", type=text, required=True)
        cmd.add_argument("--claim", type=text)
        cmd.add_argument("--decision", type=text)
    if name == "finding.reconcile":
        cmd.add_argument("--check", type=text)
