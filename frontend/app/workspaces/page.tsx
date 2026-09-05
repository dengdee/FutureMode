"use client";

import { IconBriefcase, IconPlus, IconTrash, IconUsersGroup, IconX } from "@tabler/icons-react";
import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { AppShell } from "../../components/app-shell";
import { InvitationInbox } from "../../components/invitation-inbox";
import { PageHeader } from "../../components/page-header";
import { InviteUserPicker } from "../../components/invite-user-picker";
import { type InvitationUser, createInvitation, createTeam, listTeams } from "../../lib/api/teams";
import type { Team } from "../../types/api";

type InviteRow = { id: number; user: InvitationUser | null; role: "member" | "admin" };

export default function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const submitLock = useRef(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createdTeam, setCreatedTeam] = useState<Team | null>(null);
  const [teamName, setTeamName] = useState("");
  const [inviteRows, setInviteRows] = useState<InviteRow[]>([{ id: 1, user: null, role: "member" }]);

  async function loadTeams() {
    setLoading(true);
    try {
      const result = await listTeams();
      setTeams(result.teams);
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "無法讀取團隊資料。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void loadTeams(); }, []);

  function addInviteRow() {
    setInviteRows((rows) => [...rows, { id: Date.now(), user: null, role: "member" }]);
  }

  function updateInviteRow(id: number, patch: Partial<InviteRow>) {
    setInviteRows((rows) => rows.map((row) => row.id === id ? { ...row, ...patch } : row));
  }

  async function submitTeam(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitLock.current) return;
    if (!teamName.trim()) { setCreateError("請填寫團隊名稱。"); return; }
    if (inviteRows.some((row) => !row.user?.email)) {
      setCreateError("請輸入要邀請的 Email，或移除空白列。");
      return;
    }
    submitLock.current = true;
    setSubmitting(true);
    setCreateError(null);
    try {
      const team = createdTeam ?? await createTeam({ name: teamName.trim() });
      if (!createdTeam) {
        setCreatedTeam(team);
        setTeams((current) => [...current, team]);
      }
      const invitations = inviteRows.filter((row) => row.user);
      const results = await Promise.allSettled(invitations.map((row) => createInvitation(team.id, { email: row.user!.email, role: row.role })));
      const failed = invitations.filter((_, index) => results[index].status === "rejected");
      if (failed.length) {
        setInviteRows(failed);
        const rejected = results.find((result) => result.status === "rejected");
        const reason = rejected?.status === "rejected" && rejected.reason instanceof Error ? rejected.reason.message : "請稍後重試。";
        setCreateError(`團隊已建立，但 ${failed.length} 筆邀請未完成。${reason} 再次送出只會處理剩餘邀請。`);
        return;
      }
      setCreateOpen(false);
      setCreatedTeam(null);
      setTeamName("");
      setInviteRows([{ id: 1, user: null, role: "member" }]);
      setNotice(invitations.length ? "團隊已建立；受邀者登入後可在站內接受邀請。" : "團隊已建立。現在可以建立會議或管理成員。");
    } catch (cause) {
      setCreateError(cause instanceof Error ? cause.message : "建立團隊失敗，請稍後再試。");
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
    setTeamName("");
    setInviteRows([{ id: 1, user: null, role: "member" }]);
  }

  return <AppShell>
    <PageHeader eyebrow="Teams" title="團隊" description="從團隊進入成員、會議與共用資料；每個功能都有獨立頁面，方便按流程完成會前準備。" actions={<button type="button" onClick={() => { setCreateOpen(true); setNotice(null); }} className="inline-flex cursor-pointer items-center gap-2 rounded-primary bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white"><IconPlus size={17} />建立團隊</button>} />
    <InvitationInbox />
    {error && <p role="alert" className="mt-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}<button type="button" className="ml-3 underline" onClick={() => void loadTeams()}>重新載入</button></p>}
    {notice && <p role="status" className="mt-6 rounded-lg bg-[#e9f7f4] px-4 py-3 text-sm text-[#087e6d]">{notice}</p>}
    {loading ? <div className="mt-8 rounded-2xl border border-[#e6e6e3] bg-white p-8 text-sm text-[#787774]">正在讀取團隊…</div> : !error && teams.length === 0 ? <section className="mt-8 rounded-2xl border border-dashed border-[#d8d8d5] bg-white p-12 text-center"><IconBriefcase className="mx-auto text-[#0f9f8a]" size={30} /><h2 className="mt-3 text-xl font-semibold">尚未加入團隊</h2><p className="mt-2 text-sm text-[#787774]">先建立團隊，再邀請成員並建立會議。</p></section> : !error && <section className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{teams.map((team) => <article key={team.id} className="rounded-2xl border border-[#e6e6e3] bg-white p-6"><IconUsersGroup className="text-[#0f9f8a]" size={24} /><h2 className="mt-4 text-xl font-semibold">{team.name}</h2><p className="mt-2 text-sm text-[#787774]">你的角色：{team.role === "admin" ? "管理員" : "成員"}</p><div className="mt-6 flex flex-wrap gap-2"><Link href={`/workspaces/${team.id}`} className="rounded-primary bg-[var(--accent)] px-3 py-2 text-sm font-semibold text-white">開啟團隊</Link><Link href={`/meetings/new?teamId=${team.id}`} className="rounded-primary border border-[#cde5df] px-3 py-2 text-sm font-semibold text-[#087e6d]">建立會議</Link></div></article>)}</section>}
    {createOpen && <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/35 px-4 py-8" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && closeCreate()}><section role="dialog" aria-modal="true" aria-labelledby="create-team-title" className="w-full max-w-2xl rounded-2xl border border-[#dededb] bg-white shadow-xl"><header className="flex items-center justify-between border-b border-[#e6e6e3] px-6 py-5"><div><h2 id="create-team-title" className="text-xl font-semibold">建立團隊</h2><p className="mt-1 text-sm text-[#787774]">建立後可管理成員、安排會議與查看團隊共用資料。</p></div><button type="button" disabled={submitting} onClick={closeCreate} className="cursor-pointer rounded-lg p-2 text-[#787774] hover:bg-[#f4f4f2]" aria-label="關閉"><IconX size={22} /></button></header><form onSubmit={submitTeam} className="p-6" aria-busy={submitting}>{createError && <p role="alert" className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{createError}</p>}<fieldset disabled={submitting} className="min-w-0"><label className="block text-sm font-medium">團隊名稱<input required disabled={!!createdTeam} value={teamName} onChange={(event) => setTeamName(event.target.value)} className="control-primary mt-2" placeholder="例如：產品團隊" /></label><div className="mt-6"><div className="flex items-end justify-between gap-3"><div><h3 className="text-sm font-semibold">邀請成員</h3><p className="mt-1 text-xs text-[#787774]">受邀者登入後會在站內看到邀請。</p></div><button type="button" onClick={addInviteRow} className="inline-flex cursor-pointer items-center gap-1 text-sm font-medium text-[#0f9f8a]"><IconPlus size={16} />新增一列</button></div><div className="mt-3 overflow-hidden rounded-xl border border-[#e6e6e3]"><div className="grid grid-cols-[minmax(0,1fr)_150px_42px] gap-2 bg-[#f7f7f5] px-3 py-2 text-xs font-semibold text-[#787774]"><span>已註冊帳號</span><span>Role</span><span /></div>{inviteRows.map((row) => <div key={row.id} className="grid grid-cols-[minmax(0,1fr)_150px_42px] items-center gap-2 border-t border-[#ededeb] px-3 py-2"><InviteUserPicker value={row.user} disabled={submitting} onChange={(user) => updateInviteRow(row.id, { user })} /><select value={row.role} onChange={(event) => updateInviteRow(row.id, { role: event.target.value as InviteRow["role"] })} className="control-primary cursor-pointer" aria-label="成員角色"><option value="member">Member</option><option value="admin">Admin</option></select><button type="button" disabled={inviteRows.length === 1} onClick={() => setInviteRows((rows) => rows.filter((item) => item.id !== row.id))} className="cursor-pointer rounded-lg p-2 text-[#787774] hover:bg-red-50 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-30" aria-label="移除成員列"><IconTrash size={17} /></button></div>)}</div></div><div className="mt-7 flex justify-end gap-3 border-t border-[#ededeb] pt-5"><button type="button" disabled={submitting} onClick={closeCreate} className="cursor-pointer rounded-primary border border-[#dededb] px-4 py-2.5 text-sm font-medium">取消</button><button type="submit" disabled={submitting} className="cursor-pointer rounded-primary bg-[#1f1f1f] px-4 py-2.5 text-sm font-semibold text-white">{submitting ? "處理中…" : createdTeam ? "重試剩餘邀請" : "建立團隊"}</button></div></fieldset></form></section></div>}
  </AppShell>;
}
