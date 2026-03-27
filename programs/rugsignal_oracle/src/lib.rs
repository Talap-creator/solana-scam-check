use anchor_lang::prelude::*;
use anchor_lang::system_program;

declare_id!("HXrM4MfnenFcSWiakw4A6mQAstwhpKQECGBPa7Sn4MuS");

#[program]
pub mod rugsignal_oracle {
    use super::*;

    /// Initialize the oracle with a publisher authority.
    /// Only the publisher can write risk scores.
    pub fn initialize_oracle(ctx: Context<InitializeOracle>) -> Result<()> {
        let oracle = &mut ctx.accounts.oracle_config;
        oracle.publisher = ctx.accounts.publisher.key();
        oracle.total_scores_published = 0;
        oracle.created_at = Clock::get()?.unix_timestamp;
        oracle.bump = ctx.bumps.oracle_config;
        msg!("Oracle initialized. Publisher: {}", oracle.publisher);
        Ok(())
    }

    /// AI agent publishes a risk score for a token.
    /// Only the authorized publisher can call this.
    pub fn publish_score(
        ctx: Context<PublishScore>,
        score: u8,
        risk_level: RiskLevel,
        confidence: u8,
    ) -> Result<()> {
        require!(score <= 100, OracleError::InvalidScore);
        require!(confidence <= 100, OracleError::InvalidConfidence);

        let token_score = &mut ctx.accounts.token_risk_score;
        let oracle = &mut ctx.accounts.oracle_config;

        token_score.token_mint = ctx.accounts.token_mint.key();
        token_score.score = score;
        token_score.risk_level = risk_level;
        token_score.confidence = confidence;
        token_score.updated_at = Clock::get()?.unix_timestamp;
        token_score.publisher = ctx.accounts.publisher.key();
        token_score.bump = ctx.bumps.token_risk_score;

        oracle.total_scores_published += 1;

        msg!(
            "Score published: token={} score={} risk={:?} confidence={}",
            token_score.token_mint,
            score,
            risk_level,
            confidence
        );

        Ok(())
    }

    /// User creates a guarded vault with a risk threshold.
    /// The vault will reject swaps to tokens with score above the threshold.
    pub fn create_vault(ctx: Context<CreateVault>, risk_threshold: u8) -> Result<()> {
        require!(risk_threshold <= 100, OracleError::InvalidThreshold);

        let vault = &mut ctx.accounts.user_vault;
        vault.owner = ctx.accounts.owner.key();
        vault.balance = 0;
        vault.risk_threshold = risk_threshold;
        vault.created_at = Clock::get()?.unix_timestamp;
        vault.bump = ctx.bumps.user_vault;

        msg!(
            "Vault created for {} with threshold {}",
            vault.owner,
            risk_threshold
        );
        Ok(())
    }

    /// User deposits SOL into their guarded vault.
    pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
        require!(amount > 0, OracleError::ZeroAmount);

        // Transfer SOL from user to vault PDA
        system_program::transfer(
            CpiContext::new(
                ctx.accounts.system_program.to_account_info(),
                system_program::Transfer {
                    from: ctx.accounts.owner.to_account_info(),
                    to: ctx.accounts.vault_sol.to_account_info(),
                },
            ),
            amount,
        )?;

        let vault = &mut ctx.accounts.user_vault;
        vault.balance = vault.balance.checked_add(amount).unwrap();

