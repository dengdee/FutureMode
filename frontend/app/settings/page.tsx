"use client";

import { IconBell, IconBuilding, IconChevronRight, IconShieldCheck, IconUser } from "@tabler/icons-react";
import { useState } from "react";
import { AppShell } from "../../components/app-shell";
import { PageHeader } from "../../components/page-header";

export default function SettingsPage() {
  const [selected, setSelected] = useState<string | null>(null);
  const sections = [[IconUser, "個人資料", "管理顯示名稱與個人偏好。"], [IconBuilding, "團隊工作區", "管理團隊名稱、成員與預設會議政策。"], [IconBell, "通知", "設定會議提醒與會後待確認通知。"], [IconShieldCheck, "權限與安全性", "僅限管理員調整角色與安全性設定。"]] as const;
  return <AppShell><PageHeader eyebrow="Settings" title="設定" description="管理你的個人偏好與 Proximate 工作區設定。" /><div className="mt-8 max-w-3xl overflow-hidden rounded-2xl border border-[#e6e6e3] bg-white"><div className="divide-y divide-[#e8e8e5]">{sections.map(([Icon, title, description]) => <button key={title} type="button" onClick={() => setSelected(title)} aria-current={selected === title ? "true" : undefined} className={`flex w-full items-center gap-4 px-5 py-5 text-left transition-colors hover:bg-[#fafaf9] focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[var(--accent)] ${selected === title ? "bg-[#f5fbfa]" : ""}`}><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#f1f1ef] text-[#5f5f5b]"><Icon size={20} stroke={1.8} /></span><span><span className="block font-medium">{title}</span><span className="mt-1 block text-sm text-[#787774]">{description}</span></span><IconChevronRight className="ml-auto shrink-0 text-[#9b9b97]" size={19} stroke={1.8} /></button>)}</div></div>{selected && <p role="status" className="mt-3 max-w-3xl text-sm text-[#787774]">已選取「{selected}」。詳細設定頁面將在對應功能完成後開放。</p>}</AppShell>;
}
