"use client";

import { IconRefresh, IconSearch, IconWifi } from "@tabler/icons-react";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { AppShell } from "../../../../components/app-shell";
import { MeetingWorkspaceHeader } from "../../../../components/meeting-workspace-header";
import {
  listSuggestions,
  voteSuggestion,
} from "../../../../lib/api/meeting-features";
import { getMeeting } from "../../../../lib/api/meetings";
import { searchMeetingMemory } from "../../../../lib/api/documents";
import {
  getMeetingBotStatus,
  joinMeetingBot,
  leaveMeetingBot,
} from "../../../../lib/api/meetbot";
import {
  getMeetingState,
  RealtimeEventAdapter,
} from "../../../../lib/api/realtime";
import {
  generateAndSpeakVoiceBot,
  getVoiceBotStatus,
  type VoiceBotStatusResponse,
} from "../../../../lib/api/voice";
import type {
  MeetingStateSnapshot,
  MeetingSummary,
  Suggestion,
  DocumentSearchResult,
} from "../../../../types/api";

function socketUrl(meetingId: string) {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const url = new URL(base);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `/api/v1/meetings/${meetingId}/events`;
  return url.toString();
}
function textList(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

export default function LivePage() {
  const { id } = useParams<{ id: string }>();
  const [meeting, setMeeting] = useState<MeetingSummary | null>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [snapshot, setSnapshot] = useState<MeetingStateSnapshot | null>(null);
  const [voiceStatus, setVoiceStatus] = useState<VoiceBotStatusResponse | null>(
    null,
  );
  const [speaking, setSpeaking] = useState(false);
  const [memoryQuery, setMemoryQuery] = useState("");
  const [memoryResults, setMemoryResults] = useState<DocumentSearchResult[]>([]);
  const [memoryLoading, setMemoryLoading] = useState(false);
  const [botId, setBotId] = useState<string | null>(null);
  const [botStatus, setBotStatus] = useState<string | null>(null);
  const [botLoading, setBotLoading] = useState(false);
  const [connection, setConnection] = useState<
    "connecting" | "connected" | "reconnecting" | "stale" | "offline"
  >("connecting");
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [error, setError] = useState("");
  const state = snapshot?.state ?? {};
  const meetingInProgress = Boolean(
    meeting &&
      meeting.status !== "completed" &&
      meeting.status !== "cancelled" &&
      (!meeting.scheduled_at || new Date(meeting.scheduled_at).getTime() <= Date.now()),
  );
  const currentTopic =
    typeof state.current_topic === "string"
      ? state.current_topic
      : typeof state.currentTopic === "string"
        ? state.currentTopic
        : "尚未設定目前議題";
  const questions = useMemo(
    () => textList(state.unresolved_questions ?? state.unresolvedQuestions),
    [state],
  );
  const decisions = useMemo(
    () => textList(state.provisional_decisions ?? state.provisionalDecisions),
    [state],
  );

  async function load() {
    const [meetingData, suggestionData, stateData, voiceData] =
      await Promise.all([
        getMeeting(id),
        listSuggestions(id),
        getMeetingState(id),
        getVoiceBotStatus(id),
      ]);
    setMeeting(meetingData);
    setSuggestions(suggestionData);
    setSnapshot(stateData);
    setVoiceStatus(voiceData);
  }
  useEffect(() => {
    let active = true;
    const adapter = new RealtimeEventAdapter();
    const loadTimer = window.setTimeout(() => {
      load().catch(
        (cause) =>
          active &&
          setError(cause instanceof Error ? cause.message : "無法讀取會議狀態。"),
      );
    }, 0);
    const socket = new WebSocket(socketUrl(id));
    const fallbackTimer = window.setInterval(() => {
      load().catch((cause) => {
        if (!active) return;
        setConnection((current) =>
          current === "connected" ? "stale" : current,
        );
        setError(cause instanceof Error ? cause.message : "無法更新會議狀態。");
      });
    }, 15000);
    socket.onopen = () => active && setConnection("connected");
    socket.onerror = () => active && setConnection("reconnecting");
    socket.onclose = () => active && setConnection("offline");
    socket.onmessage = (message) => {
      try {
        const event = adapter.accept(JSON.parse(message.data));
        if (!event || event.meeting_id !== id) return;
        if (event.cursor > 0 && socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: "ack", cursor: event.cursor }));
        }
        const payload =
          event.payload && typeof event.payload === "object"
            ? (event.payload as Record<string, unknown>)
            : {};
        setLastUpdated(event.timestamp);
        if (
          event.event_type === "voice_bot:status" ||
          payload.type === "voice_bot:status"
        ) {
          setVoiceStatus((current) => ({
            meeting_id: id,
            status:
              typeof payload.status === "string"
                ? payload.status
                : (current?.status ?? "not_requested"),
            request_id: current?.request_id ?? null,
            approved_text_version: current?.approved_text_version ?? null,
            message:
              typeof payload.message === "string" ? payload.message : null,
          }));
        }
        if (
          event.event_type === "meeting_state:update" ||
          event.event_type === "meeting_state:snapshot" ||
          payload.type === "meeting_state:update" ||
          payload.type === "meeting_state:snapshot"
        ) {
          const version =
            typeof payload.state_version === "number"
              ? payload.state_version
              : 0;
          const nextState =
            payload.state && typeof payload.state === "object"
              ? (payload.state as Record<string, unknown>)
              : {};
          setSnapshot((current) =>
            !current || version >= current.state_version
              ? {
                  meeting_id: id,
                  state_version: version,
                  state: nextState,
                  updated_at: event.timestamp,
                }
              : current,
          );
        }
        if (
          payload.type === "ai_suggestion:new" ||
          payload.type === "ai_suggestion:updated" ||
          event.event_type === "ai_suggestion:new" ||
          event.event_type === "ai_suggestion:updated"
        )
          void listSuggestions(id).then(setSuggestions);
      } catch {
        /* Ignore malformed realtime events; REST refresh remains available. */
      }
    };
    return () => {
      active = false;
      window.clearTimeout(loadTimer);
      window.clearInterval(fallbackTimer);
      socket.close();
    };
  }, [id]);
  useEffect(() => {
    if (!botId) return;
    let active = true;
    const refreshBotStatus = () => {
      getMeetingBotStatus(botId)
        .then((response) => active && setBotStatus(response.status))
        .catch(() => undefined);
    };
    refreshBotStatus();
    const timer = window.setInterval(refreshBotStatus, 5000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [botId]);
  async function vote(
    suggestionId: string,
    value: "support" | "reject" | "abstain",
  ) {
    try {
      await voteSuggestion(id, suggestionId, value);
      setSuggestions(await listSuggestions(id));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "投票失敗。 ");
    }
  }
  async function generateAndSpeak() {
    setSpeaking(true);
    setError("");
    try {
      const transcriptContext = textValue(
        state.latest_transcript ?? state.latestTranscript ?? state.transcript,
      );
      const ragContext = memoryResults.length
        ? memoryResults
            .map((result, index) => `[議前記憶 ${index + 1}] ${result.content}`)
            .join("\n")
        : null;
      const context = [transcriptContext && `[即時逐字稿] ${transcriptContext}`, ragContext]
        .filter(Boolean)
        .join("\n");
      const response = await generateAndSpeakVoiceBot(id, {
        prompt: `請針對目前議題「${currentTopic}」提出最重要的觀察與下一步。`,
        context: context || undefined,
      });
      setVoiceStatus(response);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Voice Bot 發言失敗。");
    } finally {
      setSpeaking(false);
    }
  }
  async function searchMeetingMemoryNow(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = memoryQuery.trim();
    if (!query) return;
    setMemoryLoading(true);
    setError("");
    try {
      setMemoryResults(await searchMeetingMemory(id, query));
    } catch (cause) {
      setMemoryResults([]);
      setError(cause instanceof Error ? cause.message : "查詢會議記憶失敗。");
    } finally {
      setMemoryLoading(false);
    }
  }
  async function startMeetingBot() {
    if (!meeting?.google_meeting_url || botLoading) return;
    setBotLoading(true);
    setError("");
    try {
      const response = await joinMeetingBot({
        meeting_url: meeting.google_meeting_url,
        meeting_id: id,
      });
      setBotId(response.bot_id ?? null);
      setBotStatus(response.status);
      if (response.text_card) {
        setError(
          response.text_card.reason === "audio_input_not_configured"
            ? "Meeting BaaS 尚未設定音訊輸入 URL，目前只能使用文字卡。"
            : "Meeting BaaS 目前無法加入，請稍後重試。",
        );
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Meeting BaaS Bot 啟動失敗。");
    } finally {
      setBotLoading(false);
    }
  }
  async function stopMeetingBot() {
    if (!botId || botLoading) return;
    setBotLoading(true);
    try {
      await leaveMeetingBot(botId);
      setBotStatus("leaving");
      setBotId(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Meeting BaaS Bot 離開失敗。");
    } finally {
      setBotLoading(false);
    }
  }
  return (
    <AppShell>
      <MeetingWorkspaceHeader phase="live" title={meeting?.title} />
      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#e6e6e3] bg-white px-4 py-3">
        <span className="inline-flex items-center gap-2 text-sm font-medium">
          <IconWifi
            size={17}
            className={
              connection === "connected" ? "text-[#0f9f8a]" : "text-[#b57a23]"
            }
          />
          {connection === "connected"
            ? "即時會議已連線"
            : connection === "connecting"
              ? "正在連線即時會議…"
              : connection === "reconnecting"
                ? "正在重新連線…"
                : connection === "stale"
                  ? "即時資料可能已過期"
                  : "即時連線暫時不可用"}
        </span>
        <span className="text-xs text-[#787774]" aria-live="polite">
          {lastUpdated
            ? `最後更新 ${new Date(lastUpdated).toLocaleTimeString("zh-TW")}`
            : "等待即時更新"}
        </span>
        <button
          type="button"
          onClick={() => void load()}
          className="inline-flex items-center gap-1 text-sm font-medium text-[#087e6d]"
        >
          <IconRefresh size={16} />
          重新整理
        </button>
      </div>
      {error && (
        <p
          role="alert"
          className="mt-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {error}
        </p>
      )}
      <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <main className="space-y-6">
          <section className="rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-6">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#0f9f8a]">
              目前討論
            </p>
            <h2 className="mt-2 text-2xl font-semibold">{currentTopic}</h2>
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <StateList
                title="尚未解決的問題"
                items={questions}
                empty="目前沒有待釐清問題。"
              />
              <StateList
                title="暫定決策"
                items={decisions}
                empty="尚未形成暫定決策。"
              />
            </div>
          </section>
          <section className="rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-6">
            <div className="flex items-center gap-2">
              <IconSearch size={19} className="text-[#0f9f8a]" />
              <div>
                <h2 className="text-lg font-semibold">查詢議前記憶</h2>
                <p className="mt-1 text-sm text-[#787774]">只搜尋本場會議已發布的議前文件。</p>
              </div>
            </div>
            <form onSubmit={searchMeetingMemoryNow} className="mt-4 flex gap-2">
              <input
                value={memoryQuery}
                onChange={(event) => setMemoryQuery(event.target.value)}
                className="control-primary min-w-0 flex-1"
                placeholder="例如：上線風險、決策依據"
                aria-label="查詢議前記憶"
              />
              <button type="submit" disabled={memoryLoading || !memoryQuery.trim()} className="rounded-lg bg-[#0f9f8a] px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
                {memoryLoading ? "搜尋中…" : "搜尋"}
              </button>
            </form>
            {memoryResults.length > 0 ? (
              <div className="mt-4 space-y-3">
                {memoryResults.map((result) => (
                  <article key={result.chunk_id} className="rounded-xl bg-[#f7f7f5] p-3">
                    <p className="text-xs font-medium text-[#087e6d]">{result.document_name}</p>
                    <p className="mt-1 text-sm leading-6 text-[#4f4f4b]">{result.content}</p>
                  </article>
                ))}
              </div>
            ) : memoryQuery && !memoryLoading ? (
              <p className="mt-4 text-sm text-[#787774]">找不到與此問題相關的議前內容。</p>
            ) : null}
          </section>
          <section className="rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-6">
            <h2 className="text-lg font-semibold">最新逐字稿</h2>
            <p className="mt-2 text-sm leading-6 text-[#787774]">
              {textValue(
                state.latest_transcript ??
                  state.latestTranscript ??
                  state.transcript,
              ) ?? "等待收音與逐字稿事件。"}
            </p>
          </section>
          <section className="rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-6">
            <div>
              <h2 className="text-lg font-semibold">AI 舉手</h2>
              <p className="mt-1 text-sm text-[#787774]">
                AI 先提出文字卡，由成員決定支持、稍後或忽略；不會自行插話。
              </p>
            </div>
            <div className="mt-5 space-y-3">
              {suggestions.map((suggestion) => (
                <article
                  key={suggestion.id}
                  className="rounded-xl border border-[#ededeb] p-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="font-medium">{suggestion.title}</h3>
                      <p className="mt-2 text-sm leading-6 text-[#787774]">
                        {suggestion.content}
                      </p>
                    </div>
                    {suggestion.confidence !== null && (
                      <span className="rounded-full bg-[#f7f7f5] px-2 py-1 text-xs text-[#787774]">
                        信心 {Math.round(suggestion.confidence * 100)}%
                      </span>
                    )}
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      onClick={() => void vote(suggestion.id, "support")}
                      className="rounded-lg bg-[#0f9f8a] px-3 py-2 text-xs font-semibold text-white"
                    >
                      支持發言
                    </button>
                    <button
                      onClick={() => void vote(suggestion.id, "abstain")}
                      className="rounded-lg border border-[#dededb] px-3 py-2 text-xs font-medium"
                    >
                      稍後
                    </button>
                    <button
                      onClick={() => void vote(suggestion.id, "reject")}
                      className="rounded-lg px-3 py-2 text-xs font-medium text-[#787774] hover:bg-[#f7f7f5]"
                    >
                      忽略
                    </button>
                  </div>
                </article>
              ))}
              {suggestions.length === 0 && (
                <div className="rounded-xl border border-dashed border-[#d8d8d5] p-8 text-center text-sm text-[#787774]">
                  目前沒有待處理的 AI 舉手。
                </div>
              )}
            </div>
          </section>
        </main>
        <aside className="space-y-5">
          <section className="rounded-2xl border border-[#e6e6e3] bg-white p-5">
            <h2 className="font-semibold">會議狀態</h2>
            <p className="mt-2 text-sm text-[#787774]">
              {meetingInProgress
                ? "會議進行中"
                : "尚未開始或已結束"}
            </p>
            <p className="mt-3 text-xs text-[#787774]">
              狀態版本 {snapshot?.state_version ?? 0}
            </p>
          </section>
          <VoiceBotStatus
            value={voiceStatus?.status ?? state.voice_bot ?? state.voiceBot}
          />
          <section className="rounded-2xl border border-[#e6e6e3] bg-white p-5">
            <h2 className="font-semibold">Meeting BaaS Bot</h2>
            <p className="mt-2 text-sm text-[#787774]">
              {botStatus
                ? `目前狀態：${botStatus}`
                : meeting?.google_meeting_url
                  ? "尚未加入這場 Google Meet。"
                  : "這場會議尚未設定 Google Meet 連結。"}
            </p>
            {botId ? (
              <button type="button" onClick={() => void stopMeetingBot()} disabled={botLoading} className="mt-4 w-full rounded-lg border border-red-200 px-3 py-2 text-sm font-semibold text-red-700 disabled:opacity-50">
                {botLoading ? "處理中…" : "讓 Bot 離開會議"}
              </button>
            ) : (
              <button type="button" onClick={() => void startMeetingBot()} disabled={botLoading || !meeting?.google_meeting_url} className="mt-4 w-full rounded-lg bg-[#0f9f8a] px-3 py-2 text-sm font-semibold text-white disabled:opacity-50">
                {botLoading ? "正在加入…" : "讓 Bot 加入會議"}
              </button>
            )}
          </section>
          <section className="rounded-2xl border border-[#e6e6e3] bg-white p-5">
            <h2 className="font-semibold">AI 語音發言</h2>
            <p className="mt-2 text-sm leading-6 text-[#787774]">
              需先由 Host 核准，接著由 Gemini 產生發言稿，再轉成語音送入會議。
            </p>
            <button
              type="button"
              disabled={speaking || voiceStatus?.status !== "approved"}
              onClick={() => void generateAndSpeak()}
              className="mt-4 w-full rounded-lg bg-[#0f9f8a] px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              {speaking ? "正在準備並播放…" : "生成文字並發言"}
            </button>
          </section>
        </aside>
      </div>
    </AppShell>
  );
}
function textValue(value: unknown) {
  return typeof value === "string" && value.trim() ? value : null;
}
function VoiceBotStatus({ value }: { value: unknown }) {
  const key = typeof value === "string" ? value : "not_requested";
  const labels: Record<string, string> = {
    not_requested: "尚未請求發言",
    waiting_for_votes: "等待成員投票",
    threshold_reached: "已達投票門檻",
    waiting_for_host: "等待 Host 核准",
    approved: "已核准，準備發言",
    preparing_audio: "正在準備音訊",
    speaking: "Voice Bot 發言中",
    completed: "發言已完成",
    failed: "發言失敗，可改用文字卡",
    fallback_text: "已回退為公開文字卡",
  };
  const active = key === "speaking" || key === "preparing_audio";
  return (
    <section
      className="rounded-2xl border border-[#e6e6e3] bg-white p-5"
      aria-live="polite"
    >
      <h2 className="font-semibold">Voice Bot 狀態</h2>
      <p className="mt-2 text-sm text-[#787774]">{labels[key] ?? key}</p>
      {active ? (
        <p className="mt-2 text-xs text-[#087e6d]">正在處理中…</p>
      ) : null}
    </section>
  );
}
function StateList({
  title,
  items,
  empty,
}: {
  title: string;
  items: string[];
  empty: string;
}) {
  return (
    <section className="rounded-xl bg-[#f7f7f5] p-4">
      <h3 className="text-sm font-semibold">{title}</h3>
      {items.length ? (
        <ul className="mt-3 space-y-2 text-sm text-[#5f5f5b]">
          {items.map((item, index) => (
            <li key={`${item}-${index}`} className="flex gap-2">
              <span className="text-[#0f9f8a]">•</span>
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-[#787774]">{empty}</p>
      )}
    </section>
  );
}
