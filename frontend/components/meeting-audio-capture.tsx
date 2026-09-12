"use client";

import { IconAlertTriangle, IconMicrophone, IconPlayerStop, IconShieldCheck } from "@tabler/icons-react";
import { useEffect, useRef, useState } from "react";
import { transcribeAudio } from "../lib/api/meeting-features";

type BrowserVad = {
  start: () => void;
  pause: () => void;
};
type VadApi = {
  MicVAD: { new: (options: Record<string, unknown>) => Promise<BrowserVad> };
};

async function loadVadApi(): Promise<VadApi> {
  if (window.vad) return window.vad as unknown as VadApi;
  const load = (src: string) => new Promise<void>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = src;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("VAD 資源載入失敗"));
    document.head.appendChild(script);
  });
  await load("https://cdn.jsdelivr.net/npm/onnxruntime-web@1.22.0/dist/ort.wasm.min.js");
  await load("https://cdn.jsdelivr.net/npm/@ricky0123/vad-web@0.0.29/dist/bundle.min.js");
  if (!window.vad) throw new Error("VAD 初始化失敗");
  return window.vad as unknown as VadApi;
}

declare global {
  interface Window { vad?: VadApi; }
}

type CaptureState = "idle" | "recording" | "uploading" | "ready" | "error";
const activeRecorders = new Map<string, MediaRecorder>();

export function stopMeetingAudioCapture(meetingId: string) {
  window.localStorage.removeItem(`meeting-audio-recording:${meetingId}`);
  const recorder = activeRecorders.get(meetingId);
  if (recorder?.state === "recording") recorder.stop();
}

export function MeetingAudioCapture({ meetingId }: { meetingId: string }) {
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const maxSignal = useRef(0);
  const [consent, setConsent] = useState(false);
  const [state, setState] = useState<CaptureState>("idle");
  const [message, setMessage] = useState("尚未請求瀏覽器麥克風權限。");

  useEffect(() => {
    if (window.localStorage.getItem(`meeting-audio-consent:${meetingId}`) === "true") {
      setConsent(true);
      setMessage(activeRecorders.has(meetingId) ? "正在收音；結束會議時會自動停止。" : "已同意收音範圍，尚未開始收音。");
      if (activeRecorders.has(meetingId)) setState("recording");
      else if (window.localStorage.getItem(`meeting-audio-recording:${meetingId}`) === "true") {
        void startCapture();
      }
    }
  }, [meetingId]);

  async function startCapture() {
    if (!consent) { setMessage("請先同意收音範圍。"); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      window.localStorage.setItem(`meeting-audio-recording:${meetingId}`, "true");
      maxSignal.current = 0;
      chunks.current = [];
      const next = new MediaRecorder(stream, { mimeType: "audio/webm" });
      let speechDetected = false;
      const vadApi = await loadVadApi();
      const vad = await vadApi.MicVAD.new({
        getStream: async () => stream,
        model: "v5",
        onSpeechStart: () => { speechDetected = true; },
        onnxWASMBasePath: "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.22.0/dist/",
        baseAssetPath: "https://cdn.jsdelivr.net/npm/@ricky0123/vad-web@0.0.29/dist/",
      });
      vad.start();
      const audioContext = new AudioContext();
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 512;
      audioContext.createMediaStreamSource(stream).connect(analyser);
      const samples = new Uint8Array(analyser.fftSize);
      const vadTimer = window.setInterval(() => {
        analyser.getByteTimeDomainData(samples);
        let energy = 0;
        for (const sample of samples) energy += (sample - 128) ** 2;
        maxSignal.current = Math.max(maxSignal.current, Math.sqrt(energy / samples.length));
      }, 100);
      activeRecorders.set(meetingId, next);
      next.ondataavailable = (event) => { if (event.data.size) chunks.current.push(event.data); };
      next.onstop = async () => {
        window.localStorage.removeItem(`meeting-audio-recording:${meetingId}`);
        window.clearInterval(vadTimer);
        await audioContext.close();
        vad.pause();
        activeRecorders.delete(meetingId);
        if (!speechDetected || maxSignal.current < 8) {
          setState("ready");
          setMessage("未偵測到人聲，已略過這段轉錄。");
          return;
        }
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(chunks.current, { type: "audio/webm" });
        setState("uploading"); setMessage("正在送交後端轉錄…");
        try {
          const result = await transcribeAudio(meetingId, new File([blob], "capture.webm", { type: "audio/webm" }), { speaker_label: "我" });
          setState("ready"); setMessage(`已完成轉錄：${result.text}`);
        } catch (error) { setState("error"); setMessage(error instanceof Error ? error.message : "轉錄失敗，請稍後重試。"); }
      };
      recorder.current = next; next.start(); setState("recording"); setMessage("正在收音；離開本頁後仍會持續，結束會議時會自動停止。");
    } catch (error) { setState("error"); setMessage(error instanceof Error ? error.message : "無法取得麥克風權限。"); }
  }

  function stopCapture() { stopMeetingAudioCapture(meetingId); }

  return <div className="space-y-4">
    <section className="rounded-xl border border-[#e6e6e3] bg-white p-5">
      <div className="flex items-start gap-3"><IconMicrophone size={20} className="mt-0.5 shrink-0 text-[#0f9f8a]" /><div><h3 className="font-semibold">設定收音</h3><p className="mt-1 text-sm leading-6 text-[#787774]">僅在你同意後收音，產生本場逐字稿；前端不保存原始音檔。</p></div></div>
      <label className="mt-4 flex items-start gap-3 rounded-xl bg-[#f7f7f5] p-4 text-sm"><input checked={consent} onChange={(event) => { setConsent(event.target.checked); window.localStorage.setItem(`meeting-audio-consent:${meetingId}`, String(event.target.checked)); }} className="mt-1 h-4 w-4 accent-[#0f9f8a]" type="checkbox" /><span><strong>我了解並同意收音範圍</strong><span className="mt-1 block text-[#787774]">同意設定會保留；開始後離開本頁仍會持續收音，結束會議時自動停止。</span></span></label>
      {state === "recording" ? <button type="button" onClick={stopCapture} className="mt-4 inline-flex items-center gap-2 rounded-lg bg-[#1f1f1f] px-4 py-2.5 text-sm font-semibold text-white"><IconPlayerStop size={17} />停止並轉錄</button> : <button type="button" disabled={state === "uploading"} onClick={() => void startCapture()} className="mt-4 inline-flex items-center gap-2 rounded-lg bg-[#0f9f8a] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"><IconMicrophone size={17} />{state === "uploading" ? "轉錄中…" : "允許麥克風並開始收音"}</button>}
    </section>
    <section className="flex gap-3 rounded-xl border border-[#e6e6e3] bg-white p-4"><IconShieldCheck size={19} className="shrink-0 text-[#0f9f8a]" /><p role="status" className="text-sm text-[#787774]">{message}</p></section>
    <p className="flex gap-2 rounded-xl border border-[#f0dca5] bg-[#fffaf0] p-4 text-xs leading-5 text-[#715b1e]"><IconAlertTriangle size={17} className="shrink-0" />背景分頁可能因省電機制停止收音；開始後請保持此頁開啟。</p>
  </div>;
}
