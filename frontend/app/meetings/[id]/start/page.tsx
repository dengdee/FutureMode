"use client";

import { IconExternalLink, IconPlayerPlay } from "@tabler/icons-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "../../../../components/app-shell";
import { MeetingAudioCapture } from "../../../../components/meeting-audio-capture";
import { MeetingWorkspaceHeader } from "../../../../components/meeting-workspace-header";
import { getMeeting } from "../../../../lib/api/meetings";
import type { MeetingSummary } from "../../../../types/api";

export default function StartMeetingPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [meeting, setMeeting] = useState<MeetingSummary | null>(null);
  const [deadline, setDeadline] = useState("");
  const [meetUrl, setMeetUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getMeeting(id)
      .then(setMeeting)
      .catch((cause) => setError(cause instanceof Error ? cause.message : "無法讀取會議。"))
      .finally(() => setLoading(false));
    setDeadline(localStorage.getItem(`proximate:prep-deadline:${id}`) ?? "");
    setMeetUrl(localStorage.getItem(`proximate:meeting-url:${id}`) ?? "");
  }, [id]);

  function enterLive() { router.push(`/meetings/${id}/live`); }

  if (loading) return <AppShell><p className="text-sm text-[#787774]">正在載入開始會議設定…</p></AppShell>;
  if (!meeting) return <AppShell><p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error || "找不到此會議。"}</p></AppShell>;
  const ready = Boolean(deadline) && new Date(deadline).getTime() <= Date.now();

  return <AppShell>
    <MeetingWorkspaceHeader phase="start" title={meeting.title} />
    {error && <p role="alert" className="mt-5 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
    <section className="mt-6 rounded-2xl border border-[#cde5df] bg-[#f0fbf8] p-5 sm:p-7">
      <h2 className="text-lg font-semibold text-[#075f52]">開始會議</h2>
      <p className="mt-1 text-sm leading-6 text-[#4c6e65]">確認收音設定後開始會議；收音會在本頁直接啟用，不需跳轉其他頁面。</p>
      <div className="mt-5">{ready ? <MeetingAudioCapture meetingId={id} /> : <p className="rounded-xl bg-[#fffaf0] p-4 text-sm text-[#715b1e]">議前討論填寫期限尚未到，收音設定會在期限到後開放。</p>}</div>
      <div className="mt-5 flex flex-wrap gap-2">
        {meetUrl ? <a href={meetUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-[#9ddbc8] bg-white px-4 py-2.5 text-sm font-semibold text-[#087e6d]"><IconExternalLink size={16} />前往 Google Meet</a> : <span title="建立會議時尚未設定 Google Meet 連結" className="inline-flex cursor-not-allowed items-center gap-2 rounded-lg border border-[#dededb] bg-white/60 px-4 py-2.5 text-sm font-semibold text-[#9b9a97]"><IconExternalLink size={16} />尚未設定 Google Meet 連結</span>}
        <button type="button" onClick={enterLive} className="inline-flex items-center gap-2 rounded-lg bg-[#0f9f8a] px-4 py-2.5 text-sm font-semibold text-white"><IconPlayerPlay size={16} />進入即時會議</button>
      </div>
    </section>
  </AppShell>;
}
