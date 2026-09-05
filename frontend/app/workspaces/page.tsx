"use client";

import { IconBriefcase, IconPlus, IconTrash, IconX } from "@tabler/icons-react";
import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { AppShell } from "../../components/app-shell";
import { PageHeader } from "../../components/page-header";
import { listMeetings } from "../../lib/api/meetings";
import { createInvitation, createTeam, listTeamMembers, listTeams, removeTeamMember, updateTeamMember } from "../../lib/api/teams";
import type { MeetingSummary, Team, TeamMember } from "../../types/api";

type InviteRow = { id: number; email: string; role: "member" | "admin" };

export default function WorkspacesPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [selectedTeamId, setSelectedTeamId] = useState("");
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const submitLock = useRef(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createdTeam, setCreatedTeam] = useState<Team | null>(null);
  const [workspaceName, setWorkspaceName] = useState("");
  const [inviteRows, setInviteRows] = useState<InviteRow[]>([{ id: 1, email: "", role: "member" }]);

  useEffect(() => {
    let active = true;
    Promise.all([listTeams(), listMeetings()])
      .then(([teamResult, meetingResult]) => {
        if (!active) return;
        setError(null);
        setTeams(teamResult.teams);
        setMeetings(meetingResult);
        setSelectedTeamId(teamResult.teams[0]?.id ?? "");
      })
      .catch((cause) => active && setError(cause instanceof Error ? cause.message : "無法讀取工作區資料。"))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [loadAttempt]);

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

  async function submitWorkspace(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitLock.current) return;
    const invalid = inviteRows.some((row) => row.email.trim() && !/^\S+@\S+\.\S+$/.test(row.email.trim()));
    if (invalid) { setCreateError("請確認每個 Email 格式正確。"); return; }
    if (!workspaceName.trim()) { setCreateError("請填寫工作區名稱。"); return; }
    submitLock.current = true;
    setSubmitting(true);
    setCreateError(null);
    try {
      const team = createdTeam ?? await createTeam({ name: workspaceName.trim() });
      if (!createdTeam) {
        setCreatedTeam(team);
        setTeams((current) => [...current.filter((item) => item.id !== team.id), team]);
        setSelectedTeamId(team.id);
        setError(null);
      }
      const invitations = inviteRows.filter((row) => row.email.trim());
      const results = await Promise.allSettled(invitations.map((row) => createInvitation(team.id, { email: row.email.trim(), role: row.role })));
      const failed = invitations.filter((_, index) => results[index].status === "rejected");
      if (failed.length) {
        setInviteRows(failed);
        const failure = results.find((result) => result.status === "rejected");
        const reason = failure?.status === "rejected" && failure.reason instanceof Error ? failure.reason.message : "請稍後重試。";
        setCreateError(`團隊已建立，但 ${failed.length} 筆邀請未完成。${reason} 重試只會處理剩餘邀請，不會重建團隊。`);
        return;
      }
      setCreateOpen(false);
      setCreatedTeam(null);
      setWorkspaceName("");
      setInviteRows([{ id: 1, email: "", role: "member" }]);
      setNotice(invitations.length ? "團隊已建立，邀請紀錄已儲存。" : "團隊已建立。");
    } catch (cause) {
      setCreateError(cause instanceof Error ? cause.message : "建立工作區失敗，請稍後再試。");
    } finally {
      submitLock.current = false;
      setSubmitting(false);
    }
  }

  function closeCreate() {
    if (submitLock.current) return;
    if (createdTeam) setNotice("團隊已建立，尚有未完成的邀請。");
    setCreateOpen(false);
    setCreatedTeam(null);
    setCreateError(null);
    setWorkspaceName("");
    setInviteRows([{ id: 1, email: "", role: "member" }]);
  }

  async function changeMemberRole(member: TeamMember, role: string) {
    if (!selectedTeamId) return;
    try { await updateTeamMember(selectedTeamId, member.user_id, { role }); setMembers((items) => items.map((item) => item.user_id === member.user_id ? { ...item, role } : item)); setNotice("成員角色已更新。"); }
    catch (cause) { setNotice(cause instanceof Error ? cause.message : "更新成員角色失敗。"); }
  }
  async function removeMember(member: TeamMember) {
    if (!selectedTeamId || !window.confirm(`確定移除 ${member.display_name || member.external_id}？`)) return;
    try { await removeTeamMember(selectedTeamId, member.user_id); setMembers((items) => items.filter((item) => item.user_id !== member.user_id)); setNotice("成員已移除。"); }
    catch (cause) { setNotice(cause instanceof Error ? cause.message : "移除成員失敗。"); }
  }

  return <AppShell>
    <PageHeader eyebrow="Teams" title="團隊" description="選擇你所屬的團隊，管理成員並在其中建立會議。" actions={<button type="button" onClick={() => { setCreateOpen(true); setNotice(null); }} className="inline-flex cursor-pointer items-center gap-2 rounded-primary bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white"><IconPlus size={17} />建立團隊</button>} />
    {error && <p role="alert" className="mt-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}<button type="button" className="ml-3 underline" onClick={() => { setLoading(true); setError(null); setLoadAttempt((value) => value + 1); }}>重新載入</button></p>}
    {notice && <p role="status" className="mt-6 rounded-lg bg-[#e9f7f4] px-4 py-3 text-sm text-[#087e6d]">{notice}</p>}
    {loading ? <div className="mt-8 rounded-2xl border border-[#e6e6e3] bg-white p-8 text-sm text-[#787774]">正在讀取團隊…</div> : error ? null : teams.length === 0 ? <section className="mt-8 rounded-2xl border border-dashed border-[#d8d8d5] bg-white p-12 text-center"><IconBriefcase className="mx-auto text-[#0f9f8a]" size={30} /><h2 className="mt-3 text-xl font-semibold">尚未加入團隊</h2><p className="mt-2 text-sm text-[#787774]">可以先建立團隊並準備邀請名單。</p></section> : <div className="mt-8 grid gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
      <aside className="h-fit rounded-2xl border border-[#e6e6e3] bg-white p-3"><p className="px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#0f9f8a]">Your teams</p>{teams.map((team) => <button key={team.id} type="button" onClick={() => setSelectedTeamId(team.id)} className={`mt-1 w-full cursor-pointer rounded-xl px-3 py-3 text-left text-sm ${team.id === selectedTeamId ? "bg-[#e9f7f4] font-semibold text-[#087e6d]" : "text-[#5f5f5b] hover:bg-[#f7f7f5]"}`}><span className="block">{team.name}</span><span className="mt-1 block text-xs font-normal text-[#8b8b87]">{team.role}</span></button>)}</aside>
      <div className="min-w-0"><section className="rounded-2xl border border-[#e6e6e3] bg-white p-6"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#0f9f8a]">Current team</p><h2 className="mt-2 text-2xl font-semibold">{currentTeam?.name}</h2><p className="mt-2 text-sm text-[#787774]">{members.length} 位成員 · 你的角色：{currentTeam?.role}</p></div><Link href={`/meetings/new?teamId=${selectedTeamId}`} className="rounded-primary bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white">在此建立會議</Link></div><div className="mt-5 space-y-2">{members.map((member) => <div key={member.user_id} className="flex flex-wrap items-center gap-2 rounded-xl bg-[#eef8f6] px-3 py-2 text-xs text-[#24776a]"><span className="min-w-0 flex-1 truncate">{member.display_name || member.external_id}</span><select value={member.role} onChange={(event) => void changeMemberRole(member, event.target.value)} className="rounded border border-[#cde5df] bg-white px-2 py-1" aria-label="成員角色"><option value="member">Member</option><option value="admin">Admin</option></select><button type="button" onClick={() => void removeMember(member)} className="text-red-600">移除</button></div>)}</div></section>
      <section className="mt-8"><div className="mb-4 flex items-center justify-between"><h2 className="text-xl font-semibold">工作區內的會議</h2><span className="text-sm text-[#787774]">{teamMeetings.length} 場</span></div>{teamMeetings.length ? <div className="grid gap-3">{teamMeetings.map((meeting) => <Link key={meeting.id} href={`/meetings/${meeting.id}/prepare`} className="rounded-2xl border border-[#e6e6e3] bg-white p-5 transition hover:-translate-y-0.5 hover:ring-1 hover:ring-[var(--accent)]"><div className="flex items-center justify-between gap-3"><h3 className="font-semibold">{meeting.title}</h3><span className="text-xs text-[#787774]">{meeting.status}</span></div><p className="mt-2 text-sm text-[#787774]">{meeting.scheduled_at ? new Date(meeting.scheduled_at).toLocaleString("zh-TW") : "尚未排程"}</p></Link>)}</div> : <div className="rounded-2xl border border-dashed border-[#d8d8d5] bg-white p-10 text-center text-sm text-[#787774]">此工作區尚未建立會議。</div>}</section></div>
    </div>}
    {selectedTeamId && <div className="mt-4"><Link href={`/memory?teamId=${selectedTeamId}&scope=shared`} className="rounded-primary border border-[#d7e8e5] bg-white px-4 py-2.5 text-sm font-semibold text-[#087e6d]">查看團隊共用文件</Link></div>}
    {createOpen && <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/35 px-4 py-8" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && closeCreate()}><section role="dialog" aria-modal="true" aria-labelledby="create-workspace-title" className="w-full max-w-2xl rounded-2xl border border-[#dededb] bg-white shadow-xl"><header className="flex items-center justify-between border-b border-[#e6e6e3] px-6 py-5"><div><h2 id="create-workspace-title" className="text-xl font-semibold">建立團隊工作區</h2><p className="mt-1 text-sm text-[#787774]">建立後即可在工作區內管理多場會議。</p></div><button type="button" disabled={submitting} onClick={closeCreate} className="cursor-pointer rounded-lg p-2 text-[#787774] hover:bg-[#f4f4f2]" aria-label="關閉"><IconX size={22} /></button></header><form onSubmit={submitWorkspace} className="p-6" aria-busy={submitting}>{createError && <p role="alert" className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{createError}</p>}{submitting && <p role="status" className="mb-4 text-sm text-[#787774]">{createdTeam ? "正在儲存邀請…" : "正在建立工作區…"}</p>}<fieldset disabled={submitting} className="min-w-0"><label className="block text-sm font-medium">工作區名稱<input required disabled={!!createdTeam} value={workspaceName} onChange={(event) => setWorkspaceName(event.target.value)} className="control-primary mt-2" placeholder="例如：FutureMode Hackathon" /></label><div className="mt-6"><div className="flex items-end justify-between gap-3"><div><h3 className="text-sm font-semibold">邀請成員</h3><p className="mt-1 text-xs text-[#787774]">每列填入 Email 並選擇團隊角色。</p></div><button type="button" onClick={addInviteRow} className="inline-flex cursor-pointer items-center gap-1 text-sm font-medium text-[#0f9f8a]"><IconPlus size={16} />新增一列</button></div><div className="mt-3 overflow-hidden rounded-xl border border-[#e6e6e3]"><div className="grid grid-cols-[minmax(0,1fr)_150px_42px] gap-2 bg-[#f7f7f5] px-3 py-2 text-xs font-semibold text-[#787774]"><span>Email address</span><span>Role</span><span /></div>{inviteRows.map((row) => <div key={row.id} className="grid grid-cols-[minmax(0,1fr)_150px_42px] items-center gap-2 border-t border-[#ededeb] px-3 py-2"><input type="email" value={row.email} onChange={(event) => updateInviteRow(row.id, { email: event.target.value })} className="control-primary" placeholder="name@example.com" aria-label="成員 Email" /><select value={row.role} onChange={(event) => updateInviteRow(row.id, { role: event.target.value as InviteRow["role"] })} className="control-primary cursor-pointer" aria-label="成員角色"><option value="member">Member</option><option value="admin">Admin</option></select><button type="button" disabled={inviteRows.length === 1} onClick={() => setInviteRows((rows) => rows.filter((item) => item.id !== row.id))} className="cursor-pointer rounded-lg p-2 text-[#787774] hover:bg-red-50 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-30" aria-label="移除成員列"><IconTrash size={17} /></button></div>)}</div></div><div className="mt-7 flex justify-end gap-3 border-t border-[#ededeb] pt-5"><button type="button" disabled={submitting} onClick={closeCreate} className="cursor-pointer rounded-primary border border-[#dededb] px-4 py-2.5 text-sm font-medium">取消</button><button type="submit" disabled={submitting} className="cursor-pointer rounded-primary bg-[#1f1f1f] px-4 py-2.5 text-sm font-semibold text-white">{submitting ? "處理中…" : createdTeam ? "重試剩餘邀請" : "建立工作區"}</button></div></fieldset></form></section></div>}
  </AppShell>;
}
