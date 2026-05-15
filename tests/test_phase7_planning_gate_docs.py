from pathlib import Path


def test_phase7_planning_doc_exists_and_constraints() -> None:
    p = Path("docs/AI_PHASE_7_TASK.md")
    assert p.exists()
    text = p.read_text(encoding="utf-8").lower()
    for must in [
        "usage + policy/reject accounting",
        "starts only after phase 6 is accepted",
        "must not enable production traffic",
        "must not enable firewall apply",
        "must not enable customer nat/customer firewall rules",
        "must not enable abuse automation",
        "phase 8 remains",
        "normal -> over_tracking -> over_grace -> hard",
        "no silent skip",
    ]:
        assert must in text
