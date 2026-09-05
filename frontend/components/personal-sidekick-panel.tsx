"use client";

import { IconLock, IconSend, IconSparkles } from "@tabler/icons-react";
import { useEffect, useState } from "react";
import { createPersonalMessage, listPersonalMessages, previewContribution, publishContribution } from "../lib/api/meeting-features";
import type { PersonalMessage } from "../types/api";

export function PersonalSidekickPanel({ meetingId }: { meetingId: string }) {
  const [messages, setMessages] = useState<PersonalMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [preview, setPreview] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { listPersonalMessages(meetingId).then(setMessages).catch(() => setNotice("目前無法讀取私人對話。")); }, [meetingId]);

  async function saveMessage() {
    if (!draft.trim()) return;
    setBusy(true); setNotice("");
    try { const item = await createPersonalMessage(meetingId, draft.trim()); setMessages((current) => [...current, item]); setDraft(""); setNotice("已儲存到你的私人準備筆記。"); }
    catch (cause) { setNotice(cause instanceof Error ? cause.message : "儲存訊息失敗。 "); }
    finally { setBusy(false); }
  }
  async function makePreview() {
    if (!draft.trim()) { setNotice("先輸入你想整理的想法。 "); return; }
    setBusy(true); setNotice("");
    try { await previewContribution(meetingId, draft.trim()); setPreview(draft.trim()); setNotice("已建立公開前預覽；尚未分享給其他人。 "); }
    catch (cause) { setNotice(cause instanceof Error ? cause.message : "無法建立預覽。 "); }
    finally { setBusy(false); }
  }
  async function publish() {
    if (!preview) return;
    setBusy(true); setNotice("");
    try { await publishContribution(meetingId, preview); setPreview(""); setDraft(""); setNotice("已將整理後的觀點公開到會議。 "); }
    catch (cause) { setNotice(cause instanceof Error ? cause.message : "發布失敗。 "); }
    finally { setBusy(false); }
  }

  return <section className="rounded-2xl border border-[#cde5df] bg-white p-5 sm:p-6"><div className="flex items-start gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#e7f7ef] text-[#087e6d]"><IconSparkles size={20} /></span><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h2 className="font-semibold">Personal Sidekick</h2><span className="inline-flex items-center gap-1 rounded-full bg-[#f1f1ef] px-2 py-0.5 text-[11px] text-[#5f5f5b]"><IconLock size={12} />只有你看得到</span></div><p className="mt-1 text-sm leading-6 text-[#787774]">先整理你的觀點、理由與疑慮；只有你按下發布後，整理版本才會進入公共會議。</p></div></div><div className="mt-5 max-h-56 space-y-2 overflow-y-auto rounded-xl bg-[#f7f7f5] p-3">{messages.length ? messages.map((message) => <div key={message.id} className="rounded-lg bg-white px-3 py-2 text-sm shadow-sm">{message.content}</div>) : <p className="p-3 text-sm text-[#787774]">還沒有私人筆記。可先把不確定的想法寫下來。</p>}</div><label className="mt-4 block text-sm font-medium">我想先和 Sidekick 討論<textarea value={draft} onChange={(event) => setDraft(event.target.value)} className="control-primary mt-2 min-h-28" placeholder="例如：我擔心這個方案忽略維運成本，想先整理成可以討論的問題。" /></label><div className="mt-3 flex flex-wrap gap-2"><button type="button" disabled={busy || !draft.trim()} onClick={() => void saveMessage()} className="inline-flex items-center gap-1 rounded-lg bg-[#0f9f8a] px-3 py-2 text-sm font-semibold text-white disabled:opacity-50"><IconSend size={16} />儲存私人想法</button><button type="button" disabled={busy || !draft.trim()} onClick={() => void makePreview()} className="rounded-lg border border-[#d7e8e5] px-3 py-2 text-sm font-medium text-[#087e6d] disabled:opacity-50">建立公開前預覽</button></div>{preview && <div className="mt-4 rounded-xl border border-[#9ddbc8] bg-[#f0fbf8] p-4"><p className="text-xs font-semibold text-[#087e6d]">公開內容預覽</p><p className="mt-2 text-sm leading-6">{preview}</p><button type="button" disabled={busy} onClick={() => void publish()} className="mt-3 rounded-lg bg-[#0f9f8a] px-3 py-2 text-sm font-semibold text-white disabled:opacity-50">確認提出觀點</button></div>}{notice && <p role="status" className="mt-3 text-sm text-[#087e6d]">{notice}</p>}</section>;
}
