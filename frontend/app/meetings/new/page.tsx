"use client";

import { IconPlus, IconSparkles, IconTrash } from "@tabler/icons-react";
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
const templates = [
  { id: "", label: "不套用範本", agenda: [""] },
  { id: "decision", label: "決策會議", agenda: ["確認今天需要做的決定", "檢視選項、風險與依據", "確認決策與下一步"] },
  { id: "sync", label: "專案同步", agenda: ["進度與重要變更", "阻礙與需要協助的事項", "本週行動項目"] },
  { id: "retro", label: "回顧會議", agenda: ["做得好的地方", "需要改善的地方", "下一次要嘗試的改變"] },
] as const;
const interventionLevels = [
  { id: "low", label: "僅在高風險時提醒", description: "AI 大多保持安靜，只有被詢問或發現重大風險時才提出觀點。" },
  { id: "medium", label: "重要時主動提醒", description: "建議的預設值；發現新的重要風險、反例或未決問題時舉手。" },
  { id: "high", label: "積極補充觀點", description: "AI 會更常提出替代方案、歷史提醒與風險，適合腦力激盪。" },
] as const;

export default function NewMeetingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [teams, setTeams] = useState<Team[]>([]);
  const [title, setTitle] = useState("");
  const [teamId, setTeamId] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [level, setLevel] = useState("medium");
  const [agenda, setAgenda] = useState<string[]>([""]);
  const [template, setTemplate] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdMeetingId, setCreatedMeetingId] = useState<string | null>(null);

  useEffect(() => {
    const selectedTeamId = searchParams.get("teamId");
    listTeams().then((result) => { setTeams(result.teams); setTeamId((current) => current || (result.teams.some((team) => team.id === selectedTeamId) ? selectedTeamId! : result.teams[0]?.id ?? "")); }).catch((cause) => setError(cause instanceof Error ? cause.message : "無法讀取團隊。"));
  }, [searchParams]);

  function chooseTemplate(value: string) {
    const next = templates.find((item) => item.id === value);
    setTemplate(value);
    if (next) setAgenda([...next.agenda]);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!title.trim() || !teamId) { setError("請選擇團隊並填寫會議名稱。 "); return; }
    setSubmitting(true); setError(null);
    try {
      const meeting = await createMeeting({ team_id: teamId, title: title.trim(), scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null, ai_intervention_level: level });
      setCreatedMeetingId(meeting.id);
      const titles = agenda.map((item) => item.trim()).filter(Boolean);
      for (const [index, item] of titles.entries()) await addAgendaItem(meeting.id, { position: index + 1, title: item });
      router.push(`/meetings/${meeting.id}/prepare`);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "建立會議失敗，請稍後再試。"); setSubmitting(false); }
  }

  return <AppShell><PageHeader eyebrow="New meeting" title="建立會議" description="先設定會議重點與參與團隊；建立後可在會前準備中產生 Brief、整理私人想法與設定代理。" />
    <form onSubmit={handleSubmit} className="mt-8 max-w-4xl space-y-6"><section className="rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-7"><h2 className="text-lg font-semibold">基本資訊</h2><div className="mt-5 grid gap-4 sm:grid-cols-2"><label className="block text-sm font-medium">所屬團隊<select required value={teamId} onChange={(event) => setTeamId(event.target.value)} className={fieldClass}><option value="">選擇團隊</option>{teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label><label className="block text-sm font-medium">開始時間<span className="ml-1 font-normal text-[#787774]">（可稍後設定）</span><input value={scheduledAt} onChange={(event) => setScheduledAt(event.target.value)} className={fieldClass} type="datetime-local" /></label></div><label className="mt-4 block text-sm font-medium">會議名稱<input required value={title} onChange={(event) => setTitle(event.target.value)} className={fieldClass} placeholder="例如：產品方向校準會議" /></label></section>
      <section className="rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-7"><div className="flex items-start gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#e7f7ef] text-[#087e6d]"><IconSparkles size={20} /></span><div><h2 className="text-lg font-semibold">AI 參與方式</h2><p className="mt-1 text-sm leading-6 text-[#787774]">產品規劃中的介入程度，決定 AI 多常以「舉手」方式提出風險或替代觀點；它不會自行插話或替人決策。</p></div></div><div className="mt-5 grid gap-3 md:grid-cols-3">{interventionLevels.map((item) => <label key={item.id} className={`cursor-pointer rounded-xl border p-4 transition ${level === item.id ? "border-[#0f9f8a] bg-[#f0fbf8] ring-1 ring-[#0f9f8a]" : "border-[#e6e6e3] hover:border-[#9ddbc8]"}`}><input className="sr-only" type="radio" name="intervention" checked={level === item.id} onChange={() => setLevel(item.id)} /><span className="block font-medium">{item.label}</span><span className="mt-2 block text-xs leading-5 text-[#787774]">{item.description}</span></label>)}</div></section>
      <section className="rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-7"><div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start"><div><h2 className="text-lg font-semibold">議程</h2><p className="mt-1 text-sm leading-6 text-[#787774]">可先套用常用會議結構，再自由增刪。建立後，會前 Brief 會依議程與已授權資料整理討論焦點。</p></div><label className="text-sm font-medium">快速套用<select value={template} onChange={(event) => chooseTemplate(event.target.value)} className="control-primary mt-2 min-w-44 text-sm">{templates.map((item) => <option key={item.id || "none"} value={item.id}>{item.label}</option>)}</select></label></div><div className="mt-5 space-y-3">{agenda.map((item, index) => <div key={index} className="flex items-center gap-2"><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#e7f7ef] text-sm font-semibold text-[#087e6d]">{index + 1}</span><input value={item} onChange={(event) => setAgenda((items) => items.map((current, itemIndex) => itemIndex === index ? event.target.value : current))} className="control-primary" placeholder="輸入要討論的議題" /><button type="button" disabled={agenda.length === 1} onClick={() => setAgenda((items) => items.filter((_, itemIndex) => itemIndex !== index))} className="rounded-lg p-2 text-[#787774] hover:bg-red-50 hover:text-red-700 disabled:opacity-40" aria-label="移除此議程"><IconTrash size={18} /></button></div>)}</div><button type="button" onClick={() => setAgenda((items) => [...items, ""])} className="mt-4 inline-flex items-center gap-1 rounded-lg border border-[#d7e8e5] px-3 py-2 text-sm font-medium text-[#087e6d]"><IconPlus size={17} />新增議題</button></section>
      {error && <div role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}{createdMeetingId && <Link href={`/meetings/${createdMeetingId}/prepare`} className="mt-2 block font-medium underline">前往已建立的會議</Link>}</div>}
      <div className="flex flex-col-reverse justify-end gap-3 sm:flex-row"><Link href="/workspaces" className="rounded-lg px-4 py-2.5 text-center text-sm font-medium text-[#5f5f5b] hover:bg-[#f4f4f2]">取消</Link><button disabled={submitting || !teams.length} type="submit" className="rounded-lg bg-[#0f9f8a] px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-60">{submitting ? "建立中…" : "建立並進入會前準備"}</button></div>
    </form></AppShell>;
}
