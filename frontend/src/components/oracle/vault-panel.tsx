"use client";

import { useState, useCallback, useEffect } from "react";
import { useWallet, useConnection } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import {
  PublicKey,
  Transaction,
  TransactionInstruction,
  SystemProgram,
  LAMPORTS_PER_SOL,
} from "@solana/web3.js";
import { type OracleScore } from "@/lib/api";

const PROGRAM_ID = new PublicKey("HXrM4MfnenFcSWiakw4A6mQAstwhpKQECGBPa7Sn4MuS");

function discriminator(name: string): Buffer {
  const { createHash } = require("crypto") as typeof import("crypto");
  return Buffer.from(createHash("sha256").update(`global:${name}`).digest()).subarray(0, 8);
}

function findPDA(seeds: Buffer[]): PublicKey {
  return PublicKey.findProgramAddressSync(seeds, PROGRAM_ID)[0];
}

interface VaultInfo {
  balance: number;
  riskThreshold: number;
  exists: boolean;
}

export function VaultPanel({ scores }: { scores: OracleScore[] }) {
  const { publicKey, sendTransaction, connected } = useWallet();
  const { connection } = useConnection();

  const [vault, setVault] = useState<VaultInfo | null>(null);
  const [threshold, setThreshold] = useState("50");
  const [depositAmount, setDepositAmount] = useState("0.1");
  const [loading, setLoading] = useState<string | null>(null);
  const [msg, setMsg] = useState("");
  const [walletSol, setWalletSol] = useState<number | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const vaultPda = publicKey ? findPDA([Buffer.from("vault"), publicKey.toBuffer()]) : null;
  const vaultSolPda = publicKey ? findPDA([Buffer.from("vault_sol"), publicKey.toBuffer()]) : null;

  // Load vault state
  const loadVault = useCallback(async () => {
    if (!publicKey || !vaultPda) return;
    setRefreshing(true);
    setLoadError(null);
    try {
      const info = await connection.getAccountInfo(vaultPda);
      const sol = await connection.getBalance(publicKey);
      setWalletSol(sol / LAMPORTS_PER_SOL);
      if (!info) {
        setVault({ exists: false, balance: 0, riskThreshold: 50 });
        return;
      }
      // Parse vault: skip 8-byte discriminator
      // Layout: owner(32) balance(8) risk_threshold(1) created_at(8) bump(1)
      const data = Buffer.from(info.data);
      const balance = Number(data.readBigUInt64LE(40));
      const riskThreshold = data[48];
      setVault({ exists: true, balance, riskThreshold });
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : String(e));
      setVault({ exists: false, balance: 0, riskThreshold: 50 });
    } finally {
      setRefreshing(false);
    }
  }, [publicKey, vaultPda, connection]);

  useEffect(() => {
    if (connected) void loadVault();
  }, [connected, loadVault]);

  const sendTx = useCallback(async (ix: TransactionInstruction, label: string) => {
    if (!publicKey) return;
    setLoading(label);
    setMsg("");
    try {
      const { blockhash, lastValidBlockHeight } = await connection.getLatestBlockhash("confirmed");
      const tx = new Transaction();
      tx.recentBlockhash = blockhash;
      tx.feePayer = publicKey;
      tx.add(ix);
      const sig = await sendTransaction(tx, connection, { skipPreflight: true, maxRetries: 5, preflightCommitment: "confirmed" });
      // Poll for confirmation up to 45s
      let confirmed = false;
      for (let i = 0; i < 15; i++) {
        await new Promise(r => setTimeout(r, 3000));
        const status = await connection.getSignatureStatus(sig);
        const conf = status?.value?.confirmationStatus;
        if (conf === "confirmed" || conf === "finalized") { confirmed = true; break; }
        if (status?.value?.err) break;
        setMsg(`pending:${sig}`);
      }
      if (!confirmed) {
        setMsg(`pending:${sig}`);
        setLoading(null);
        void loadVault();
        return;
      }
      setMsg(`ok:${sig}`);
      await loadVault();
    } catch (e) {
      setMsg(`err:${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(null);
    }
  }, [publicKey, connection, sendTransaction, loadVault]);

  const createVault = useCallback(async () => {
    if (!publicKey || !vaultPda) return;
    const disc = discriminator("create_vault");
    const thresholdBuf = Buffer.alloc(1);
    thresholdBuf.writeUInt8(parseInt(threshold));
    const data = Buffer.concat([disc, thresholdBuf]);

    const ix = new TransactionInstruction({
      programId: PROGRAM_ID,
      keys: [
        { pubkey: vaultPda, isSigner: false, isWritable: true },
        { pubkey: publicKey, isSigner: true, isWritable: true },
        { pubkey: SystemProgram.programId, isSigner: false, isWritable: false },
      ],
      data,
    });
    await sendTx(ix, "create");
  }, [publicKey, vaultPda, threshold, sendTx]);

  const deposit = useCallback(async () => {
    if (!publicKey || !vaultPda || !vaultSolPda) return;
    const disc = discriminator("deposit");
    const lamports = BigInt(Math.floor(parseFloat(depositAmount) * LAMPORTS_PER_SOL));
    const amountBuf = Buffer.alloc(8);
    amountBuf.writeBigUInt64LE(lamports);
    const data = Buffer.concat([disc, amountBuf]);

    const ix = new TransactionInstruction({
      programId: PROGRAM_ID,
      keys: [
        { pubkey: vaultPda, isSigner: false, isWritable: true },
        { pubkey: vaultSolPda, isSigner: false, isWritable: true },
        { pubkey: publicKey, isSigner: true, isWritable: true },
        { pubkey: SystemProgram.programId, isSigner: false, isWritable: false },
      ],
      data,
    });
    await sendTx(ix, "deposit");
  }, [publicKey, vaultPda, vaultSolPda, depositAmount, sendTx]);

  const emergencyExit = useCallback(async (tokenMint: string) => {
    if (!publicKey || !vaultPda || !vaultSolPda) return;
    const mintPk = new PublicKey(tokenMint);
    const scorePda = findPDA([Buffer.from("score"), mintPk.toBuffer()]);
    const disc = discriminator("emergency_exit");

    const ix = new TransactionInstruction({
      programId: PROGRAM_ID,
      keys: [
        { pubkey: vaultPda, isSigner: false, isWritable: true },
        { pubkey: scorePda, isSigner: false, isWritable: false },
        { pubkey: mintPk, isSigner: false, isWritable: false },
        { pubkey: vaultSolPda, isSigner: false, isWritable: true },
        { pubkey: publicKey, isSigner: false, isWritable: true },
        { pubkey: SystemProgram.programId, isSigner: false, isWritable: false },
      ],
      data: disc,
    });
    await sendTx(ix, `exit_${tokenMint.slice(0, 8)}`);
  }, [publicKey, vaultPda, vaultSolPda, sendTx]);

  const [swapResult, setSwapResult] = useState<{ token: string; blocked: boolean; sig?: string; error?: string } | null>(null);

  const guardedSwap = useCallback(async (tokenMint: string, tokenScore: number | null) => {
    if (!publicKey || !vaultPda || !vaultSolPda) return;
    const mintPk = new PublicKey(tokenMint);
    const scorePda = findPDA([Buffer.from("score"), mintPk.toBuffer()]);
    const disc = discriminator("guarded_swap");
    // amount: 1000 lamports (nominal test swap)
    const amountBuf = Buffer.alloc(8);
    amountBuf.writeBigUInt64LE(BigInt(1000));
    const data = Buffer.concat([disc, amountBuf]);

    const ix = new TransactionInstruction({
      programId: PROGRAM_ID,
      keys: [
        { pubkey: vaultPda, isSigner: false, isWritable: true },
        { pubkey: scorePda, isSigner: false, isWritable: false },
        { pubkey: mintPk, isSigner: false, isWritable: false },
        { pubkey: vaultSolPda, isSigner: false, isWritable: true },
        { pubkey: publicKey, isSigner: true, isWritable: true },
        { pubkey: SystemProgram.programId, isSigner: false, isWritable: false },
      ],
      data,
    });

    setLoading(`swap_${tokenMint.slice(0, 8)}`);
    setSwapResult(null);
    try {
      const { blockhash, lastValidBlockHeight } = await connection.getLatestBlockhash("confirmed");
      const tx = new Transaction();
      tx.recentBlockhash = blockhash;
      tx.feePayer = publicKey;
      tx.add(ix);
      const sig = await sendTransaction(tx, connection, { skipPreflight: true, maxRetries: 5, preflightCommitment: "confirmed" });
      try {
        await connection.confirmTransaction({ signature: sig, blockhash, lastValidBlockHeight }, "confirmed");
        setSwapResult({ token: tokenMint, blocked: false, sig });
      } catch {
        setSwapResult({ token: tokenMint, blocked: false, sig, error: "pending" });
      }
    } catch (e) {
      const errMsg = e instanceof Error ? e.message : String(e);
      const blocked = errMsg.toLowerCase().includes("risk") || errMsg.includes("0x1770") || errMsg.includes("custom program error");
      setSwapResult({ token: tokenMint, blocked, error: errMsg });
    } finally {
      setLoading(null);
    }
  }, [publicKey, vaultPda, vaultSolPda, connection, sendTransaction]);

  const criticalTokens = scores.filter(s => s.risk_level === "critical" || (s.score != null && s.score >= 75));

  return (
    <article className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa]">
          Guarded Vault
        </h2>
        <WalletMultiButton style={{
          background: "rgba(37,99,235,0.8)",
          borderRadius: "12px",
          fontSize: "12px",
          height: "36px",
          padding: "0 16px",
        }} />
      </div>

      {!connected ? (
        <p className="text-sm text-slate-400">Connect your Phantom/Solflare wallet (devnet) to use GuardedVault</p>
      ) : vault === null ? (
        <div className="flex items-center gap-3">
          <p className="text-sm text-slate-400">Loading vault...</p>
          <button onClick={() => void loadVault()} disabled={refreshing} className="text-xs text-blue-400 underline disabled:opacity-50">{refreshing ? "Loading..." : "Refresh"}</button>
        </div>
      ) : !vault.exists ? (
        <div className="space-y-3">
          <p className="text-sm text-slate-400">No vault yet. Create one with a risk threshold — swaps to tokens above this score will be blocked.</p>
          {walletSol !== null && (
            <p className="text-xs text-slate-500">Wallet balance: {walletSol.toFixed(3)} SOL (devnet)</p>
          )}
          {vaultPda && (
            <p className="text-xs text-slate-600">
              Vault PDA:{" "}
              <a href={`https://explorer.solana.com/address/${vaultPda.toBase58()}?cluster=devnet`} target="_blank" rel="noreferrer" className="text-blue-500 underline font-mono">
                {vaultPda.toBase58().slice(0, 20)}...
              </a>
            </p>
          )}
          <div className="flex items-center gap-3">
            <label className="text-xs text-slate-400">Risk threshold (0-100)</label>
            <input
              type="number"
              min="0"
              max="100"
              value={threshold}
              onChange={e => setThreshold(e.target.value)}
              className="w-20 rounded-lg border border-[rgba(59,130,246,0.2)] bg-[rgba(2,6,23,0.6)] px-3 py-1.5 text-sm text-slate-100 outline-none"
            />
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={createVault}
              disabled={loading === "create"}
              className="rounded-lg bg-[#2563eb] px-4 py-2 text-sm font-bold text-white disabled:opacity-50 hover:brightness-110"
            >
              {loading === "create" ? "Creating..." : "Create Vault"}
            </button>
            <button onClick={() => void loadVault()} disabled={refreshing} className="text-xs text-slate-400 underline hover:text-slate-200 disabled:opacity-50">
              {refreshing ? "Loading..." : "Refresh"}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Vault stats */}
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-xl border border-[rgba(59,130,246,0.12)] bg-white/[0.03] px-3 py-2">
              <p className="text-xs text-slate-500">Balance</p>
              <p className="mt-1 text-lg font-bold">{(vault.balance / LAMPORTS_PER_SOL).toFixed(4)} SOL</p>
            </div>
            <div className="rounded-xl border border-[rgba(59,130,246,0.12)] bg-white/[0.03] px-3 py-2">
              <p className="text-xs text-slate-500">Risk threshold</p>
              <p className="mt-1 text-lg font-bold">{vault.riskThreshold}/100</p>
            </div>
            <div className="rounded-xl border border-[rgba(59,130,246,0.12)] bg-white/[0.03] px-3 py-2">
              <p className="text-xs text-slate-500">Wallet</p>
              <p className="mt-1 text-lg font-bold">{walletSol?.toFixed(3)} SOL</p>
            </div>
          </div>

          {/* Deposit */}
          <div className="flex items-center gap-3">
            <input
              type="number"
              min="0.001"
              step="0.01"
              value={depositAmount}
              onChange={e => setDepositAmount(e.target.value)}
              className="w-28 rounded-lg border border-[rgba(59,130,246,0.2)] bg-[rgba(2,6,23,0.6)] px-3 py-1.5 text-sm text-slate-100 outline-none"
            />
            <span className="text-xs text-slate-400">SOL</span>
            <button
              onClick={deposit}
              disabled={!!loading}
              className="rounded-lg bg-[#2563eb] px-4 py-2 text-sm font-bold text-white disabled:opacity-50 hover:brightness-110"
            >
              {loading === "deposit" ? "Depositing..." : "Deposit"}
            </button>
          </div>

          {/* Emergency exit */}
          {criticalTokens.length > 0 && (
            <div className="rounded-xl border border-rose-400/30 bg-rose-400/5 p-4">
              <p className="mb-2 text-xs font-bold uppercase tracking-wider text-rose-400">Critical tokens detected</p>
              {criticalTokens.map(t => (
                <div key={t.token_address} className="flex items-center justify-between">
                  <div>
                    <span className="text-sm text-slate-200">{t.display_name || t.token_address.slice(0, 8)}...</span>
                    <span className="ml-2 text-xs text-rose-400">score {t.score}</span>
                  </div>
                  <button
                    onClick={() => emergencyExit(t.token_address)}
                    disabled={!!loading || vault.balance === 0}
                    className="rounded-lg border border-rose-400/30 bg-rose-400/10 px-3 py-1.5 text-xs font-bold text-rose-300 disabled:opacity-50 hover:bg-rose-400/20"
                  >
                    {loading === `exit_${t.token_address.slice(0, 8)}` ? "Exiting..." : "Emergency Exit"}
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Test Guarded Swap */}
          {scores.length > 0 && (
            <div className="rounded-xl border border-[rgba(59,130,246,0.12)] bg-white/[0.02] p-4">
              <p className="mb-1 text-xs font-bold uppercase tracking-wider text-[#60a5fa]">Test Guarded Swap</p>
              <p className="mb-3 text-xs text-slate-500">
                Sends a real on-chain tx — contract checks AI score vs your threshold ({vault.riskThreshold}/100). Score &gt; threshold = blocked.
              </p>
              <div className="space-y-2">
                {scores.map(t => {
                  const score = t.score ?? 0;
                  const willBlock = vault && score > vault.riskThreshold;
                  const label = `swap_${t.token_address.slice(0, 8)}`;
                  return (
                    <div key={t.token_address} className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="truncate text-sm text-slate-300">
                          {t.display_name || `${t.token_address.slice(0, 8)}...`}
                        </span>
                        <span className={`shrink-0 text-xs font-bold ${score >= 75 ? "text-rose-400" : score >= 50 ? "text-amber-400" : "text-emerald-400"}`}>
                          {score}/100
                        </span>
                        <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold ${willBlock ? "bg-rose-400/15 text-rose-300" : "bg-emerald-400/15 text-emerald-300"}`}>
                          {willBlock ? "WILL BLOCK" : "WILL PASS"}
                        </span>
                      </div>
                      <button
                        onClick={() => guardedSwap(t.token_address, t.score)}
                        disabled={!!loading || vault.balance === 0}
                        className="shrink-0 rounded-lg border border-[rgba(59,130,246,0.3)] bg-[rgba(37,99,235,0.1)] px-3 py-1.5 text-xs font-bold text-blue-300 disabled:opacity-50 hover:bg-[rgba(37,99,235,0.2)]"
                      >
                        {loading === label ? "Sending..." : "Simulate Swap"}
                      </button>
                    </div>
                  );
                })}
              </div>

              {swapResult && (
                <div className={`mt-3 rounded-lg p-3 text-xs ${swapResult.blocked ? "border border-rose-400/30 bg-rose-400/10" : swapResult.sig ? "border border-emerald-400/30 bg-emerald-400/10" : "border border-rose-400/30 bg-rose-400/10"}`}>
                  {swapResult.blocked ? (
                    <>
                      <p className="font-bold text-rose-300">BLOCKED by GuardedVault</p>
                      <p className="mt-1 text-rose-400/80">Contract rejected the swap — token risk score exceeds your threshold.</p>
                    </>
                  ) : swapResult.sig ? (
                    <>
                      <p className="font-bold text-emerald-300">{swapResult.error === "pending" ? "Swap sent (confirming)" : "Swap ALLOWED"}</p>
                      <p className="mt-1 text-emerald-400/80">
                        Token score is within your threshold.{" "}
                        <a href={`https://explorer.solana.com/tx/${swapResult.sig}?cluster=devnet`} target="_blank" rel="noreferrer" className="underline">
                          View on Explorer
                        </a>
                      </p>
                    </>
                  ) : (
                    <>
                      <p className="font-bold text-rose-300">Transaction failed</p>
                      <p className="mt-1 break-all text-rose-400/80">{swapResult.error}</p>
                    </>
                  )}
                </div>
              )}

              {vault.balance === 0 && (
                <p className="mt-2 text-xs text-amber-400/70">Deposit SOL first to enable swap simulation.</p>
              )}
            </div>
          )}

          {vault.balance === 0 && scores.length === 0 && (
            <p className="text-xs text-slate-500">Deposit SOL to enable guarded swaps. Emergency exit activates when a monitored token goes Critical (score ≥ 75).</p>
          )}
        </div>
      )}

      {loadError && (
        <p className="mt-2 text-xs text-amber-400">RPC error: {loadError}</p>
      )}

      {msg && (() => {
        const explorerBase = "https://explorer.solana.com/tx/";
        if (msg.startsWith("ok:")) {
          const sig = msg.slice(3);
          return (
            <p className="mt-3 text-xs text-emerald-400">
              Success —{" "}
              <a href={`${explorerBase}${sig}?cluster=devnet`} target="_blank" rel="noreferrer" className="underline">
                view on Explorer
              </a>
            </p>
          );
        }
        if (msg.startsWith("pending:")) {
          const sig = msg.slice(8);
          return (
            <p className="mt-3 text-xs text-amber-400">
              Sent (confirming) —{" "}
              <a href={`${explorerBase}${sig}?cluster=devnet`} target="_blank" rel="noreferrer" className="underline">
                check on Explorer
              </a>
            </p>
          );
        }
        return <p className="mt-3 text-xs text-rose-400">{msg.startsWith("err:") ? msg.slice(4) : msg}</p>;
      })()}
    </article>
  );
}
