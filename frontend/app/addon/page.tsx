"use client";

import { useEffect, useState } from "react";
import { AddonShell } from "../../components/meeting-addon/addon-shell";

const CLOUD_PROJECT_NUMBER = "446517015863";

type MeetClient = {
  getMeetingInfo: () => Promise<{ meetingId?: string; meetingCode?: string }>;
};

type MeetRuntime = {
  addon?: {
    createAddonSession: (options: { cloudProjectNumber: string }) => Promise<{
      createSidePanelClient: () => Promise<MeetClient>;
    }>;
  };
};

declare global {
  interface Window {
    meet?: MeetRuntime;
  }
}

export default function AddonEntryPage() {
  const [message, setMessage] = useState("正在取得 Google Meet 會議 context…");
  const [meetingId, setMeetingId] = useState<string | null>(null);
  const [meetingCode, setMeetingCode] = useState<string | null>(null);
  const [preview, setPreview] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const requestedMeetingId = params.get("meetingId");
    const previewMode = params.get("preview") === "live";
    if (requestedMeetingId) {
      setMeetingId(requestedMeetingId);
      setMeetingCode(params.get("meetingCode"));
      setPreview(previewMode);
      return;
    }
    if (previewMode) {
      setPreview(true);
      setMeetingId("preview-meeting");
      return;
    }

    let cancelled = false;
    async function resolveMeeting() {
      try {
        if (!window.meet?.addon) {
          await loadMeetSdk();
        }
        const addon = window.meet?.addon;
        if (!addon) throw new Error("Google Meet Add-ons SDK 尚未載入");
        const session = await addon.createAddonSession({
          cloudProjectNumber: CLOUD_PROJECT_NUMBER,
        });
        const client = await session.createSidePanelClient();
        const info = await client.getMeetingInfo();
        if (!info.meetingId && !info.meetingCode) throw new Error("Google Meet 未提供 meeting context");
        setMeetingId(info.meetingId ?? info.meetingCode ?? null);
        setMeetingCode(info.meetingCode ?? null);
      } catch {
        if (!cancelled) {
          setMessage("無法取得會議 context，請從 Google Meet 的活動面板重新開啟 Proximate。");
        }
      }
    }
    void resolveMeeting();
    return () => {
      cancelled = true;
    };
  }, []);

  if (meetingId) return <AddonShell meetingId={meetingId} meetingCode={meetingCode ?? undefined} preview={preview} />;

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f7f7f5] p-6 text-center text-sm text-[#787774]">
      <p>{message}</p>
    </main>
  );
}

function loadMeetSdk() {
  return new Promise<void>((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(
      'script[src="https://www.gstatic.com/meetjs/addons/1.1.0/meet.addons.js"]',
    );
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("SDK 載入失敗")), { once: true });
      return;
    }
    const script = document.createElement("script");
    script.src = "https://www.gstatic.com/meetjs/addons/1.1.0/meet.addons.js";
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("SDK 載入失敗"));
    document.head.appendChild(script);
  });
}
