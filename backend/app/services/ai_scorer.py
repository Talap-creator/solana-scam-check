"""AI Token Risk Scorer — uses Claude to analyze token features."""

import json
import logging
import os

import anthropic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Solana token risk analyst. You analyze on-chain data and return a risk assessment.

You MUST respond with ONLY valid JSON, no markdown, no explanation outside the JSON:
{
  "score": <integer 0-100, higher = more dangerous>,
  "risk_level": "<low|medium|high|critical>",
  "confidence": <float 0.0-1.0>,
  "reasoning": "<1-2 sentence explanation>"
}

Scoring guide:
- 0-24 (low): Established token, good distribution, locked liquidity, old deployer
- 25-49 (medium): Some concerns but not alarming
- 50-74 (high): Multiple red flags, proceed with caution
- 75-100 (critical): Likely rug pull — concentrated supply, unlocked LP, fresh deployer, honeypot signals"""


def _build_analysis_prompt(token_address: str, features: dict) -> str:
    """Build the analysis prompt from token features."""
    lines = [f"Analyze this Solana token for rug pull risk: {token_address}\n"]
    lines.append("On-chain data:")

    key_features = [
        ("mint_authority_enabled", "Mint authority (can mint more tokens)"),
        ("freeze_authority_enabled", "Freeze authority (can freeze wallets)"),
        ("update_authority_enabled", "Update authority (can change metadata)"),
        ("top_1_holder_share", "Top 1 holder share"),
        ("top_10_holder_share", "Top 10 holder share"),
        ("total_liquidity_usd", "Total liquidity USD"),
        ("lp_locked", "LP locked"),
        ("lp_lock_duration_days", "LP lock duration (days)"),
        ("deployer_wallet_age_days", "Deployer wallet age (days)"),
        ("deployer_previous_token_count", "Deployer previous tokens"),
        ("deployer_previous_rug_count", "Deployer previous rugs"),
        ("token_age_hours", "Token age (hours)"),
        ("volume_24h_usd", "24h volume USD"),
        ("market_cap_usd", "Market cap USD"),
        ("honeypot_simulation_failed", "Honeypot simulation failed"),
        ("transfer_tax_detected", "Transfer tax detected"),
        ("dev_cluster_share", "Developer cluster share"),
        ("insider_wallet_detected", "Insider wallet detected"),
        ("wash_trade_score", "Wash trade score"),
        ("early_sell_ratio", "Early sell ratio"),
        ("mint_after_launch_detected", "Mint after launch detected"),
        ("pool_count", "Pool count"),
        ("dex_count", "DEX count"),
        ("gini_coefficient", "Gini coefficient (holder inequality)"),
    ]

    for key, label in key_features:
        val = features.get(key)
        if val is not None:
            lines.append(f"  - {label}: {val}")

    if not any(features.get(k) is not None for k, _ in key_features):
        lines.append("  - Limited on-chain data available")
        lines.append("  - Assess based on token address pattern and general risk factors")

    return "\n".join(lines)


async def ai_score_token(token_address: str, features: dict | None = None) -> dict:
    """Score a token using Claude AI.

    Returns dict with score, risk_level, confidence, reasoning.
    Falls back to rule-based scoring if API unavailable.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, skipping AI scoring")
        return None

    if features is None:
        features = {}

    prompt = _build_analysis_prompt(token_address, features)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        text = message.content[0].text.strip()
        result = json.loads(text)

        score = max(0, min(100, int(result.get("score", 50))))
        risk_level = result.get("risk_level", "medium")
        if risk_level not in ("low", "medium", "high", "critical"):
            risk_level = "medium"
        confidence = max(0.0, min(1.0, float(result.get("confidence", 0.5))))
        reasoning = result.get("reasoning", "")

        logger.info(
            "AI scored %s: score=%d risk=%s conf=%.2f reason=%s",
            token_address[:12], score, risk_level, confidence, reasoning,
        )

        return {
            "score": score,
            "risk_level": risk_level,
            "confidence": confidence,
            "reasoning": reasoning,
        }

    except json.JSONDecodeError as e:
        logger.error("AI returned invalid JSON for %s: %s", token_address[:12], e)
        return None
    except Exception as e:
        logger.error("AI scoring failed for %s: %s", token_address[:12], e)
        return None
