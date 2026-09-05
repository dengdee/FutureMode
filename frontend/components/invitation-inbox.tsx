"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { authClient } from "../lib/auth/client";
import { http, request } from "../lib/api/client";

type Invite = { id: string; team_id: string; team_name: string; role: string };

export function InvitationInbox() {
  const router = useRouter();
  const { data: session } = authClient.useSession();
  const userId = session?.user?.id;
  const [items, setItems] = useState<Invite[]>([]);
  const [recipient, setRecipient] = useState<string>();
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [attempt, setAttempt] = useState(0);
  const lock = useRef(false);

  useEffect(() => {
    if (!userId) return;
    let active = true;
    let fetching = false;
    async function load() {
      if (fetching || document.visibilityState === "hidden") return;
      fetching = true;
      try {
        const result = await request<Invite[]>(() => http.get("/api/v1/me/invitations"));
        if (active) { setRecipient(userId); setItems(result); setError(""); }
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : "無法讀取站內邀請。");
      } finally { fetching = false; }
    }
    void load();
    const timer = setInterval(() => void load(), 30000);
    window.addEventListener("focus", load);
    return () => { active = false; clearInterval(timer); window.removeEventListener("focus", load); };
  }, [userId, attempt]);

  async function respond(item: Invite, action: "accept" | "decline") {
    if (lock.current) return;
    lock.current = true;
    setBusy(item.id);
    setError("");
    try {
      await request(() => http.post(`/api/v1/me/invitations/${item.id}/${action}`));
      setItems((current) => current.filter((invite) => invite.id !== item.id));
      setNotice(action === "accept" ? "已加入團隊。" : "已拒絕邀請。");
      if (action === "accept") router.push(`/workspaces?teamId=${item.team_id}`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "處理邀請失敗，請重試。");
    } finally { lock.current = false; setBusy(""); }
  }

  const visibleItems = recipient === userId ? items : [];
  if (!userId || (!visibleItems.length && !error && !notice)) return null;
  return <section aria-label="站內團隊邀請" className="mb-6 rounded-2xl border border-[#cde5df] bg-white p-5">
    <h2 className="text-lg font-semibold">團隊邀請</h2>
    {notice && <p role="status" className="mt-3 text-sm text-[#087e6d]">{notice}</p>}
    {error && <p role="alert" className="mt-3 text-sm text-red-700">{error}<button type="button" onClick={() => setAttempt((value) => value + 1)} className="ml-2 min-h-11 underline">重新載入邀請</button></p>}
    {visibleItems.map((item) => <div key={item.id} className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t pt-3">
      <p><span className="font-semibold">{item.team_name}</span><span className="ml-2 text-sm">邀請你以 {item.role === "admin" ? "Admin" : "Member"} 加入</span></p>
      <div className="flex gap-3" aria-busy={busy === item.id}>
        <button type="button" disabled={!!busy} onClick={() => void respond(item, "decline")} className="min-h-11 rounded-lg border px-4 disabled:opacity-50">拒絕</button>
        <button type="button" disabled={!!busy} onClick={() => void respond(item, "accept")} className="min-h-11 rounded-lg bg-[#087e6d] px-4 text-white disabled:opacity-50">{busy === item.id ? "處理中…" : "接受邀請"}</button>
      </div>
    </div>)}
  </section>;
}
