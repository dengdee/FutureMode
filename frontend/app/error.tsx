"use client";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <main className="grid min-h-screen place-items-center bg-[#fbfbfa] p-6 text-center"><div><p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#b35c3a]">Something went wrong</p><h1 className="mt-3 text-3xl font-semibold">暫時無法載入此頁面</h1><p className="mt-3 text-sm text-[#787774]">請稍後再試，或返回工作區。</p><div className="mt-6 flex justify-center gap-3"><button type="button" onClick={reset} className="rounded-lg bg-[#0f9f8a] px-4 py-2.5 text-sm font-semibold text-white">重新嘗試</button><a href="/dashboard" className="rounded-lg border border-[#dededb] px-4 py-2.5 text-sm font-medium">返回 Dashboard</a></div></div></main>;
}
