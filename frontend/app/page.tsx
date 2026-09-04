import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#fbfbfa] text-[#1f1f1f]">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <Link href="/" className="text-lg font-semibold tracking-tight">Proximate</Link>
        <div className="flex items-center gap-3 text-sm text-[#787774]">
          <Link href="/sign-in" className="rounded-lg border border-[#d7e8e5] bg-white px-4 py-2 font-medium text-[#0f806f] hover:bg-[#f2fbf9]">登入</Link><Link href="/sign-up" className="rounded-lg bg-[var(--accent)] px-4 py-2 font-medium text-white hover:bg-[#0b8978]">註冊</Link>
        </div>
      </nav>

      <section className="mx-auto max-w-6xl px-6 pb-24 pt-20 sm:pt-28">
        <div className="max-w-3xl">
          <p className="mb-5 text-sm font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">AI teammate for better meetings</p>
          <h1 className="text-5xl font-semibold leading-[1.05] tracking-[-0.04em] sm:text-7xl">讓每一場會議，<br /><span className="text-[#787774]">多一個會思考的組員。</span></h1>
          <p className="mt-7 max-w-2xl text-lg leading-8 text-[#787774]">Proximate 在會議前整理脈絡、會議中主動提出風險與反例，會議後把討論收斂成可追蹤的決策與行動。</p>
          <div className="mt-9 flex flex-wrap gap-3"><Link href="/sign-up" className="rounded-lg bg-[var(--accent)] px-5 py-3 font-medium text-white hover:bg-[#0b8978]">註冊</Link><Link href="/sign-in" className="rounded-lg border border-[#e6e6e3] bg-white px-5 py-3 font-medium hover:bg-[#f7f7f5]">登入</Link></div>
        </div>
        <div className="mt-20 grid gap-3 border-y border-[#e6e6e3] py-5 text-sm text-[#787774] sm:grid-cols-3"><div><span className="text-[#1f1f1f]">01</span><p className="mt-2">會前形成共同脈絡</p></div><div><span className="text-[#1f1f1f]">02</span><p className="mt-2">會中主動發現盲點</p></div><div><span className="text-[#1f1f1f]">03</span><p className="mt-2">會後留下可執行決策</p></div></div>
      </section>

      <section id="how-it-works" className="border-t border-[#e6e6e3] bg-white"><div className="mx-auto max-w-6xl px-6 py-20"><div className="grid gap-12 md:grid-cols-[0.8fr_1.2fr]"><div><p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#0f9f8a]">One meeting workspace</p><h2 className="mt-4 text-3xl font-semibold tracking-tight">從準備到回顧，<br />都在同一個脈絡裡。</h2></div><div className="grid gap-8 sm:grid-cols-3">{[['Prepare','先理解，再開始討論','Brief、議程與 Personal Sidekick 讓每個人帶著想法進場。'],['Live','在對的時機加入','AI 只在發現重要風險且通過團隊門檻時提出發言。'],['Review','把共識變成行動','版本化決策、理由與負責人，不讓結論散落在聊天紀錄。']].map(([title, lead, body]) => <article key={title} className="border-l border-[#e6e6e3] pl-5"><p className="text-sm text-[#787774]">{title}</p><h3 className="mt-3 font-semibold">{lead}</h3><p className="mt-3 text-sm leading-6 text-[#787774]">{body}</p></article>)}</div></div></div></section>
      <footer className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-10 text-sm text-[#787774] sm:flex-row sm:items-center sm:justify-between"><span>Proximate · thoughtful meetings, together</span><Link href="/dashboard" className="text-[#0f9f8a] hover:underline">前往 Dashboard →</Link></footer>
    </main>
  );
}
