from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class SolanaRpcError(Exception):
    pass


class SolanaRpcClient:
    def __init__(self, rpc_urls: tuple[str, ...]) -> None:
        self.rpc_urls = rpc_urls

    def call(self, method: str, params: object) -> dict:
        last_error: Exception | None = None

        for rpc_url in self.rpc_urls:
            payload = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": method,
                    "params": params,
                }
            ).encode("utf-8")
            request = Request(
                rpc_url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "RugSignal/0.2",
                },
                method="POST",
            )

            try:
                with urlopen(request, timeout=20) as response:
                    response_payload = json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                if exc.code in {403, 429}:
                    last_error = exc
                    continue
                raise SolanaRpcError(f"Solana RPC request failed: HTTP Error {exc.code}") from exc
            except (URLError, TimeoutError) as exc:
                last_error = exc
                continue

            if response_payload.get("error"):
                message = response_payload["error"].get("message", "Unknown Solana RPC error")
                raise SolanaRpcError(message)

            return response_payload["result"]

        if last_error is not None:
            raise SolanaRpcError(f"Solana RPC request failed: {last_error}") from last_error

        raise SolanaRpcError("Solana RPC request failed")

    def call_with_url(self, rpc_url: str, method: str, params: object) -> dict:
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params,
            }
        ).encode("utf-8")
        request = Request(
            rpc_url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "RugSignal/0.2",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=20) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise SolanaRpcError(f"Solana RPC request failed: HTTP Error {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            raise SolanaRpcError(f"Solana RPC request failed: {exc}") from exc

        if response_payload.get("error"):
            message = response_payload["error"].get("message", "Unknown Solana RPC error")
            raise SolanaRpcError(message)

        return response_payload["result"]