        msg!("Deposited {} lamports. New balance: {}", amount, vault.balance);
        Ok(())
    }

    /// Guarded swap: checks oracle score before allowing the operation.
    /// If the token's risk score exceeds the vault's threshold, the swap is REJECTED.
    pub fn guarded_swap(ctx: Context<GuardedSwap>, amount: u64) -> Result<()> {
        let score_val = ctx.accounts.token_risk_score.score;
        let threshold = ctx.accounts.user_vault.risk_threshold;
        let balance = ctx.accounts.user_vault.balance;

        require!(amount > 0, OracleError::ZeroAmount);
        require!(balance >= amount, OracleError::InsufficientBalance);

        // THE KEY LOGIC: AI score gates the on-chain action
        require!(
            score_val <= threshold,
            OracleError::RiskTooHigh
        );

        // In a real implementation, this would execute a swap via Jupiter/Raydium CPI.
        // For the hackathon MVP, we simulate by transferring SOL out of the vault.
        let bump = ctx.bumps.vault_sol;
        let owner_key = ctx.accounts.owner.key();

        let seeds = &[
            b"vault_sol" as &[u8],
            owner_key.as_ref(),
            &[bump],
        ];
        let signer_seeds = &[&seeds[..]];

        system_program::transfer(
            CpiContext::new_with_signer(
                ctx.accounts.system_program.to_account_info(),
                system_program::Transfer {
                    from: ctx.accounts.vault_sol.to_account_info(),
                    to: ctx.accounts.owner.to_account_info(),
                },
                signer_seeds,
            ),
            amount,
        )?;

        ctx.accounts.user_vault.balance = balance.checked_sub(amount).unwrap();

        msg!(
            "Swap APPROVED. Token score {} <= threshold {}. Amount: {}",
            score_val,
            threshold,
            amount
        );
        Ok(())
    }

    /// Emergency exit: withdraw all funds if a token's score goes critical.
    /// Anyone can trigger this for a vault if the associated token is critical (score >= 75).
    pub fn emergency_exit(ctx: Context<EmergencyExit>) -> Result<()> {
        let score_val = ctx.accounts.token_risk_score.score;
        let token_mint = ctx.accounts.token_risk_score.token_mint;
        let balance = ctx.accounts.user_vault.balance;

        require!(
            score_val >= 75,
            OracleError::NotCritical
        );
        require!(balance > 0, OracleError::ZeroAmount);

        // Use actual SOL in vault_sol PDA, not the recorded balance
        let vault_sol_lamports = ctx.accounts.vault_sol.lamports();
        let transfer_amount = vault_sol_lamports.min(balance);

        if transfer_amount > 0 {
            let bump = ctx.bumps.vault_sol;
            let owner_key = ctx.accounts.owner.key();

            let seeds = &[
                b"vault_sol" as &[u8],
                owner_key.as_ref(),
                &[bump],
            ];
            let signer_seeds = &[&seeds[..]];

            system_program::transfer(
                CpiContext::new_with_signer(
                    ctx.accounts.system_program.to_account_info(),
                    system_program::Transfer {
                        from: ctx.accounts.vault_sol.to_account_info(),
                        to: ctx.accounts.owner.to_account_info(),
                    },
                    signer_seeds,
                ),
                transfer_amount,
            )?;
        }

        ctx.accounts.user_vault.balance = 0;

        msg!(
            "EMERGENCY EXIT triggered! Token {} score={} (critical). Withdrew {} lamports.",
            token_mint,
            score_val,
            transfer_amount
        );
        Ok(())
    }

    /// Update the risk threshold of an existing vault.
    pub fn update_threshold(ctx: Context<UpdateThreshold>, new_threshold: u8) -> Result<()> {
        require!(new_threshold <= 100, OracleError::InvalidThreshold);
        let vault = &mut ctx.accounts.user_vault;
        vault.risk_threshold = new_threshold;
        msg!("Threshold updated to {}", new_threshold);
        Ok(())
    }
}

// ─── Accounts ────────────────────────────────────────────────────────────────

