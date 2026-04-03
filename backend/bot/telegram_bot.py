"""
RugSignal Telegram Bot
======================
Instant token risk scoring in Telegram.
Send a Solana token address -> get risk analysis in 3 seconds.

Usage:
    TELEGRAM_BOT_TOKEN=... python bot/telegram_bot.py

Environment:
    TELEGRAM_BOT_TOKEN  - Bot token from @BotFather
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from pathlib import Path

import httpx
import numpy as np
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ── Setup paths ──────────────────────────────────────────────────────────────

BACKEND_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = BACKEND_DIR / "models"

# ── Load ML model ────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("rugsignal-bot")

ONNX_SESSION = None
FEATURE_COLS: list[str] = []

try:
    import onnxruntime as ort

    onnx_path = MODELS_DIR / "rugsignal_model.onnx"
    cols_path = MODELS_DIR / "feature_cols.json"
    if onnx_path.exists() and cols_path.exists():
        ONNX_SESSION = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
        with open(cols_path) as f:
            FEATURE_COLS = json.load(f)
        log.info("ML model loaded: %d features", len(FEATURE_COLS))
    else:
        log.warning("Model files not found at %s", MODELS_DIR)
except ImportError:
    log.warning("onnxruntime not installed, ML scoring disabled")

# ── DexScreener client ───────────────────────────────────────────────────────

DEXSCREENER_BASE = "https://api.dexscreener.com"
SOLANA_RPC = "https://api.mainnet-beta.solana.com"


def fetch_dexscreener(token_address: str) -> dict | None:
    """Fetch best pair from DexScreener for a Solana token."""
    try:
        r = httpx.get(
            f"{DEXSCREENER_BASE}/latest/dex/tokens/{token_address}",
            timeout=10,
        )
        data = r.json()
        pairs = data.get("pairs") or []
        sol_pairs = [p for p in pairs if p.get("chainId") == "solana"]
        if not sol_pairs:
            return None
        # Pick highest liquidity pair
        sol_pairs.sort(
            key=lambda p: float((p.get("liquidity") or {}).get("usd", 0) or 0),
            reverse=True,
        )
        return sol_pairs[0]
    except Exception as e:
        log.error("DexScreener error: %s", e)
        return None


def fetch_rpc_authorities(token_address: str) -> dict:
    """Check mint/freeze authority via Solana RPC."""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccountInfo",
            "params": [token_address, {"encoding": "jsonParsed"}],
        }
        r = httpx.post(SOLANA_RPC, json=payload, timeout=8)
        result = r.json().get("result", {}).get("value", {})
        parsed = (result.get("data") or {}).get("parsed") or {}
        info = parsed.get("info") or {}
        return {
            "mint_authority": info.get("mintAuthority") is not None,
            "freeze_authority": info.get("freezeAuthority") is not None,
            "decimals": (info.get("decimals") or 0),
        }
    except Exception:
        return {"mint_authority": False, "freeze_authority": False, "decimals": 0}


# ── Feature extraction (same as inference.py) ────────────────────────────────


def extract_features(pair: dict, rpc: dict | None = None) -> dict[str, float]:
    """Extract ML features from DexScreener pair data."""
    liq = pair.get("liquidity") or {}
    vol = pair.get("volume") or {}
    txns = pair.get("txns") or {}
    pc = pair.get("priceChange") or {}
    info = pair.get("info") or {}
    socials = info.get("socials") or []
    websites = info.get("websites") or []

    social_types = {s.get("type", "").lower() for s in socials}
    pair_created = pair.get("pairCreatedAt") or 0
    age_hours = (time.time() * 1000 - pair_created) / 3_600_000 if pair_created else 0

    t5 = txns.get("m5") or {}
    t1h = txns.get("h1") or {}
    t6h = txns.get("h6") or {}
    t24h = txns.get("h24") or {}

    buys_1h = float(t1h.get("buys") or 0)
    sells_1h = float(t1h.get("sells") or 0)
    buys_24h = float(t24h.get("buys") or 0)
    sells_24h = float(t24h.get("sells") or 0)

    mcap = float(pair.get("marketCap") or 0)
    liquidity_usd = float(liq.get("usd") or 0)

    rpc = rpc or {}

    return {
        "price_usd": float(pair.get("priceUsd") or 0),
        "price_native": float(pair.get("priceNative") or 0),
        "fdv": float(pair.get("fdv") or 0),
        "market_cap": mcap,
        "liquidity_usd": liquidity_usd,
        "liquidity_base": float(liq.get("base") or 0),
        "liquidity_quote": float(liq.get("quote") or 0),
        "volume_5m": float(vol.get("m5") or 0),
        "volume_1h": float(vol.get("h1") or 0),
        "volume_6h": float(vol.get("h6") or 0),
        "volume_24h": float(vol.get("h24") or 0),
        "txns_5m_buys": float(t5.get("buys") or 0),
        "txns_5m_sells": float(t5.get("sells") or 0),
        "txns_1h_buys": buys_1h,
        "txns_1h_sells": sells_1h,
        "txns_6h_buys": float(t6h.get("buys") or 0),
        "txns_6h_sells": float(t6h.get("sells") or 0),
        "txns_24h_buys": buys_24h,
        "txns_24h_sells": sells_24h,
        "price_change_5m": float(pc.get("m5") or 0),
        "price_change_1h": float(pc.get("h1") or 0),
        "price_change_6h": float(pc.get("h6") or 0),
        "price_change_24h": float(pc.get("h24") or 0),
        "pair_age_hours": age_hours,
        "has_website": 1.0 if websites else 0.0,
        "has_twitter": 1.0 if "twitter" in social_types else 0.0,
        "has_telegram": 1.0 if "telegram" in social_types else 0.0,
        "has_discord": 1.0 if "discord" in social_types else 0.0,
        "social_count": float(len(socials) + len(websites)),
        "mint_authority_exists": 1.0 if rpc.get("mint_authority") else 0.0,
        "freeze_authority_exists": 1.0 if rpc.get("freeze_authority") else 0.0,
        "decimals": float(rpc.get("decimals", 0)),
        "buy_sell_ratio_1h": buys_1h / sells_1h if sells_1h > 0 else (2.0 if buys_1h > 0 else 1.0),
        "buy_sell_ratio_24h": buys_24h / sells_24h if sells_24h > 0 else (2.0 if buys_24h > 0 else 1.0),
        "liquidity_to_mcap_ratio": liquidity_usd / mcap if mcap > 0 else 0.0,
        "volume_to_liquidity_ratio": float(vol.get("h24") or 0) / liquidity_usd if liquidity_usd > 0 else 0.0,
        "txns_total_24h": buys_24h + sells_24h,
    }


# ── Scoring engine ───────────────────────────────────────────────────────────


def ml_predict(features: dict[str, float]) -> float:
    """Run ONNX model, return rug probability (0-1). Returns -1 if no model."""
    if ONNX_SESSION is None or not FEATURE_COLS:
        return -1.0
    vector = np.array(
        [[features.get(col, 0.0) for col in FEATURE_COLS]],
        dtype=np.float32,
    )
    input_name = ONNX_SESSION.get_inputs()[0].name
    result = ONNX_SESSION.run(None, {input_name: vector})
    probas = result[1][0]
    return float(probas[1]) if len(probas) > 1 else float(probas[0])


def rule_score(features: dict[str, float]) -> tuple[int, list[str]]:
    """Rule-based pre-rug signal detection. Returns (score, signals)."""
    signals = []
    score = 0

    # Volume-to-Liquidity ratio
    vol_liq = features["volume_to_liquidity_ratio"]
    if vol_liq > 20:
        score += 25
        signals.append(f"Extreme Vol/Liq: {vol_liq:.0f}x (normal <3x)")
    elif vol_liq > 10:
        score += 18
        signals.append(f"High Vol/Liq: {vol_liq:.0f}x")
    elif vol_liq > 5:
        score += 10
        signals.append(f"Elevated Vol/Liq: {vol_liq:.1f}x")

    # Token age
    age = features["pair_age_hours"]
    if age < 2:
        score += 20
        signals.append(f"Brand new: {age:.1f}h old")
    elif age < 6:
        score += 15
        signals.append(f"Very new: {age:.0f}h old")
    elif age < 24:
        score += 8
        signals.append(f"New: {age:.0f}h old")

    # Buy/Sell imbalance
    bs = features["buy_sell_ratio_24h"]
    if bs > 5:
        score += 20
        signals.append(f"FOMO buying: {bs:.1f}x buy/sell ratio")
    elif bs > 3:
        score += 12
        signals.append(f"Buy-heavy: {bs:.1f}x ratio")

    # Liquidity-to-MCap ratio
    liq_mcap = features["liquidity_to_mcap_ratio"]
    if 0 < liq_mcap < 0.02:
        score += 20
        signals.append(f"Paper thin liquidity: {liq_mcap*100:.1f}% of mcap")
    elif 0 < liq_mcap < 0.05:
        score += 12
        signals.append(f"Thin liquidity: {liq_mcap*100:.1f}% of mcap")

    # Mint authority
    if features["mint_authority_exists"]:
        score += 15
        signals.append("Mint authority ACTIVE")

    # Freeze authority
    if features["freeze_authority_exists"]:
        score += 10
        signals.append("Freeze authority ACTIVE")

    # No socials
    if not features["has_website"] and not features["has_twitter"]:
        score += 10
        signals.append("No website or Twitter")

    # Price pump
    pc24 = features["price_change_24h"]
    if pc24 > 1000:
        score += 15
        signals.append(f"Insane pump: +{pc24:.0f}% in 24h")
    elif pc24 > 500:
        score += 10
        signals.append(f"Extreme pump: +{pc24:.0f}%")
    elif pc24 > 200:
        score += 5
        signals.append(f"Strong pump: +{pc24:.0f}%")

    # Zero liquidity = dead/rugged
    if features["liquidity_usd"] == 0:
        score += 30
        signals.append("ZERO liquidity (likely rugged)")

    return min(100, score), signals


def compute_risk_level(score: int) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"


RISK_EMOJI = {
    "CRITICAL": "\u26d4",  # no_entry
    "HIGH": "\U0001f534",  # red_circle
    "MEDIUM": "\U0001f7e1",  # yellow_circle
    "LOW": "\U0001f7e2",  # green_circle
}


def score_token(token_address: str) -> dict:
    """Full scoring pipeline for a token. Returns result dict."""
    t0 = time.time()

    # 1. Fetch DexScreener data
    pair = fetch_dexscreener(token_address)
    if not pair:
        return {"error": "Token not found on DexScreener. Check the address."}

    # 2. Fetch on-chain authorities
    rpc = fetch_rpc_authorities(token_address)

    # 3. Extract features
    features = extract_features(pair, rpc)

    # 4. ML model prediction
    ml_prob = ml_predict(features)

    # 5. Rule-based scoring
    rules, signals = rule_score(features)

    # 6. Combine: rules + ML
    if ml_prob >= 0:
        combined = min(100, rules + int(ml_prob * 100))
    else:
        combined = rules

    risk_level = compute_risk_level(combined)
    elapsed = time.time() - t0

    # Token info
    bt = pair.get("baseToken") or {}
    liq = pair.get("liquidity") or {}
    vol = pair.get("volume") or {}

    return {
        "name": bt.get("name", "Unknown"),
        "symbol": bt.get("symbol", "???"),
        "address": token_address,
        "score": combined,
        "risk_level": risk_level,
        "ml_probability": round(ml_prob * 100, 1) if ml_prob >= 0 else None,
        "rule_score": rules,
        "signals": signals,
        "liquidity_usd": float(liq.get("usd", 0) or 0),
        "market_cap": float(pair.get("marketCap", 0) or 0),
        "volume_24h": float(vol.get("h24", 0) or 0),
        "price_usd": pair.get("priceUsd", "0"),
        "price_change_24h": float((pair.get("priceChange") or {}).get("h24", 0) or 0),
        "pair_age_hours": features["pair_age_hours"],
        "mint_authority": rpc.get("mint_authority", False),
        "freeze_authority": rpc.get("freeze_authority", False),
        "has_website": bool(features["has_website"]),
        "has_twitter": bool(features["has_twitter"]),
        "has_telegram": bool(features["has_telegram"]),
        "dex_url": f"https://dexscreener.com/solana/{token_address}",
        "elapsed": round(elapsed, 1),
    }


# ── Format message ───────────────────────────────────────────────────────────


def format_result(r: dict) -> str:
    """Format scoring result as Telegram message."""
    if "error" in r:
        return f"\u274c {r['error']}"

    emoji = RISK_EMOJI.get(r["risk_level"], "")
    score = r["score"]
    risk = r["risk_level"]

    # Header
    lines = [
        f"{emoji} <b>{r['symbol']}</b> - {r['name']}",
        f"<b>Score: {score}/100 ({risk})</b>",
        "",
    ]

    # Stats
    liq = r["liquidity_usd"]
    mcap = r["market_cap"]
    vol = r["volume_24h"]
    age = r["pair_age_hours"]

    lines.append(f"<b>Market Data:</b>")
    lines.append(f"  Price: ${r['price_usd']}")
    lines.append(f"  Liquidity: ${liq:,.0f}")
    lines.append(f"  Market Cap: ${mcap:,.0f}")
    lines.append(f"  Volume 24h: ${vol:,.0f}")
    lines.append(f"  Age: {age:.0f}h" if age >= 1 else f"  Age: {age*60:.0f}min")
    lines.append(f"  24h Change: {r['price_change_24h']:+.1f}%")
    lines.append("")

    # Authority flags
    flags = []
    if r["mint_authority"]:
        flags.append("\u26a0\ufe0f Mint authority active")
    if r["freeze_authority"]:
        flags.append("\u26a0\ufe0f Freeze authority active")
    if not r["has_website"] and not r["has_twitter"]:
        flags.append("\u26a0\ufe0f No website or Twitter")
    if flags:
        lines.append("<b>Flags:</b>")
        for f in flags:
            lines.append(f"  {f}")
        lines.append("")

    # Risk signals
    if r["signals"]:
        lines.append(f"<b>Risk Signals ({len(r['signals'])}):</b>")
        for sig in r["signals"][:8]:
            lines.append(f"  \u2022 {sig}")
        lines.append("")

    # ML model
    if r["ml_probability"] is not None:
        lines.append(f"ML Model: {r['ml_probability']:.1f}% rug probability")

    # Footer
    lines.append(f"\n<a href=\"{r['dex_url']}\">View on DexScreener</a>")
    lines.append(f"<i>Scanned in {r['elapsed']}s by RugSignal</i>")

    return "\n".join(lines)


# ── Telegram handlers ────────────────────────────────────────────────────────

# Solana address pattern: base58, 32-44 chars
SOLANA_ADDR_RE = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")

WELCOME_TEXT = """<b>RugSignal Bot</b> - Solana Token Risk Scanner

