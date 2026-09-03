const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl items-center px-6 py-16">
      <section className="w-full rounded-3xl bg-[var(--surface)] p-8 shadow-sm ring-1 ring-black/5 sm:p-12">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-[var(--accent)]">
          Proximate
        </p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          初始專案已準備完成
        </h1>
        <p className="mt-5 max-w-2xl text-lg leading-8 text-[var(--muted)]">
          前端已可執行。這個頁面只用於驗證基礎架構，不包含登入、AI、會議或資料功能。
        </p>
        <dl className="mt-8 grid gap-4 rounded-2xl bg-[var(--background)] p-5 text-sm sm:grid-cols-2">
          <div>
            <dt className="font-medium">前端狀態</dt>
            <dd className="mt-1 text-[var(--accent)]">Ready</dd>
          </div>
          <div>
            <dt className="font-medium">API Base URL</dt>
            <dd className="mt-1 break-all text-[var(--muted)]">{apiBaseUrl}</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}

