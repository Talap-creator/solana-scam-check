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
    getOracleHistory(20),
  ]);

  return (
    <OracleWalletProvider>
      <PlatformShell
        eyebrow="Oracle"
        title="AI Risk Oracle"
        subtitle="Autonomous AI agent scores tokens and enforces decisions on-chain via smart contract."
        stats={[
          { label: "Monitored", value: String(status.monitored_tokens) },
          { label: "Published", value: String(status.total_published) },
          {
            label: "Agent",
            value: status.agent_running ? "Running" : "Stopped",
          },
        ]}
        headerContent={<OracleAgentControls initialRunning={status.agent_running} />}
      >
        <div className="space-y-6">
          {/* Hero: AI Agent Chat */}
          <AgentChat />

          {/* Add token — compact */}
          <section id="oracle-add-token">
            <OracleAddToken />
          </section>

          {/* Guarded Vault */}
          <div id="guarded-vault">
            <VaultPanel scores={scores} />
          </div>

          {/* On-chain scores */}
          <section>
            <h2 className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa]">
              On-Chain Scores
            </h2>
            <OracleScoresTable scores={scores} />
          </section>

          {/* Publish history — compact */}
          <details className="group rounded-[24px] border border-[rgba(59,130,246,0.10)] bg-[rgba(15,23,42,0.60)]">
            <summary className="cursor-pointer select-none px-6 py-4 text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa]">
              Publish History ({history.length})
              <span className="ml-2 text-slate-500 group-open:hidden">▸</span>
              <span className="ml-2 text-slate-500 hidden group-open:inline">▾</span>
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
