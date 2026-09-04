"use client";

import { IconFileText, IconFolder, IconSearch } from "@tabler/icons-react";
import { useSearchParams } from "next/navigation";
import { useEffect, useState, type DragEvent } from "react";
import { AppShell } from "../../components/app-shell";
import { PageHeader } from "../../components/page-header";
import { listTeams } from "../../lib/api/teams";
import { listMeetings } from "../../lib/api/meetings";
import type { MeetingSummary, Team } from "../../types/api";

export default function MemoryPage() {
  const searchParams = useSearchParams();
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamId, setTeamId] = useState(() => searchParams.get("teamId") ?? "");
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [meetingId, setMeetingId] = useState(() => searchParams.get("meetingId") ?? "");
  const [scope, setScope] = useState<"shared" | "meeting">(() => searchParams.get("scope") === "meeting" ? "meeting" : "shared");
  const [files, setFiles] = useState<string[]>([]);
  const [dragging, setDragging] = useState(false);

  useEffect(() => { Promise.all([listTeams(), listMeetings()]).then(([teamResult, meetingResult]) => { setTeams(teamResult.teams); setTeamId(teamResult.teams[0]?.id ?? ""); setMeetings(meetingResult); setMeetingId(meetingResult[0]?.id ?? ""); }).catch(() => undefined); }, []);
  function acceptFiles(fileList: FileList | null) { if (fileList) setFiles((current) => [...current, ...Array.from(fileList).map((file) => file.name)]); }
  function onDrop(event: DragEvent<HTMLDivElement>) { event.preventDefault(); setDragging(false); acceptFiles(event.dataTransfer.files); }

  return <AppShell><PageHeader eyebrow="Team memory" title="團隊記憶" description="依工作區整理共用文件與單次會議資料，讓 AI 使用正確的脈絡。" />
    <div className="mt-8 flex flex-wrap items-center gap-3"><label className="text-sm font-medium">目前工作區<select value={teamId} onChange={(event) => setTeamId(event.target.value)} className="control-primary ml-3 inline-block w-auto min-w-52 cursor-pointer"><option value="">選擇工作區</option>{teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label>{scope === "meeting" && <label className="text-sm font-medium">目前會議<select value={meetingId} onChange={(event) => setMeetingId(event.target.value)} className="control-primary ml-3 inline-block w-auto min-w-64 cursor-pointer"><option value="">選擇會議</option>{meetings.filter((meeting) => meeting.team_id === teamId).map((meeting) => <option key={meeting.id} value={meeting.id}>{meeting.title}</option>)}</select></label>}</div>
    <div className="mt-5 grid gap-6 lg:grid-cols-[240px_minmax(0,1fr)]"><aside className="rounded-2xl border border-[#e6e6e3] bg-white p-3"><p className="px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#8b8b87]">文件範圍</p>{[["shared", "團隊共用文件"], ["meeting", "單次會議文件"]].map(([value, label]) => <button key={value} type="button" onClick={() => setScope(value as "shared" | "meeting")} className={`flex w-full cursor-pointer items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm ${scope === value ? "bg-[#efefec] font-medium" : "text-[#787774] hover:bg-[#f7f7f5]"}`}><IconFolder size={17} />{label}</button>)}</aside>
      <section><label className="relative block"><IconSearch className="absolute left-3 top-3 text-[#8b8b87]" size={18} /><input className="control-primary w-full pl-10" placeholder="搜尋文件、決策或關鍵字" /></label><div role="button" tabIndex={0} onClick={() => document.getElementById("memory-file-picker")?.click()} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") document.getElementById("memory-file-picker")?.click(); }} onDragEnter={(event) => { event.preventDefault(); setDragging(true); }} onDragOver={(event) => event.preventDefault()} onDragLeave={() => setDragging(false)} onDrop={onDrop} className={`mt-5 cursor-pointer rounded-2xl border-2 border-dashed bg-white p-10 text-center transition-colors ${dragging ? "border-[#0f9f8a] bg-[#f0fbf8]" : "border-[#e6e6e3]"}`}><IconFileText className="mx-auto text-[#0f9f8a]" size={32} /><h2 className="mt-4 font-semibold">將文件拖曳到這裡</h2><p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-[#787774]">目前區域：{scope === "shared" ? "團隊共用文件" : `單次會議文件${meetingId ? ` · ${meetings.find((meeting) => meeting.id === meetingId)?.title ?? ""}` : " · 請先選擇會議"}`}。支援 PDF 與純文字檔案。</p><input id="memory-file-picker" className="sr-only" type="file" accept=".pdf,.txt" multiple onClick={(event) => event.stopPropagation()} onChange={(event) => acceptFiles(event.target.files)} />{files.length > 0 && <div className="mx-auto mt-6 max-w-xl space-y-2 text-left">{files.map((file, index) => <div key={`${file}-${index}`} className="flex items-center gap-3 rounded-xl bg-[#f7f7f5] px-4 py-3 text-sm"><IconFileText className="text-[#0f9f8a]" size={19} /><span className="truncate">{file}</span><span className="ml-auto text-xs text-[#8b8b87]">待上傳</span></div>)}</div>}</div></section></div>
  </AppShell>;
}
