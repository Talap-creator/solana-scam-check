import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { PublicKey, Keypair, SystemProgram, LAMPORTS_PER_SOL } from "@solana/web3.js";
import { assert } from "chai";

describe("rugsignal_oracle", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.RugsignalOracle;
  const publisher = provider.wallet;

  // A fake token mint for testing
  const tokenMint = Keypair.generate();
  const safeTokenMint = Keypair.generate();

  // PDAs
  let oracleConfigPda: PublicKey;
  let tokenScorePda: PublicKey;
  let safeTokenScorePda: PublicKey;
  let userVaultPda: PublicKey;
  let vaultSolPda: PublicKey;

  before(async () => {
    [oracleConfigPda] = PublicKey.findProgramAddressSync(
      [Buffer.from("oracle")],
      program.programId
    );
    [tokenScorePda] = PublicKey.findProgramAddressSync(
      [Buffer.from("score"), tokenMint.publicKey.toBuffer()],
      program.programId
    );
    [safeTokenScorePda] = PublicKey.findProgramAddressSync(
      [Buffer.from("score"), safeTokenMint.publicKey.toBuffer()],
      program.programId
    );
    [userVaultPda] = PublicKey.findProgramAddressSync(
      [Buffer.from("vault"), publisher.publicKey.toBuffer()],
      program.programId
    );
    [vaultSolPda] = PublicKey.findProgramAddressSync(
      [Buffer.from("vault_sol"), publisher.publicKey.toBuffer()],
      program.programId
    );
  });

  it("initializes the oracle", async () => {
    await program.methods
      .initializeOracle()
      .accounts({
        oracleConfig: oracleConfigPda,
        publisher: publisher.publicKey,
        systemProgram: SystemProgram.programId,
      })
      .rpc();

    const oracle = await program.account.oracleConfig.fetch(oracleConfigPda);
    assert.ok(oracle.publisher.equals(publisher.publicKey));
    assert.equal(oracle.totalScoresPublished.toNumber(), 0);
  });

  it("publishes a HIGH risk score for a scam token", async () => {
    await program.methods
      .publishScore(78, { high: {} }, 87)
      .accounts({
        oracleConfig: oracleConfigPda,
        tokenRiskScore: tokenScorePda,
        tokenMint: tokenMint.publicKey,
        publisher: publisher.publicKey,
        systemProgram: SystemProgram.programId,
      })
      .rpc();

    const score = await program.account.tokenRiskScore.fetch(tokenScorePda);
    assert.equal(score.score, 78);
    assert.deepEqual(score.riskLevel, { high: {} });
    assert.equal(score.confidence, 87);
  });

  it("publishes a LOW risk score for a safe token", async () => {
    await program.methods
      .publishScore(15, { low: {} }, 92)
      .accounts({
        oracleConfig: oracleConfigPda,
        tokenRiskScore: safeTokenScorePda,
        tokenMint: safeTokenMint.publicKey,
        publisher: publisher.publicKey,
        systemProgram: SystemProgram.programId,
      })
      .rpc();

    const score = await program.account.tokenRiskScore.fetch(safeTokenScorePda);
    assert.equal(score.score, 15);
    assert.deepEqual(score.riskLevel, { low: {} });
  });

  it("creates a user vault with threshold 50", async () => {
    await program.methods
      .createVault(50)
      .accounts({
        userVault: userVaultPda,
        owner: publisher.publicKey,
        systemProgram: SystemProgram.programId,
      })
      .rpc();

    const vault = await program.account.userVault.fetch(userVaultPda);
    assert.equal(vault.riskThreshold, 50);
    assert.equal(vault.balance.toNumber(), 0);
  });

  it("deposits SOL into the vault", async () => {
    const amount = 0.5 * LAMPORTS_PER_SOL;

    await program.methods
      .deposit(new anchor.BN(amount))
      .accounts({
        userVault: userVaultPda,
        vaultSol: vaultSolPda,
        owner: publisher.publicKey,
        systemProgram: SystemProgram.programId,
      })
      .rpc();

    const vault = await program.account.userVault.fetch(userVaultPda);
    assert.equal(vault.balance.toNumber(), amount);
  });

  it("REJECTS guarded_swap for high-risk token (score 78 > threshold 50)", async () => {
    try {
      await program.methods
        .guardedSwap(new anchor.BN(0.1 * LAMPORTS_PER_SOL))
        .accounts({
          userVault: userVaultPda,
          tokenRiskScore: tokenScorePda,
          tokenMint: tokenMint.publicKey,
          vaultSol: vaultSolPda,
          owner: publisher.publicKey,
          systemProgram: SystemProgram.programId,
        })
        .rpc();
      assert.fail("Should have been rejected");
    } catch (err) {
      assert.include(err.message, "RiskTooHigh");
    }
  });

  it("ALLOWS guarded_swap for safe token (score 15 <= threshold 50)", async () => {
    const amount = 0.1 * LAMPORTS_PER_SOL;

    await program.methods
      .guardedSwap(new anchor.BN(amount))
      .accounts({
        userVault: userVaultPda,
        tokenRiskScore: safeTokenScorePda,
        tokenMint: safeTokenMint.publicKey,
        vaultSol: vaultSolPda,
        owner: publisher.publicKey,
        systemProgram: SystemProgram.programId,
      })
      .rpc();

    const vault = await program.account.userVault.fetch(userVaultPda);
    // Balance should have decreased
    assert.isBelow(vault.balance.toNumber(), 0.5 * LAMPORTS_PER_SOL);
  });

  it("triggers emergency_exit when token goes critical", async () => {
    // Update the scam token score to critical (85)
    await program.methods
      .publishScore(85, { critical: {} }, 95)
      .accounts({
        oracleConfig: oracleConfigPda,
        tokenRiskScore: tokenScorePda,
        tokenMint: tokenMint.publicKey,
        publisher: publisher.publicKey,
        systemProgram: SystemProgram.programId,
      })
      .rpc();

    // Emergency exit
    await program.methods
      .emergencyExit()
      .accounts({
        userVault: userVaultPda,
        tokenRiskScore: tokenScorePda,
        tokenMint: tokenMint.publicKey,
        vaultSol: vaultSolPda,
        owner: publisher.publicKey,
        systemProgram: SystemProgram.programId,
      })
      .rpc();

    const vault = await program.account.userVault.fetch(userVaultPda);
    assert.equal(vault.balance.toNumber(), 0);
  });
});
