import { PlatformShell } from "@/components/platform-shell";
import { getOracleStatus, getOracleScores, getOracleHistory } from "@/lib/api";
import { OracleScoresTable } from "@/components/oracle/oracle-scores-table";
import { OracleHistoryTable } from "@/components/oracle/oracle-history-table";
import { OracleAgentControls } from "@/components/oracle/oracle-agent-controls";
import { OracleAddToken } from "@/components/oracle/oracle-add-token";
import { OracleFlowDiagram } from "@/components/oracle/oracle-flow-diagram";
import { OracleWalletProvider } from "@/components/oracle/wallet-provider";
import { VaultPanel } from "@/components/oracle/vault-panel";

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
        subtitle="Autonomous AI scoring published on-chain. Smart contracts read these scores to protect user funds."
        stats={[
          { label: "Monitored tokens", value: String(status.monitored_tokens) },
          { label: "Scores published", value: String(status.total_published) },
          {
            label: "Agent status",
            value: status.agent_running ? "Running" : "Stopped",
          },
          { label: "Errors", value: String(status.errors) },
        ]}
        headerContent={<OracleAgentControls initialRunning={status.agent_running} />}
      >
        <div className="space-y-8">
          {/* Flow diagram — shows AI → On-chain pipeline */}
          <OracleFlowDiagram />

          {/* Controls: add token + how it works */}
          <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
            <OracleAddToken />

            <article className="rounded-[24px] border border-[rgba(59,130,246,0.16)] bg-[rgba(15,23,42,0.82)] p-6">
              <h2 className="mb-1 text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa]">
                How It Works
              </h2>
              <ul className="mt-3 space-y-2 text-sm text-slate-300">
                <li className="flex gap-2">
                  <span className="text-[#3b82f6]">1.</span>
                  Add a token address to monitor
                </li>
                <li className="flex gap-2">
                  <span className="text-[#3b82f6]">2.</span>
                  AI agent scores it using RugSignal ML pipeline (50+ features)
                </li>
                <li className="flex gap-2">
                  <span className="text-[#3b82f6]">3.</span>
                  Score is published on-chain to Solana program (PDA)
                </li>
                <li className="flex gap-2">
                  <span className="text-[#3b82f6]">4.</span>
                  GuardedVault reads score and blocks risky swaps automatically
                </li>
              </ul>
            </article>
          </section>

          {/* Guarded Vault — wallet connect + create vault + deposit + emergency exit */}
          <VaultPanel scores={scores} />

          {/* On-chain scores table */}
          <section>
            <h2 className="mb-4 text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa]">
              On-Chain Scores
            </h2>
            <OracleScoresTable scores={scores} />
          </section>

          {/* Publish history */}
          <section>
            <h2 className="mb-4 text-xs font-bold uppercase tracking-[0.2em] text-[#60a5fa]">
              Publish History
            </h2>
            <OracleHistoryTable events={history} />
          </section>
        </div>
      </PlatformShell>
    </OracleWalletProvider>
  );
}
