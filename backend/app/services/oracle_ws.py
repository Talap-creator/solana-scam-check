"""Solana WebSocket listener for Oracle real-time triggers.

Subscribes to program account changes for monitored token mints via
standard Solana WebSocket (wss://api.mainnet-beta.solana.com).
When a significant change is detected, calls the provided callback
to trigger an immediate re-score — cutting latency from 90s to seconds.

No Helius required. Uses standard Solana WebSocket JSON-RPC.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)

# Standard public Solana WebSocket endpoints (fallback chain)
_WS_URLS = [
    "wss://api.mainnet-beta.solana.com",
    "wss://solana-rpc.publicnode.com",
]

# Token Program ID — subscribe to its account changes
_TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"


class OracleWebSocketListener:
    """
    Maintains a WebSocket connection to Solana and fires score triggers
    when monitored token accounts change.

    Usage:
        listener = OracleWebSocketListener(on_trigger=agent.score_and_publish)
        asyncio.create_task(listener.run(mint_addresses))
    """

    def __init__(
        self,
        on_trigger: Callable[[str], Awaitable[None]],
        ws_urls: tuple[str, ...] = tuple(_WS_URLS),
    ):
        self._on_trigger = on_trigger
        self._ws_urls = ws_urls
        self._subscriptions: dict[int, str] = {}  # sub_id → mint
        self._running = False

    async def run(self, mints: list[str]) -> None:
        """Connect and subscribe. Reconnects on disconnect."""
        self._running = True
        while self._running:
            for ws_url in self._ws_urls:
                try:
                    await self._connect(ws_url, mints)
                except Exception as exc:
                    logger.warning("WS connect failed (%s): %s", ws_url, exc)
            if self._running:
                logger.info("WebSocket disconnected, retrying in 10s...")
                await asyncio.sleep(10)

    def stop(self) -> None:
        self._running = False

    async def _connect(self, ws_url: str, mints: list[str]) -> None:
        try:
            import websockets  # type: ignore
        except ImportError:
            logger.warning(
                "websockets package not installed. "
                "Run: pip install websockets  — falling back to polling."
            )
            return

        logger.info("Connecting to Solana WebSocket: %s", ws_url)
        async with websockets.connect(
            ws_url,
            ping_interval=30,
            ping_timeout=10,
            close_timeout=5,
        ) as ws:
            logger.info("WebSocket connected, subscribing to %d mints", len(mints))
            self._subscriptions = {}

            # Subscribe to each mint account
            for i, mint in enumerate(mints):
                sub_msg = {
                    "jsonrpc": "2.0",
                    "id": i + 1,
                    "method": "accountSubscribe",
                    "params": [
                        mint,
                        {"encoding": "base64", "commitment": "confirmed"},
                    ],
                }
                await ws.send(json.dumps(sub_msg))

            # Handle subscription confirmations and notifications
            async for raw in ws:
                if not self._running:
                    break
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                # Subscription confirmation: map sub_id → mint
                if "result" in msg and "id" in msg:
                    req_id = msg["id"]
                    if 1 <= req_id <= len(mints):
                        sub_id = msg["result"]
                        mint = mints[req_id - 1]
                        self._subscriptions[sub_id] = mint
                        logger.debug("Subscribed to %s (sub_id=%d)", mint[:12], sub_id)
                    continue

                # Notification
                if msg.get("method") == "accountNotification":
                    params = msg.get("params", {})
                    sub_id = params.get("subscription")
                    mint = self._subscriptions.get(sub_id)
                    if mint:
                        logger.info("WS trigger: account change on %s", mint[:12])
                        asyncio.create_task(self._fire(mint))

    async def _fire(self, mint: str) -> None:
        try:
            await self._on_trigger(mint)
        except Exception as exc:
            logger.warning("WS trigger callback failed for %s: %s", mint[:12], exc)
