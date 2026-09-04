"use client";

import { IconBell, IconBuilding, IconShieldCheck, IconUser } from "@tabler/icons-react";
import { useEffect, useState } from "react";
import { AppShell } from "../../components/app-shell";
import { PageHeader } from "../../components/page-header";
import { getCurrentUser } from "../../lib/api/me";

export default function SettingsPage() {
  const [identity, setIdentity] = useState("尚未載入");
  useEffect(() => { getCurrentUser().then((user) => { const value = user.claims.name ?? user.claims.email ?? user.id; setIdentity(typeof value === "string" ? value : user.id); }).catch(() => setIdentity("無法取得登入身分")); }, []);
  const sections = [[IconUser, "個人資料", "管理顯示名稱與個人偏好。", identity], [IconBuilding, "團隊工作區", "管理團隊名稱、成員與預設會議政策。", "請至工作區頁面管理"], [IconBell, "通知", "設定會議提醒與會後待確認通知。", "尚未設定"], [IconShieldCheck, "權限與安全性", "僅限管理員調整角色與安全性設定。", "依登入角色限制"]] as const;
  return <AppShell><PageHeader eyebrow="Settings" title="設定" description="查看登入身分與管理 Proximate 工作區設定。" /><div className="mt-8 max-w-3xl overflow-hidden rounded-2xl border border-[#e6e6e3] bg-white"><div className="divide-y divide-[#e8e8e5]">{sections.map(([Icon, title, description, value]) => <section key={title} className="flex items-center gap-4 px-5 py-5"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#f1f1ef] text-[#5f5f5b]"><Icon size={20} stroke={1.8} /></span><div className="min-w-0"><h2 className="font-medium">{title}</h2><p className="mt-1 text-sm text-[#787774]">{description}</p><p className="mt-2 text-sm font-medium text-[#0f9f8a]">{value}</p></div></section>)}</div></div></AppShell>;
}
