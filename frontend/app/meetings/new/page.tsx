"use client";

import { IconCalendar, IconPlus, IconTrash } from "@tabler/icons-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { AppShell } from "../../../components/app-shell";
import { PageHeader } from "../../../components/page-header";
import { addAgendaItem } from "../../../lib/api/agenda";
import { createMeeting } from "../../../lib/api/meetings";
import { listTeams } from "../../../lib/api/teams";
import type { Team } from "../../../types/api";

const fieldClass = "control-primary mt-2 placeholder:text-[#a5a5a1]";

export default function NewMeetingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [teams, setTeams] = useState<Team[]>([]);
  const [title, setTitle] = useState("");
  const [teamId, setTeamId] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [level, setLevel] = useState("medium");
  const [agenda, setAgenda] = useState<string[]>([""]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdMeetingId, setCreatedMeetingId] = useState<string | null>(null);

  useEffect(() => {
    const fromWorkspace = searchParams.get("teamId");
    listTeams().then((result) => {
      setTeams(result.teams);
      setTeamId((current) => current || (result.teams.some((team) => team.id === fromWorkspace) ? fromWorkspace! : result.teams[0]?.id ?? ""));
    }).catch((cause) => setError(cause instanceof Error ? cause.message : "無法讀取團隊工作區。"));
  }, [searchParams]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim() || !teamId) { setError("請選擇工作區並填寫會議名稱。"); return; }
    setSubmitting(true); setError(null);
    try {
      const meeting = await createMeeting({ team_id: teamId, title: title.trim(), scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null, ai_intervention_level: level });
      setCreatedMeetingId(meeting.id);
      const agendaTitles = agenda.map((item) => item.trim()).filter(Boolean);
      for (const [index, item] of agendaTitles.entries()) {
        await addAgendaItem(meeting.id, { position: index + 1, title: item });
      }
      router.push(`/meetings/${meeting.id}/prepare`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "建立會議失敗，請稍後再試。");
      setSubmitting(false);
    }
  }

  return <AppShell><PageHeader eyebrow="New meeting" title="建立會議" description="從一個團隊工作區建立會議，並一次完成基本議程設定。" />
    <form onSubmit={handleSubmit} className="mt-8 max-w-3xl space-y-6 rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-7">
      <section><h2 className="font-semibold">會議資訊</h2><label className="mt-5 block text-sm font-medium">所屬工作區<select required value={teamId} onChange={(event) => setTeamId(event.target.value)} className={fieldClass}><option value="">選擇工作區</option>{teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label><label className="mt-4 block text-sm font-medium">會議名稱<input required value={title} onChange={(event) => setTitle(event.target.value)} className={fieldClass} placeholder="例如：產品方向校準會議" /></label><label className="mt-4 block text-sm font-medium">開始時間<div className="relative"><input value={scheduledAt} onChange={(event) => setScheduledAt(event.target.value)} className={fieldClass} type="datetime-local" /><IconCalendar className="pointer-events-none absolute right-3 top-4 text-[#8b8b87]" size={17} /></div></label><label className="mt-4 block text-sm font-medium">AI 介入程度<select value={level} onChange={(event) => setLevel(event.target.value)} className={fieldClass}><option value="low">低</option><option value="medium">中</option><option value="high">高</option></select></label></section>
      <section className="border-t border-[#ededeb] pt-6"><div className="flex items-center justify-between"><div><h2 className="font-semibold">議程</h2><p className="mt-1 text-sm text-[#787774]">送出後會依序建立為本場會議的正式議程。</p></div><button type="button" onClick={() => setAgenda((items) => [...items, ""])} className="inline-flex cursor-pointer items-center gap-1 text-sm font-medium text-[#0f9f8a]"><IconPlus size={17} />新增議題</button></div><div className="mt-4 space-y-3">{agenda.map((item, index) => <div key={index} className="flex gap-2"><span className="flex w-8 shrink-0 items-center justify-center text-sm font-semibold text-[#0f9f8a]">{index + 1}</span><input value={item} onChange={(event) => setAgenda((items) => items.map((current, itemIndex) => itemIndex === index ? event.target.value : current))} className="control-primary" placeholder="輸入議題" /><button type="button" disabled={agenda.length === 1} onClick={() => setAgenda((items) => items.filter((_, itemIndex) => itemIndex !== index))} className="cursor-pointer rounded-lg px-2 text-[#8b8b87] hover:bg-[#f7f7f5] disabled:cursor-not-allowed disabled:opacity-40" aria-label="移除議題"><IconTrash size={18} /></button></div>)}</div></section>
      {error && <div role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700"><p>{error}</p>{createdMeetingId && <Link href={`/meetings/${createdMeetingId}/prepare`} className="mt-2 inline-block font-medium underline">前往已建立的會議</Link>}</div>}
      <div className="flex flex-col-reverse justify-end gap-3 border-t border-[#ededeb] pt-6 sm:flex-row"><Link href="/workspaces" className="rounded-lg px-4 py-2.5 text-center text-sm font-medium text-[#5f5f5b] hover:bg-[#f4f4f2]">取消</Link><button disabled={submitting || !teams.length} type="submit" className="cursor-pointer rounded-lg bg-[#0f9f8a] px-4 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60">{submitting ? "建立中…" : "建立會議"}</button></div>
    </form>
  </AppShell>;
}
