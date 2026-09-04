"use client";

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <div className="mx-auto max-w-xl rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-8 text-center"><p className="text-sm font-semibold text-[var(--danger)]">發生錯誤</p><h1 className="mt-2 text-2xl font-semibold">頁面暫時無法載入</h1><p className="mt-3 text-[var(--muted)]">請重試；這個畫面目前仍是前端路由骨架。</p><button type="button" onClick={() => reset()} className="mt-6 rounded-lg bg-[var(--accent)] px-4 py-2.5 font-semibold text-white hover:bg-[var(--accent-strong)]">重新載入</button></div>;
}
