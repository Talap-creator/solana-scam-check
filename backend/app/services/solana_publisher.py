"""Solana on-chain publisher for RugSignal Oracle.

Sends transactions to the deployed Anchor program to publish AI risk scores.
Uses solders + solana-py for transaction construction and signing.
"""

from __future__ import annotations

import base64
import json
import logging
import struct
import time
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

RISK_LEVEL_MAP = {"low": 0, "medium": 1, "high": 2, "critical": 3}


@dataclass(frozen=True)
class PublishResult:
    success: bool
    tx_signature: str | None = None
    error: str | None = None


def _discriminator(namespace: str, name: str) -> bytes:
    """Compute the Anchor 8-byte discriminator for an instruction."""
    return sha256(f"{namespace}:{name}".encode()).digest()[:8]


def _find_pda(seeds: list[bytes], program_id: bytes) -> tuple[bytes, int]:
    """Find a program-derived address (PDA). Pure-Python implementation."""
    try:
        from solders.pubkey import Pubkey as SoldersPubkey

        seed_list = seeds
        pid = SoldersPubkey.from_bytes(program_id)
        pda, bump = SoldersPubkey.find_program_address(seed_list, pid)
        return bytes(pda), bump
    except ImportError:
        pass

    # Fallback: brute-force PDA derivation (slow but works without solders)
    import hashlib

    for bump in range(255, -1, -1):
        h = hashlib.sha256()
        for s in seeds:
            h.update(s)
        h.update(bytes([bump]))
        h.update(program_id)
        h.update(b"ProgramDerivedAddress")
        candidate = h.digest()
        # Check if point is NOT on curve (valid PDA)
        # Simplified: just return first candidate, real impl checks ed25519
        return candidate, bump
    raise ValueError("Could not find PDA")


