"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "../../components/app-shell";
import { listMeetings } from "../../lib/api/meetings";
import type { MeetingSummary } from "../../types/api";

export default function DashboardPage() {
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [meetingsLoaded, setMeetingsLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    listMeetings()
      .then((result) => {
        if (!active) return;
        setMeetings(result);
        setMeetingsLoaded(true);
      })
      .catch(() => {
        if (active) setMeetingsLoaded(true);
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <AppShell>
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--accent)]">Workspace</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">你的會議</h1>
          <p className="mt-2 text-[var(--muted)]">集中查看會前準備、即時討論與會後決策。</p>
        </div>
        <Link href="/meetings/new" className="rounded-xl bg-[var(--accent)] px-4 py-2.5 text-center text-sm font-semibold text-white">建立會議</Link>
      </div>
      <section className="mt-8 grid gap-4 sm:grid-cols-3">
        {[['進行中會議', '—'], ['待確認共識', '—'], ['我的行動項目', '—']].map(([label, value]) => (
          <div key={label} className="rounded-2xl bg-[var(--surface)] p-5 ring-1 ring-black/5"><p className="text-sm text-[var(--muted)]">{label}</p><p className="mt-2 text-3xl font-semibold">{value}</p><p className="mt-1 text-xs text-[var(--muted)]">等待正式資料 API</p></div>
        ))}
      </section>
      <section className="mt-10">
        <div className="mb-4 flex items-center justify-between"><h2 className="text-xl font-semibold">近期會議</h2><span className="text-sm text-[var(--muted)]">{meetingsLoaded ? `${meetings.length} 場` : "載入中…"}</span></div>
        {meetings.length > 0 ? <div className="grid gap-3">{meetings.map((meeting) => <Link key={meeting.id} href={`/meetings/${meeting.id}/prepare`} className="rounded-2xl border border-black/5 bg-[var(--surface)] p-5 transition hover:-translate-y-0.5 hover:ring-1 hover:ring-[var(--accent)]"><div className="flex flex-wrap items-center justify-between gap-3"><h3 className="font-semibold">{meeting.title}</h3><span className="rounded-full bg-[#e7f7ef] px-3 py-1 text-xs text-[#1d6b4d]">{meeting.status}</span></div><p className="mt-2 text-sm text-[var(--muted)]">{meeting.scheduled_at ? new Date(meeting.scheduled_at).toLocaleString("zh-TW") : "尚未排程"}</p></Link>)}</div> : <div className="rounded-2xl border border-dashed border-black/10 bg-[var(--surface)] p-8 text-center"><p className="font-medium">目前沒有可顯示的會議</p><p className="mt-2 text-sm text-[var(--muted)]">建立第一場會議後，這裡會顯示正式資料。</p><Link href="/meetings/new" className="mt-5 inline-block rounded-xl bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white">建立會議</Link></div>}
      </section>
    </AppShell>
  );
}
