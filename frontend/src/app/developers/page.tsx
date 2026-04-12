import { PlatformShell } from "@/components/platform-shell";
import { DeveloperWalletBoard } from "@/components/developer-wallet-board";
import { getDeveloperProfiles } from "@/lib/api";

export default async function DevelopersPage() {
  const profiles = await getDeveloperProfiles();

  const walletCount = profiles.filter((p) => p.kind === "wallet").length;
  const clusterCount = profiles.filter((p) => p.kind === "cluster").length;

  return (
    <PlatformShell
      eyebrow="Developers"
      title="Developer Wallet Intelligence"
      subtitle="Ranked wallets and launch clusters surfaced from recent token reports: shared funders, repeat launches, linked exits, hidden clusters, and operator reputation."
      stats={[
        { label: "Resolved wallets", value: String(walletCount) },
        { label: "Hidden clusters", value: String(clusterCount) },
        { label: "Total operators", value: String(profiles.length) },
        {
          label: "Avg operator score",
          value: profiles.length
            ? String(Math.round(profiles.reduce((s, p) => s + p.operatorScore, 0) / profiles.length))
            : "0",
        },
      ]}
    >
      <DeveloperWalletBoard profiles={profiles} />
    </PlatformShell>
  );
}
