"use client";

import { useRouter } from "next/navigation";

type RecheckButtonProps = {
  entityId: string;
  entityType: "token" | "wallet" | "project";
};

export function RecheckButton({ entityId, entityType }: RecheckButtonProps) {
  const router = useRouter();

  const onClick = () => {
    const params = new URLSearchParams({
      value: entityId,
      entityType,
    });
    router.push(`/analysis?${params.toString()}`);
  };

  return (
    <button
      className="rounded-full bg-[linear-gradient(135deg,#11b8ff,#7effc1)] px-5 py-3 text-sm font-bold text-slate-950"
      onClick={onClick}
      type="button"
    >
      Recheck
    </button>
  );
}
