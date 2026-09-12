"use client";

import { IconExternalLink, IconPlayerPlay, IconPlayerStop } from "@tabler/icons-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "../../../../components/app-shell";
import { isMeetingAudioCapturing, MeetingAudioCapture, stopMeetingAudioCapture } from "../../../../components/meeting-audio-capture";
import { MeetingWorkspaceHeader } from "../../../../components/meeting-workspace-header";
import { endMeeting, getMeeting, startMeeting, updateMeeting } from "../../../../lib/api/meetings";
import type { MeetingSummary } from "../../../../types/api";

export default function StartMeetingPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [meeting, setMeeting] = useState<MeetingSummary | null>(null);
  const [deadline, setDeadline] = useState("");
  const [meetUrl, setMeetUrl] = useState("");
  const [savingMeetUrl, setSavingMeetUrl] = useState(false);
  const [ending, setEnding] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getMeeting(id)
      .then((current) => {
        setMeeting(current);
        setMeetUrl(current.google_meeting_url ?? "");
        setDeadline(current.preparation_deadline ?? "");
      })
      .catch((cause) => setError(cause instanceof Error ? cause.message : "無法讀取會議。"))
      .finally(() => setLoading(false));
  }, [id]);

  async function enterLive() {
    if (!meeting) return;
    if (meeting?.scheduled_at && new Date(meeting.scheduled_at).getTime() > Date.now()) return;
    if (meeting.status !== "in_progress") {
      const updated = await startMeeting(id);
      setMeeting(updated);
    }
    router.push(`/meetings/${id}/start/live`);
  }

  async function saveMeetUrl() {
    const normalized = meetUrl.trim();
    const googleMeetingId = normalized.match(/meet\.google\.com\/([a-z0-9-]+)/i)?.[1];
    if (!googleMeetingId) {
      setError("請輸入有效的 Google Meet 連結，例如 https://meet.google.com/abc-defg-hij。");
      return;
    }
    setSavingMeetUrl(true);
    setError("");
    try {
      const updated = await updateMeeting(id, { google_meeting_id: googleMeetingId, google_meeting_url: normalized });
      setMeeting(updated);
      setMeetUrl(updated.google_meeting_url ?? normalized);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "無法儲存 Google Meet 連結。");
    } finally {
      setSavingMeetUrl(false);
    }
  }

  async function finishMeeting() {
    if (!meeting) return;
    if (!window.confirm("確定要結束這場會議嗎？結束後將無法繼續收音。")) return;
    setEnding(true);
    setError("");
    try {
      stopMeetingAudioCapture(id);
      if (meeting.status !== "in_progress") await startMeeting(id);
      await endMeeting(id);
      router.push(`/meetings/${id}/review`);
    } catch (cause) {
      if ((cause as { status?: number }).status === 409) {
        try {
          const latest = await getMeeting(id);
          if (latest.status === "completed") {
            router.push(`/meetings/${id}/review`);
            return;
          }
        } catch {
          // Keep the original conflict message below when the refresh fails.
        }
      }
      setError(cause instanceof Error ? cause.message : "無法結束會議。");
      setEnding(false);
    }
  }

  if (loading) return <AppShell><p className="text-sm text-[#787774]">正在載入開始會議設定…</p></AppShell>;
  if (!meeting) return <AppShell><p role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error || "找不到此會議。"}</p></AppShell>;
  const ready = Boolean(deadline) && new Date(deadline).getTime() <= Date.now();
  const canStart = !meeting.scheduled_at || new Date(meeting.scheduled_at).getTime() <= Date.now();

  return <AppShell>
    <MeetingWorkspaceHeader phase="start" title={meeting.title} />
    {error && <p role="alert" className="mt-5 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
    <section className="mt-6 rounded-2xl border border-[#cde5df] bg-[#f0fbf8] p-5 sm:p-7">
      <h2 className="text-lg font-semibold text-[#075f52]">開始會議</h2>
      <p className="mt-1 text-sm leading-6 text-[#4c6e65]">確認收音設定後開始會議；收音會在本頁直接啟用，不需跳轉其他頁面。</p>
      <div className="mt-5">{ready ? <MeetingAudioCapture meetingId={id} /> : <p className="rounded-xl bg-[#fffaf0] p-4 text-sm text-[#715b1e]">議前討論填寫期限尚未到，收音設定會在期限到後開放。</p>}</div>
      <div className="mt-5 flex flex-wrap gap-2">
        {meetUrl ? <a href={meetUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-[#9ddbc8] bg-white px-4 py-2.5 text-sm font-semibold text-[#087e6d]"><IconExternalLink size={16} />前往 Google Meet</a> : <span title="建立會議時尚未設定 Google Meet 連結" className="inline-flex cursor-not-allowed items-center gap-2 rounded-lg border border-[#dededb] bg-white/60 px-4 py-2.5 text-sm font-semibold text-[#9b9a97]"><IconExternalLink size={16} />尚未設定 Google Meet 連結</span>}
        <button type="button" onClick={() => void enterLive()} disabled={!canStart} title={!canStart ? "尚未到會議時間" : undefined} className="inline-flex items-center gap-2 rounded-lg bg-[#0f9f8a] px-4 py-2.5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-[#b8d8d0]"><IconPlayerPlay size={16} />進入即時會議</button>
        {meeting.status !== "completed" && meeting.status !== "cancelled" && <button type="button" onClick={() => void finishMeeting()} disabled={ending || (meeting.status !== "in_progress" && !isMeetingAudioCapturing(id))} title={meeting.status !== "in_progress" && !isMeetingAudioCapturing(id) ? "請先進入即時會議或開始收音" : undefined} className="inline-flex items-center gap-2 rounded-lg border border-rose-200 bg-white px-4 py-2.5 text-sm font-semibold text-rose-700 hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-50"><IconPlayerStop size={16} />{ending ? "結束中…" : "結束會議"}</button>}
      </div>
      <div className="mt-5 rounded-xl border border-[#d7e8e5] bg-white/80 p-4">
        <label className="block text-sm font-semibold text-[#27554c]">Google Meet 連結
          <input value={meetUrl} onChange={(event) => setMeetUrl(event.target.value)} className="control-primary mt-2" placeholder="https://meet.google.com/abc-defg-hij" />
        </label>
        <p className="mt-2 text-xs leading-5 text-[#787774]">儲存後，Google Meet Add-on 才能辨識並載入這場 Proximate 會議。</p>
        <button type="button" onClick={() => void saveMeetUrl()} disabled={savingMeetUrl} className="mt-3 rounded-lg border border-[#9ddbc8] px-3 py-2 text-sm font-semibold text-[#087e6d] disabled:opacity-50">{savingMeetUrl ? "儲存中…" : "儲存並綁定 Meet"}</button>
      </div>
    </section>
  </AppShell>;
}
