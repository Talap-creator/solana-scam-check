"""Holder Intelligence — analyzes top token holders using standard Solana RPC.

No Helius required. Uses:
  - getTokenLargestAccounts  → top-20 token accounts + amounts
  - getMultipleAccounts      → resolve token account → owner wallet (batched)
  - getSignaturesForAddress  → wallet tx count / age estimate

Classifies each holder:
  fresh_wallet  — < 10 txs, likely new burner
  active        — 10-100 txs, normal user
  heavy_trader  — > 100 txs, bot or active trader
  whale         — holds > 5% of supply

Outputs HolderIntelligenceResult with:
  - smart_money_pct    % established (non-fresh) top holders
  - fresh_wallet_pct   % suspicious fresh wallets
  - holder_risk_score  0-100 (higher = riskier holder profile)
  - top_holders        list of classified holders
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .solana_rpc import SolanaRpcClient, SolanaRpcError

logger = logging.getLogger(__name__)

_FRESH_TX_THRESHOLD = 10     # wallets with fewer txs = fresh/suspicious
_WHALE_SUPPLY_PCT = 5.0      # % supply = whale


@dataclass
class HolderEntry:
    token_account: str
    owner_wallet: str | None
    ui_amount: float
    supply_pct: float          # % of total supply
    tx_count: int              # estimated from signatures
    classification: str        # fresh_wallet | active | heavy_trader | whale
    is_suspicious: bool


@dataclass
class HolderIntelligenceResult:
    total_holders_checked: int
    fresh_wallet_count: int
    fresh_wallet_pct: float        # 0.0–1.0
    smart_money_pct: float         # 0.0–1.0  (1 - fresh)
    whale_count: int
    top5_concentration_pct: float  # combined % of top-5 holders
    holder_risk_score: int         # 0-100
    risk_label: str                # low | medium | high | critical
    top_holders: list[HolderEntry] = field(default_factory=list)
    error: str | None = None


# ─── RPC helpers ──────────────────────────────────────────────────────────────

def _get_largest_accounts(mint: str, rpc: SolanaRpcClient) -> list[dict]:
    """Returns up to 20 token accounts: {address, uiAmount}."""
    try:
        result = rpc.call("getTokenLargestAccounts", [mint, {"commitment": "confirmed"}])
        return (result or {}).get("value", [])
    except SolanaRpcError as e:
        logger.debug("getTokenLargestAccounts failed for %s: %s", mint[:12], e)
        return []


def _get_account_owners(addresses: list[str], rpc: SolanaRpcClient) -> list[str | None]:
    """Batch-resolve token account addresses → owner wallets."""
    if not addresses:
        return []
    try:
        result = rpc.call("getMultipleAccounts", [addresses, {"encoding": "jsonParsed"}])
        owners: list[str | None] = []
        for acc in (result or {}).get("value", []):
            if acc and isinstance(acc.get("data"), dict):
                info = acc["data"].get("parsed", {}).get("info", {})
                owners.append(info.get("owner"))
            else:
                owners.append(None)
        return owners
    except SolanaRpcError as e:
        logger.debug("getMultipleAccounts failed: %s", e)
        return [None] * len(addresses)


def _get_tx_count(wallet: str, rpc: SolanaRpcClient, limit: int = 50) -> int:
    """Estimate wallet tx activity by counting recent signatures."""
    try:
        result = rpc.call("getSignaturesForAddress", [wallet, {"limit": limit}])
        return len(result) if isinstance(result, list) else 0
    except SolanaRpcError:
        return 0


def _classify(ui_amount: float, supply_pct: float, tx_count: int) -> tuple[str, bool]:
    """Returns (classification, is_suspicious)."""
    if supply_pct >= _WHALE_SUPPLY_PCT:
        # Whales with fresh wallets are the most dangerous
        if tx_count < _FRESH_TX_THRESHOLD:
            return "whale", True
        return "whale", False
    if tx_count < _FRESH_TX_THRESHOLD:
        return "fresh_wallet", True
    if tx_count >= 100:
        return "heavy_trader", False
    return "active", False


# ─── Main entry point ─────────────────────────────────────────────────────────

def get_holder_intelligence(
    mint: str,
    rpc: SolanaRpcClient,
    max_holders: int = 20,
) -> HolderIntelligenceResult:
    """Full holder intelligence analysis for a token mint."""

    # 1. Get largest token accounts
    accounts = _get_largest_accounts(mint, rpc)
    if not accounts:
        return HolderIntelligenceResult(
            total_holders_checked=0,
            fresh_wallet_count=0,
            fresh_wallet_pct=0.0,
            smart_money_pct=0.0,
            whale_count=0,
            top5_concentration_pct=0.0,
            holder_risk_score=0,
            risk_label="unknown",
            error="Could not fetch token holders",
        )

    accounts = accounts[:max_holders]

    # 2. Compute total supply from accounts (approximate)
    total_amount = sum(float(a.get("uiAmount") or 0) for a in accounts)
    if total_amount <= 0:
        total_amount = 1.0

    # 3. Batch-resolve owners
    token_account_addrs = [a["address"] for a in accounts]
    owners = _get_account_owners(token_account_addrs, rpc)

    # 4. For each holder, get tx count (only for top 5 to avoid RPC rate limits)
    entries: list[HolderEntry] = []
    for i, acc in enumerate(accounts):
        owner = owners[i] if i < len(owners) else None
        ui_amount = float(acc.get("uiAmount") or 0)
        supply_pct = (ui_amount / total_amount) * 100

        tx_count = 0
        if owner and i < 5:  # Only check tx counts for top-5 holders
            tx_count = _get_tx_count(owner, rpc, limit=50)
        elif owner:
            tx_count = 50  # Assume established wallet for holders beyond top-5

        classification, is_suspicious = _classify(ui_amount, supply_pct, tx_count)

        entries.append(HolderEntry(
            token_account=acc["address"],
            owner_wallet=owner,
            ui_amount=ui_amount,
            supply_pct=round(supply_pct, 2),
            tx_count=tx_count,
            classification=classification,
            is_suspicious=is_suspicious,
        ))

    # 5. Aggregate
    n = len(entries)
    fresh_count = sum(1 for e in entries if e.classification == "fresh_wallet")
    whale_count = sum(1 for e in entries if e.classification == "whale")
    suspicious_count = sum(1 for e in entries if e.is_suspicious)

    fresh_pct = fresh_count / n if n > 0 else 0.0
    smart_pct = 1.0 - fresh_pct

    top5_pct = sum(e.supply_pct for e in entries[:5])

    # Risk score formula:
    # 40% — fresh wallet ratio
    # 30% — top-5 concentration
    # 30% — suspicious whale presence
    concentration_score = min(1.0, top5_pct / 80.0)  # 80%+ concentration = max risk
    suspicious_whale = any(e.is_suspicious and e.classification == "whale" for e in entries)

    raw = (
        0.40 * fresh_pct
        + 0.30 * concentration_score
        + 0.20 * (suspicious_count / max(n, 1))
        + 0.10 * float(suspicious_whale)
    )
    holder_risk_score = min(100, int(round(raw * 100)))

    if holder_risk_score >= 70:
        risk_label = "critical"
    elif holder_risk_score >= 45:
        risk_label = "high"
    elif holder_risk_score >= 20:
        risk_label = "medium"
    else:
        risk_label = "low"

    return HolderIntelligenceResult(
        total_holders_checked=n,
        fresh_wallet_count=fresh_count,
        fresh_wallet_pct=round(fresh_pct, 3),
        smart_money_pct=round(smart_pct, 3),
        whale_count=whale_count,
        top5_concentration_pct=round(top5_pct, 2),
        holder_risk_score=holder_risk_score,
        risk_label=risk_label,
        top_holders=entries,
    )
