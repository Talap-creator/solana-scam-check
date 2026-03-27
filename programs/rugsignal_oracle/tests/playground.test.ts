// Solana Playground test file — paste this into anchor.test.ts in Playground

describe("rugsignal_oracle", () => {
  // Playground provides pg.program and pg.wallet automatically
  const program = pg.program;
  const wallet = pg.wallet;

  // Fake token mints for testing
  const tokenMint = web3.Keypair.generate();
  const safeTokenMint = web3.Keypair.generate();

  // PDAs
  const [oracleConfigPda] = web3.PublicKey.findProgramAddressSync(
    [Buffer.from("oracle")],
    program.programId
  );
  const [tokenScorePda] = web3.PublicKey.findProgramAddressSync(
    [Buffer.from("score"), tokenMint.publicKey.toBuffer()],
    program.programId
  );
  const [safeTokenScorePda] = web3.PublicKey.findProgramAddressSync(
    [Buffer.from("score"), safeTokenMint.publicKey.toBuffer()],
    program.programId
  );
  const [userVaultPda] = web3.PublicKey.findProgramAddressSync(
    [Buffer.from("vault"), wallet.publicKey.toBuffer()],
    program.programId
  );
  const [vaultSolPda] = web3.PublicKey.findProgramAddressSync(
    [Buffer.from("vault_sol"), wallet.publicKey.toBuffer()],
    program.programId
  );

  it("1. Initialize Oracle", async () => {
    const tx = await program.methods
      .initializeOracle()
      .accounts({
        oracleConfig: oracleConfigPda,
        publisher: wallet.publicKey,
        systemProgram: web3.SystemProgram.programId,
      })
      .rpc();

    console.log("Init Oracle TX:", tx);

    const oracle = await program.account.oracleConfig.fetch(oracleConfigPda);
    console.log("Publisher:", oracle.publisher.toBase58());
    console.log("Total published:", oracle.totalScoresPublished.toNumber());
    assert(oracle.publisher.equals(wallet.publicKey));
  });

  it("2. Publish HIGH risk score (scam token, score=78)", async () => {
    const tx = await program.methods
      .publishScore(78, { high: {} }, 87)
      .accounts({
        oracleConfig: oracleConfigPda,
        tokenRiskScore: tokenScorePda,
        tokenMint: tokenMint.publicKey,
        publisher: wallet.publicKey,
        systemProgram: web3.SystemProgram.programId,
      })
      .rpc();

    console.log("Publish SCAM score TX:", tx);

    const score = await program.account.tokenRiskScore.fetch(tokenScorePda);
    console.log("Score:", score.score, "Risk:", JSON.stringify(score.riskLevel), "Confidence:", score.confidence);
    assert(score.score === 78);
  });

  it("3. Publish LOW risk score (safe token, score=15)", async () => {
    const tx = await program.methods
      .publishScore(15, { low: {} }, 92)
      .accounts({
        oracleConfig: oracleConfigPda,
        tokenRiskScore: safeTokenScorePda,
        tokenMint: safeTokenMint.publicKey,
        publisher: wallet.publicKey,
        systemProgram: web3.SystemProgram.programId,
      })
      .rpc();

    console.log("Publish SAFE score TX:", tx);

    const score = await program.account.tokenRiskScore.fetch(safeTokenScorePda);
    console.log("Score:", score.score, "Risk:", JSON.stringify(score.riskLevel));
    assert(score.score === 15);
  });

  it("4. Create vault with threshold=50", async () => {
    const tx = await program.methods
      .createVault(50)
      .accounts({
        userVault: userVaultPda,
        owner: wallet.publicKey,
        systemProgram: web3.SystemProgram.programId,
      })
      .rpc();

    console.log("Create Vault TX:", tx);

    const vault = await program.account.userVault.fetch(userVaultPda);
    console.log("Threshold:", vault.riskThreshold, "Balance:", vault.balance.toNumber());
    assert(vault.riskThreshold === 50);
  });

  it("5. Deposit 0.1 SOL into vault", async () => {
    const amount = 0.1 * web3.LAMPORTS_PER_SOL;

    const tx = await program.methods
      .deposit(new BN(amount))
      .accounts({
        userVault: userVaultPda,
        vaultSol: vaultSolPda,
        owner: wallet.publicKey,
        systemProgram: web3.SystemProgram.programId,
      })
      .rpc();

    console.log("Deposit TX:", tx);

    const vault = await program.account.userVault.fetch(userVaultPda);
    console.log("New balance:", vault.balance.toNumber(), "lamports");
    assert(vault.balance.toNumber() === amount);
  });

  it("6. REJECT swap to scam token (score 78 > threshold 50)", async () => {
    try {
      await program.methods
        .guardedSwap(new BN(0.01 * web3.LAMPORTS_PER_SOL))
        .accounts({
          userVault: userVaultPda,
          tokenRiskScore: tokenScorePda,
          tokenMint: tokenMint.publicKey,
          vaultSol: vaultSolPda,
          owner: wallet.publicKey,
          systemProgram: web3.SystemProgram.programId,
        })
        .rpc();

      assert(false, "Should have been rejected!");
    } catch (err) {
      console.log("CORRECTLY REJECTED:", err.message.includes("RiskTooHigh") ? "RiskTooHigh" : err.message);
      assert(err.message.includes("RiskTooHigh") || err.message.includes("6005"));
    }
  });

  it("7. ALLOW swap to safe token (score 15 <= threshold 50)", async () => {
    const amount = 0.01 * web3.LAMPORTS_PER_SOL;

    const tx = await program.methods
      .guardedSwap(new BN(amount))
      .accounts({
        userVault: userVaultPda,
        tokenRiskScore: safeTokenScorePda,
        tokenMint: safeTokenMint.publicKey,
        vaultSol: vaultSolPda,
        owner: wallet.publicKey,
        systemProgram: web3.SystemProgram.programId,
      })
      .rpc();

    console.log("SWAP APPROVED TX:", tx);

    const vault = await program.account.userVault.fetch(userVaultPda);
    console.log("Balance after swap:", vault.balance.toNumber(), "lamports");
    assert(vault.balance.toNumber() < 0.1 * web3.LAMPORTS_PER_SOL);
  });

  it("8. Emergency exit (update score to critical=85, then exit)", async () => {
    // Update scam token to critical
    await program.methods
      .publishScore(85, { critical: {} }, 95)
      .accounts({
        oracleConfig: oracleConfigPda,
        tokenRiskScore: tokenScorePda,
        tokenMint: tokenMint.publicKey,
        publisher: wallet.publicKey,
        systemProgram: web3.SystemProgram.programId,
      })
      .rpc();

    console.log("Score updated to CRITICAL (85)");

    // Emergency exit
    const tx = await program.methods
      .emergencyExit()
      .accounts({
        userVault: userVaultPda,
        tokenRiskScore: tokenScorePda,
        tokenMint: tokenMint.publicKey,
        vaultSol: vaultSolPda,
        owner: wallet.publicKey,
        systemProgram: web3.SystemProgram.programId,
      })
      .rpc();

    console.log("EMERGENCY EXIT TX:", tx);

    const vault = await program.account.userVault.fetch(userVaultPda);
    console.log("Balance after exit:", vault.balance.toNumber());
    assert(vault.balance.toNumber() === 0);
  });
});
