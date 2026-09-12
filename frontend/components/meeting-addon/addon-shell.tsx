"use client";

import {
  IconAlertTriangle,
  IconCircleCheck,
  IconLoader2,
  IconRefresh,
} from "@tabler/icons-react";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { getLiveSnapshot } from "../../lib/api/addon";
import { listAgendaItems } from "../../lib/api/agenda";
import { listDocumentChunks, listDocuments } from "../../lib/api/documents";
import { getMeetingByGoogleId } from "../../lib/api/meetings";
import {
  previewContribution,
  publishContribution,
} from "../../lib/api/meeting-features";
import {
  createPreparationMessage,
  listPreparationMessages,
} from "../../lib/api/preparation";
import type {
  LiveSnapshotResponse,
  MeetingSummary,
  PreparationMessage,
  AgendaItem,
} from "../../types/api";
import { LiveStateTab } from "./live-state";

type Tab = "brief" | "live" | "sidekick";
type Status = "loading" | "connected" | "unauthorized" | "unbound" | "error";
const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function AddonShell({
  meetingId,
  meetingCode,
  preview = false,
}: {
  meetingId: string;
  meetingCode?: string;
  preview?: boolean;
}) {
  const embedded = useSyncExternalStore(
    noopSubscribe,
    getEmbeddedSnapshot,
    getStandaloneSnapshot,
  );
  const [tab, setTab] = useState<Tab>(preview ? "live" : "brief");
  const [status, setStatus] = useState<Status>(
    preview ? "connected" : "loading",
  );
  const [meeting, setMeeting] = useState<MeetingSummary | null>(
    preview ? previewMeeting(meetingId) : null,
  );
  const [snapshot, setSnapshot] = useState<LiveSnapshotResponse | null>(
    preview ? previewSnapshot : null,
  );
  const [errorMessage, setErrorMessage] = useState("");
  const [apiMeetingId, setApiMeetingId] = useState<string | null>(null);
  const [agenda, setAgenda] = useState<AgendaItem[]>([]);
  const [sharedDocuments, setSharedDocuments] = useState<string[]>([]);
  const hasLoadedRef = useRef(preview);
  const loadContext = useCallback(async () => {
    if (preview) return;
    // Polling refreshes data in the background. Keep the existing panel visible
    // instead of flashing the whole Add-on back to a loading skeleton.
    if (!hasLoadedRef.current) setStatus("loading");
    setErrorMessage("");
    try {
      const identifiers = uuidPattern.test(meetingId)
        ? [meetingId]
        : [meetingId, meetingCode].filter((value): value is string => Boolean(value));
      let appMeetingId: string | null = null;
      for (const identifier of identifiers) {
        try {
          appMeetingId = uuidPattern.test(identifier)
            ? identifier
            : (await getMeetingByGoogleId(identifier)).id;
          break;
        } catch (error) {
          const apiError = error as { status?: number };
          if (apiError.status !== 404) throw error;
        }
      }
      if (!appMeetingId) {
        setStatus("unbound");
        setErrorMessage("這個 Google Meet 尚未綁定 Proximate 會議。");
        return;
      }
      setApiMeetingId(appMeetingId);
      const snapshotResponse = await getLiveSnapshot(appMeetingId);
      const agendaResponse = await listAgendaItems(appMeetingId);
      const publishedDocuments = snapshotResponse.meeting
        ? await listDocuments(snapshotResponse.meeting.team_id, { scope: "meeting", meeting_id: appMeetingId })
        : [];
      const documentContents = await Promise.all(publishedDocuments.map(async (document) => {
        const chunks = await listDocumentChunks(document.id);
        return chunks.sort((a, b) => a.position - b.position).map((chunk) => chunk.content).join("\n\n");
      }));
      setMeeting(snapshotResponse.meeting ?? null);
      setSnapshot(snapshotResponse);
      setAgenda(agendaResponse.items);
      setSharedDocuments(documentContents.filter((content) => content.trim()));
      hasLoadedRef.current = true;
      setStatus("connected");
    } catch (error) {
      const apiError = error as { status?: number; message?: string };
      if (hasLoadedRef.current) {
        // A transient refresh failure should not interrupt an otherwise usable
        // meeting panel. The next interval or manual refresh can recover it.
        return;
      }
      setStatus(apiError.status === 401 || apiError.status === 403 ? "unauthorized" : "error");
      setErrorMessage(apiError.message ?? "無法載入會議資料。");
    }
  }, [meetingCode, meetingId, preview]);

  useEffect(() => {
    if (preview) return;
    void Promise.resolve().then(loadContext);
    const timer = window.setInterval(() => void loadContext(), 5000);
    return () => window.clearInterval(timer);
  }, [loadContext, preview]);

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "brief", label: "Brief" },
    { id: "live", label: "Live State" },
    { id: "sidekick", label: "Sidekick" },
  ];

  return (
    <main
      className={`addon-preview-root ${embedded ? "is-embedded" : "is-standalone"} min-h-screen overflow-x-hidden text-[#1f1f1f]`}
    >
      <div className="addon-panel-shell">
        <header className="flex items-center justify-between gap-3 border-b border-[#e9e9e6] px-[clamp(12px,3vw,20px)] py-3">
          <div className="min-w-0">
            <p className="text-sm font-semibold">
              Proximate{" "}
              {preview ? (
                <span className="ml-1 text-[10px] font-normal text-[#8b8b87]">
                  Preview
                </span>
              ) : null}
            </p>
            <p className="truncate text-xs text-[#8b8b87]">
              {meeting?.title ?? "正在載入會議資料"}
            </p>
          </div>
          <ConnectionStatus status={status} />
        </header>
        <div className="border-b border-[#e9e9e6] px-3 py-2">
          <div
            role="tablist"
            aria-label="會議面板"
            className="flex gap-1 overflow-x-auto"
          >
            {tabs.map((item) => (
              <button
                key={item.id}
                type="button"
                role="tab"
                aria-selected={tab === item.id}
                onClick={() => setTab(item.id)}
                className={`shrink-0 rounded-lg px-3 py-2 text-xs font-medium transition ${tab === item.id ? "bg-[#e7f7ef] text-[#1d6b4d]" : "text-[#787774] hover:bg-[#f7f7f5]"}`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
        <div className="addon-panel-content min-h-0 flex-1 overflow-y-auto p-[clamp(12px,3vw,20px)]">
          {status === "loading" ? (
            <LoadingState />
          ) : status === "unbound" ? (
            <StateMessage
              title="尚未綁定 Proximate 會議"
              description={`Google Meet 提供了永久 space ID${meetingCode ? `與會議代碼「${meetingCode}」` : ""}，但找不到對應的 Proximate 會議。請在 Proximate 的「開始會議」頁儲存同一個 Google Meet 連結後，再回到此面板重新連線。`}
              action={
                <a href="/dashboard" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-[#dededb] px-3 py-2 text-xs font-semibold">
                  開啟 Proximate Web App
                </a>
              }
            />
          ) : status === "unauthorized" ? (
            <StateMessage
              title="需要重新登入"
              description="此 Add-on 沒有有效的 Proximate 登入狀態。請先在同一個網站登入 Proximate，再重新開啟會議。"
              action={<a href="/sign-in" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-[#dededb] px-3 py-2 text-xs font-semibold">登入 Proximate</a>}
            />
          ) : status === "error" ? (
            <StateMessage
              title="無法連線至會議"
              description={errorMessage}
              action={
                <button
                  type="button"
                  onClick={() => void loadContext()}
                  className="inline-flex items-center gap-2 rounded-lg border border-[#dededb] px-3 py-2 text-xs font-semibold"
                >
                  <IconRefresh size={15} />
                  重新連線
                </button>
              }
            />
          ) : (
            <TabContent
              tab={tab}
              meetingId={apiMeetingId ?? meetingId}
              meeting={meeting}
              snapshot={snapshot}
              agenda={agenda}
              sharedDocuments={sharedDocuments}
            />
          )}
        </div>
      </div>
    </main>
  );
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
  suggestions: [
    {
      id: "preview-suggestion",
      title: "Proximate 想發言",
      body: "這個門檻可能會讓少數觀點被忽略。是否要保留少數意見提醒？",
      support_count: 4,
      participant_count: 6,
      threshold_percent: 75,
    },
  ],
  policy: { intervention_level: "medium" },
};

function previewMeeting(meetingId: string): MeetingSummary {
  return {
    id: meetingId,
    team_id: "preview-team",
    title: "MVP 共識會議",
    scheduled_at: null,
    preparation_deadline: null,
    google_meeting_id: null,
    google_meeting_url: null,
    status: "in_progress",
    ai_intervention_level: "medium",
  };
}

function noopSubscribe() {
  return () => undefined;
}
function getEmbeddedSnapshot() {
  return typeof window !== "undefined" && window.self !== window.top;
}
function getStandaloneSnapshot() {
  return false;
}

function ConnectionStatus({ status }: { status: Status }) {
  if (status === "loading")
    return (
      <span className="inline-flex items-center gap-1 text-xs text-[#8b8b87]">
        <IconLoader2 size={13} className="animate-spin" />
        載入中
      </span>
    );
  if (status === "connected")
    return (
      <span className="inline-flex items-center gap-1 text-xs text-[#0f9f8a]">
        <IconCircleCheck size={14} />
        已連線
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 text-xs text-[#b42318]">
      <IconAlertTriangle size={14} />
      連線異常
    </span>
  );
}

function TabContent({
  tab,
  meetingId,
  meeting,
  snapshot,
  agenda,
  sharedDocuments,
}: {
  tab: Tab;
  meetingId: string;
  meeting: MeetingSummary | null;
  snapshot: LiveSnapshotResponse | null;
  agenda: AgendaItem[];
  sharedDocuments: string[];
}) {
  if (tab === "brief")
    return (
      <section>
        <p className="text-xs font-semibold uppercase tracking-wide text-[#8b8b87]">
          會議 Brief
        </p>
        <h1 className="mt-2 text-lg font-semibold">
          {meeting?.title ?? "目前會議"}
        </h1>
        <p className="mt-3 text-sm leading-6 text-[#787774]">
          正式會議資料已載入。Brief 詳細內容將由後續正式 API 欄位提供。
        </p>
        <InfoCard label="會議狀態" value={meeting?.status ?? "未知"} />
        <InfoCard
          label="目前議題"
          value={
            agenda.length ? (
              <div className="mt-2 space-y-2">
                {agenda.map((item) => (
                  <div key={item.id} className="rounded-lg bg-white px-3 py-2 leading-5">
                    <span className="mr-1 text-[#0f9f8a]">{item.position}.</span>
                    {item.title}
                  </div>
                ))}
              </div>
            ) : "尚未設定公開議題"
          }
        />
        <InfoCard
          label="團隊共識文件"
          value={
            sharedDocuments.length ? (
              <div className="mt-2 space-y-3">
                {sharedDocuments.map((content, index) => (
                  <div key={`${index}-${content.slice(0, 20)}`} className="whitespace-pre-wrap break-words rounded-lg bg-white px-3 py-2 leading-5">
                    {content}
                  </div>
                ))}
              </div>
            ) : "尚未發布團隊共識"
          }
        />
      </section>
    );
  if (tab === "live")
    return (
      <LiveStateTab
        meetingId={meetingId}
        meeting={meeting}
        snapshot={snapshot}
      />
    );
  return <SidekickTab meetingId={meetingId} />;
}

function SidekickTab({ meetingId }: { meetingId: string }) {
  const [messages, setMessages] = useState<PreparationMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [preview, setPreview] = useState("");
  const [notice, setNotice] = useState("");
  const [sending, setSending] = useState(false);
  useEffect(() => {
    listPreparationMessages(meetingId).then(setMessages).catch(() => undefined);
  }, [meetingId]);
  async function send() {
    const content = draft.trim();
    if (!content || sending) return;
    setSending(true);
    try {
      const response = await createPreparationMessage(meetingId, content);
      setMessages((current) => [...current, ...response.filter((item) => !current.some((existing) => existing.id === item.id))]);
      setDraft("");
      setNotice("");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "訊息送出失敗");
    } finally {
      setSending(false);
    }
  }
  async function previewAndPublish() {
    if (!draft.trim()) return;
    try {
      await previewContribution(meetingId, draft.trim());
      setPreview(draft.trim());
      setNotice("已產生公開內容預覽");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "預覽失敗");
    }
  }
  const prompts = ["幫我釐清目前最重要的問題", "有哪些風險或反例？", "幫我整理成可以提出的觀點"];
  return <section><h2 className="text-lg font-semibold">Personal Sidekick</h2><p className="mt-2 text-xs text-[#787774]">只有你看得到，會中可隨時和私人 Agent 討論，不會自動公開。</p><div className="mt-4 max-h-64 space-y-3 overflow-y-auto">{messages.length ? messages.map((message) => <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}><div className={`max-w-[90%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-sm leading-6 ${message.role === "user" ? "rounded-br-md bg-[#0f9f8a] text-white" : "rounded-bl-md bg-[#f7f7f5] text-[#2f5446]"}`}>{message.content}</div></div>) : <p className="rounded-xl border border-dashed border-[#d8d8d5] p-4 text-sm text-[#787774]">先從一個問題開始，Agent 會協助你整理假設、風險與可提出的觀點。</p>}{sending && <p className="text-xs text-[#787774]">Agent 正在整理想法…</p>}</div><div className="mt-4 flex gap-2 overflow-x-auto pb-1">{prompts.map((prompt) => <button key={prompt} type="button" onClick={() => setDraft(prompt)} className="shrink-0 rounded-full border border-[#d7e8e5] px-3 py-1.5 text-[11px] text-[#087e6d]">{prompt}</button>)}</div><textarea value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void send(); } }} className="control-primary mt-3 min-h-20 w-full" placeholder="和 Agent 討論一個問題…" aria-label="Sidekick 訊息" /><div className="mt-2 flex flex-wrap gap-2"><button type="button" disabled={!draft.trim() || sending} onClick={() => void send()} className="rounded-lg bg-[#0f9f8a] px-3 py-2 text-xs font-semibold text-white disabled:opacity-40">{sending ? "整理中…" : "送出訊息"}</button><button type="button" disabled={!draft.trim() || sending} onClick={() => void previewAndPublish()} className="rounded-lg border border-[#dededb] px-3 py-2 text-xs font-semibold disabled:opacity-40">預覽發布</button></div>{preview && <div className="mt-4 rounded-xl border border-[#b9e9cc] bg-[#effbf4] p-3 text-sm"><p className="text-xs font-semibold text-[#087f5b]">公開內容預覽</p><p className="mt-2">{preview}</p><button type="button" onClick={() => publishContribution(meetingId, preview).then(() => { setNotice("內容已發布"); setPreview(""); }).catch(() => setNotice("發布失敗"))} className="mt-3 rounded-lg bg-[#0f9f8a] px-3 py-2 text-xs font-semibold text-white">確認提出觀點</button></div>}{notice && <p role="status" className="mt-3 text-xs text-[#787774]">{notice}</p>}</section>;
}

function InfoCard({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="mt-5 rounded-xl bg-[#f7f7f5] p-4">
      <p className="text-xs text-[#8b8b87]">{label}</p>
      <div className="mt-1 text-sm font-medium">{value}</div>
    </div>
  );
}
function LoadingState() {
  return (
    <div className="space-y-4" aria-label="載入會議資料">
      <div className="flex items-center gap-2 text-sm text-[#787774]">
        <IconLoader2 size={17} className="animate-spin" />
        正在載入會議 context…
      </div>
      <div className="h-28 animate-pulse rounded-xl bg-[#f7f7f5]" />
      <div className="h-20 animate-pulse rounded-xl bg-[#f7f7f5]" />
    </div>
  );
}
function StateMessage({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <section className="rounded-xl border border-dashed border-[#d8d8d5] p-6 text-center">
      <h2 className="font-semibold">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-[#787774]">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </section>
  );
}
