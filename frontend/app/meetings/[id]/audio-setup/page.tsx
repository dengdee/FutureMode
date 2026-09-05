"use client";

import { IconAlertTriangle, IconMicrophone, IconPlayerStop, IconShieldCheck } from "@tabler/icons-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useRef, useState } from "react";
import { AppShell } from "../../../../components/app-shell";
import { MeetingWorkspaceHeader } from "../../../../components/meeting-workspace-header";
import { transcribeAudio } from "../../../../lib/api/meeting-features";

type CaptureState = "idle" | "recording" | "uploading" | "ready" | "error";

export default function AudioSetupPage() {
  const { id } = useParams<{ id: string }>();
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const [consent, setConsent] = useState(false);
  const [state, setState] = useState<CaptureState>("idle");
  const [message, setMessage] = useState("尚未請求瀏覽器麥克風權限。");

  async function startCapture() {
    if (!consent) { setMessage("請先同意收音範圍。"); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunks.current = [];
      const next = new MediaRecorder(stream, { mimeType: "audio/webm" });
      next.ondataavailable = (event) => { if (event.data.size) chunks.current.push(event.data); };
      next.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(chunks.current, { type: "audio/webm" });
        setState("uploading"); setMessage("正在送交後端轉錄…");
        try { const result = await transcribeAudio(id, new File([blob], "capture.webm", { type: "audio/webm" }), { speaker_label: "我" }); setState("ready"); setMessage(`已完成轉錄：${result.text}`); }
        catch (error) { setState("error"); setMessage(error instanceof Error ? error.message : "轉錄失敗，請稍後重試。"); }
      };
      recorder.current = next; next.start(); setState("recording"); setMessage("正在收音；按下停止後會送到後端轉錄。");
    } catch (error) { setState("error"); setMessage(error instanceof Error ? error.message : "無法取得麥克風權限。"); }
  }

  function stopCapture() { if (recorder.current?.state === "recording") recorder.current.stop(); }

  return <AppShell><MeetingWorkspaceHeader meetingId={id} phase="audio" /><div className="mx-auto mt-8 max-w-2xl space-y-5"><section className="rounded-2xl border border-[#e6e6e3] bg-white p-6"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#e7f7ef] text-[#1d6b4d]"><IconMicrophone size={23} /></div><h2 className="mt-5 text-xl font-semibold">開啟個人音訊偵測</h2><p className="mt-2 text-sm leading-6 text-[#787774]">音訊會以短片段送至後端 `/transcription`，產生本場逐字稿；前端不保存原始音檔。</p><label className="mt-5 flex items-start gap-3 rounded-xl bg-[#f7f7f5] p-4 text-sm"><input checked={consent} onChange={(event) => setConsent(event.target.checked)} className="mt-1 h-4 w-4 accent-[#0f9f8a]" type="checkbox" /><span><strong>我了解並同意收音範圍</strong><span className="mt-1 block text-[#787774]">請在需要時保持此頁開啟；瀏覽器會在第一次啟動時詢問麥克風權限。</span></span></label>{state === "recording" ? <button type="button" onClick={stopCapture} className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-[#1f1f1f] px-4 py-3 text-sm font-semibold text-white"><IconPlayerStop size={17} />停止並轉錄</button> : <button type="button" disabled={state === "uploading"} onClick={() => void startCapture()} className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-[#0f9f8a] px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"><IconMicrophone size={17} />{state === "uploading" ? "轉錄中…" : "允許麥克風並開始收音"}</button>}</section><section className="rounded-2xl border border-[#e6e6e3] bg-white p-5"><div className="flex gap-3"><IconShieldCheck size={20} className="shrink-0 text-[#0f9f8a]" /><div><h2 className="font-semibold">目前狀態</h2><p role="status" className="mt-1 text-sm text-[#787774]">{message}</p></div></div></section><section className="flex gap-3 rounded-2xl border border-[#f0dca5] bg-[#fffaf0] p-5 text-sm text-[#715b1e]"><IconAlertTriangle size={20} className="shrink-0" />背景分頁可能因省電機制停止收音；開始後請保持此 Capture Page 開啟。</section><Link href={`/meetings/${id}/live`} className="block text-center text-sm text-[#0f9f8a] hover:underline">改用瀏覽器 Live fallback</Link></div></AppShell>;
}
