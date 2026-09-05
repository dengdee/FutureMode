"use client";
import { IconExternalLink, IconRefresh } from "@tabler/icons-react";
import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "../../../../components/app-shell";
import { MeetingWorkspaceHeader } from "../../../../components/meeting-workspace-header";
import { listSuggestions, voteSuggestion } from "../../../../lib/api/meeting-features";
import type { Suggestion } from "../../../../types/api";

export default function LivePage({ params }: { params: Promise<{ id: string }> }) {
  const [id, setId] = useState(""); const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  useEffect(() => { params.then(({ id: meetingId }) => { setId(meetingId); listSuggestions(meetingId).then(setSuggestions).catch(() => undefined); }); }, [params]);
  async function vote(suggestionId: string, voteValue: "support" | "reject" | "abstain") { if (!id) return; await voteSuggestion(id, suggestionId, voteValue); }
  return <AppShell><MeetingWorkspaceHeader meetingId={id} phase="live" /><div className="mt-7 grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]"><section className="rounded-2xl border border-[#e6e6e3] bg-white p-6"><p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#0f9f8a]">Browser fallback</p><h2 className="mt-2 text-2xl font-semibold">在瀏覽器查看會議即時狀態</h2><p className="mt-3 max-w-xl text-sm leading-6 text-[#787774]">無法開啟 Google Meet Add-on 時，可在這裡查看公開資訊與 AI 建議。</p><div className="mt-7 space-y-3">{suggestions.map((suggestion) => <article key={suggestion.id} className="rounded-xl border border-[#e6e6e3] p-4"><p className="font-medium">{suggestion.title}</p><p className="mt-1 text-sm text-[#787774]">{suggestion.content}</p><div className="mt-3 flex gap-2"><button onClick={() => vote(suggestion.id, "support")} className="rounded-lg border px-3 py-1 text-xs">支持</button><button onClick={() => vote(suggestion.id, "reject")} className="rounded-lg border px-3 py-1 text-xs">不支持</button></div></article>)}{suggestions.length === 0 && <div className="rounded-xl border border-dashed border-[#d8d8d5] bg-[#f7f7f5] px-5 py-12 text-center"><p className="font-medium">正在等待即時會議資料</p><p className="mt-2 text-sm text-[#787774]">正式 WebSocket 與 meeting token 完成後，此區將自動更新。</p><button onClick={() => id && listSuggestions(id).then(setSuggestions)} className="mt-5 inline-flex items-center gap-2 rounded-lg border bg-white px-4 py-2 text-sm font-medium"><IconRefresh size={17} />重新整理狀態</button></div>}</div></section><aside className="rounded-2xl border border-[#e6e6e3] bg-white p-5"><h2 className="font-semibold">返回 Google Meet</h2><p className="mt-2 text-sm leading-6 text-[#787774]">建議保持 Google Meet 與 Capture Page 開啟。</p><Link href={id ? `/meetings/${id}/audio-setup` : "#"} className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#0f9f8a]">查看 Capture 狀態 <IconExternalLink size={16} /></Link></aside></div></AppShell>;
}
