"use client";

import { useGSAP } from "@gsap/react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Image from "next/image";
import Link from "next/link";
import { useRef } from "react";

gsap.registerPlugin(useGSAP, ScrollTrigger);

export default function Home() {
  const pageRef = useRef<HTMLElement>(null);
  useGSAP(() => {
    const page = pageRef.current;
    if (!page || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const sections = Array.from(page.children);
    gsap.set(sections, { autoAlpha: 0, y: 18 });
    ScrollTrigger.batch(sections, { start: "top 88%", once: true, onEnter: (elements) => gsap.to(elements, { autoAlpha: 1, y: 0, duration: 0.42, stagger: 0.08, ease: "power2.out", overwrite: "auto" }) });
    ScrollTrigger.refresh();
  }, { scope: pageRef });
  return (
    <main ref={pageRef} className="min-h-screen bg-[#fbfbfa] text-[#1f1f1f]">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <Link href="/" className="inline-flex items-center gap-2 text-lg font-semibold tracking-tight">
          <Image src="/logo.png" alt="" width={32} height={32} className="h-8 w-8 rounded-lg object-contain" priority />
          <span>Proximate</span>
        </Link>
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

      <section className="border-t border-[#e6e6e3] bg-[#f4f8f7]"><div className="mx-auto max-w-6xl px-6 py-20"><div className="max-w-2xl"><p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#0f9f8a]">Why Proximate</p><h2 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">不只記錄發生了什麼，<br />也幫團隊看見還沒被說出口的事。</h2><p className="mt-5 leading-7 text-[#787774]">好的會議不是讓每個人都同意得更快，而是讓重要的風險、不同立場與決策理由被看見，最後留下所有人都能理解的共同脈絡。</p></div><div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4">{[['團隊記憶','把決策、理由與來源留在團隊，而不是散落在不同文件。'],['少數觀點','AI 協助整理還沒成形的疑慮，但不替任何人自動發言。'],['可追溯決策','每個結論都保留版本、限制與未決問題，方便日後回頭檢查。'],['安全邊界','私人 Sidekick 只有本人可見，公開內容一定經過本人授權。']].map(([title, body], index) => <article key={title} className="rounded-2xl border border-[#dfeae7] bg-white p-5"><span className="text-xs font-semibold text-[#0f9f8a]">0{index + 1}</span><h3 className="mt-5 font-semibold">{title}</h3><p className="mt-3 text-sm leading-6 text-[#787774]">{body}</p></article>)}</div></div></section>

      <section className="border-t border-[#e6e6e3] bg-white"><div className="mx-auto grid max-w-6xl gap-10 px-6 py-20 md:grid-cols-[1fr_0.8fr] md:items-center"><div><p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#0f9f8a]">Built for thoughtful teams</p><h2 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">讓會議結束時，<br />每個人都知道下一步。</h2><p className="mt-5 max-w-xl leading-7 text-[#787774]">從小型產品團隊到跨職能決策會議，Proximate 將團隊成員、歷史文件與當下討論放進同一個工作區，讓共識不只停留在會議當下。</p><Link href="/sign-up" className="mt-7 inline-flex rounded-lg bg-[var(--accent)] px-5 py-3 font-medium text-white hover:bg-[#0b8978]">開始建立工作區</Link></div><div className="rounded-3xl bg-[#0f9f8a] p-7 text-white sm:p-9"><p className="text-sm font-semibold uppercase tracking-[0.18em] text-white/70">A better meeting loop</p><div className="mt-8 space-y-5">{[['01','整理脈絡','會前先知道今天要解決什麼'],['02','提出觀點','會中保留不同意見與風險'],['03','確認共識','會後留下決策與負責人']].map(([number, title, body]) => <div key={number} className="flex gap-4 border-b border-white/20 pb-5 last:border-0 last:pb-0"><span className="text-sm text-white/60">{number}</span><div><h3 className="font-semibold">{title}</h3><p className="mt-1 text-sm leading-6 text-white/70">{body}</p></div></div>)}</div></div></div></section>
      <footer className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-10 text-sm text-[#787774] sm:flex-row sm:items-center sm:justify-between"><span>Proximate · thoughtful meetings, together</span><Link href="/dashboard" className="text-[#0f9f8a] hover:underline">前往 Dashboard →</Link></footer>
    </main>
  );
}
