"use client";

import { IconAt, IconCircleCheck, IconUser } from "@tabler/icons-react";
import { useEffect, useState, type FormEvent } from "react";
import { AppShell } from "../../components/app-shell";
import { PageHeader } from "../../components/page-header";
import { authClient } from "../../lib/auth/client";
import { getCurrentUser, updateCurrentUser } from "../../lib/api/me";

export default function SettingsPage() {
  const { data: authSession } = authClient.useSession();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => { getCurrentUser().then((user) => { setName(user.display_name ?? authSession?.user?.name ?? ""); setEmail(user.email ?? authSession?.user?.email ?? ""); }).catch(() => { setName(authSession?.user?.name ?? ""); setEmail(authSession?.user?.email ?? ""); }); }, [authSession?.user?.email, authSession?.user?.name]);
  async function save(event: FormEvent<HTMLFormElement>) { event.preventDefault(); if (!name.trim()) { setError("請輸入顯示名稱。 "); return; } setSaving(true); setError(""); setNotice(""); try { const user = await updateCurrentUser({ display_name: name.trim(), email: email.trim() || undefined }); setName(user.display_name ?? name.trim()); setEmail(user.email ?? email.trim()); setNotice("個人資料已儲存。 "); } catch (cause) { setError(cause instanceof Error ? cause.message : "更新失敗，請稍後再試。 "); } finally { setSaving(false); } }
  return <AppShell><PageHeader eyebrow="Settings" title="設定" description="更新你在團隊中顯示的名稱與聯絡 Email。登入憑證仍由 Neon Auth 安全管理。" /><form onSubmit={save} className="mt-8 max-w-2xl rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-7"><div className="flex items-start gap-4"><span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#e7f7ef] text-[#087e6d]"><IconUser size={21} /></span><div><h2 className="text-lg font-semibold">個人資料</h2><p className="mt-1 text-sm leading-6 text-[#787774]">這些欄位會由 Proximate API 保存，團隊成員會看到你的顯示名稱。</p></div></div><div className="mt-7 grid gap-5"><label className="block text-sm font-medium">顯示名稱<input required value={name} onChange={(event) => setName(event.target.value)} className="control-primary mt-2" placeholder="例如：王小明" /></label><label className="block text-sm font-medium">聯絡 Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="control-primary mt-2" placeholder="name@example.com" /><span className="mt-2 flex items-center gap-1 text-xs font-normal text-[#787774]"><IconAt size={14} />用於顯示與團隊站內邀請比對。</span></label></div>{error && <p role="alert" className="mt-5 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}{notice && <p role="status" className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#e7f7ef] px-4 py-3 text-sm text-[#087e6d]"><IconCircleCheck size={17} />{notice}</p>}<div className="mt-7 border-t border-[#ededeb] pt-5"><button disabled={saving} className="rounded-lg bg-[#0f9f8a] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60">{saving ? "儲存中…" : "儲存個人資料"}</button></div></form></AppShell>;
}
