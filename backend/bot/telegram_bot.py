"""
RugSignal Telegram Bot
======================
Instant token risk scoring in Telegram via backend scoring API.
Send a Solana token address -> get the same score as on solanatrust.tech.

Usage:
    TELEGRAM_BOT_TOKEN=... python bot/telegram_bot.py

Environment:
    TELEGRAM_BOT_TOKEN  - Bot token from @BotFather
    BACKEND_URL         - Backend base URL (default: http://127.0.0.1:8000)
"""
from __future__ import annotations

import logging
import os
import re
import sys
import time

import httpx
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("rugsignal-bot")

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# ── Backend API client ───────────────────────────────────────────────────────


async def score_via_backend(token_address: str) -> dict:
    """Call backend v2 scan endpoint — same pipeline as the website."""
    t0 = time.time()
    url = f"{BACKEND_URL}/api/v1/v2/scan/token"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json={
                "token_address": token_address,
                "chain": "solana",
            })

            if resp.status_code == 400:
                return {"error": "Invalid token address or not found on Solana."}
            if resp.status_code == 502:
                return {"error": "Token not found. Check the address."}
            if resp.status_code != 200:
                return {"error": f"Backend error ({resp.status_code}). Try again later."}

            data = resp.json()

    except httpx.TimeoutException:
        return {"error": "Scoring timed out. Try again later."}
    except httpx.ConnectError:
        return {"error": "Cannot reach backend. Service may be starting up."}
    except Exception as e:
        return {"error": f"Scoring failed: {e}"}

    elapsed = time.time() - t0

    # Extract top findings as signals
    signals = []
    for finding in data.get("top_findings", []):
        title = finding.get("title", "")
        desc = finding.get("description", "")
        severity = finding.get("severity", "").upper()
        if title:
            signals.append(f"[{severity}] {title}: {desc}" if desc else f"[{severity}] {title}")

    return {
        "address": token_address,
        "score": data.get("score", 0),
        "risk_level": data.get("risk_level", "unknown").upper(),
        "ml_probability": round(data.get("ml_probability", 0) * 100, 1),
        "rule_score": round(data.get("rule_score", 0), 1),
        "rug_probability": round(data.get("rug_probability", 0) * 100, 1),
        "confidence": round(data.get("confidence", 0) * 100),
        "signals": signals,
        "explanation": data.get("explanation", {}),
        "category_scores": data.get("category_scores", {}),
        "elapsed": round(elapsed, 1),
    }


# ── Format message ───────────────────────────────────────────────────────────

RISK_EMOJI = {
    "CRITICAL": "\u26d4",
    "HIGH": "\U0001f534",
    "MEDIUM": "\U0001f7e1",
    "LOW": "\U0001f7e2",
}


def format_result(r: dict) -> str:
    """Format backend scoring result as Telegram message."""
    if "error" in r:
        return f"\u274c {r['error']}"

    emoji = RISK_EMOJI.get(r["risk_level"], "\u2753")
    score = r["score"]
    risk = r["risk_level"]
    addr = r["address"]

    lines = [
        f"{emoji} <b>RugSignal Score: {score}/100 ({risk})</b>",
        f"Token: <code>{addr}</code>",
        "",
    ]

    # Category scores
    cats = r.get("category_scores", {})
    if cats:
        lines.append("<b>Risk Breakdown:</b>")
        cat_labels = {
            "technical_risk": "Technical",
            "distribution_risk": "Distribution",
            "market_execution_risk": "Market",
            "market_maturity": "Maturity",
            "behaviour_risk": "Behaviour",
        }
        for key, label in cat_labels.items():
            val = cats.get(key)
            if val is not None:
                bar = "\u2588" * (val // 10) + "\u2591" * (10 - val // 10)
                lines.append(f"  {label}: {bar} {val}/100")
        lines.append("")

    # Top findings
    if r["signals"]:
        lines.append(f"<b>Top Findings ({len(r['signals'])}):</b>")
        for sig in r["signals"][:6]:
            lines.append(f"  \u2022 {sig}")
        lines.append("")

    # Scores
    lines.append(f"<b>ML Model:</b> {r['ml_probability']:.1f}% rug probability")
    lines.append(f"<b>Rule Engine:</b> {r['rule_score']:.0f}/100")
    lines.append(f"<b>Confidence:</b> {r['confidence']}%")

    # Explanation
    explanation = r.get("explanation", {})
    summary = explanation.get("summary", "")
    if summary:
        if len(summary) > 400:
            summary = summary[:400] + "..."
        lines.append(f"\n<b>Summary:</b> {summary}")

    # Footer
    lines.append(f"\n<a href=\"https://dexscreener.com/solana/{addr}\">DexScreener</a>"
                 f" | <a href=\"https://solanatrust.tech\">SolanaTrust</a>")
    lines.append(f"<i>Scored in {r['elapsed']}s via RugSignal Oracle</i>")

    return "\n".join(lines)


# ── Telegram handlers ────────────────────────────────────────────────────────

SOLANA_ADDR_RE = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")

WELCOME_TEXT = """<b>RugSignal Bot</b> - Solana Token Risk Scanner

Send me a Solana token address and I'll analyze it through the RugSignal scoring engine.

<b>How it works:</b>
1. Fetches on-chain data (authorities, holders, liquidity)
2. Runs ML model (XGBoost, trained on 2350 tokens)
3. Applies 56-feature rule engine across 6 risk categories
4. Blends scores: 60% Rule Engine + 40% ML
5. Returns risk score (0-100) with detailed breakdown

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

    addresses = SOLANA_ADDR_RE.findall(text)
    if not addresses:
        await update.message.reply_text(
            "Send me a Solana token mint address to scan.\n"
            "Example: <code>7BgBvyjrZX1YKz4oh9mjb8ZScatkkwb8DzFx7LoiVkM3</code>",
            parse_mode="HTML",
        )
        return

    for addr in addresses[:3]:
        scanning_msg = await update.message.reply_text(
            f"\U0001f50d Scanning <code>{addr[:8]}...{addr[-4:]}</code> via RugSignal...",
            parse_mode="HTML",
        )

        result = await score_via_backend(addr)
        response = format_result(result)

        try:
            await scanning_msg.edit_text(response, parse_mode="HTML", disable_web_page_preview=True)
        except Exception:
            await update.message.reply_text(response, parse_mode="HTML", disable_web_page_preview=True)

        log.info(
            "Scored %s: %s/100 %s [%.1fs]",
            addr[:8],
            result.get("score", "?"),
            result.get("risk_level", "?"),
            result.get("elapsed", 0),
        )


# ── Main ────────────────────────────────────────────────────────────────────


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
        log.info("Scoring via backend API: %s", BACKEND_URL)
        async with tg_app:
            await tg_app.updater.start_polling(drop_pending_updates=True)
            await tg_app.start()
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
    log.info("Scoring via backend API: %s", BACKEND_URL)

    app = _build_app(token)
    log.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
