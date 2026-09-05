"use client";

import { IconUser } from "@tabler/icons-react";
import { useEffect, useState } from "react";
import { AppShell } from "../../components/app-shell";
import { PageHeader } from "../../components/page-header";
import { authClient } from "../../lib/auth/client";
import { getCurrentUser, updateCurrentUser } from "../../lib/api/me";

export default function SettingsPage() {
  const { data: authSession } = authClient.useSession();
  const identity = authSession?.user?.name ?? authSession?.user?.email ?? "尚未登入";
  const [name, setName] = useState(identity);
  const [email, setEmail] = useState(authSession?.user?.email ?? "");
  const [notice, setNotice] = useState<string | null>(null);
  useEffect(() => { getCurrentUser().then((user) => { if (user.display_name) setName(user.display_name); if (user.email) setEmail(user.email); }).catch(() => undefined); }, []);
  async function save() { setNotice(null); try { const user = await updateCurrentUser({ display_name: name.trim(), email: email.trim() || undefined }); setName(user.display_name ?? name); setNotice("個人資料已更新。"); } catch (error) { setNotice(error instanceof Error ? error.message : "更新失敗，請稍後再試。"); } }
  return <AppShell><PageHeader eyebrow="Settings" title="設定" description="管理 Proximate 的個人帳號設定。" /><div className="mt-8 max-w-xl overflow-hidden rounded-2xl border border-[#e6e6e3] bg-white"><section className="flex items-start gap-4 px-6 py-6"><span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-[#f1f1ef] text-[#5f5f5b]"><IconUser size={20} stroke={1.8} /></span><div className="min-w-0 flex-1"><h2 className="font-medium">個人資料</h2><p className="mt-1 text-sm text-[#787774]">資料會從 Neon Auth 與 Proximate API 同步。</p><label className="mt-4 block text-sm">顯示名稱<input value={name} onChange={(event) => setName(event.target.value)} className="control-primary mt-1" /></label><label className="mt-3 block text-sm">Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="control-primary mt-1" /></label><div className="mt-4 flex items-center gap-3"><button type="button" onClick={save} className="rounded-lg bg-[#0f9f8a] px-4 py-2 text-sm font-semibold text-white">儲存變更</button>{notice && <span role="status" className="text-sm text-[#087e6d]">{notice}</span>}</div></div></section></div></AppShell>;
}
