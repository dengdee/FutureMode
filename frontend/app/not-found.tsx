import Link from "next/link";

export default function NotFound() {
  return <div className="mx-auto max-w-xl rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-8 text-center"><p className="text-sm font-semibold text-[var(--accent)]">404</p><h1 className="mt-2 text-2xl font-semibold">找不到這個頁面</h1><p className="mt-3 text-[var(--muted)]">請確認網址，或回到 Dashboard 繼續。</p><Link href="/dashboard" className="mt-6 inline-block rounded-lg bg-[var(--accent)] px-4 py-2.5 font-semibold text-white no-underline hover:bg-[var(--accent-strong)]">回到 Dashboard</Link></div>;
}
