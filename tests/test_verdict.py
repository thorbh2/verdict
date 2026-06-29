"""
Tests for VERDICT (direct runner, no network/wallet needed).

Run with:  python -m pytest -v
The web fetch and LLM verdict are mocked deterministically so runs repeat.
"""

import json
from pathlib import Path

CONTRACT = str(Path(__file__).resolve().parents[1] / "contracts" / "verdict.py")

GEN = 10 ** 18

STATUS_OPEN = 0
STATUS_RESOLVED = 1
STATUS_VOID = 2
YES = 1
NO = 2

URL = "https://example.com/result"
CRIT = "YES if the page states the team won."


def _market(v, vm, creator, q="Did team X win the final?", url=URL, crit=CRIT):
    vm.sender = creator
    mid = v.create_market(q, url, crit)
    return mid


def _stake(v, vm, who, mid, side, amount):
    vm.sender = who
    vm.value = amount
    sid = v.stake(mid, side)
    vm.value = 0
    return sid


# --------------------------------------------------------------- creation
def test_create_market(deploy, direct_vm, direct_alice):
    v = deploy(CONTRACT)
    mid = _market(v, direct_vm, direct_alice)
    assert mid == 0
    m = v.get_market(0)
    assert m["status"] == STATUS_OPEN
    assert m["resolution_url"] == URL
    assert m["yes_pool"] == "0"


def test_create_requires_url(deploy, direct_vm, direct_alice):
    v = deploy(CONTRACT)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("URL"):
        v.create_market("q?", "  ", "crit")


# --------------------------------------------------------------- staking
def test_stake_updates_pools(deploy, direct_vm, direct_alice, direct_bob, direct_charlie):
    v = deploy(CONTRACT)
    _market(v, direct_vm, direct_alice)
    _stake(v, direct_vm, direct_bob, 0, YES, 3 * GEN)
    _stake(v, direct_vm, direct_charlie, 0, NO, 1 * GEN)
    m = v.get_market(0)
    assert m["yes_pool"] == str(3 * GEN)
    assert m["no_pool"] == str(1 * GEN)
    assert m["stake_count"] == 2


def test_stake_requires_value(deploy, direct_vm, direct_alice, direct_bob):
    v = deploy(CONTRACT)
    _market(v, direct_vm, direct_alice)
    direct_vm.sender = direct_bob
    direct_vm.value = 0
    with direct_vm.expect_revert("GEN"):
        v.stake(0, YES)


def test_cannot_stake_invalid_side(deploy, direct_vm, direct_alice, direct_bob):
    v = deploy(CONTRACT)
    _market(v, direct_vm, direct_alice)
    direct_vm.sender = direct_bob
    direct_vm.value = GEN
    with direct_vm.expect_revert("YES or NO"):
        v.stake(0, 7)
    direct_vm.value = 0


# --------------------------------------------------------------- resolve (mocked)
def test_resolve_yes_from_web(deploy, direct_vm, direct_alice, direct_bob, direct_charlie):
    v = deploy(CONTRACT)
    _market(v, direct_vm, direct_alice)
    _stake(v, direct_vm, direct_bob, 0, YES, 4 * GEN)
    _stake(v, direct_vm, direct_charlie, 0, NO, 2 * GEN)

    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "Team X won the final 3-1."})
    direct_vm.mock_llm(r"Resolution rule", json.dumps({"outcome": "YES"}))

    direct_vm.sender = direct_bob
    v.resolve(0)

    m = v.get_market(0)
    assert m["status"] == STATUS_RESOLVED
    assert m["outcome"] == YES


def test_resolve_void_when_unknown(deploy, direct_vm, direct_alice, direct_bob):
    v = deploy(CONTRACT)
    _market(v, direct_vm, direct_alice)
    _stake(v, direct_vm, direct_bob, 0, YES, GEN)

    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "The page says nothing relevant."})
    direct_vm.mock_llm(r"Resolution rule", json.dumps({"outcome": "UNKNOWN"}))

    direct_vm.sender = direct_bob
    v.resolve(0)
    assert v.get_market(0)["status"] == STATUS_VOID


def test_resolve_void_when_winning_side_empty(deploy, direct_vm, direct_alice, direct_bob):
    v = deploy(CONTRACT)
    _market(v, direct_vm, direct_alice)
    _stake(v, direct_vm, direct_bob, 0, NO, GEN)  # only NO has money

    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "Team X won."})
    direct_vm.mock_llm(r"Resolution rule", json.dumps({"outcome": "YES"}))

    direct_vm.sender = direct_bob
    v.resolve(0)
    # YES won but nobody staked YES -> void so NO can reclaim
    assert v.get_market(0)["status"] == STATUS_VOID


def test_cannot_resolve_twice(deploy, direct_vm, direct_alice, direct_bob):
    v = deploy(CONTRACT)
    _market(v, direct_vm, direct_alice)
    _stake(v, direct_vm, direct_bob, 0, YES, GEN)
    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "Team X won."})
    direct_vm.mock_llm(r"Resolution rule", json.dumps({"outcome": "YES"}))
    direct_vm.sender = direct_bob
    v.resolve(0)
    with direct_vm.expect_revert("already resolved"):
        v.resolve(0)


# --------------------------------------------------------------- claim
def test_winner_claims_pro_rata(deploy, direct_vm, direct_alice, direct_bob, direct_charlie):
    v = deploy(CONTRACT)
    _market(v, direct_vm, direct_alice)
    # Bob YES 4, Charlie NO 2. YES wins -> Bob gets 4 back + all of NO pool (2).
    sid_bob = _stake(v, direct_vm, direct_bob, 0, YES, 4 * GEN)
    _stake(v, direct_vm, direct_charlie, 0, NO, 2 * GEN)

    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "Team X won."})
    direct_vm.mock_llm(r"Resolution rule", json.dumps({"outcome": "YES"}))
    direct_vm.sender = direct_bob
    v.resolve(0)

    direct_vm.sender = direct_bob
    v.claim(0, sid_bob)
    assert v.get_stake(0, sid_bob)["claimed"] is True


def test_loser_cannot_claim(deploy, direct_vm, direct_alice, direct_bob, direct_charlie):
    v = deploy(CONTRACT)
    _market(v, direct_vm, direct_alice)
    _stake(v, direct_vm, direct_bob, 0, YES, GEN)
    sid_c = _stake(v, direct_vm, direct_charlie, 0, NO, GEN)

    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "Team X won."})
    direct_vm.mock_llm(r"Resolution rule", json.dumps({"outcome": "YES"}))
    direct_vm.sender = direct_bob
    v.resolve(0)

    direct_vm.sender = direct_charlie
    with direct_vm.expect_revert("losing side"):
        v.claim(0, sid_c)


def test_void_lets_everyone_reclaim(deploy, direct_vm, direct_alice, direct_bob):
    v = deploy(CONTRACT)
    _market(v, direct_vm, direct_alice)
    sid = _stake(v, direct_vm, direct_bob, 0, YES, GEN)

    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "nothing here"})
    direct_vm.mock_llm(r"Resolution rule", json.dumps({"outcome": "UNKNOWN"}))
    direct_vm.sender = direct_bob
    v.resolve(0)

    direct_vm.sender = direct_bob
    v.claim(0, sid)  # void -> stake returned
    assert v.get_stake(0, sid)["claimed"] is True


def test_unknown_market_reverts(deploy, direct_vm):
    v = deploy(CONTRACT)
    with direct_vm.expect_revert("no such market"):
        v.get_market(0)