#[derive(Accounts)]
pub struct InitializeOracle<'info> {
    #[account(
        init,
        payer = publisher,
        space = 8 + OracleConfig::INIT_SPACE,
        seeds = [b"oracle"],
        bump,
    )]
    pub oracle_config: Account<'info, OracleConfig>,

    #[account(mut)]
    pub publisher: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct PublishScore<'info> {
    #[account(
        mut,
        seeds = [b"oracle"],
        bump = oracle_config.bump,
        has_one = publisher,
    )]
    pub oracle_config: Account<'info, OracleConfig>,

    #[account(
        init_if_needed,
        payer = publisher,
        space = 8 + TokenRiskScore::INIT_SPACE,
        seeds = [b"score", token_mint.key().as_ref()],
        bump,
    )]
    pub token_risk_score: Account<'info, TokenRiskScore>,

    /// CHECK: This is the token mint we're scoring. We only store its pubkey.
    pub token_mint: UncheckedAccount<'info>,

    #[account(mut)]
    pub publisher: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct CreateVault<'info> {
    #[account(
        init,
        payer = owner,
        space = 8 + UserVault::INIT_SPACE,
        seeds = [b"vault", owner.key().as_ref()],
        bump,
    )]
    pub user_vault: Account<'info, UserVault>,

    #[account(mut)]
    pub owner: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Deposit<'info> {
    #[account(
        mut,
        seeds = [b"vault", owner.key().as_ref()],
        bump = user_vault.bump,
        has_one = owner,
    )]
    pub user_vault: Account<'info, UserVault>,

    /// CHECK: PDA that holds the SOL for this vault.
    #[account(
        mut,
        seeds = [b"vault_sol", owner.key().as_ref()],
        bump,
    )]
    pub vault_sol: SystemAccount<'info>,

    #[account(mut)]
    pub owner: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct GuardedSwap<'info> {
    #[account(
        mut,
        seeds = [b"vault", owner.key().as_ref()],
        bump = user_vault.bump,
        has_one = owner,
    )]
    pub user_vault: Account<'info, UserVault>,

    #[account(
        seeds = [b"score", token_mint.key().as_ref()],
        bump = token_risk_score.bump,
    )]
    pub token_risk_score: Account<'info, TokenRiskScore>,

    /// CHECK: The token mint being swapped to.
    pub token_mint: UncheckedAccount<'info>,

    /// CHECK: PDA that holds the SOL for this vault.
    #[account(
        mut,
        seeds = [b"vault_sol", owner.key().as_ref()],
        bump,
    )]
    pub vault_sol: SystemAccount<'info>,

    #[account(mut)]
    pub owner: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct EmergencyExit<'info> {
    #[account(
        mut,
        seeds = [b"vault", owner.key().as_ref()],
        bump = user_vault.bump,
        has_one = owner,
    )]
    pub user_vault: Account<'info, UserVault>,

    #[account(
        seeds = [b"score", token_mint.key().as_ref()],
        bump = token_risk_score.bump,
    )]
    pub token_risk_score: Account<'info, TokenRiskScore>,

    /// CHECK: The token mint that triggered the emergency.
    pub token_mint: UncheckedAccount<'info>,

    /// CHECK: PDA that holds the SOL for this vault.
    #[account(
        mut,
        seeds = [b"vault_sol", owner.key().as_ref()],
        bump,
    )]
    pub vault_sol: SystemAccount<'info>,

    /// CHECK: The vault owner who receives the funds.
    #[account(mut)]
    pub owner: SystemAccount<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateThreshold<'info> {
    #[account(
        mut,
        seeds = [b"vault", owner.key().as_ref()],
        bump = user_vault.bump,
        has_one = owner,
    )]
    pub user_vault: Account<'info, UserVault>,

    pub owner: Signer<'info>,
}

// ─── State ───────────────────────────────────────────────────────────────────

#[account]
#[derive(InitSpace)]
pub struct OracleConfig {
    pub publisher: Pubkey,
    pub total_scores_published: u64,
    pub created_at: i64,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct TokenRiskScore {
    pub token_mint: Pubkey,
    pub score: u8,
    pub risk_level: RiskLevel,
    pub confidence: u8,
    pub updated_at: i64,
    pub publisher: Pubkey,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct UserVault {
    pub owner: Pubkey,
    pub balance: u64,
    pub risk_threshold: u8,
    pub created_at: i64,
    pub bump: u8,
}

// ─── Enums ───────────────────────────────────────────────────────────────────

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Copy, Debug, PartialEq, Eq, InitSpace)]
pub enum RiskLevel {
    Low,
    Medium,
    High,
    Critical,
}

// ─── Errors ──────────────────────────────────────────────────────────────────

#[error_code]
pub enum OracleError {
    #[msg("Score must be between 0 and 100")]
    InvalidScore,
    #[msg("Confidence must be between 0 and 100")]
    InvalidConfidence,
    #[msg("Risk threshold must be between 0 and 100")]
    InvalidThreshold,
    #[msg("Amount must be greater than zero")]
    ZeroAmount,
    #[msg("Insufficient vault balance")]
    InsufficientBalance,
    #[msg("Token risk score exceeds vault threshold — swap rejected")]
    RiskTooHigh,
    #[msg("Token is not in critical state (score < 75)")]
    NotCritical,
}
