"use client";

import { IconAlertTriangle, IconCircleCheck, IconLoader2, IconLock, IconRefresh } from "@tabler/icons-react";
import { useCallback, useEffect, useState, useSyncExternalStore, type ReactNode } from "react";
import { getCurrentUser } from "../../lib/api/me";
import { createMeetingAccessToken, getLiveSnapshot } from "../../lib/api/addon";
import { getMeeting } from "../../lib/api/meetings";
import type { LiveSnapshotResponse, MeetingSummary, UserResponse } from "../../types/api";
import { HostControlsTab, LiveStateTab } from "./live-state";

type Tab = "brief" | "live" | "sidekick" | "host";
type Status = "loading" | "connected" | "unauthorized" | "error";

export function AddonShell({ meetingId, preview = false }: { meetingId: string; preview?: boolean }) {
  const embedded = useSyncExternalStore(noopSubscribe, getEmbeddedSnapshot, getStandaloneSnapshot);
  const [tab, setTab] = useState<Tab>(preview ? "live" : "brief");
  const [status, setStatus] = useState<Status>(preview ? "connected" : "loading");
  const [meeting, setMeeting] = useState<MeetingSummary | null>(preview ? previewMeeting(meetingId) : null);
  const [snapshot, setSnapshot] = useState<LiveSnapshotResponse | null>(preview ? previewSnapshot : null);
  const [isHost, setIsHost] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const loadContext = useCallback(async () => {
    if (preview) return;
    setStatus("loading");
    setErrorMessage("");
    try {
      const [meetingResponse, snapshotResponse, userResponse] = await Promise.all([
        getMeeting(meetingId),
        getLiveSnapshot(meetingId),
        getCurrentUser(),
      ]);
      await createMeetingAccessToken(meetingId);
      setMeeting(meetingResponse);
      setSnapshot(snapshotResponse);
      setIsHost(hasHostRole(userResponse));
      setStatus("connected");
    } catch (error) {
      const apiError = error as { status?: number; message?: string };
      setStatus(apiError.status === 401 || apiError.status === 403 ? "unauthorized" : "error");
      setErrorMessage(apiError.message ?? "無法載入會議資料。");
    }
  }, [meetingId, preview]);

  useEffect(() => {
    if (preview) return;
    void Promise.resolve().then(loadContext);
  }, [loadContext, preview]);

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "brief", label: "Brief" },
    { id: "live", label: "Live State" },
    { id: "sidekick", label: "Sidekick" },
    ...(isHost ? [{ id: "host" as const, label: "Host Controls" }] : []),
  ];

  return <main className={`addon-preview-root ${embedded ? "is-embedded" : "is-standalone"} min-h-screen overflow-x-hidden text-[#1f1f1f]`}><div className="addon-panel-shell"><header className="flex items-center justify-between gap-3 border-b border-[#e9e9e6] px-[clamp(12px,3vw,20px)] py-3"><div className="min-w-0"><p className="text-sm font-semibold">Proximate {preview ? <span className="ml-1 text-[10px] font-normal text-[#8b8b87]">Preview</span> : null}</p><p className="truncate text-xs text-[#8b8b87]">{meeting?.title ?? `Meeting #${meetingId}`}</p></div><ConnectionStatus status={status} /></header><div className="border-b border-[#e9e9e6] px-3 py-2"><div role="tablist" aria-label="會議面板" className="flex gap-1 overflow-x-auto">{tabs.map((item) => <button key={item.id} type="button" role="tab" aria-selected={tab === item.id} onClick={() => setTab(item.id)} className={`shrink-0 rounded-lg px-3 py-2 text-xs font-medium transition ${tab === item.id ? "bg-[#e7f7ef] text-[#1d6b4d]" : "text-[#787774] hover:bg-[#f7f7f5]"}`}>{item.label}</button>)}</div></div><div className="addon-panel-content min-h-0 flex-1 overflow-y-auto p-[clamp(12px,3vw,20px)]">{status === "loading" ? <LoadingState /> : status === "unauthorized" ? <StateMessage title="需要重新開啟會議" description="此 Add-on 沒有有效的會議權限，請從已登入的 Web App 重新開啟。" /> : status === "error" ? <StateMessage title="無法連線至會議" description={errorMessage} action={<button type="button" onClick={() => void loadContext()} className="inline-flex items-center gap-2 rounded-lg border border-[#dededb] px-3 py-2 text-xs font-semibold"><IconRefresh size={15} />重新連線</button>} /> : <TabContent tab={tab} meetingId={meetingId} meeting={meeting} snapshot={snapshot} />}</div></div></main>;
}

