export function CoinsFeedSkeleton() {
  return (
    <div className="space-y-3 p-4 md:p-5">
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          key={index}
          className="animate-pulse rounded-[26px] border border-[color:var(--border)] bg-white/6 px-4 py-4"
        >
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1.8fr)_120px_140px_140px_minmax(0,1.1fr)] lg:items-center">
            <div className="flex items-center gap-3">
              <div className="h-11 w-11 rounded-2xl bg-white/10" />
              <div className="min-w-0 flex-1 space-y-2">
                <div className="h-4 w-40 rounded bg-white/10" />
                <div className="h-3 w-24 rounded bg-white/10" />
                <div className="h-3 w-56 rounded bg-white/10" />
              </div>
            </div>
            <div className="h-4 w-16 rounded bg-white/10" />
            <div className="h-4 w-20 rounded bg-white/10" />
            <div className="h-4 w-24 rounded bg-white/10" />
            <div className="flex gap-2">
              <div className="h-8 w-24 rounded-full bg-white/10" />
              <div className="h-8 w-28 rounded-full bg-white/10" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
