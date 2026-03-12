from __future__ import annotations

from .config import get_settings
from .services.dexscreener import DexScreenerClient
from .services.repository import ReportRepository
from .services.solana_rpc import SolanaRpcClient


settings = get_settings()
solana_rpc = SolanaRpcClient(settings.solana_rpc_urls)
dexscreener = DexScreenerClient(settings.dexscreener_base_url)
repository = ReportRepository(solana_rpc, settings.token_holders_max_pages, dexscreener)


def get_repository():
    return repository


def get_solana_rpc():
    return solana_rpc


def get_dexscreener():
    return dexscreener
