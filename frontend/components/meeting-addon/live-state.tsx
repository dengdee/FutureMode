"use client";

import { IconCheck, IconLoader2, IconPlayerPause, IconRobot, IconVolume } from "@tabler/icons-react";
import { useState } from "react";
import { updateInterventionPolicy, voteOnSuggestion } from "../../lib/api/addon";
import type { LiveSnapshotResponse, MeetingSummary, VoteChoice } from "../../types/api";

export function LiveStateTab({ meetingId, meeting, snapshot }: { meetingId: string; meeting: MeetingSummary | null; snapshot: LiveSnapshotResponse | null }) {
  const state = snapshot?.state ?? {};
  const suggestions = Array.isArray(snapshot?.suggestions) ? snapshot.suggestions : [];
  const currentTopic = textValue(state.current_topic ?? state.currentTopic) ?? "目前尚未有公開議題";
  const positions = stringList(state.positions);
  const questions = stringList(state.unresolved_questions ?? state.unresolvedQuestions);
  const decisions = stringList(state.provisional_decisions ?? state.provisionalDecisions);
  const parkingLot = stringList(state.parking_lot ?? state.parkingLot);

  return <div className="space-y-4"><div aria-live="polite">{suggestions.length ? <div className="space-y-3">{suggestions.map((suggestion) => <AiSuggestionCard key={String(suggestion.id ?? suggestion.suggestion_id)} meetingId={meetingId} suggestion={suggestion} prominent showRaiseHeader />)}</div> : <section className="rounded-xl border-2 border-[#8bd3b2] bg-[#effbf4] p-4 text-sm text-[#5d806f] shadow-[0_4px_16px_rgba(15,159,138,0.12)]">目前沒有待處理的 AI 舉手。</section>}</div><section className="rounded-xl bg-[#f7f7f5] p-4"><p className="text-xs font-semibold uppercase tracking-wide text-[#8b8b87]">目前議題</p><h2 className="mt-2 font-semibold">{currentTopic}</h2><p className="mt-2 text-sm text-[#787774]">{meeting?.status ? `會議狀態：${meeting.status}` : "等待正式會議狀態資料"}</p></section><DataSection title="目前立場" items={positions} empty="尚未收到公開立場" /><DataSection title="未決問題" items={questions} empty="尚未收到未決問題" /><DataSection title="暫定決策" items={decisions} empty="尚未形成暫定決策" /><ParkingLot items={parkingLot} /><VoiceBotStatus value={state.voice_bot ?? state.voiceBot} /></div>;
}

export function HostControlsTab({ meetingId, snapshot }: { meetingId: string; snapshot: LiveSnapshotResponse | null }) {
  const rawLevel = snapshot?.policy?.intervention_level ?? snapshot?.policy?.interventionLevel;
  const [level, setLevel] = useState(typeof rawLevel === "string" ? rawLevel : "medium");
  const [pending, setPending] = useState(false);
  const [feedback, setFeedback] = useState("");
  async function savePolicy() {
    setPending(true); setFeedback("");
    try { await updateInterventionPolicy(meetingId, { intervention_level: level }); setFeedback("政策已更新"); }
    catch (error) { setFeedback((error as { message?: string }).message ?? "政策更新失敗"); }
    finally { setPending(false); }
  }
  return <section className="space-y-5"><div><p className="text-xs font-semibold uppercase tracking-wide text-[#8b8b87]">主持控制</p><h2 className="mt-2 text-lg font-semibold">介入政策</h2><p className="mt-2 text-sm leading-6 text-[#787774]">調整後會套用至本場會議；不會改寫已產生的公共紀錄。</p></div><label className="block text-sm font-medium">AI 介入程度<select value={level} onChange={(event) => setLevel(event.target.value)} className="control-primary mt-2"><option value="low">低</option><option value="medium">中</option><option value="high">高</option></select></label><button type="button" disabled={pending} onClick={() => void savePolicy()} className="inline-flex items-center gap-2 rounded-lg bg-[#0f9f8a] px-3 py-2 text-sm font-semibold text-white disabled:opacity-50">{pending ? <IconLoader2 size={15} className="animate-spin" /> : <IconCheck size={15} />}儲存政策</button>{feedback ? <p role="status" className="text-sm text-[#787774]">{feedback}</p> : null}<div className="rounded-xl border border-[#e6e6e3] p-4"><div className="flex items-center gap-2"><IconPlayerPause size={16} className="text-[#787774]" /><h3 className="text-sm font-semibold">暫停 AI 介入</h3></div><p className="mt-2 text-sm text-[#787774]">暫停／恢復操作將在正式 Host action API 提供後啟用。</p></div></section>;
}

