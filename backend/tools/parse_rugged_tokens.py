"""
Rugged Token Parser
===================
Finds confirmed/likely rugged Solana tokens for ML training labels.

Strategy:
1. Search DexScreener for pump.fun tokens with zero liquidity (rug pulled)
2. Search for tokens with -90%+ price drops
3. Enrich with on-chain data (mint/freeze authority)
4. Label as rug=1

Usage:
    python tools/parse_rugged_tokens.py                    # default
    python tools/parse_rugged_tokens.py --count 1000       # target count
    python tools/parse_rugged_tokens.py --output rugs.csv  # custom output
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

DEXSCREENER_BASE = "https://api.dexscreener.com"
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
REQUEST_DELAY = 0.4

# Reuse column schema from main parser + label
COLUMNS = [
    "mint", "name", "symbol",
    "price_usd", "price_native", "fdv", "market_cap",
    "liquidity_usd", "liquidity_base", "liquidity_quote",
    "volume_5m", "volume_1h", "volume_6h", "volume_24h",
    "txns_5m_buys", "txns_5m_sells",
    "txns_1h_buys", "txns_1h_sells",
    "txns_6h_buys", "txns_6h_sells",
    "txns_24h_buys", "txns_24h_sells",
    "price_change_5m", "price_change_1h", "price_change_6h", "price_change_24h",
    "dex_id", "pair_address", "pair_created_at",
    "pair_age_hours",
    "has_website", "has_twitter", "has_telegram", "has_discord",
    "social_count",
    "mint_authority_exists", "freeze_authority_exists",
    "supply", "decimals",
    "buy_sell_ratio_1h", "buy_sell_ratio_24h",
    "liquidity_to_mcap_ratio",
    "volume_to_liquidity_ratio",
    "txns_total_24h",
    "parsed_at",
    # Label
    "is_rug", "rug_signal",
]


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Rug detection heuristics
# ---------------------------------------------------------------------------
RUG_SIGNALS = {
    "zero_liquidity": "Liquidity is $0 (pulled)",
    "near_zero_liquidity": "Liquidity < $50 (abandoned)",
    "price_crash_99": "Price dropped 99%+",
    "price_crash_90": "Price dropped 90%+",
    "no_transactions": "Zero transactions in 24h",
    "mint_authority_active": "Mint authority still enabled (can print tokens)",
    "freeze_authority_active": "Freeze authority enabled (can freeze wallets)",
    "extreme_sell_ratio": "Sells massively outnumber buys (exit dump)",
    "pump_fun_dead": "pump.fun token with no liquidity",
}


def classify_rug(pair: dict, rpc_info: dict | None) -> tuple[bool, list[str]]:
    """Determine if token is likely rugged and why."""
    signals = []

    liq_usd = float(pair.get("liquidity", {}).get("usd", 0) or 0)
    vol_24h = float(pair.get("volume", {}).get("h24", 0) or 0)
    pc_24h = float(pair.get("priceChange", {}).get("h24", 0) or 0)
    txns = pair.get("txns", {})
    buys_24h = int(txns.get("h24", {}).get("buys", 0) or 0)
    sells_24h = int(txns.get("h24", {}).get("sells", 0) or 0)
    mint_addr = pair.get("baseToken", {}).get("address", "")

    # Liquidity signals
    if liq_usd == 0:
        signals.append("zero_liquidity")
    elif liq_usd < 50:
        signals.append("near_zero_liquidity")

    # Price crash
    if pc_24h <= -99:
        signals.append("price_crash_99")
    elif pc_24h <= -90:
        signals.append("price_crash_90")

    # No activity
    if buys_24h + sells_24h == 0:
        signals.append("no_transactions")

    # Extreme sell ratio
    if sells_24h > 0 and buys_24h > 0:
        ratio = sells_24h / buys_24h
        if ratio > 10:
            signals.append("extreme_sell_ratio")

    # On-chain red flags
    if rpc_info:
        if rpc_info.get("mint_authority_exists") == 1:
            signals.append("mint_authority_active")
        if rpc_info.get("freeze_authority_exists") == 1:
            signals.append("freeze_authority_active")

    # pump.fun dead token
    if mint_addr.endswith("pump") and liq_usd < 50:
        signals.append("pump_fun_dead")

    # Need at least 2 signals or 1 strong signal to confirm rug
    strong_signals = {"zero_liquidity", "price_crash_99", "pump_fun_dead"}
    is_rug = (
        len(signals) >= 2
        or any(s in strong_signals for s in signals)
    )

    return is_rug, signals


# ---------------------------------------------------------------------------
# Search strategies to find rugged tokens
# ---------------------------------------------------------------------------
# pump.fun address suffixes + random hex patterns to find diverse dead tokens
PUMP_SUFFIXES = [
    "pump", "0pump", "1pump", "2pump", "3pump", "4pump",
    "5pump", "6pump", "7pump", "8pump", "9pump",
    "apump", "bpump", "cpump", "dpump", "epump", "fpump",
    "gpump", "hpump", "ipump", "jpump", "kpump", "lpump",
    "mpump", "npump", "opump", "ppump", "qpump", "rpump",
    "spump", "tpump", "upump", "vpump", "wpump", "xpump",
    "ypump", "zpump",
]

# Names commonly associated with scams/rugs
SCAM_NAMES = [
    "rug", "rugged", "scam", "honeypot", "rugpull", "fake",
    "elonmusk", "100x", "1000x", "moonshot", "safemoon",
    "presale", "airdrop free", "giveaway",
    "pump.fun", "pumpfun dead",
    # Dead meme patterns
    "test token", "migration", "old token", "v1 deprecated",
]

# Search for tokens with extreme negative price action
BEARISH_QUERIES = [
    "solana -99", "solana crash", "solana dead",
    "pump fun new", "pump fun sol",
    "raydium new", "meteora new",
]


def search_dead_tokens(client: httpx.Client, query: str) -> list[dict]:
    """Search for Solana tokens with zero/near-zero liquidity."""
    try:
        r = client.get(f"{DEXSCREENER_BASE}/latest/dex/search", params={"q": query})
        r.raise_for_status()
        pairs = r.json().get("pairs", [])
        # Filter: Solana only, low liquidity = likely rugged
        dead = []
        for p in pairs:
            if p.get("chainId") != "solana":
                continue
            liq = float(p.get("liquidity", {}).get("usd", 0) or 0)
            if liq < 500:  # tokens with < $500 liq are dead/rugged
                dead.append(p)
        return dead
    except Exception as e:
        log(f"  search error '{query}': {e}")
        return []


def get_single_mint_info(client: httpx.Client, mint: str) -> dict:
    """Fetch mint info from Solana RPC."""
    fail = {"mint_authority_exists": -1, "freeze_authority_exists": -1, "supply": "0", "decimals": 0}
    payload = {
        "jsonrpc": "2.0", "id": 1,
        "method": "getAccountInfo",
        "params": [mint, {"encoding": "jsonParsed"}],
    }
    for attempt in range(3):
        try:
            r = client.post(SOLANA_RPC, json=payload, timeout=15)
            r.raise_for_status()
            info = r.json()["result"]["value"]["data"]["parsed"]["info"]
            return {
                "mint_authority_exists": 1 if info.get("mintAuthority") else 0,
                "freeze_authority_exists": 1 if info.get("freezeAuthority") else 0,
                "supply": info.get("supply", "0"),
                "decimals": info.get("decimals", 0),
            }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                time.sleep(3 * (attempt + 1))
                continue
            return fail
        except Exception:
            return fail
    return fail


def parse_pair(pair: dict, rpc_info: dict | None, is_rug: bool, signals: list[str]) -> dict:
    base = pair.get("baseToken", {})
    liq = pair.get("liquidity", {})
    vol = pair.get("volume", {})
    txns = pair.get("txns", {})
    pc = pair.get("priceChange", {})
    info = pair.get("info", {})

    socials = info.get("socials", [])
    websites = info.get("websites", [])
    social_types = {s.get("type", "") for s in socials}
    has_website = 1 if websites else 0
    has_twitter = 1 if "twitter" in social_types else 0
    has_telegram = 1 if "telegram" in social_types else 0
    has_discord = 1 if "discord" in social_types else 0

    created_ts = pair.get("pairCreatedAt", 0)
    pair_age_hours = round((time.time() * 1000 - created_ts) / 3_600_000, 1) if created_ts else 0

    liq_usd = float(liq.get("usd", 0) or 0)
    mcap = float(pair.get("marketCap", 0) or 0)
    vol_24h = float(vol.get("h24", 0) or 0)

    buys_1h = int(txns.get("h1", {}).get("buys", 0) or 0)
    sells_1h = int(txns.get("h1", {}).get("sells", 0) or 0)
    buys_24h = int(txns.get("h24", {}).get("buys", 0) or 0)
    sells_24h = int(txns.get("h24", {}).get("sells", 0) or 0)

    rpc = rpc_info or {}

    return {
        "mint": base.get("address", ""),
        "name": base.get("name", "")[:100],
        "symbol": base.get("symbol", "")[:20],
        "price_usd": pair.get("priceUsd", 0),
        "price_native": pair.get("priceNative", 0),
        "fdv": pair.get("fdv", 0),
        "market_cap": mcap,
        "liquidity_usd": liq_usd,
        "liquidity_base": liq.get("base", 0),
        "liquidity_quote": liq.get("quote", 0),
        "volume_5m": vol.get("m5", 0),
        "volume_1h": vol.get("h1", 0),
        "volume_6h": vol.get("h6", 0),
        "volume_24h": vol_24h,
        "txns_5m_buys": txns.get("m5", {}).get("buys", 0),
        "txns_5m_sells": txns.get("m5", {}).get("sells", 0),
        "txns_1h_buys": buys_1h,
        "txns_1h_sells": sells_1h,
        "txns_6h_buys": txns.get("h6", {}).get("buys", 0),
        "txns_6h_sells": txns.get("h6", {}).get("sells", 0),
        "txns_24h_buys": buys_24h,
        "txns_24h_sells": sells_24h,
        "price_change_5m": pc.get("m5", 0),
        "price_change_1h": pc.get("h1", 0),
        "price_change_6h": pc.get("h6", 0),
        "price_change_24h": pc.get("h24", 0),
        "dex_id": pair.get("dexId", ""),
        "pair_address": pair.get("pairAddress", ""),
        "pair_created_at": created_ts,
        "pair_age_hours": pair_age_hours,
        "has_website": has_website,
        "has_twitter": has_twitter,
        "has_telegram": has_telegram,
        "has_discord": has_discord,
        "social_count": has_website + has_twitter + has_telegram + has_discord,
        "mint_authority_exists": rpc.get("mint_authority_exists", -1),
        "freeze_authority_exists": rpc.get("freeze_authority_exists", -1),
        "supply": rpc.get("supply", "0"),
        "decimals": rpc.get("decimals", 0),
        "buy_sell_ratio_1h": round(buys_1h / max(sells_1h, 1), 3),
        "buy_sell_ratio_24h": round(buys_24h / max(sells_24h, 1), 3),
        "liquidity_to_mcap_ratio": round(liq_usd / max(mcap, 1), 6) if mcap > 0 else 0,
        "volume_to_liquidity_ratio": round(vol_24h / max(liq_usd, 1), 3) if liq_usd > 0 else 0,
        "txns_total_24h": buys_24h + sells_24h,
        "parsed_at": datetime.now(timezone.utc).isoformat(),
        "is_rug": 1 if is_rug else 0,
        "rug_signal": "|".join(signals),
    }


def main():
    parser = argparse.ArgumentParser(description="Parse rugged Solana tokens for ML training")
    parser.add_argument("--count", type=int, default=1000, help="Target rugged tokens")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    parser.add_argument("--skip-rpc", action="store_true", help="Skip Solana RPC")
    args = parser.parse_args()

    target = args.count
    out_path = args.output or str(
        Path(__file__).resolve().parent.parent / "data" / f"rugged_tokens.csv"
    )
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    log(f"Target: {target} rugged tokens -> {out_path}")

    seen_mints: set[str] = set()
    best_pairs: dict[str, dict] = {}  # mint -> pair with lowest liquidity

    client = httpx.Client(timeout=20, follow_redirects=True)

    # Phase 1: Discover dead tokens
    log("Phase 1: Searching for rugged tokens...")

    all_queries = PUMP_SUFFIXES + SCAM_NAMES + BEARISH_QUERIES
    for qi, query in enumerate(all_queries):
        if len(seen_mints) >= target:
            break
        dead = search_dead_tokens(client, query)
        new = 0
        for p in dead:
            mint = p.get("baseToken", {}).get("address")
            if not mint or mint in seen_mints:
                continue
            best_pairs[mint] = p
            seen_mints.add(mint)
            new += 1
        if new > 0:
            log(f"  [{qi+1}/{len(all_queries)}] '{query}': +{new} dead -> {len(seen_mints)} total")
        time.sleep(REQUEST_DELAY)

    log(f"Phase 1 done: {len(seen_mints)} dead tokens found")

    if len(seen_mints) < target:
        log(f"  (Only found {len(seen_mints)}/{target} - DexScreener search API has limits)")

    # Phase 2: RPC enrichment
    rpc_data: dict[str, dict] = {}
    if args.skip_rpc:
        log("Phase 2: SKIPPED (--skip-rpc)")
    else:
        log("Phase 2: Fetching on-chain data from Solana RPC...")
        all_mints = list(best_pairs.keys())
        enriched = 0
        for idx, mint in enumerate(all_mints):
            rpc = get_single_mint_info(client, mint)
            rpc_data[mint] = rpc
            if rpc["mint_authority_exists"] != -1:
                enriched += 1
            if idx % 50 == 0 and idx > 0:
                log(f"  RPC progress: {idx}/{len(all_mints)} ({enriched} enriched)")
            time.sleep(0.6)
        log(f"  RPC data: {enriched}/{len(all_mints)} tokens enriched")

    # Phase 3: Classify and write
    log("Phase 3: Classifying and writing...")
    rows = []
    rug_count = 0
    signal_counts: dict[str, int] = {}

    for mint, pair in best_pairs.items():
        rpc = rpc_data.get(mint)
        is_rug, signals = classify_rug(pair, rpc)
        row = parse_pair(pair, rpc, is_rug, signals)
        rows.append(row)
        if is_rug:
            rug_count += 1
        for s in signals:
            signal_counts[s] = signal_counts.get(s, 0) + 1

    rows.sort(key=lambda r: float(r.get("liquidity_usd", 0) or 0))

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    log(f"\nDataset ready: {len(rows)} tokens")
    log(f"  Confirmed rugs:      {rug_count} ({round(100*rug_count/max(len(rows),1))}%)")
    log(f"  Not confirmed:       {len(rows) - rug_count}")

    has_mint = sum(1 for r in rows if r["mint_authority_exists"] == 1)
    has_freeze = sum(1 for r in rows if r["freeze_authority_exists"] == 1)
    log(f"  Mint authority:      {has_mint} ({round(100*has_mint/max(len(rows),1))}%)")
    log(f"  Freeze authority:    {has_freeze} ({round(100*has_freeze/max(len(rows),1))}%)")

    log(f"\n  Signal breakdown:")
    for signal, count in sorted(signal_counts.items(), key=lambda x: -x[1]):
        log(f"    {signal:30} {count:4}  {RUG_SIGNALS.get(signal, '')}")

    log(f"\nSaved to: {out_path}")


if __name__ == "__main__":
    main()
