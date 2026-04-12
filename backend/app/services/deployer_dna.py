"""Deployer DNA — fetches the mint authority of a Solana token and looks up
their launch history from the local database.

Flow:
  token_address → getParsedAccountInfo (Solana RPC) → mintAuthority wallet
  → query LaunchFeedToken + DeveloperOperatorProfile in DB
  → DeployerDNAResult
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from ..models import DeveloperOperatorProfile, LaunchFeedToken
from .solana_rpc import SolanaRpcClient, SolanaRpcError

logger = logging.getLogger(__name__)


@dataclass
class DeployerTokenEntry:
    mint: str
    name: str
    symbol: str
    rug_probability: float
    risk_level: str


@dataclass
class DeployerDNAResult:
    deployer_wallet: str | None
    total_launches: int
    rug_count: int
    rug_ratio: float          # 0.0–1.0
    avg_rug_probability: float
    risk_label: str           # "unknown" | "clean" | "suspicious" | "serial_rugger"
    recent_tokens: list[DeployerTokenEntry] = field(default_factory=list)
    from_db: bool = False     # True if we found historical data in DB


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _risk_label(rug_ratio: float, rug_count: int) -> str:
    if rug_count == 0:
        return "clean"
    if rug_ratio >= 0.7 or rug_count >= 3:
        return "serial_rugger"
    if rug_ratio >= 0.3 or rug_count >= 2:
        return "suspicious"
    return "clean"


def _short(wallet: str) -> str:
    return f"{wallet[:6]}...{wallet[-4:]}" if len(wallet) > 10 else wallet


def _get_mint_authority(token_address: str, rpc: SolanaRpcClient) -> str | None:
    """Returns the mintAuthority of a token mint, or None if renounced / error."""
    try:
        result = rpc.call(
            "getParsedAccountInfo",
            [token_address, {"encoding": "jsonParsed"}],
        )
        value = (result or {}).get("value")
        if not value:
            return None
        data = value.get("data", {})
        if not isinstance(data, dict):
            return None
        parsed = data.get("parsed", {})
        info = parsed.get("info", {})
        return info.get("mintAuthority")  # None when renounced
    except (SolanaRpcError, Exception) as exc:
        logger.debug("Could not fetch mintAuthority for %s: %s", token_address, exc)
        return None


# ─── Main entry point ─────────────────────────────────────────────────────────

def get_deployer_dna(
    token_address: str,
    db: Session,
    rpc: SolanaRpcClient,
) -> DeployerDNAResult:
    """Full Deployer DNA lookup for a token address."""

    deployer = _get_mint_authority(token_address, rpc)

    if not deployer:
        return DeployerDNAResult(
            deployer_wallet=None,
            total_launches=0,
            rug_count=0,
            rug_ratio=0.0,
            avg_rug_probability=0.0,
            risk_label="unknown",
        )

    # ── 1. Check DeveloperOperatorProfile (keyed by full wallet) ──────────────
    profile: DeveloperOperatorProfile | None = (
        db.query(DeveloperOperatorProfile)
        .filter(DeveloperOperatorProfile.operator_key == deployer)
        .first()
    )
    if profile:
        rug_ratio = (
            profile.high_risk_launches / profile.launches_count
            if profile.launches_count > 0
            else 0.0
        )
        recent: list[DeployerTokenEntry] = [
            DeployerTokenEntry(
                mint=t.get("mint", ""),
                name=t.get("name", "Unknown"),
                symbol=t.get("symbol", "???"),
                rug_probability=float(t.get("rug_probability", 0)),
                risk_level=t.get("rug_risk_level", "unknown"),
            )
            for t in (profile.latest_launches_json or [])[:5]
        ]
        return DeployerDNAResult(
            deployer_wallet=deployer,
            total_launches=profile.launches_count,
            rug_count=profile.high_risk_launches,
            rug_ratio=round(rug_ratio, 3),
            avg_rug_probability=float(profile.avg_rug_probability),
            risk_label=profile.profile_status or _risk_label(rug_ratio, profile.high_risk_launches),
            recent_tokens=recent,
            from_db=True,
        )

    # ── 2. Fallback: scan LaunchFeedToken by deployer_short_address prefix ────
    # deployer_short_address is stored as e.g. "AbCd...wxyz" (first4...last4)
    short_prefix = deployer[:4]
    short_suffix = deployer[-4:]
    launches = (
        db.query(LaunchFeedToken)
        .filter(
            LaunchFeedToken.deployer_short_address.like(f"{short_prefix}%{short_suffix}")
        )
        .order_by(LaunchFeedToken.report_created_at.desc())
        .limit(20)
        .all()
    )

    if not launches:
        return DeployerDNAResult(
            deployer_wallet=deployer,
            total_launches=0,
            rug_count=0,
            rug_ratio=0.0,
            avg_rug_probability=0.0,
            risk_label="unknown",
        )

    rug_count = sum(1 for t in launches if float(t.rug_probability or 0) >= 0.65)
    total = len(launches)
    rug_ratio = rug_count / total if total > 0 else 0.0
    avg_prob = sum(float(t.rug_probability or 0) for t in launches) / total

    recent = [
        DeployerTokenEntry(
            mint=t.mint,
            name=t.name,
            symbol=t.symbol,
            rug_probability=float(t.rug_probability or 0),
            risk_level=t.rug_risk_level,
        )
        for t in launches[:5]
    ]

    return DeployerDNAResult(
        deployer_wallet=deployer,
        total_launches=total,
        rug_count=rug_count,
        rug_ratio=round(rug_ratio, 3),
        avg_rug_probability=round(avg_prob, 3),
        risk_label=_risk_label(rug_ratio, rug_count),
        recent_tokens=recent,
        from_db=True,
    )
