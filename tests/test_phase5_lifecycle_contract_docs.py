from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_doc(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_customer_lifecycle_contract_preserves_phase5_db_only_gate() -> None:
    text = read_doc("docs/CUSTOMER_LIFECYCLE.md")

    assert "Status: Phase 5 contract" in text
    assert "Phase 5 may model customer lifecycle state in PostgreSQL" in text
    assert "It must not activate runtime traffic behavior" in text
    assert "customer NAT redirects" in text
    assert "customer firewall rules" in text
    assert "firewall apply" in text
    assert "production customer traffic" in text
    assert "usage timers" in text
    assert "abuse runner automation" in text
    assert "public API binding" in text


def test_first_connect_is_contract_only_in_phase5() -> None:
    text = read_doc("docs/CUSTOMER_LIFECYCLE.md")

    assert "first_connect" in text
    assert "first-connect runtime detection" in text
    assert "That runtime is not part of Phase 5" in text
    assert "status remains active" in text
    assert "Do not introduce a `pending_activation` customer status" in text
    assert "activated_at = null" in text
    assert "expires_at = null" in text


def test_auto_expire_and_auto_delete_runtime_are_forbidden_in_phase5() -> None:
    text = read_doc("docs/CUSTOMER_LIFECYCLE.md")

    assert "auto-expire timer" in text
    assert "auto-delete timer" in text
    assert "systemd timer that changes active -> expired" in text
    assert "systemd timer that changes expired -> deleted" in text
    assert "automatic expiry job" in text
    assert "automatic delete job" in text
    assert "list_expiring_customers()" in text
    assert "list_delete_eligible_customers()" in text


def test_soft_delete_customer_key_and_abuse_invariants_are_documented() -> None:
    text = read_doc("docs/CUSTOMER_LIFECYCLE.md")

    assert "Customer delete means soft delete" in text
    assert "status = deleted" in text
    assert "deleted_at = now()" in text
    assert "DELETE FROM customers" in text
    assert "customers.customer_key" in text
    assert "customer_key is unique" in text
    assert "Every active customer in every enabled lane must remain evaluatable" in text
    assert "Silent exclusion from future abuse evaluation is forbidden" in text
    assert "miners" in text
    assert "farms" in text
    assert "maxconn" in text


def test_phase5_task_references_lifecycle_contract_and_stop_conditions() -> None:
    text = read_doc("docs/AI_PHASE_5_TASK.md")

    assert "docs/CUSTOMER_LIFECYCLE.md" in text
    assert "Customer Lifecycle Requirements" in text
    assert "activation_mode = immediate | first_connect" in text
    assert "first_connect runtime detection is future-only" in text
    assert "delete means soft delete" in text
    assert "customer_key is the stable operator/API target identifier" in text
    assert "auto-expire job" in text
    assert "auto-delete job" in text
    assert "first-connect runtime detector" in text
    assert "no lifecycle timer exists" in text


def test_index_includes_lifecycle_contract_in_phase5_reading_path() -> None:
    text = read_doc("docs/history/INDEX_LEGACY_0.1.299.md")

    assert "docs/CUSTOMER_LIFECYCLE.md" in text
    assert "customer lifecycle" in text.lower()
    assert "first-connect" in text.lower()
    assert "auto-expire" in text.lower()
    assert "auto-delete" in text.lower()
    assert "soft-delete" in text.lower()
