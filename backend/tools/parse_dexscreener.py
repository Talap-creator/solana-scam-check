"""
DexScreener + Solana RPC Token Parser
=====================================
Pulls Solana tokens from DexScreener (free API, no key needed) and enriches
with on-chain authority data from Solana mainnet RPC.

Outputs: CSV dataset ready for ML training.

Usage:
    python tools/parse_dexscreener.py                    # default: 500 tokens
    python tools/parse_dexscreener.py --count 2000       # parse 2000 tokens
    python tools/parse_dexscreener.py --output data.csv  # custom output path
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

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEXSCREENER_BASE = "https://api.dexscreener.com"
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
REQUEST_DELAY = 0.35  # be nice to free APIs
RPC_BATCH_SIZE = 5  # batch RPC requests (public RPC is strict)

# Search queries to discover diverse tokens
SEARCH_QUERIES = [
    # popular meme themes
    "pump", "sol", "meme", "dog", "cat", "pepe", "doge", "trump",
    "ai", "gpt", "bot", "moon", "inu", "baby", "safe", "elon",
    "bonk", "jup", "ray", "orca", "wif", "popcat", "bome", "wen",
    "nft", "dao", "defi", "swap", "stake", "yield", "farm",
    "chad", "based", "wojak", "frog", "bear", "bull", "rocket",
    "gold", "diamond", "gem", "fire", "king", "queen", "god",
    "cash", "money", "rich", "whale", "shark", "lion", "eagle",
    # more themes
    "token", "coin", "crypto", "chain", "block", "web3", "meta",
    "world", "war", "game", "play", "earn", "win", "bet", "luck",
    "dragon", "wolf", "fox", "panda", "monkey", "ape", "gorilla",
    "pixel", "punk", "art", "music", "film", "anime", "manga",
    "usa", "china", "japan", "korea", "india", "russia", "brazil",
    "love", "hate", "happy", "sad", "angry", "crazy", "wild",
    "super", "mega", "ultra", "hyper", "turbo", "nitro", "power",
    "dark", "light", "shadow", "ghost", "demon", "angel", "saint",
    "pizza", "burger", "sushi", "coffee", "beer", "wine", "water",
    "mars", "venus", "jupiter", "saturn", "neptune", "pluto", "star",
    "wizard", "ninja", "samurai", "pirate", "viking", "knight", "hero",
    "flash", "speed", "fast", "quick", "rapid", "instant", "swift",
    "green", "blue", "red", "black", "white", "pink", "purple",
    "solana meme", "solana pump", "solana new", "solana token",
    "pumpfun", "raydium", "meteora", "jupiter token",
    "degen", "wagmi", "ngmi", "hodl", "fomo", "yolo", "gm",
]

# CSV columns
COLUMNS = [
    # identifiers
    "mint", "name", "symbol",
    # market data
    "price_usd", "price_native", "fdv", "market_cap",
    "liquidity_usd", "liquidity_base", "liquidity_quote",
    # volume
    "volume_5m", "volume_1h", "volume_6h", "volume_24h",
    # transactions
    "txns_5m_buys", "txns_5m_sells",
    "txns_1h_buys", "txns_1h_sells",
    "txns_6h_buys", "txns_6h_sells",
    "txns_24h_buys", "txns_24h_sells",
    # price changes
    "price_change_5m", "price_change_1h", "price_change_6h", "price_change_24h",
    # pair info
    "dex_id", "pair_address", "pair_created_at",
    "pair_age_hours",
    # socials
    "has_website", "has_twitter", "has_telegram", "has_discord",
    "social_count",
    # on-chain (from RPC)
    "mint_authority_exists", "freeze_authority_exists",
    "supply", "decimals",
    # derived features
    "buy_sell_ratio_1h", "buy_sell_ratio_24h",
    "liquidity_to_mcap_ratio",
    "volume_to_liquidity_ratio",
    "txns_total_24h",
    # metadata
    "parsed_at",
]


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# DexScreener API
# ---------------------------------------------------------------------------
def search_tokens(client: httpx.Client, query: str) -> list[dict]:
    """Search DexScreener for Solana pairs matching query."""
    try:
        r = client.get(f"{DEXSCREENER_BASE}/latest/dex/search", params={"q": query})
        r.raise_for_status()
        pairs = r.json().get("pairs", [])
        return [p for p in pairs if p.get("chainId") == "solana"]
    except Exception as e:
        log(f"  search error for '{query}': {e}")
        return []


def get_token_profiles(client: httpx.Client) -> list[dict]:
    """Get latest token profiles (trending/boosted)."""
    results = []
    for endpoint in ["/token-profiles/latest/v1", "/token-boosts/top/v1"]:
        try:
            r = client.get(f"{DEXSCREENER_BASE}{endpoint}")
            r.raise_for_status()
            data = r.json()
            sol_tokens = [t for t in data if t.get("chainId") == "solana"]
            results.extend(sol_tokens)
        except Exception as e:
            log(f"  profiles error {endpoint}: {e}")
    return results


def get_token_pairs(client: httpx.Client, mint: str) -> list[dict]:
    """Get all pairs for a specific token."""
    try:
        r = client.get(f"{DEXSCREENER_BASE}/latest/dex/tokens/{mint}")
        r.raise_for_status()
        return r.json().get("pairs", []) or []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Solana RPC — batch mint info
# ---------------------------------------------------------------------------
def batch_get_mint_info(client: httpx.Client, mints: list[str]) -> dict[str, dict]:
    """Fetch mint authority, freeze authority, supply, decimals one by one."""
    results: dict[str, dict] = {}
    fail_default = {"mint_authority_exists": -1, "freeze_authority_exists": -1, "supply": "0", "decimals": 0}
    consecutive_429 = 0

    for idx, mint in enumerate(mints):
        if consecutive_429 >= 10:
            log(f"  RPC blocked after {idx} tokens, skipping rest")
            for m in mints[idx:]:
                results[m] = dict(fail_default)
            break

        payload = {
            "jsonrpc": "2.0", "id": 1,
            "method": "getAccountInfo",
            "params": [mint, {"encoding": "jsonParsed"}],
        }
        for attempt in range(3):
            try:
                r = client.post(SOLANA_RPC, json=payload, timeout=15)
                r.raise_for_status()
                resp = r.json()
                info = resp["result"]["value"]["data"]["parsed"]["info"]
                results[mint] = {
                    "mint_authority_exists": 1 if info.get("mintAuthority") else 0,
                    "freeze_authority_exists": 1 if info.get("freezeAuthority") else 0,
                    "supply": info.get("supply", "0"),
                    "decimals": info.get("decimals", 0),
                }
                consecutive_429 = 0
                break
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    consecutive_429 += 1
                    wait = 3 * (attempt + 1)
                    time.sleep(wait)
                    continue
                results[mint] = dict(fail_default)
                break
            except Exception:
                results[mint] = dict(fail_default)
                break
        else:
            results[mint] = dict(fail_default)

        if idx % 50 == 0 and idx > 0:
            ok = sum(1 for v in results.values() if v["mint_authority_exists"] != -1)
            log(f"  RPC progress: {idx}/{len(mints)} ({ok} enriched)")
        time.sleep(0.6)

    return results


# ---------------------------------------------------------------------------
# Parse pair into row
# ---------------------------------------------------------------------------
def parse_pair(pair: dict, rpc_info: dict | None) -> dict:
    base = pair.get("baseToken", {})
    liq = pair.get("liquidity", {})
    vol = pair.get("volume", {})
    txns = pair.get("txns", {})
    pc = pair.get("priceChange", {})
    info = pair.get("info", {})

    # Socials
    socials = info.get("socials", [])
    websites = info.get("websites", [])
    social_types = {s.get("type", "") for s in socials}
    has_website = 1 if websites else 0
    has_twitter = 1 if "twitter" in social_types else 0
    has_telegram = 1 if "telegram" in social_types else 0
    has_discord = 1 if "discord" in social_types else 0

    # Pair age
    created_ts = pair.get("pairCreatedAt", 0)
    pair_age_hours = 0
    if created_ts:
        pair_age_hours = round((time.time() * 1000 - created_ts) / 3_600_000, 1)

    # Derived
    liq_usd = float(liq.get("usd", 0) or 0)
    mcap = float(pair.get("marketCap", 0) or 0)
    vol_24h = float(vol.get("h24", 0) or 0)

    buys_1h = int(txns.get("h1", {}).get("buys", 0) or 0)
    sells_1h = int(txns.get("h1", {}).get("sells", 0) or 0)
    buys_24h = int(txns.get("h24", {}).get("buys", 0) or 0)
    sells_24h = int(txns.get("h24", {}).get("sells", 0) or 0)

    buy_sell_1h = round(buys_1h / max(sells_1h, 1), 3)
    buy_sell_24h = round(buys_24h / max(sells_24h, 1), 3)
    liq_mcap_ratio = round(liq_usd / max(mcap, 1), 6) if mcap > 0 else 0
    vol_liq_ratio = round(vol_24h / max(liq_usd, 1), 3) if liq_usd > 0 else 0

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
        "buy_sell_ratio_1h": buy_sell_1h,
        "buy_sell_ratio_24h": buy_sell_24h,
        "liquidity_to_mcap_ratio": liq_mcap_ratio,
        "volume_to_liquidity_ratio": vol_liq_ratio,
        "txns_total_24h": buys_24h + sells_24h,
        "parsed_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def enrich_csv_with_rpc(csv_path: str):
    """Add RPC data (mint/freeze authority) to an existing CSV."""
    import shutil

    log(f"Enriching {csv_path} with Solana RPC data...")
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Find rows missing RPC data
    need_rpc = [r for r in rows if r.get("mint_authority_exists", "-1") == "-1"]
    log(f"  {len(need_rpc)}/{len(rows)} rows need RPC enrichment")

    if not need_rpc:
        log("  Nothing to enrich")
        return

    mints = [r["mint"] for r in need_rpc]
    client = httpx.Client(timeout=20, follow_redirects=True)
    rpc_data = batch_get_mint_info(client, mints)

    enriched = 0
    for row in rows:
        rpc = rpc_data.get(row["mint"])
        if rpc and rpc["mint_authority_exists"] != -1:
            row["mint_authority_exists"] = rpc["mint_authority_exists"]
            row["freeze_authority_exists"] = rpc["freeze_authority_exists"]
            row["supply"] = rpc["supply"]
            row["decimals"] = rpc["decimals"]
            enriched += 1

    # Backup and write
    shutil.copy2(csv_path, csv_path + ".bak")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    log(f"  Enriched {enriched}/{len(need_rpc)} rows. Saved to {csv_path}")


def main():
    parser = argparse.ArgumentParser(description="Parse Solana tokens from DexScreener + RPC")
    parser.add_argument("--count", type=int, default=500, help="Target number of unique tokens")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    parser.add_argument("--skip-rpc", action="store_true", help="Skip Solana RPC enrichment (faster)")
    parser.add_argument("--enrich-rpc", type=str, default=None, help="Enrich existing CSV with RPC data")
    args = parser.parse_args()

    # Enrich mode: add RPC data to existing CSV
    if args.enrich_rpc:
        enrich_csv_with_rpc(args.enrich_rpc)
        return

    target = args.count
    out_path = args.output or str(
        Path(__file__).resolve().parent.parent / "data" / f"dexscreener_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    )
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    log(f"Target: {target} unique tokens -> {out_path}")

    seen_mints: set[str] = set()
    best_pairs: dict[str, dict] = {}  # mint -> best pair (highest liquidity)

    client = httpx.Client(timeout=20, follow_redirects=True)

    # Phase 1: Discover tokens via search + profiles
    log("Phase 1: Discovering tokens via DexScreener...")

    # Boosted/trending tokens first
    profiles = get_token_profiles(client)
    profile_mints = [t["tokenAddress"] for t in profiles if "tokenAddress" in t]
    log(f"  Found {len(profile_mints)} trending/boosted tokens")

    # Fetch pair data for profile tokens (batch by 30 — DexScreener supports comma-separated)
    for i in range(0, len(profile_mints), 30):
        batch = profile_mints[i : i + 30]
        addr_str = ",".join(batch)
        try:
            r = client.get(f"{DEXSCREENER_BASE}/latest/dex/tokens/{addr_str}")
            r.raise_for_status()
            for p in r.json().get("pairs", []):
                mint = p.get("baseToken", {}).get("address")
                if not mint or mint in seen_mints:
                    continue
                liq = float(p.get("liquidity", {}).get("usd", 0) or 0)
                if mint not in best_pairs or liq > float(best_pairs[mint].get("liquidity", {}).get("usd", 0) or 0):
                    best_pairs[mint] = p
                    seen_mints.add(mint)
        except Exception as e:
            log(f"  batch fetch error: {e}")
        time.sleep(REQUEST_DELAY)

    log(f"  After profiles: {len(seen_mints)} unique tokens")

    # Search queries
    for qi, query in enumerate(SEARCH_QUERIES):
        if len(seen_mints) >= target:
            break
        pairs = search_tokens(client, query)
        new = 0
        for p in pairs:
            mint = p.get("baseToken", {}).get("address")
            if not mint or mint in seen_mints:
                continue
            liq = float(p.get("liquidity", {}).get("usd", 0) or 0)
            if mint not in best_pairs or liq > float(best_pairs[mint].get("liquidity", {}).get("usd", 0) or 0):
                best_pairs[mint] = p
                seen_mints.add(mint)
                new += 1
        log(f"  [{qi+1}/{len(SEARCH_QUERIES)}] '{query}': +{new} new -> {len(seen_mints)} total")
        time.sleep(REQUEST_DELAY)

    log(f"Phase 1 done: {len(seen_mints)} unique tokens discovered")

    # Phase 2: Enrich with Solana RPC (mint/freeze authority)
    rpc_data: dict[str, dict] = {}
    if args.skip_rpc:
        log("Phase 2: SKIPPED (--skip-rpc)")
    else:
        log("Phase 2: Fetching on-chain authority data from Solana RPC...")
        all_mints = list(best_pairs.keys())
        rpc_data = batch_get_mint_info(client, all_mints)
        rpc_ok = sum(1 for v in rpc_data.values() if v["mint_authority_exists"] != -1)
        log(f"  RPC data: {rpc_ok}/{len(all_mints)} tokens enriched")

    # Phase 3: Write CSV
    log(f"Phase 3: Writing {len(best_pairs)} rows to {out_path}...")
    rows = []
    for mint, pair in best_pairs.items():
        row = parse_pair(pair, rpc_data.get(mint))
        rows.append(row)

    # Sort by liquidity descending
    rows.sort(key=lambda r: float(r.get("liquidity_usd", 0) or 0), reverse=True)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    # Stats
    has_liq = sum(1 for r in rows if float(r["liquidity_usd"] or 0) > 0)
    has_vol = sum(1 for r in rows if float(r["volume_24h"] or 0) > 0)
    has_mint_auth = sum(1 for r in rows if r["mint_authority_exists"] == 1)
    has_freeze_auth = sum(1 for r in rows if r["freeze_authority_exists"] == 1)
    has_socials = sum(1 for r in rows if r["social_count"] > 0)

    log(f"\nDataset ready: {len(rows)} tokens")
    log(f"  With liquidity:      {has_liq}")
    log(f"  With 24h volume:     {has_vol}")
    log(f"  Mint authority:      {has_mint_auth} ({round(100*has_mint_auth/max(len(rows),1))}%)")
    log(f"  Freeze authority:    {has_freeze_auth} ({round(100*has_freeze_auth/max(len(rows),1))}%)")
    log(f"  Has socials:         {has_socials} ({round(100*has_socials/max(len(rows),1))}%)")
    log(f"\nSaved to: {out_path}")


if __name__ == "__main__":
    main()
