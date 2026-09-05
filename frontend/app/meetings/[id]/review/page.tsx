"use client";

import { IconChecklist, IconFileText, IconMessageCircle, IconPlus, IconScale, IconTrash } from "@tabler/icons-react";
import { useEffect, useState, type FormEvent } from "react";
import { MeetingWorkspaceHeader } from "../../../../components/meeting-workspace-header";
import { getMeeting } from "../../../../lib/api/meetings";
import { createActionItem, createConsensus, confirmConsensus, createConsensusFeedback, deleteActionItem, listActionItems, listConsensus, listConsensusFeedback, listTranscripts, updateActionItem } from "../../../../lib/api/meeting-features";
import { listTeamMembers } from "../../../../lib/api/teams";
import type { ActionItem, Consensus, ConsensusFeedback, TeamMember, Transcript } from "../../../../types/api";

const actionStatus = { open: "待開始", in_progress: "進行中", done: "已完成", cancelled: "已取消" } as Record<string, string>;

function memberName(member: TeamMember) {
  return member.display_name || "未設定名稱的成員";
}

export default function ReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const [id, setId] = useState("");
  const [title, setTitle] = useState("");
  const [consensus, setConsensus] = useState<Consensus[]>([]);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [transcripts, setTranscripts] = useState<Transcript[]>([]);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [feedback, setFeedback] = useState<Record<string, ConsensusFeedback[]>>({});
  const [openFeedback, setOpenFeedback] = useState<string | null>(null);
  const [feedbackDrafts, setFeedbackDrafts] = useState<Record<string, string>>({});
  const [consensusDraft, setConsensusDraft] = useState("");
  const [actionTitle, setActionTitle] = useState("");
  const [actionAssignee, setActionAssignee] = useState("");
  const [actionDueDate, setActionDueDate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    params.then(async ({ id: meetingId }) => {
      setId(meetingId);
      try {
        const meeting = await getMeeting(meetingId);
        const [consensusResult, actionResult, transcriptResult, memberResult] = await Promise.all([
          listConsensus(meetingId), listActionItems(meetingId), listTranscripts(meetingId), listTeamMembers(meeting.team_id),
        ]);
        if (!active) return;
        setTitle(meeting.title);
        setConsensus(consensusResult);
        setActions(actionResult);
        setTranscripts(transcriptResult);
        setMembers(memberResult.members);
      } catch (cause) {
        active && setError(cause instanceof Error ? cause.message : "無法讀取會後資料。");
      }
    });
    return () => { active = false; };
  }, [params]);

  async function submitConsensus(event: FormEvent) {
    event.preventDefault();
    if (!consensusDraft.trim()) return;
    try {
      const item = await createConsensus(id, consensusDraft.trim());
      setConsensus((current) => [...current, item]);
      setConsensusDraft("");
      setNotice("已建立共識版本，請邀請成員回饋或確認。");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "建立共識失敗。"); }
  }

  async function loadFeedback(versionId: string) {
    try {
      const result = await listConsensusFeedback(id, versionId);
      setFeedback((current) => ({ ...current, [versionId]: result }));
      setOpenFeedback((current) => current === versionId ? null : versionId);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "讀取共識回饋失敗。"); }
  }

  async function submitFeedback(versionId: string, decision: "agree" | "revise" | "reject") {
    try {
      await createConsensusFeedback(id, versionId, { decision, comment: feedbackDrafts[versionId]?.trim() || undefined });
      setFeedbackDrafts((current) => ({ ...current, [versionId]: "" }));
      setNotice("已送出你的共識回饋。");
      const result = await listConsensusFeedback(id, versionId);
      setFeedback((current) => ({ ...current, [versionId]: result }));
      setOpenFeedback(versionId);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "送出共識回饋失敗。"); }
  }

  async function submitAction(event: FormEvent) {
    event.preventDefault();
    if (!actionTitle.trim()) return;
    try {
      const item = await createActionItem(id, { title: actionTitle.trim(), assignee_user_id: actionAssignee || null, due_date: actionDueDate || null });
      setActions((current) => [...current, item]);
      setActionTitle(""); setActionAssignee(""); setActionDueDate("");
      setNotice("行動項目已建立。");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "建立行動項目失敗。"); }
  }

  async function patchAction(itemId: string, patch: Parameters<typeof updateActionItem>[2]) {
    try {
      const updated = await updateActionItem(id, itemId, patch);
      setActions((current) => current.map((item) => item.id === itemId ? updated : item));
      setNotice("行動項目已更新。");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "更新行動項目失敗。"); }
  }

  return <main>
    <MeetingWorkspaceHeader meetingId={id} title={title || undefined} phase="review" />
    {error && <p role="alert" className="mt-5 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
    {notice && <p role="status" className="mt-5 rounded-lg bg-[#e9f7f4] px-4 py-3 text-sm text-[#087e6d]">{notice}</p>}
    <div className="mt-7 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <div className="space-y-6">
        <section className="rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-6"><div className="flex items-center gap-2"><IconScale size={19} className="text-[#0f9f8a]" /><div><h2 className="font-semibold">決策與共識</h2><p className="mt-1 text-sm text-[#787774]">將會議結論整理成可回饋、可確認的版本。</p></div></div>{consensus.length ? <div className="mt-5 space-y-3">{consensus.map((item) => <article key={item.id} className="rounded-xl border border-[#e6e6e3] p-4"><div className="flex flex-wrap items-start justify-between gap-3"><p className="text-sm leading-6">{item.content}</p><span className="rounded-full bg-[#f3f3f1] px-2.5 py-1 text-xs text-[#5f5f5b]">{item.status === "confirmed" ? "已確認" : "待確認"}</span></div><p className="mt-3 text-xs text-[#787774]">版本 {item.version}</p>{item.status !== "confirmed" && <><label className="mt-4 block text-xs font-medium text-[#5f5f5b]">補充回饋（選填）<input value={feedbackDrafts[item.id] ?? ""} onChange={(event) => setFeedbackDrafts((current) => ({ ...current, [item.id]: event.target.value }))} className="control-primary mt-1" placeholder="例如：請補上時程風險" /></label><div className="mt-3 flex flex-wrap gap-2"><button type="button" onClick={() => void submitFeedback(item.id, "agree")} className="rounded-primary bg-[#e7f7ef] px-3 py-2 text-xs font-semibold text-[#087e6d]">同意</button><button type="button" onClick={() => void submitFeedback(item.id, "revise")} className="rounded-primary bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-800">要求修改</button><button type="button" onClick={() => void submitFeedback(item.id, "reject")} className="rounded-primary bg-red-50 px-3 py-2 text-xs font-semibold text-red-700">不同意</button><button type="button" onClick={() => void confirmConsensus(id, item.id).then((updated) => { setConsensus((current) => current.map((entry) => entry.id === item.id ? updated : entry)); setNotice("此版本已確認。"); }).catch((cause) => setError(cause instanceof Error ? cause.message : "確認共識失敗。"))} className="ml-auto rounded-primary border border-[#cde5df] px-3 py-2 text-xs font-semibold text-[#087e6d]">確認此版本</button></div></>}<button type="button" onClick={() => void loadFeedback(item.id)} className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-[#5f5f5b] underline"><IconMessageCircle size={14} />{openFeedback === item.id ? "收起回饋" : "查看回饋"}</button>{openFeedback === item.id && <div className="mt-3 space-y-2 rounded-lg bg-[#f7f7f5] p-3">{(feedback[item.id] ?? []).length ? feedback[item.id].map((entry) => <div key={entry.id} className="text-sm"><span className="mr-2 font-medium">{({ agree: "同意", revise: "要求修改", reject: "不同意" } as Record<string, string>)[entry.decision] ?? entry.decision}</span>{entry.comment && <span className="text-[#5f5f5b]">{entry.comment}</span>}</div>) : <p className="text-sm text-[#787774]">尚無回饋。</p>}</div>}</article>)}</div> : <p className="mt-4 rounded-xl border border-dashed border-[#d8d8d5] p-5 text-sm text-[#787774]">尚未產生共識版本。</p>}<form onSubmit={submitConsensus} className="mt-5 flex gap-2"><input value={consensusDraft} onChange={(event) => setConsensusDraft(event.target.value)} className="control-primary" placeholder="補充決策或共識草稿" /><button type="submit" className="inline-flex shrink-0 items-center gap-1 rounded-primary bg-[var(--accent)] px-3 py-2 text-sm font-semibold text-white"><IconPlus size={16} />新增</button></form></section>
        <section className="rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-6"><div className="flex items-center gap-2"><IconFileText size={19} className="text-[#0f9f8a]" /><div><h2 className="font-semibold">逐字稿</h2><p className="mt-1 text-sm text-[#787774]">會議內容的原始紀錄。</p></div></div>{transcripts.length ? <div className="mt-4 max-h-80 space-y-3 overflow-y-auto">{transcripts.map((item) => <p key={item.id} className="text-sm leading-6"><span className="mr-2 text-xs text-[#787774]">{item.speaker_label ?? "參與者"}</span>{item.text}</p>)}</div> : <p className="mt-4 text-sm text-[#787774]">尚無逐字稿資料。</p>}</section>
      </div>
      <aside><section className="rounded-2xl border border-[#e6e6e3] bg-white p-5"><div className="flex items-center gap-2"><IconChecklist size={19} className="text-[#0f9f8a]" /><div><h2 className="font-semibold">行動項目</h2><p className="mt-1 text-sm text-[#787774]">明確指定負責人與期限，讓會後能追蹤。</p></div></div>{actions.length ? <div className="mt-4 space-y-3">{actions.map((item) => <article key={item.id} className="rounded-xl bg-[#f7f7f5] p-3"><input className="w-full bg-transparent text-sm font-medium outline-none" defaultValue={item.title} aria-label="行動項目名稱" onBlur={(event) => { const next = event.target.value.trim(); if (next && next !== item.title) void patchAction(item.id, { title: next }); }} /><div className="mt-3 grid gap-2"><select value={item.assignee_user_id ?? ""} onChange={(event) => void patchAction(item.id, { assignee_user_id: event.target.value || null })} className="control-primary text-xs" aria-label="負責人"><option value="">未指派負責人</option>{members.map((member) => <option key={member.user_id} value={member.user_id}>{memberName(member)}</option>)}</select><input type="date" value={item.due_date ?? ""} onChange={(event) => void patchAction(item.id, { due_date: event.target.value || null })} className="control-primary text-xs" aria-label="期限" /><div className="flex gap-2"><select value={item.status} onChange={(event) => void patchAction(item.id, { status: event.target.value })} className="control-primary min-w-0 flex-1 text-xs" aria-label="狀態">{Object.entries(actionStatus).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><button type="button" aria-label="刪除行動項目" onClick={() => void deleteActionItem(id, item.id).then(() => { setActions((current) => current.filter((entry) => entry.id !== item.id)); setNotice("行動項目已刪除。"); }).catch((cause) => setError(cause instanceof Error ? cause.message : "刪除行動項目失敗。"))} className="rounded-lg px-2 text-red-600 hover:bg-red-50"><IconTrash size={16} /></button></div></div></article>)}</div> : <p className="mt-3 text-sm text-[#787774]">尚未建立行動項目。</p>}<form onSubmit={submitAction} className="mt-5 space-y-2 border-t border-[#e6e6e3] pt-4"><input value={actionTitle} onChange={(event) => setActionTitle(event.target.value)} className="control-primary" placeholder="例如：確認上線日期" /><select value={actionAssignee} onChange={(event) => setActionAssignee(event.target.value)} className="control-primary text-sm"><option value="">選擇負責人（可略過）</option>{members.map((member) => <option key={member.user_id} value={member.user_id}>{memberName(member)}</option>)}</select><input type="date" value={actionDueDate} onChange={(event) => setActionDueDate(event.target.value)} className="control-primary" aria-label="行動項目期限" /><button type="submit" className="w-full rounded-primary border border-[#d7e8e5] px-3 py-2 text-sm font-medium text-[#087e6d]">新增行動項目</button></form></section></aside>
    </div>
  </main>;
}
