import { IconBell, IconBuilding, IconShieldCheck, IconUser } from "@tabler/icons-react";
import { AppShell } from "../../components/app-shell";
import { PageHeader } from "../../components/page-header";

export default function SettingsPage() {
  const sections = [[IconUser, "個人資料", "管理顯示名稱與個人偏好。"], [IconBuilding, "團隊工作區", "管理團隊名稱、成員與預設會議政策。"], [IconBell, "通知", "設定會議提醒與會後待確認通知。"], [IconShieldCheck, "權限與安全性", "僅限管理員調整角色與安全性設定。"]] as const;
  return <AppShell><PageHeader eyebrow="Settings" title="設定" description="管理你的個人偏好與 Proximate 工作區設定。" /><div className="mt-8 max-w-3xl divide-y divide-[#e8e8e5] overflow-hidden rounded-2xl border border-[#e6e6e3] bg-white">{sections.map(([Icon, title, description]) => <button key={title} type="button" className="flex w-full items-center gap-4 px-5 py-5 text-left hover:bg-[#fafaf9]"><span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#f1f1ef] text-[#5f5f5b]"><Icon size={20} /></span><span><span className="block font-medium">{title}</span><span className="mt-1 block text-sm text-[#787774]">{description}</span></span><span className="ml-auto text-[#9b9b97]">→</span></button>)}</div></AppShell>;
}
