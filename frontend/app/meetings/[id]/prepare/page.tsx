"use client";

import { IconArrowUpRight, IconCheck, IconPlayerPlay, IconPlus, IconTrash } from "@tabler/icons-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { AppShell } from "../../../../components/app-shell";
import { MeetingWorkspaceHeader } from "../../../../components/meeting-workspace-header";
import { addAgendaItem, listAgendaItems, removeAgendaItem, updateAgendaItem } from "../../../../lib/api/agenda";
import { endMeeting, getMeeting, startMeeting, updateMeeting } from "../../../../lib/api/meetings";
import { addParticipant, listParticipants, removeParticipant, updateParticipant } from "../../../../lib/api/participants";
import { listTeamMembers } from "../../../../lib/api/teams";
import type { AgendaItem, MeetingSummary, Participant, TeamMember } from "../../../../types/api";

const inputClass = "control-primary mt-1 text-sm";

function messageFrom(cause: unknown, fallback: string) {
  return cause instanceof Error ? cause.message : fallback;
}

export default function PreparePage() {
  const { id } = useParams<{ id: string }>();
  const [meeting, setMeeting] = useState<MeetingSummary | null>(null);
  const [agenda, setAgenda] = useState<AgendaItem[]>([]);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [agendaTitle, setAgendaTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [selectedMember, setSelectedMember] = useState("");

  async function refresh() {
    const current = await getMeeting(id);
    const [agendaResult, participantResult] = await Promise.all([listAgendaItems(id), listParticipants(id)]);
    setMeeting(current);
    setAgenda(agendaResult.items);
    setParticipants(participantResult.participants);
    listTeamMembers(current.team_id).then((result) => setMembers(result.members)).catch(() => setMembers([]));
  }

  useEffect(() => {
    let active = true;
    Promise.resolve().then(refresh).catch((cause) => active && setError(messageFrom(cause, "無法讀取會議資料。"))).finally(() => active && setLoading(false));
    return () => { active = false; };
  // The meeting id is a route identity, and refresh intentionally owns all dependent requests.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function run(action: () => Promise<void>, success: string) {
    setBusy(true); setError(null); setNotice(null);
    try { await action(); setNotice(success); await refresh(); }
    catch (cause) { setError(messageFrom(cause, "操作失敗，請稍後再試。")); }
    finally { setBusy(false); }
  }

  async function addAgenda(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!agendaTitle.trim()) return;
    await run(async () => { await addAgendaItem(id, { position: agenda.length + 1, title: agendaTitle.trim() }); setAgendaTitle(""); }, "已新增議程。");
  }

  if (loading) return <AppShell><div className="text-sm text-[#787774]">正在載入會議資料…</div></AppShell>;
  if (!meeting) return <AppShell><div className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error ?? "找不到此會議。"}</div></AppShell>;

  return <AppShell><MeetingWorkspaceHeader meetingId={id} phase="prepare" />
    <div className="mt-5 flex flex-wrap items-center gap-3 rounded-xl border border-[#e6e6e3] bg-white px-4 py-3 text-sm"><span className="font-semibold">{meeting.title}</span><span className="rounded-full bg-[#eef8f6] px-2.5 py-1 text-xs text-[#087e6d]">{meeting.status}</span><span className="text-[#787774]">{meeting.scheduled_at ? new Date(meeting.scheduled_at).toLocaleString("zh-TW") : "尚未排程"}</span><div className="ml-auto flex gap-2">{meeting.status === "draft" || meeting.status === "scheduled" ? <button type="button" disabled={busy} onClick={() => run(async () => { await startMeeting(id); }, "會議已開始。")} className="inline-flex cursor-pointer items-center gap-1 rounded-lg bg-[#0f9f8a] px-3 py-2 text-xs font-semibold text-white disabled:opacity-60"><IconPlayerPlay size={16} />開始會議</button> : meeting.status === "in_progress" ? <button type="button" disabled={busy} onClick={() => run(async () => { await endMeeting(id); }, "會議已結束。")} className="inline-flex cursor-pointer items-center gap-1 rounded-lg bg-[#1f1f1f] px-3 py-2 text-xs font-semibold text-white disabled:opacity-60"><IconCheck size={16} />結束會議</button> : null}</div></div>
    {(notice || error) && <p role="status" className={`mt-4 rounded-lg px-4 py-3 text-sm ${error ? "bg-red-50 text-red-700" : "bg-[#e9f7f4] text-[#087e6d]"}`}>{error ?? notice}</p>}
    <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]"><div className="space-y-6">
      <section className="rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-6"><h2 className="font-semibold">會議設定</h2><div className="mt-4 grid gap-4 sm:grid-cols-2"><label className="text-sm font-medium">會議名稱<input defaultValue={meeting.title} onBlur={(event) => { const title = event.target.value.trim(); if (title && title !== meeting.title) run(async () => { await updateMeeting(id, { title }); }, "已更新會議名稱。"); }} className={inputClass} /></label><label className="text-sm font-medium">AI 介入程度<select defaultValue={meeting.ai_intervention_level} onChange={(event) => run(async () => { await updateMeeting(id, { ai_intervention_level: event.target.value }); }, "已更新 AI 介入程度。")} className={inputClass}><option value="low">低</option><option value="medium">中</option><option value="high">高</option></select></label></div></section>
      <section className="rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-6"><div className="flex items-center justify-between"><h2 className="font-semibold">議程</h2><span className="text-xs text-[#787774]">{agenda.length} 項</span></div><ol className="mt-4 space-y-3">{agenda.map((item) => <li key={item.id} className="flex gap-3 rounded-xl border border-[#ededeb] p-3"><span className="pt-2 text-sm font-semibold text-[#0f9f8a]">{item.position}</span><div className="min-w-0 flex-1"><input defaultValue={item.title} onBlur={(event) => event.target.value.trim() !== item.title && run(async () => { await updateAgendaItem(id, item.id, { title: event.target.value.trim() }); }, "已更新議程。")} className="w-full bg-transparent text-sm font-medium outline-none" /><select value={item.status} onChange={(event) => run(async () => { await updateAgendaItem(id, item.id, { status: event.target.value }); }, "已更新議程狀態。")} className="mt-2 cursor-pointer bg-transparent text-xs text-[#787774] outline-none"><option value="pending">待處理</option><option value="in_progress">進行中</option><option value="completed">完成</option></select></div><button type="button" onClick={() => run(async () => { await removeAgendaItem(id, item.id); }, "已移除議程。")} className="cursor-pointer self-center rounded-lg p-2 text-[#8b8b87] hover:bg-red-50 hover:text-red-700" aria-label="刪除議程"><IconTrash size={17} /></button></li>)}</ol><form onSubmit={addAgenda} className="mt-4 flex gap-2"><input value={agendaTitle} onChange={(event) => setAgendaTitle(event.target.value)} className="control-primary" placeholder="新增一個議程" /><button disabled={busy} className="inline-flex cursor-pointer items-center gap-1 rounded-lg border border-[#dededb] px-3 text-sm font-medium disabled:opacity-60"><IconPlus size={16} />新增</button></form></section>
    </div><aside className="space-y-6"><section className="rounded-2xl border border-[#e6e6e3] bg-white p-5"><h2 className="font-semibold">參與者</h2><p className="mt-1 text-xs leading-5 text-[#787774]">從目前工作區成員加入本場會議，並管理出席狀態。</p><div className="mt-4 flex gap-2"><select value={selectedMember} onChange={(event) => setSelectedMember(event.target.value)} className="control-primary min-w-0 flex-1 text-xs"><option value="">選擇成員</option>{members.filter((member) => !participants.some((participant) => participant.user_id === member.user_id)).map((member) => <option key={member.user_id} value={member.user_id}>{member.display_name || member.external_id}</option>)}</select><button type="button" disabled={!selectedMember || busy} onClick={() => run(async () => { await addParticipant(id, { user_id: selectedMember }); setSelectedMember(""); }, "已加入參與者。")} className="rounded-lg bg-[#0f9f8a] px-3 text-xs font-semibold text-white disabled:opacity-50">加入</button></div><div className="mt-4 space-y-2">{participants.map((participant) => <div key={participant.user_id} className="rounded-xl bg-[#f7f7f5] p-3"><p className="text-sm font-medium">{members.find((member) => member.user_id === participant.user_id)?.display_name || "會議參與者"}</p><p className="mt-1 text-xs text-[#787774]">{participant.role}</p><div className="mt-2 flex gap-2"><select value={participant.attendance_status} onChange={(event) => run(async () => { await updateParticipant(id, participant.user_id, { attendance_status: event.target.value }); }, "已更新出席狀態。")} className="min-w-0 cursor-pointer bg-transparent text-xs text-[#787774]"><option value="invited">已邀請</option><option value="joined">已加入</option><option value="left">已離開</option></select><button type="button" onClick={() => run(async () => { await removeParticipant(id, participant.user_id); }, "已移除參與者。")} className="ml-auto cursor-pointer text-xs text-red-700">移除</button></div></div>)}</div>{participants.length === 0 && <p className="mt-4 rounded-xl bg-[#f7f7f5] p-3 text-xs leading-5 text-[#787774]">尚無參與者。</p>}</section>
      <section className="rounded-2xl border border-[#e6e6e3] bg-white p-5"><h2 className="font-semibold">Voice Bot</h2><p className="mt-2 text-xs leading-5 text-[#787774]">Voice Bot 目前只有未綁定會議的測試 join API，尚未具備本場會議的政策、投票與 Host 授權流程，因此暫不在正式會前 UI 開放操作。</p><p className="mt-3 text-xs text-[#8b8b87]">後端完成 meeting-scoped voice-bot contract 後，會在此顯示狀態與核准後的發言結果。</p></section></aside></div>
    <div className="mt-7 flex flex-wrap gap-3"><Link href={`/meetings/${id}/audio-setup`} className="inline-flex items-center gap-2 rounded-lg bg-[#0f9f8a] px-4 py-2.5 text-sm font-semibold text-white">設定收音 <IconArrowUpRight size={17} /></Link><Link href={`/meetings/${id}/addon`} className="rounded-lg border border-[#dededb] px-4 py-2.5 text-sm font-medium hover:bg-[#f7f7f5]">開啟 Meet Add-on 預覽</Link></div>
  </AppShell>;
}
