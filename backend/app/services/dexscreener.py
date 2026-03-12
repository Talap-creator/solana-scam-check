from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class DexScreenerError(Exception):
    pass


class DexScreenerClient:
    def __init__(self, base_url: str = "https://api.dexscreener.com") -> None:
        self.base_url = base_url.rstrip("/")

    def get_latest_token_profiles(self) -> list[dict]:
        request = Request(
            f"{self.base_url}/token-profiles/latest/v1",
            headers={
                "Accept": "application/json",
                "User-Agent": "RugSignal/0.2",
            },
            method="GET",
        )

        try:
            with urlopen(request, timeout=12) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise DexScreenerError(f"DEX Screener request failed: HTTP Error {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise DexScreenerError(f"DEX Screener request failed: {exc}") from exc

        if not isinstance(payload, list):
            raise DexScreenerError("DEX Screener returned an unexpected payload")

        return payload

    def get_token_pairs(self, chain_id: str, token_address: str) -> list[dict]:
        request = Request(
            f"{self.base_url}/tokens/v1/{chain_id}/{token_address}",
            headers={
                "Accept": "application/json",
                "User-Agent": "RugSignal/0.2",
            },
            method="GET",
        )

        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise DexScreenerError(f"DEX Screener request failed: HTTP Error {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise DexScreenerError(f"DEX Screener request failed: {exc}") from exc

        if not isinstance(payload, list):
            raise DexScreenerError("DEX Screener returned an unexpected payload")

        return payload


def pick_most_liquid_pair(pairs: list[dict]) -> dict | None:
    best_pair: dict | None = None
    best_liquidity = -1.0

    for pair in pairs:
        liquidity = pair.get("liquidity") or {}
        usd_liquidity = float(liquidity.get("usd") or 0)
        if usd_liquidity > best_liquidity:
            best_liquidity = usd_liquidity
            best_pair = pair

    return best_pair


def extract_token_profile(pair: dict, token_address: str) -> tuple[str | None, str | None, str | None]:
    base_token = pair.get("baseToken") or {}
    quote_token = pair.get("quoteToken") or {}
    info = pair.get("info") or {}

    if base_token.get("address") == token_address:
        name = base_token.get("name")
        symbol = base_token.get("symbol")
    elif quote_token.get("address") == token_address:
        name = quote_token.get("name")
        symbol = quote_token.get("symbol")
    else:
        name = base_token.get("name")
        symbol = base_token.get("symbol")

    logo_url = info.get("imageUrl")
    return name, symbol, logo_url
