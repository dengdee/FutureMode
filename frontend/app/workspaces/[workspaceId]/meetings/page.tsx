"use client";

import { IconCalendarPlus, IconClock } from "@tabler/icons-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "../../../../components/app-shell";
import { PageHeader } from "../../../../components/page-header";
import { TeamSubnav } from "../../../../components/team-subnav";
import { listMeetings } from "../../../../lib/api/meetings";
import { listTeams } from "../../../../lib/api/teams";
import type { MeetingSummary, Team } from "../../../../types/api";

const labels: Record<string, string> = { draft: "草稿", scheduled: "已排程", in_progress: "進行中", completed: "已結束", cancelled: "已取消" };

export default function WorkspaceMeetingsPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const [team, setTeam] = useState<Team | null>(null);
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { Promise.all([listTeams(), listMeetings()]).then(([teams, allMeetings]) => { setTeam(teams.teams.find((item) => item.id === workspaceId) ?? null); setMeetings(allMeetings.filter((item) => item.team_id === workspaceId)); }).catch((cause) => setError(cause instanceof Error ? cause.message : "無法讀取團隊會議。")); }, [workspaceId]);
  return <AppShell><PageHeader eyebrow="Team meetings" title={team ? `${team.name} 的會議` : "團隊會議"} description="從排程開始，進入每一場會議的會前準備、會中協作與會後回顧。" actions={<Link href={`/meetings/new?teamId=${workspaceId}`} className="inline-flex items-center gap-2 rounded-primary bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white"><IconCalendarPlus size={17} />建立會議</Link>} />
    <div className="mt-8"><TeamSubnav teamId={workspaceId} active="meetings" /></div>{error ? <p role="alert" className="mt-6 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : <section className="mt-6 space-y-3">{meetings.map((meeting) => <Link key={meeting.id} href={`/meetings/${meeting.id}/prepare`} className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#e6e6e3] bg-white p-5 transition hover:border-[#9ddbc8] hover:shadow-sm"><div className="min-w-0"><h2 className="truncate font-semibold">{meeting.title}</h2><p className="mt-2 flex items-center gap-2 text-sm text-[#787774]"><IconClock size={16} />{meeting.scheduled_at ? new Date(meeting.scheduled_at).toLocaleString("zh-TW") : "尚未設定時間"}</p></div><span className="rounded-full bg-[#e7f7ef] px-3 py-1 text-xs font-medium text-[#087e6d]">{labels[meeting.status] ?? meeting.status}</span></Link>)}{meetings.length === 0 && <div className="rounded-2xl border border-dashed border-[#d8d8d5] bg-white p-12 text-center"><h2 className="font-semibold">尚未建立會議</h2><p className="mt-2 text-sm text-[#787774]">建立第一場會議，再交由 Brief 協助整理會前討論焦點。</p></div>}</section>}
  </AppShell>;
}
