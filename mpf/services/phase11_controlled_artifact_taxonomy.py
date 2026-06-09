"""Shared Phase 11 controlled MPF artifact taxonomy.

Only exact official controlled artifact names/comments are accepted.
Arbitrary MPF-prefixed artifacts remain unknown and fail closed.
"""
from __future__ import annotations

OFFICIAL_CONTROLLED_CHAINS = frozenset({
    "MPF_INPUT",
    "MPF_CUSTOMERS",
    "MPF_GUARD",
    "MPF_ACCT_IN",
    "MPF_ACCT_OUT",
    "MPF_NAT_PRE",
    "MPF_NAT_POST",
    "MPFL_btc",
    "MPFC_20001",
    "MPFO_20001",
    "MPFC_20101",
    "MPFO_20101",
})
OFFICIAL_CONTROLLED_COMMENTS = frozenset({
    "mpf:hook:nat_prerouting",
    "mpf:hook:filter_input",
    "mpf:canary-btc-001:customer_nat_redirect",
    "mpf:limited-btc-001:customer_nat_redirect",
    "mpf:canary-btc-001:customer_filter",
    "mpf:limited-btc-001:customer_filter",
})


def is_official_controlled_chain(name: str) -> bool:
    return name in OFFICIAL_CONTROLLED_CHAINS


def is_mpf_like_chain(name: str) -> bool:
    return name.startswith(("MPF", "MPFBTC", "MPFC_", "MPFO_", "MPFL_"))


def is_official_controlled_comment(comment: str | None) -> bool:
    return bool(comment) and str(comment) in OFFICIAL_CONTROLLED_COMMENTS


def is_mpf_like_comment(comment: str | None) -> bool:
    text = str(comment or "")
    return "mpf:" in text or "customer_" in text


def classify_controlled_artifact(*, chain: str, comment: str | None = None) -> str:
    if is_official_controlled_chain(chain) or is_official_controlled_comment(comment):
        return "official_phase11_controlled_artifact"
    if is_mpf_like_chain(chain) or is_mpf_like_comment(comment):
        return "unknown_mpf_artifact"
    return "not_mpf_artifact"
