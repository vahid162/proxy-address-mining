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
    "mpf:hook:verified_user_forward_post_dnat:backend_guard",
    "mpf:hook:verified_user_forward_post_dnat:accounting",
    "mpf:hook:verified_user_forward_post_dnat:customers",
    "mpf:backend_guard:btc:60010",
    "mpf:canary-btc-001:customer_dispatch",
    "mpf:canary-btc-001:customer_connlimit_reject",
    "mpf:canary-btc-001:customer_hashlimit_reject",
    "mpf:canary-btc-001:customer_accounting_in",
    "mpf:canary-btc-001:customer_accounting_out",
    "mpf:canary-btc-001:customer_whitelist_allow",
    "mpf:canary-btc-001:customer_whitelist_reject",
    "mpf:canary-btc-001:customer_nat_redirect",
    "mpf:limited-btc-001:customer_dispatch",
    "mpf:limited-btc-001:customer_connlimit_reject",
    "mpf:limited-btc-001:customer_hashlimit_reject",
    "mpf:limited-btc-001:customer_accounting_in",
    "mpf:limited-btc-001:customer_accounting_out",
    "mpf:limited-btc-001:customer_whitelist_allow",
    "mpf:limited-btc-001:customer_whitelist_reject",
    "mpf:limited-btc-001:customer_nat_redirect",
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
    # A known chain does not launder an unknown MPF/customer comment. Comments
    # carry customer/action semantics, so an MPF-like comment must be exact.
    if comment is not None and is_mpf_like_comment(comment) and not is_official_controlled_comment(comment):
        return "unknown_mpf_artifact"
    if is_official_controlled_chain(chain):
        return "official_phase11_controlled_artifact"
    if is_official_controlled_comment(comment):
        return "official_phase11_controlled_artifact"
    if is_mpf_like_chain(chain) or is_mpf_like_comment(comment):
        return "unknown_mpf_artifact"
    return "not_mpf_artifact"