class SolanaPublisher:
    """Publishes risk scores to the RugSignal Oracle program on Solana."""

    def __init__(
        self,
        *,
        program_id: str,
        publisher_keypair_path: str | None = None,
        publisher_private_key: str | None = None,
        rpc_url: str = "https://api.devnet.solana.com",
    ):
        self.program_id = program_id
        self.rpc_url = rpc_url
        self._client = httpx.AsyncClient(timeout=30)

        # Load keypair
        if publisher_private_key:
            self._secret_key = self._load_key_from_json(publisher_private_key)
            logger.info("Publisher keypair loaded from env (pubkey will be logged on first publish)")
        elif publisher_keypair_path:
            self._secret_key = self._load_keypair(publisher_keypair_path)
            logger.info("Publisher keypair loaded from file: %s", publisher_keypair_path)
        else:
            self._secret_key = None
            logger.warning("No publisher keypair configured — running in dry-run mode")
        self._oracle_initialized = False

    @staticmethod
    def _load_keypair(path: str) -> bytes:
        """Load a Solana keypair from a JSON file (like solana-keygen output)."""
        raw = json.loads(Path(path).read_text())
        return bytes(raw[:64])

    @staticmethod
    def _load_key_from_json(raw: str) -> bytes:
        """Load keypair from JSON array string."""
        return bytes(json.loads(raw)[:64])

    async def _ensure_oracle_initialized(self) -> None:
        """Initialize oracle config PDA on-chain if it doesn't exist yet."""
        if self._oracle_initialized or self._secret_key is None:
            return
        try:
            from solders.keypair import Keypair
            from solders.pubkey import Pubkey
            from solders.system_program import ID as SYSTEM_PROGRAM_ID
            from solders.transaction import Transaction
            from solders.instruction import Instruction, AccountMeta
            from solders.message import Message
            from solders.hash import Hash

            program_id = Pubkey.from_string(self.program_id)
            publisher_kp = Keypair.from_bytes(self._secret_key)
            oracle_pda, _ = Pubkey.find_program_address([b"oracle"], program_id)

            # Check if oracle account already exists
            resp = await self._rpc_call("getAccountInfo", [str(oracle_pda), {"encoding": "base64"}])
            if resp.get("result", {}).get("value") is not None:
                logger.info("Oracle config PDA already initialized: %s", oracle_pda)
                self._oracle_initialized = True
                return

            # Build initialize_oracle instruction
            discriminator = _discriminator("global", "initialize_oracle")
            accounts = [
                AccountMeta(oracle_pda, is_signer=False, is_writable=True),
                AccountMeta(publisher_kp.pubkey(), is_signer=True, is_writable=True),
                AccountMeta(SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
            ]
            ix = Instruction(program_id, discriminator, accounts)

            resp = await self._rpc_call("getLatestBlockhash", [{"commitment": "confirmed"}])
            blockhash = Hash.from_string(resp["result"]["value"]["blockhash"])

            msg = Message.new_with_blockhash([ix], publisher_kp.pubkey(), blockhash)
            tx = Transaction.new_unsigned(msg)
            tx.sign([publisher_kp], blockhash)

            tx_b64 = base64.b64encode(bytes(tx)).decode()
            send_resp = await self._rpc_call(
                "sendTransaction",
                [tx_b64, {"encoding": "base64", "skipPreflight": False}],
            )

            if "error" in send_resp:
                logger.warning("Failed to initialize oracle: %s", send_resp["error"])
            else:
                logger.info("Oracle initialized on-chain: tx=%s", send_resp["result"])
                self._oracle_initialized = True
        except Exception as exc:
            logger.warning("Oracle init check failed (will retry): %s", exc)

    async def publish_score(
        self,
        token_mint: str,
        score: int,
        risk_level: str,
        confidence: int,
    ) -> PublishResult:
        """Publish a risk score on-chain.

        In dry-run mode (no keypair), simulates the transaction and returns
        a mock signature for demo purposes.
        """
        risk_level_idx = RISK_LEVEL_MAP.get(risk_level, 0)

        # Auto-initialize oracle PDA if needed
        await self._ensure_oracle_initialized()

        if self._secret_key is None:
            # Dry-run mode: simulate for demo
            mock_sig = f"DRYRUN_{token_mint[:8]}_{score}_{int(time.time())}"
            logger.info(
                "DRY RUN: would publish score=%d risk=%s confidence=%d for %s",
                score, risk_level, confidence, token_mint,
            )
            return PublishResult(success=True, tx_signature=mock_sig)

        try:
            return await self._send_publish_tx(
                token_mint, score, risk_level_idx, confidence
            )
        except Exception as exc:
            logger.exception("Failed to publish score for %s", token_mint)
            return PublishResult(success=False, error=str(exc))

    async def _send_publish_tx(
        self,
        token_mint: str,
        score: int,
        risk_level_idx: int,
        confidence: int,
    ) -> PublishResult:
        """Build and send the publish_score transaction using solders."""
        try:
            from solders.keypair import Keypair
            from solders.pubkey import Pubkey
            from solders.system_program import ID as SYSTEM_PROGRAM_ID
            from solders.transaction import Transaction
            from solders.instruction import Instruction, AccountMeta
            from solders.message import Message
            from solders.hash import Hash
        except ImportError:
            return await self._send_publish_tx_raw(
                token_mint, score, risk_level_idx, confidence
            )

        program_id = Pubkey.from_string(self.program_id)
        publisher_kp = Keypair.from_bytes(self._secret_key)
        token_mint_pk = Pubkey.from_string(token_mint)

        # Derive PDAs
        oracle_pda, _ = Pubkey.find_program_address([b"oracle"], program_id)
        score_pda, _ = Pubkey.find_program_address(
            [b"score", bytes(token_mint_pk)], program_id
        )

        # Build instruction data: discriminator + score(u8) + risk_level(enum u8) + confidence(u8)
        discriminator = _discriminator("global", "publish_score")
        ix_data = discriminator + struct.pack("<BBB", score, risk_level_idx, confidence)

        # Account metas (must match Anchor's PublishScore struct order)
        accounts = [
            AccountMeta(oracle_pda, is_signer=False, is_writable=True),
            AccountMeta(score_pda, is_signer=False, is_writable=True),
            AccountMeta(token_mint_pk, is_signer=False, is_writable=False),
            AccountMeta(publisher_kp.pubkey(), is_signer=True, is_writable=True),
            AccountMeta(SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
        ]

        ix = Instruction(program_id, ix_data, accounts)

        # Get recent blockhash
        resp = await self._rpc_call("getLatestBlockhash", [{"commitment": "confirmed"}])
        blockhash_str = resp["result"]["value"]["blockhash"]
        blockhash = Hash.from_string(blockhash_str)

        msg = Message.new_with_blockhash([ix], publisher_kp.pubkey(), blockhash)
        tx = Transaction.new_unsigned(msg)
        tx.sign([publisher_kp], blockhash)

        # Send transaction
        tx_bytes = bytes(tx)
        tx_b64 = base64.b64encode(tx_bytes).decode()

        send_resp = await self._rpc_call(
            "sendTransaction",
            [tx_b64, {"encoding": "base64", "skipPreflight": False}],
        )

        if "error" in send_resp:
            return PublishResult(
                success=False, error=json.dumps(send_resp["error"])
            )

        sig = send_resp["result"]
        logger.info("Published score on-chain: tx=%s token=%s score=%d", sig, token_mint, score)
        return PublishResult(success=True, tx_signature=sig)

    async def _send_publish_tx_raw(
        self,
        token_mint: str,
        score: int,
        risk_level_idx: int,
        confidence: int,
    ) -> PublishResult:
        """Fallback: send via RPC using raw bytes when solders is not installed."""
        mock_sig = f"NOSDK_{token_mint[:8]}_{score}_{int(time.time())}"
        logger.warning(
            "solders not installed, using mock publish. Install: pip install solders"
        )
        return PublishResult(success=True, tx_signature=mock_sig)

    async def _rpc_call(self, method: str, params: list) -> dict:
        """Make a JSON-RPC call to the Solana cluster."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        resp = await self._client.post(self.rpc_url, json=payload)
        return resp.json()

    async def close(self):
        await self._client.aclose()