const previewSnapshot: LiveSnapshotResponse = {
  state: {
    current_topic: "確認 MVP 的發言與共識機制",
    positions: ["希望保留少數意見提醒", "擔心 AI 發言打斷討論節奏"],
    unresolved_questions: ["達到多少支持比例才讓 Proximate 發言？"],
    provisional_decisions: ["先以文字卡驗證流程，再接 Voice Bot"],
    parking_lot: ["Google Meet Add-on development deployment"],
    voice_bot: "等待團隊決定是否發言",
  },
  suggestions: [{ id: "preview-suggestion", title: "Proximate 想發言", body: "這個門檻可能會讓少數觀點被忽略。是否要保留少數意見提醒？", support_count: 4, participant_count: 6, threshold_percent: 75 }],
  policy: { intervention_level: "medium" },
};

function previewMeeting(meetingId: string): MeetingSummary { return { id: meetingId, team_id: "preview-team", title: "MVP 共識會議", scheduled_at: null, status: "in_progress", ai_intervention_level: "medium" }; }

function noopSubscribe() { return () => undefined; }
function getEmbeddedSnapshot() { return typeof window !== "undefined" && window.self !== window.top; }
function getStandaloneSnapshot() { return false; }

function ConnectionStatus({ status }: { status: Status }) {
  if (status === "loading") return <span className="inline-flex items-center gap-1 text-xs text-[#8b8b87]"><IconLoader2 size={13} className="animate-spin" />載入中</span>;
  if (status === "connected") return <span className="inline-flex items-center gap-1 text-xs text-[#0f9f8a]"><IconCircleCheck size={14} />已連線</span>;
  return <span className="inline-flex items-center gap-1 text-xs text-[#b42318]"><IconAlertTriangle size={14} />連線異常</span>;
}

function TabContent({ tab, meetingId, meeting, snapshot }: { tab: Tab; meetingId: string; meeting: MeetingSummary | null; snapshot: LiveSnapshotResponse | null }) {
  if (tab === "brief") return <section><p className="text-xs font-semibold uppercase tracking-wide text-[#8b8b87]">會議 Brief</p><h1 className="mt-2 text-lg font-semibold">{meeting?.title ?? "目前會議"}</h1><p className="mt-3 text-sm leading-6 text-[#787774]">正式會議資料已載入。Brief 詳細內容將由後續正式 API 欄位提供。</p><InfoCard label="會議狀態" value={meeting?.status ?? "未知"} /></section>;
  if (tab === "live") return <LiveStateTab meetingId={meetingId} meeting={meeting} snapshot={snapshot} />;
  if (tab === "host") return <HostControlsTab meetingId={meetingId} snapshot={snapshot} />;
  return <section><div className="flex items-center gap-2"><h2 className="text-lg font-semibold">Personal Sidekick</h2><IconLock size={14} className="text-[#8b8b87]" /></div><p className="mt-2 text-xs text-[#787774]">僅你可見</p><div className="mt-5 rounded-xl border border-dashed border-[#d8d8d5] p-5 text-sm text-[#787774]">私人對話區域已保留，正式 Sidekick API 將在後續工作接入。</div></section>;
}

function InfoCard({ label, value }: { label: string; value: string }) { return <div className="mt-5 rounded-xl bg-[#f7f7f5] p-4"><p className="text-xs text-[#8b8b87]">{label}</p><p className="mt-1 text-sm font-medium">{value}</p></div>; }
function LoadingState() { return <div className="space-y-4" aria-label="載入會議資料"><div className="flex items-center gap-2 text-sm text-[#787774]"><IconLoader2 size={17} className="animate-spin" />正在載入會議 context…</div><div className="h-28 animate-pulse rounded-xl bg-[#f7f7f5]" /><div className="h-20 animate-pulse rounded-xl bg-[#f7f7f5]" /></div>; }
function StateMessage({ title, description, action }: { title: string; description: string; action?: ReactNode }) { return <section className="rounded-xl border border-dashed border-[#d8d8d5] p-6 text-center"><h2 className="font-semibold">{title}</h2><p className="mt-2 text-sm leading-6 text-[#787774]">{description}</p>{action ? <div className="mt-4">{action}</div> : null}</section>; }

function hasHostRole(user: UserResponse) {
  const claims = user.claims;
  if (!claims || typeof claims !== "object") return false;
  const role = (claims as { role?: unknown; roles?: unknown }).role;
  const roles = (claims as { roles?: unknown }).roles;
  const values = Array.isArray(roles) ? roles : [role];
  return values.some((value) => typeof value === "string" && ["host", "owner", "admin"].includes(value.toLowerCase()));
}
