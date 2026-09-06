"use client";

import { useEffect, useState } from "react";

const CLOUD_PROJECT_NUMBER = "446517015863";

type MeetClient = {
  getMeetingInfo: () => Promise<{ meetingId?: string }>;
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

  useEffect(() => {
    const meetingId = new URLSearchParams(window.location.search).get("meetingId");
    if (meetingId) {
      window.location.replace(`/meetings/${encodeURIComponent(meetingId)}/addon`);
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
        if (!info.meetingId) throw new Error("Google Meet 未提供 meeting ID");
        window.location.replace(`/meetings/${encodeURIComponent(info.meetingId)}/addon`);
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
