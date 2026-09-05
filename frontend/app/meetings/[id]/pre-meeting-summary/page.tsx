"use client";

import { IconArrowUpRight, IconClock, IconSparkles } from "@tabler/icons-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "../../../../components/app-shell";
import { MeetingWorkspaceHeader } from "../../../../components/meeting-workspace-header";
import { listAgendaItems } from "../../../../lib/api/agenda";
import { getMeeting } from "../../../../lib/api/meetings";
import type { AgendaItem, MeetingSummary } from "../../../../types/api";

export default function PreMeetingSummaryPage() {
  const { id } = useParams<{ id: string }>();
  const [meeting, setMeeting] = useState<MeetingSummary | null>(null); const [agenda, setAgenda] = useState<AgendaItem[]>([]); const [deadline, setDeadline] = useState(""); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  useEffect(() => { Promise.all([getMeeting(id), listAgendaItems(id)]).then(([current, agendaResult]) => { setMeeting(current); setAgenda(agendaResult.items); setDeadline(localStorage.getItem(`proximate:prep-deadline:${id}`) ?? ""); }).catch((cause) => setError(cause instanceof Error ? cause.message : "無法讀取議前整理。")).finally(() => setLoading(false)); }, [id]);
  if (loading) return <AppShell><p className="text-sm text-[#787774]">正在整理會前資料…</p></AppShell>;
  if (!meeting) return <AppShell><p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error || "找不到此會議。"}</p></AppShell>;
  const ready = Boolean(deadline) && new Date(deadline).getTime() <= Date.now();
  return <AppShell><MeetingWorkspaceHeader phase="summary" title={meeting.title} /><section className="mt-6 rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-7"><div className="flex items-start gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#e7f7ef] text-[#087e6d]"><IconSparkles size={20} /></span><div><h2 className="text-lg font-semibold">AI 議前整理</h2><p className="mt-1 text-sm leading-6 text-[#787774]">在所有參與者完成期限前的議前討論後，這裡會彙整共同議程、已確認共識與待解決衝突。</p></div></div><div className={`mt-6 rounded-xl p-4 ${ready ? "bg-[#f0fbf8] text-[#075f52]" : "bg-[#fffaf0] text-[#715b1e]"}`}><p className="inline-flex items-center gap-2 text-sm font-semibold"><IconClock size={17} />{deadline ? `參與者填寫期限：${new Date(deadline).toLocaleString("zh-TW")}` : "尚未設定參與者填寫期限"}</p><p className="mt-2 text-sm leading-6">{ready ? "期限已到；可檢視本場共通議程並設定收音。" : deadline ? "期限尚未到，為保護每位成員的準備時間，議前整理與收音設定目前保持停用。" : "請在建立下一場會議時設定期限，AI 才能在正確時間開放議前整理。"}</p></div></section><section className="mt-6 rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-7"><h2 className="text-lg font-semibold">本場共同議程</h2><ol className="mt-5 space-y-3">{agenda.map((item) => <li key={item.id} className="flex gap-3 rounded-xl bg-[#f7f7f5] p-4"><span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white text-sm font-semibold text-[#087e6d]">{item.position}</span><div><p className="font-medium">{item.title}</p><p className="mt-1 text-sm text-[#787774]">{item.status === "completed" ? "已完成討論" : "待於會議中確認"}</p></div></li>)}{agenda.length === 0 && <li className="rounded-xl bg-[#f7f7f5] p-4 text-sm text-[#787774]">本場尚未設定議程。</li>}</ol></section><section className="mt-6 rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-7"><h2 className="text-lg font-semibold">進入會議前</h2><p className="mt-1 text-sm leading-6 text-[#787774]">收音設定只在議前整理完成後開放，讓每位成員先了解本場脈絡與授權範圍。</p>{ready ? <Link href={`/meetings/${id}/audio-setup`} className="mt-5 inline-flex items-center gap-2 rounded-lg bg-[#0f9f8a] px-4 py-2.5 text-sm font-semibold text-white">設定收音 <IconArrowUpRight size={17} /></Link> : <button type="button" disabled className="mt-5 inline-flex cursor-not-allowed items-center gap-2 rounded-lg bg-[#e6e6e3] px-4 py-2.5 text-sm font-semibold text-[#9b9a97]">設定收音 <IconArrowUpRight size={17} /></button>}</section></AppShell>;
}
