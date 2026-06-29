# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
VERDICT - A Truth-Oracle Prediction Market
==========================================
Stake GEN on YES or NO for a real-world question. When the market resolves, the
contract does something a normal smart contract cannot: it reads the live web at
the poster's resolution source, and a decentralised validator set agrees (via the
Equivalence Principle) on what actually happened. The winning side splits the
entire pot, pro-rata to their stake. No human oracle, no trusted reporter.

Lifecycle:
    OPEN     -> accepting YES/NO stakes
    RESOLVED -> outcome decided from live web data, winners can claim
    VOID     -> the web gave no clear answer; everyone can reclaim their stake
"""

from genlayer import *
from dataclasses import dataclass
import json
import typing


STATUS_OPEN = 0
STATUS_RESOLVED = 1
STATUS_VOID = 2

OUTCOME_NONE = 0
OUTCOME_YES = 1
OUTCOME_NO = 2


@allow_storage
@dataclass
class Stake:
    backer: Address
    side: u8          # OUTCOME_YES or OUTCOME_NO
    amount: u256
    claimed: bool


@allow_storage
@dataclass
class Market:
    creator: Address
    question: str
    resolution_url: str
    criteria: str
    status: u8
    outcome: u8
    yes_pool: u256
    no_pool: u256
    stakes: DynArray[Stake]


class Verdict(gl.Contract):
    markets: DynArray[Market]

    def __init__(self) -> None:
        pass

    # ----------------------------------------------------------------- writes
    @gl.public.write
    def create_market(self, question: str, resolution_url: str, criteria: str) -> int:
        if len(question.strip()) == 0:
            raise gl.vm.UserError("question is required")
        if len(resolution_url.strip()) == 0:
            raise gl.vm.UserError("a resolution source URL is required")
        m = self.markets.append_new_get()
        m.creator = gl.message.sender_address
        m.question = question
        m.resolution_url = resolution_url
        m.criteria = criteria
        m.status = u8(STATUS_OPEN)
        m.outcome = u8(OUTCOME_NONE)
        m.yes_pool = u256(0)
        m.no_pool = u256(0)
        return len(self.markets) - 1

    @gl.public.write.payable
    def stake(self, market_id: int, side: int) -> int:
        m = self._get(market_id)
        if m.status != STATUS_OPEN:
            raise gl.vm.UserError("market is not open")
        amount = gl.message.value
        if amount == u256(0):
            raise gl.vm.UserError("stake must include GEN")
        if side != OUTCOME_YES and side != OUTCOME_NO:
            raise gl.vm.UserError("side must be YES or NO")
        s = m.stakes.append_new_get()
        s.backer = gl.message.sender_address
        s.side = u8(side)
        s.amount = amount
        s.claimed = False
        if side == OUTCOME_YES:
            m.yes_pool = m.yes_pool + amount
        else:
            m.no_pool = m.no_pool + amount
        return len(m.stakes) - 1

    @gl.public.write
    def resolve(self, market_id: int) -> None:
        m = self._get(market_id)
        if m.status != STATUS_OPEN:
            raise gl.vm.UserError("market already resolved")

        url = m.resolution_url
        question = m.question
        criteria = m.criteria

        def leader_fn() -> str:
            page = gl.nondet.web.get(url).body.decode("utf-8")
            page = page[:6000]
            prompt = (
                f"Question: {question}\n"
                f"Resolution rule: {criteria}\n\n"
                f"Source page content:\n{page}\n\n"
                "Based ONLY on the source content, did the event happen? "
                'Reply with ONLY JSON: {"outcome": "YES"} or {"outcome": "NO"} '
                'or {"outcome": "UNKNOWN"} if the page does not say.'
            )
            return gl.nondet.exec_prompt(prompt)

        def validator_fn(leader_res) -> bool:
            if not isinstance(leader_res, gl.vm.Return):
                return False
            return self._outcome_of(leader_res.calldata) == self._outcome_of(leader_fn())

        verdict = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        outcome = self._outcome_of(verdict)

        if outcome == OUTCOME_NONE:
            m.status = u8(STATUS_VOID)
            return
        # if the winning side has no stakers, the market voids so funds return.
        if (outcome == OUTCOME_YES and m.yes_pool == u256(0)) or (
            outcome == OUTCOME_NO and m.no_pool == u256(0)
        ):
            m.status = u8(STATUS_VOID)
            return
        m.outcome = u8(outcome)
        m.status = u8(STATUS_RESOLVED)

    @gl.public.write
    def claim(self, market_id: int, stake_id: int) -> None:
        m = self._get(market_id)
        if stake_id < 0 or stake_id >= len(m.stakes):
            raise gl.vm.UserError("no such stake")
        s = m.stakes[stake_id]
        if s.backer != gl.message.sender_address:
            raise gl.vm.UserError("not your stake")
        if s.claimed:
            raise gl.vm.UserError("already claimed")

        if m.status == STATUS_VOID:
            s.claimed = True
            self._pay(s.backer, s.amount)
            return
        if m.status != STATUS_RESOLVED:
            raise gl.vm.UserError("market not resolved yet")
        if int(s.side) != int(m.outcome):
            raise gl.vm.UserError("this stake backed the losing side")

        win_pool = m.yes_pool if int(m.outcome) == OUTCOME_YES else m.no_pool
        lose_pool = m.no_pool if int(m.outcome) == OUTCOME_YES else m.yes_pool
        # payout = your stake back + your pro-rata cut of the losing pool
        share = (s.amount * lose_pool) // win_pool
        s.claimed = True
        self._pay(s.backer, s.amount + share)

    # ------------------------------------------------------------------ views
    @gl.public.view
    def get_market_count(self) -> int:
        return len(self.markets)

    @gl.public.view
    def get_market(self, market_id: int) -> dict:
        m = self._get(market_id)
        return {
            "creator": m.creator.as_hex,
            "question": m.question,
            "resolution_url": m.resolution_url,
            "criteria": m.criteria,
            "status": int(m.status),
            "outcome": int(m.outcome),
            "yes_pool": str(m.yes_pool),
            "no_pool": str(m.no_pool),
            "stake_count": len(m.stakes),
        }

    @gl.public.view
    def get_stake(self, market_id: int, stake_id: int) -> dict:
        m = self._get(market_id)
        if stake_id < 0 or stake_id >= len(m.stakes):
            raise gl.vm.UserError("no such stake")
        s = m.stakes[stake_id]
        return {
            "backer": s.backer.as_hex,
            "side": int(s.side),
            "amount": str(s.amount),
            "claimed": bool(s.claimed),
        }

    # -------------------------------------------------------------- internals
    def _get(self, market_id: int) -> Market:
        if market_id < 0 or market_id >= len(self.markets):
            raise gl.vm.UserError("no such market")
        return self.markets[market_id]

    def _outcome_of(self, verdict: typing.Any) -> int:
        data = verdict
        if isinstance(data, str):
            data = self._extract_json(data)
        if not isinstance(data, dict):
            return OUTCOME_NONE
        raw = str(data.get("outcome", "")).strip().upper()
        if raw == "YES":
            return OUTCOME_YES
        if raw == "NO":
            return OUTCOME_NO
        return OUTCOME_NONE

    def _extract_json(self, text: str) -> typing.Any:
        try:
            return json.loads(text)
        except (ValueError, TypeError):
            pass
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except (ValueError, TypeError):
                return None
        return None

    def _pay(self, recipient: Address, amount: u256) -> None:
        if amount == u256(0):
            return
        _Payee(recipient).emit_transfer(value=amount)


@gl.evm.contract_interface
class _Payee:
    class View:
        pass

    class Write:
        pass
