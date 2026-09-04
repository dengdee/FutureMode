"use client";

import { IconBriefcase, IconPlus, IconTrash, IconX } from "@tabler/icons-react";
import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { AppShell } from "../../components/app-shell";
import { PageHeader } from "../../components/page-header";
import { listMeetings } from "../../lib/api/meetings";
import { listTeamMembers, listTeams } from "../../lib/api/teams";
import type { MeetingSummary, Team, TeamMember } from "../../types/api";

type InviteRow = { id: number; email: string; role: "member" | "owner" };

export default function WorkspacesPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [selectedTeamId, setSelectedTeamId] = useState("");
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [workspaceName, setWorkspaceName] = useState("");
  const [inviteRows, setInviteRows] = useState<InviteRow[]>([{ id: 1, email: "", role: "member" }]);

  useEffect(() => {
    let active = true;
    Promise.all([listTeams(), listMeetings()])
      .then(([teamResult, meetingResult]) => {
        if (!active) return;
        setTeams(teamResult.teams);
        setMeetings(meetingResult);
        setSelectedTeamId(teamResult.teams[0]?.id ?? "");
      })
      .catch((cause) => active && setError(cause instanceof Error ? cause.message : "無法讀取工作區資料。"))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!selectedTeamId) return;
    listTeamMembers(selectedTeamId).then((result) => setMembers(result.members)).catch(() => setMembers([]));
  }, [selectedTeamId]);

  const currentTeam = teams.find((team) => team.id === selectedTeamId);
  const teamMeetings = meetings.filter((meeting) => meeting.team_id === selectedTeamId);

  function addInviteRow() {
    setInviteRows((rows) => [...rows, { id: Date.now(), email: "", role: "member" }]);
  }

  function updateInviteRow(id: number, patch: Partial<InviteRow>) {
    setInviteRows((rows) => rows.map((row) => row.id === id ? { ...row, ...patch } : row));
  }

  function submitWorkspace(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const invalid = inviteRows.some((row) => row.email.trim() && !/^\S+@\S+\.\S+$/.test(row.email.trim()));
    if (invalid) { setNotice("請確認每個 Email 格式正確。"); return; }
    setNotice("工作區與邀請表格已準備完成；後端目前尚未提供建立工作區／寄送邀請 API，因此尚未送出資料。");
  }

  return <AppShell>
    <PageHeader eyebrow="Workspaces" title="團隊工作區" description="選擇你所屬的團隊工作區，管理成員並在其中建立會議。" actions={<button type="button" onClick={() => { setCreateOpen(true); setNotice(null); }} className="inline-flex cursor-pointer items-center gap-2 rounded-primary bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white"><IconPlus size={17} />建立團隊工作區</button>} />
    {error && <p role="alert" className="mt-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
    {notice && <p role="status" className="mt-6 rounded-lg bg-[#e9f7f4] px-4 py-3 text-sm text-[#087e6d]">{notice}</p>}
    {loading ? <div className="mt-8 rounded-2xl border border-[#e6e6e3] bg-white p-8 text-sm text-[#787774]">正在讀取工作區…</div> : teams.length === 0 ? <section className="mt-8 rounded-2xl border border-dashed border-[#d8d8d5] bg-white p-12 text-center"><IconBriefcase className="mx-auto text-[#0f9f8a]" size={30} /><h2 className="mt-3 text-xl font-semibold">尚未加入團隊工作區</h2><p className="mt-2 text-sm text-[#787774]">可以先建立工作區並準備邀請名單；實際建立與寄送邀請需等待後端 API。</p></section> : <div className="mt-8 grid gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
      <aside className="h-fit rounded-2xl border border-[#e6e6e3] bg-white p-3"><p className="px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#0f9f8a]">Your teams</p>{teams.map((team) => <button key={team.id} type="button" onClick={() => setSelectedTeamId(team.id)} className={`mt-1 w-full cursor-pointer rounded-xl px-3 py-3 text-left text-sm ${team.id === selectedTeamId ? "bg-[#e9f7f4] font-semibold text-[#087e6d]" : "text-[#5f5f5b] hover:bg-[#f7f7f5]"}`}><span className="block">{team.name}</span><span className="mt-1 block text-xs font-normal text-[#8b8b87]">{team.role}</span></button>)}</aside>
      <div className="min-w-0"><section className="rounded-2xl border border-[#e6e6e3] bg-white p-6"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#0f9f8a]">Current workspace</p><h2 className="mt-2 text-2xl font-semibold">{currentTeam?.name}</h2><p className="mt-2 text-sm text-[#787774]">{members.length} 位成員 · 你的角色：{currentTeam?.role}</p></div><Link href={`/meetings/new?teamId=${selectedTeamId}`} className="rounded-primary bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white">在此建立會議</Link></div><div className="mt-5 flex flex-wrap gap-2">{members.map((member) => <span key={member.external_id} className="rounded-full bg-[#eef8f6] px-3 py-1.5 text-xs text-[#24776a]">{member.display_name || member.external_id} · {member.role}</span>)}</div></section>
      <section className="mt-8"><div className="mb-4 flex items-center justify-between"><h2 className="text-xl font-semibold">工作區內的會議</h2><span className="text-sm text-[#787774]">{teamMeetings.length} 場</span></div>{teamMeetings.length ? <div className="grid gap-3">{teamMeetings.map((meeting) => <Link key={meeting.id} href={`/meetings/${meeting.id}/prepare`} className="rounded-2xl border border-[#e6e6e3] bg-white p-5 transition hover:-translate-y-0.5 hover:ring-1 hover:ring-[var(--accent)]"><div className="flex items-center justify-between gap-3"><h3 className="font-semibold">{meeting.title}</h3><span className="text-xs text-[#787774]">{meeting.status}</span></div><p className="mt-2 text-sm text-[#787774]">{meeting.scheduled_at ? new Date(meeting.scheduled_at).toLocaleString("zh-TW") : "尚未排程"}</p></Link>)}</div> : <div className="rounded-2xl border border-dashed border-[#d8d8d5] bg-white p-10 text-center text-sm text-[#787774]">此工作區尚未建立會議。</div>}</section></div>
    </div>}
    {createOpen && <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/35 px-4 py-8" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setCreateOpen(false)}><section role="dialog" aria-modal="true" aria-labelledby="create-workspace-title" className="w-full max-w-2xl rounded-2xl border border-[#dededb] bg-white shadow-xl"><header className="flex items-center justify-between border-b border-[#e6e6e3] px-6 py-5"><div><h2 id="create-workspace-title" className="text-xl font-semibold">建立團隊工作區</h2><p className="mt-1 text-sm text-[#787774]">建立後即可在工作區內管理多場會議。</p></div><button type="button" onClick={() => setCreateOpen(false)} className="cursor-pointer rounded-lg p-2 text-[#787774] hover:bg-[#f4f4f2]" aria-label="關閉"><IconX size={22} /></button></header><form onSubmit={submitWorkspace} className="p-6"><label className="block text-sm font-medium">工作區名稱<input required value={workspaceName} onChange={(event) => setWorkspaceName(event.target.value)} className="control-primary mt-2" placeholder="例如：FutureMode Hackathon" /></label><div className="mt-6"><div className="flex items-end justify-between gap-3"><div><h3 className="text-sm font-semibold">邀請成員</h3><p className="mt-1 text-xs text-[#787774]">每列填入 Email 並選擇團隊角色。</p></div><button type="button" onClick={addInviteRow} className="inline-flex cursor-pointer items-center gap-1 text-sm font-medium text-[#0f9f8a]"><IconPlus size={16} />新增一列</button></div><div className="mt-3 overflow-hidden rounded-xl border border-[#e6e6e3]"><div className="grid grid-cols-[minmax(0,1fr)_150px_42px] gap-2 bg-[#f7f7f5] px-3 py-2 text-xs font-semibold text-[#787774]"><span>Email address</span><span>Role</span><span /></div>{inviteRows.map((row) => <div key={row.id} className="grid grid-cols-[minmax(0,1fr)_150px_42px] items-center gap-2 border-t border-[#ededeb] px-3 py-2"><input type="email" value={row.email} onChange={(event) => updateInviteRow(row.id, { email: event.target.value })} className="control-primary" placeholder="name@example.com" aria-label="成員 Email" /><select value={row.role} onChange={(event) => updateInviteRow(row.id, { role: event.target.value as InviteRow["role"] })} className="control-primary cursor-pointer" aria-label="成員角色"><option value="member">Member</option><option value="owner">Owner</option></select><button type="button" disabled={inviteRows.length === 1} onClick={() => setInviteRows((rows) => rows.filter((item) => item.id !== row.id))} className="cursor-pointer rounded-lg p-2 text-[#787774] hover:bg-red-50 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-30" aria-label="移除成員列"><IconTrash size={17} /></button></div>)}</div></div><div className="mt-7 flex justify-end gap-3 border-t border-[#ededeb] pt-5"><button type="button" onClick={() => setCreateOpen(false)} className="cursor-pointer rounded-primary border border-[#dededb] px-4 py-2.5 text-sm font-medium">取消</button><button type="submit" className="cursor-pointer rounded-primary bg-[#1f1f1f] px-4 py-2.5 text-sm font-semibold text-white">建立工作區</button></div></form></section></div>}
  </AppShell>;
}
