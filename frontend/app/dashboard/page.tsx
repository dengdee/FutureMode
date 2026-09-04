"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "../../components/app-shell";
import { listMeetings } from "../../lib/api/meetings";
import { listTeams } from "../../lib/api/teams";
import type { MeetingSummary } from "../../types/api";
import type { Team } from "../../types/api";

export default function DashboardPage() {
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [meetingsLoaded, setMeetingsLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([listMeetings(), listTeams()])
      .then(([meetingResult, teamResult]) => {
        if (!active) return;
        setMeetings(meetingResult);
        setTeams(teamResult.teams);
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
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--accent)]">Overview</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">工作總覽</h1>
          <p className="mt-2 text-[var(--muted)]">從團隊工作區進入會議、文件與成員管理。</p>
        </div>
        <Link href="/meetings/new" className="inline-flex w-fit items-center justify-center rounded-primary bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#0b8978]">快速建立會議</Link>
      </div>
      <section className="mt-8 grid gap-4 sm:grid-cols-2">
        <Link href="/workspaces" className="rounded-2xl bg-[var(--surface)] p-5 ring-1 ring-black/5 transition hover:-translate-y-0.5 hover:ring-[var(--accent)]">
          <p className="text-sm text-[var(--muted)]">我的團隊</p><p className="mt-2 text-3xl font-semibold">{teams.length}</p><p className="mt-1 text-xs text-[var(--muted)]">進入團隊管理成員與會議</p>
        </Link>
        <div className="rounded-2xl bg-[var(--surface)] p-5 ring-1 ring-black/5"><p className="text-sm text-[var(--muted)]">近期會議</p><p className="mt-2 text-3xl font-semibold">{meetingsLoaded ? meetings.length : "—"}</p><p className="mt-1 text-xs text-[var(--muted)]">跨團隊的最近會議</p></div>
      </section>
      <section className="mt-10">
        <div className="mb-4 flex items-center justify-between"><h2 className="text-xl font-semibold">近期會議</h2><span className="text-sm text-[var(--muted)]">{meetingsLoaded ? `${meetings.length} 場` : "載入中…"}</span></div>
        {meetings.length > 0 ? <div className="grid gap-3">{meetings.map((meeting) => <Link key={meeting.id} href={`/meetings/${meeting.id}/prepare`} className="rounded-2xl border border-black/5 bg-[var(--surface)] p-5 transition hover:-translate-y-0.5 hover:ring-1 hover:ring-[var(--accent)]"><div className="flex flex-wrap items-center justify-between gap-3"><h3 className="font-semibold">{meeting.title}</h3><span className="rounded-full bg-[#e7f7ef] px-3 py-1 text-xs text-[#1d6b4d]">{meeting.status}</span></div><p className="mt-2 text-sm text-[var(--muted)]">{meeting.scheduled_at ? new Date(meeting.scheduled_at).toLocaleString("zh-TW") : "尚未排程"}</p></Link>)}</div> : <div className="rounded-2xl border border-dashed border-black/10 bg-[var(--surface)] p-8 text-center"><p className="font-medium">目前沒有可顯示的會議</p><p className="mt-2 text-sm text-[var(--muted)]">請先到「團隊」選擇工作區，再建立第一場會議。</p></div>}
      </section>
    </AppShell>
  );
}
