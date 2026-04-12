import { PlatformShell } from "@/components/platform-shell";
import { getOracleStatus, getOracleScores, getOracleHistory } from "@/lib/api";
import { OracleScoresTable } from "@/components/oracle/oracle-scores-table";
import { OracleHistoryTable } from "@/components/oracle/oracle-history-table";
import { OracleAgentControls } from "@/components/oracle/oracle-agent-controls";
import { OracleAddToken } from "@/components/oracle/oracle-add-token";
import { OracleWalletProvider } from "@/components/oracle/wallet-provider";
import { VaultPanel } from "@/components/oracle/vault-panel";
import { AgentChat } from "@/components/oracle/agent-chat";

export default async function OraclePage() {
  const [status, scores, history] = await Promise.all([
    getOracleStatus(),
    getOracleScores(),
    getOracleHistory(500),
  ]);

  return (
    <OracleWalletProvider>
      <PlatformShell
        eyebrow="Oracle"
        title="AI Risk Oracle"
        subtitle="Autonomous AI agent scores Solana tokens and enforces decisions on-chain via smart contract."
        stats={[
          { label: "Monitored Tokens", value: String(status.monitored_tokens) },
          { label: "Scores Published", value: String(status.total_published) },
          {
            label: "Agent Status",
            value: status.agent_running ? "Running" : "Stopped",
          },
        ]}
        headerContent={<OracleAgentControls initialRunning={status.agent_running} />}
      >
        <div className="space-y-6">
          {/* Pipeline flow indicator */}
          <div className="flex items-center justify-center gap-2 rounded-2xl border border-[rgba(59,130,246,0.1)] bg-[rgba(15,23,42,0.4)] px-4 py-3 sm:gap-3">
            <span className="flex items-center gap-1.5 text-xs font-medium text-cyan-400 sm:text-sm">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
              </svg>
              AI Scoring
            </span>
            <svg className="h-3 w-3 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
            <span className="flex items-center gap-1.5 text-xs font-medium text-blue-400 sm:text-sm">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" />
              </svg>
              Solana PDA
            </span>
            <svg className="h-3 w-3 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
            <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 sm:text-sm">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
              GuardedVault
            </span>
          </div>

          {/* AI Agent Chat - hero section */}
          <AgentChat />

          {/* Add token */}
          <section id="oracle-add-token">
            <OracleAddToken />
          </section>

          {/* On-chain scores */}
          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa]">
                On-Chain Scores
              </h2>
              <span className="text-[10px] text-slate-500">
                {scores.length} token{scores.length !== 1 ? "s" : ""} monitored
              </span>
            </div>
            <OracleScoresTable scores={scores} history={history} />
          </section>

          {/* Guarded Vault */}
          <div id="guarded-vault">
            <VaultPanel scores={scores} />
          </div>

          {/* Publish history */}
          <details className="group rounded-[24px] border border-[rgba(59,130,246,0.10)] bg-[rgba(15,23,42,0.60)]">
            <summary className="cursor-pointer select-none px-4 py-3 text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa] sm:px-6 sm:py-4">
              Publish History ({history.length})
              <span className="ml-2 text-slate-500 group-open:hidden">&#9656;</span>
              <span className="ml-2 text-slate-500 hidden group-open:inline">&#9662;</span>
            </summary>
            <div className="px-2 pb-4">
              <OracleHistoryTable events={history} />
            </div>
          </details>
        </div>
      </PlatformShell>
    </OracleWalletProvider>
  );
}