function AiSuggestionCard({ meetingId, suggestion, prominent = false, showRaiseHeader = false }: { meetingId: string; suggestion: Record<string, unknown>; prominent?: boolean; showRaiseHeader?: boolean }) {
  const suggestionId = String(suggestion.id ?? suggestion.suggestion_id ?? "");
  const [choice, setChoice] = useState<VoteChoice | null>(asVote(suggestion.my_vote ?? suggestion.vote));
  const [pending, setPending] = useState(false);
  const [feedback, setFeedback] = useState("");
  const support = numberValue(suggestion.support_count ?? suggestion.supportCount);
  const total = numberValue(suggestion.participant_count ?? suggestion.participantCount);
  const threshold = numberValue(suggestion.threshold_percent ?? suggestion.thresholdPercent);
  async function vote(nextChoice: VoteChoice) {
    if (!suggestionId) return;
    setPending(true); setFeedback("");
    try { await voteOnSuggestion(meetingId, suggestionId, nextChoice); setChoice(nextChoice); setFeedback("投票已更新"); }
    catch (error) { setFeedback((error as { message?: string }).message ?? "投票失敗，請稍後重試"); }
    finally { setPending(false); }
  }
  const laterCount = numberValue(suggestion.later_count ?? suggestion.laterCount) ?? 0;
  const ignoreCount = numberValue(suggestion.ignore_count ?? suggestion.ignoreCount) ?? 0;
  const hasVoteData = support !== null && total !== null;
  const undecided = hasVoteData ? Math.max(0, total - support - laterCount - ignoreCount) : null;
  return <article className={`rounded-xl border-2 p-4 shadow-[0_4px_16px_rgba(15,159,138,0.12)] ${prominent ? "border-[#8bd3b2] bg-[#effbf4]" : "border-[#e6e6e3]"}`}>{showRaiseHeader ? <div className="mb-4 flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-[#087f5b]"><span className="h-2 w-2 rounded-full bg-[#0f9f8a] motion-safe:animate-pulse" />AI 舉手</div> : null}<div className="flex items-start gap-4"><span className="addon-bot-pop relative flex h-16 w-16 shrink-0 items-center justify-center rounded-3xl bg-[#d5f5e3] text-[#087f5b] motion-safe:animate-[addon-bot-pop_1.7s_ease-in-out_infinite]"><span className="absolute inset-0 rounded-3xl border-[3px] border-[#8bd3b2] motion-safe:animate-[addon-bot-ring_1.7s_ease-out_infinite]" /><IconRobot size={38} stroke={1.8} /></span><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h3 className="text-lg font-bold text-[#155443]">{textValue(suggestion.title) ?? "Proximate 想發言"}</h3><span className="rounded-full bg-white/80 px-2 py-0.5 text-[10px] font-semibold text-[#087f5b]">會議成員</span></div><p className="mt-2 text-sm font-medium leading-6 text-[#2f5446]">{textValue(suggestion.body ?? suggestion.content) ?? "正式 API 尚未提供意見摘要。"}</p></div></div><div className="mt-4 border-t border-[#b9e9cc] pt-4"><p className="text-xs font-semibold text-[#5d806f]">Proximate 想加入討論</p><p className="mt-1 text-xs leading-5 text-[#787774]">它會先提出文字摘要，等待與會者決定是否開放發言。</p><div className="mt-3 flex flex-col gap-4 min-[360px]:flex-row min-[360px]:items-center"><VotePie support={support} later={laterCount} ignore={ignoreCount} undecided={undecided} /><div role="group" aria-label="Proximate 發言決策" className="flex flex-1 flex-wrap gap-2">{(["support", "later", "ignore"] as const).map((item) => <button key={item} type="button" disabled={pending} onClick={() => void vote(item)} className={`rounded-lg border px-3 py-2 text-xs font-semibold disabled:opacity-50 ${choice === item ? "border-[#0f9f8a] bg-[#0f9f8a] text-white" : item === "support" ? "border-[#0f9f8a] text-[#087f5b] hover:bg-[#e7f7ef]" : "border-[#dededb]"}`}>{item === "support" ? "允許發言" : item === "later" ? "稍後" : "忽略"}</button>)}</div></div>{hasVoteData ? <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-[#787774]"><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-[#0f9f8a]" />允許 {support}</span><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-[#f0b45b]" />稍後 {laterCount}</span><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-[#c8cfcc]" />未決定 {undecided}</span>{threshold !== null ? <span>門檻 {threshold}%</span> : null}</div> : <p className="mt-3 text-xs text-[#787774]">等待正式票數資料</p>}</div>{feedback ? <p role="status" className="mt-2 text-xs text-[#787774]">{feedback}</p> : null}</article>;
}

function VotePie({ support, later, ignore, undecided }: { support: number | null; later: number; ignore: number; undecided: number | null }) {
  if (support === null || undecided === null) return <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full border-4 border-[#dfe8e3] text-center text-[9px] text-[#8b8b87]">等待<br />票數</div>;
  const total = Math.max(1, support + later + ignore + undecided);
  const supportEnd = (support / total) * 100;
  const laterEnd = supportEnd + (later / total) * 100;
  const ignoreEnd = laterEnd + (ignore / total) * 100;
  return <div className="relative h-16 w-16 shrink-0 rounded-full" style={{ background: `conic-gradient(#0f9f8a 0 ${supportEnd}%, #f0b45b ${supportEnd}% ${laterEnd}%, #c77f86 ${laterEnd}% ${ignoreEnd}%, #dfe8e3 ${ignoreEnd}% 100%)` }} aria-label={`允許發言 ${support} 人，稍後 ${later} 人，忽略 ${ignore} 人，未決定 ${undecided} 人`} role="img"><span className="absolute inset-2 flex items-center justify-center rounded-full bg-white text-center text-[10px] font-semibold leading-3 text-[#2f5446]">{support}<br />允許</span></div>;
}

function DataSection({ title, items, empty }: { title: string; items: string[]; empty: string }) { return <section className="rounded-xl border border-[#e6e6e3] p-4"><h2 className="text-sm font-semibold">{title}</h2>{items.length ? <ul className="mt-3 space-y-2 text-sm">{items.map((item) => <li key={item} className="rounded-lg bg-[#f7f7f5] px-3 py-2">{item}</li>)}</ul> : <p className="mt-2 text-sm text-[#8b8b87]">{empty}</p>}</section>; }
function ParkingLot({ items }: { items: string[] }) { return <DataSection title="Parking Lot" items={items} empty="目前沒有暫存議題" />; }
function VoiceBotStatus({ value }: { value: unknown }) { const status = textValue(value) ?? "尚未收到 Voice Bot 狀態"; return <section className="rounded-xl border border-[#e6e6e3] p-4"><div className="flex items-center gap-2"><IconVolume size={17} className="text-[#0f9f8a]" /><h2 className="text-sm font-semibold">Voice Bot</h2></div><p className="mt-2 text-sm text-[#787774]">{status}</p></section>; }
function textValue(value: unknown) { return typeof value === "string" && value.trim() ? value : null; }
function numberValue(value: unknown) { return typeof value === "number" ? value : null; }
function stringList(value: unknown): string[] { return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : []; }
function asVote(value: unknown): VoteChoice | null { return value === "support" || value === "later" || value === "ignore" ? value : null; }