Send me a Solana token address and I'll analyze it for rug pull risk in seconds.

<b>How it works:</b>
1. Fetches live market data from DexScreener
2. Checks on-chain authorities (mint/freeze) via Solana RPC
3. Runs ML model (XGBoost, trained on 2350 tokens)
4. Applies rule-based pre-rug signal detection
5. Returns combined risk score (0-100)

<b>Risk levels:</b>
\U0001f7e2 LOW (0-24) - Appears safe
\U0001f7e1 MEDIUM (25-49) - Some concerns
\U0001f534 HIGH (50-74) - Significant risk
\u26d4 CRITICAL (75-100) - Likely scam/rug

Just paste a token address to start!

<i>Website: solanatrust.tech</i>"""


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, parse_mode="HTML", disable_web_page_preview=True)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, parse_mode="HTML", disable_web_page_preview=True)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any message - look for Solana addresses."""
    text = (update.message.text or "").strip()
    if not text:
        return

    # Find Solana addresses in message
    addresses = SOLANA_ADDR_RE.findall(text)
    if not addresses:
        await update.message.reply_text(
            "Send me a Solana token mint address to scan.\n"
            "Example: <code>7BgBvyjrZX1YKz4oh9mjb8ZScatkkwb8DzFx7LoiVkM3</code>",
            parse_mode="HTML",
        )
        return

    for addr in addresses[:3]:  # max 3 per message
        # Send "scanning" indicator
        scanning_msg = await update.message.reply_text(
            f"\U0001f50d Scanning <code>{addr[:8]}...{addr[-4:]}</code>...",
            parse_mode="HTML",
        )

        # Score the token
        result = score_token(addr)
        response = format_result(result)

        # Edit the scanning message with result
        try:
            await scanning_msg.edit_text(response, parse_mode="HTML", disable_web_page_preview=True)
        except Exception:
            await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True)

        log.info(
            "Scored %s (%s): %s/100 %s [%.1fs]",
            result.get("symbol", "?"),
            addr[:8],
            result.get("score", "?"),
            result.get("risk_level", "?"),
            result.get("elapsed", 0),
        )


# ── Main ─────────────────────────────────────────────────────────────────────


def _build_app(token: str):
    """Build telegram Application with handlers."""
    tg_app = ApplicationBuilder().token(token).build()
    tg_app.add_handler(CommandHandler("start", cmd_start))
    tg_app.add_handler(CommandHandler("help", cmd_help))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return tg_app


def run_in_thread(token: str):
    """Run bot in a background thread (called from FastAPI startup)."""
    import asyncio

    async def _run():
        tg_app = _build_app(token)
        log.info("Telegram bot starting (background thread)...")
        log.info("ML model: %s", "loaded" if ONNX_SESSION else "not available")
        async with tg_app:
            await tg_app.updater.start_polling(drop_pending_updates=True)
            await tg_app.start()
            # Block forever (daemon thread will be killed on process exit)
            stop_event = asyncio.Event()
            await stop_event.wait()

    asyncio.run(_run())


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("ERROR: Set TELEGRAM_BOT_TOKEN environment variable")
        print("Get one from @BotFather on Telegram")
        sys.exit(1)

    log.info("Starting RugSignal Telegram Bot...")
    log.info("ML model: %s", "loaded" if ONNX_SESSION else "not available")

    app = _build_app(token)
    log.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
