"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { AppShell } from "../../components/app-shell";
import { PageHeader } from "../../components/page-header";
import { listMeetings } from "../../lib/api/meetings";
import { listTeams } from "../../lib/api/teams";
import type { MeetingSummary } from "../../types/api";

const defaultMembers = ["Proximate", "負責人",];

export default function WorkspacesPage() {
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [workspaceName, setWorkspaceName] = useState<string | null>(null);
  const [members, setMembers] = useState(defaultMembers);
  const [draftName, setDraftName] = useState("");
  const [draftMembers, setDraftMembers] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    listMeetings().then(setMeetings).catch(() => setMeetings([]));
    listTeams().then((result) => { const value = result as Record<string, unknown>; const name = value.name ?? value.title; if (typeof name === "string") setWorkspaceName(name); }).catch(() => undefined);
  }, []);

  const createWorkspace = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); if (!draftName.trim()) return; setWorkspaceName(draftName.trim()); setMembers(draftMembers.split(",").map((member) => member.trim()).filter(Boolean)); setDraftName(""); setDraftMembers(""); setShowCreate(false); };

  return <AppShell><PageHeader eyebrow="Workspaces" title="團隊工作區" description="先建立團隊，再在工作區內管理成員與多場會議。" actions={<button type="button" onClick={() => setShowCreate((visible) => !visible)} className="rounded-xl bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white">{workspaceName ? "編輯工作區" : "建立團隊工作區"}</button>} />
    {showCreate && <form onSubmit={createWorkspace} className="mt-6 max-w-2xl rounded-primary border border-[#e6e6e3] bg-white p-5"><h2 className="font-semibold">{workspaceName ? "編輯團隊工作區" : "建立團隊工作區"}</h2><label className="mt-4 block text-sm font-medium">工作區名稱<input autoFocus required value={draftName} onChange={(event) => setDraftName(event.target.value)} placeholder={workspaceName ?? "例如：FutureMode Hackathon"} className="control-primary mt-2" /></label><label className="mt-4 block text-sm font-medium">邀請成員<span className="mt-1 block text-xs font-normal text-[#787774]">以逗號分隔姓名或 Email；之後可隨時調整。</span><input value={draftMembers} onChange={(event) => setDraftMembers(event.target.value)} placeholder="例如：Alex, Jamie, design@example.com" className="control-primary mt-2" /></label><div className="mt-5 flex justify-end gap-3"><button type="button" onClick={() => setShowCreate(false)} className="rounded-primary border border-[#dededb] px-4 py-2 text-sm font-medium">取消</button><button type="submit" className="rounded-primary bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-white">儲存工作區</button></div></form>}
    {workspaceName ? <><section className="mt-8 rounded-2xl border border-[#e6e6e3] bg-white p-6"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--accent)]">Current workspace</p><h2 className="mt-2 text-2xl font-semibold">{workspaceName}</h2><p className="mt-2 text-sm text-[#787774]">{members.length} 位成員 · 共同管理會議、文件與 AI 政策</p></div><Link href="/meetings/new" className="rounded-primary border border-[#dededb] px-4 py-2 text-sm font-medium hover:bg-[#f7f7f5]">在此工作區建立會議</Link></div><div className="mt-5 flex flex-wrap gap-2">{members.map((member) => <span key={member} className="rounded-full bg-[#eef8f6] px-3 py-1.5 text-xs text-[#24776a]">{member}</span>)}</div></section><section className="mt-8"><div className="mb-4 flex items-center justify-between"><h2 className="text-xl font-semibold">工作區內的會議</h2><span className="text-sm text-[#787774]">{meetings.length} 場</span></div>{meetings.length > 0 ? <div className="grid gap-3">{meetings.map((meeting) => <Link key={meeting.id} href={`/meetings/${meeting.id}/prepare`} className="rounded-2xl border border-[#e6e6e3] bg-white p-5 transition hover:-translate-y-0.5 hover:ring-1 hover:ring-[var(--accent)]"><div className="flex items-center justify-between gap-3"><h3 className="font-semibold">{meeting.title}</h3><span className="text-xs text-[#787774]">{meeting.status}</span></div><p className="mt-2 text-sm text-[#787774]">{meeting.scheduled_at ? new Date(meeting.scheduled_at).toLocaleString("zh-TW") : "尚未排程"}</p></Link>)}</div> : <div className="rounded-2xl border border-dashed border-[#d8d8d5] bg-white p-10 text-center text-sm text-[#787774]">尚未建立會議，先建立第一場團隊討論吧。</div>}</section></> : <section className="mt-8 rounded-2xl border border-dashed border-[#d8d8d5] bg-white p-12 text-center"><h2 className="text-xl font-semibold">還沒有團隊工作區</h2><p className="mt-2 text-sm text-[#787774]">建立工作區後，再邀請團隊成員並開始建立會議。</p><button type="button" onClick={() => setShowCreate(true)} className="mt-5 rounded-primary bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white">建立第一個工作區</button></section>}
  </AppShell>;
}
