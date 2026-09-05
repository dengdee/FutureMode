"use client";

import { useEffect, useState } from "react";
import type { InvitationUser } from "../lib/api/teams";

export function InviteUserPicker({ value, onChange, disabled = false }: {
  value: InvitationUser | null; onChange: (user: InvitationUser | null) => void; disabled?: boolean;
}) {
  const [query, setQuery] = useState("");
  useEffect(() => { if (value) setQuery(value.email); }, [value]);
  if (value) return <div className="rounded-lg border border-[#cde5df] p-3">
    <p className="break-words text-sm font-medium">{value.display_name}</p>
    {value.email && <p className="break-all text-xs text-[#787774]">{value.email}</p>}
    <button type="button" disabled={disabled} onClick={() => { onChange(null); setQuery(""); }} className="mt-1 min-h-11 text-sm text-[#087e6d] underline">重新輸入</button>
  </div>;
  return <div>
    <label className="block text-sm">搜尋已註冊帳號<input disabled={disabled} value={query}
      onChange={(event) => { const next = event.target.value; setQuery(next); onChange(next.trim() ? { id: "", display_name: next.trim(), email: next.trim() } : null); }}
      className="control-primary mt-2" placeholder="名稱（至少兩字）或完整 Email" /></label>
    <p className="mt-1 text-xs text-[#787774]">送出時才檢查此 Email 是否已註冊，不會顯示帳號清單。</p>
  </div>;
}
