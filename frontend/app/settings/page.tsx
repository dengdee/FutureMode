"use client";

import { IconUser } from "@tabler/icons-react";
import { AppShell } from "../../components/app-shell";
import { PageHeader } from "../../components/page-header";
import { authClient } from "../../lib/auth/client";

export default function SettingsPage() {
  const { data: authSession } = authClient.useSession();
  const identity = authSession?.user?.name ?? authSession?.user?.email ?? "尚未登入";
  const sections = [[IconUser, "帳號", "", identity]] as const;
  return <AppShell><PageHeader eyebrow="Settings" title="設定" description="管理 Proximate 的個人帳號設定。" /><div className="mt-8 max-w-xl overflow-hidden rounded-2xl border border-[#e6e6e3] bg-white"><div className="divide-y divide-[#e8e8e5]">{sections.map(([Icon, title, description, value]) => <section key={title} className="flex items-center gap-4 px-6 py-6"><span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-[#f1f1ef] text-[#5f5f5b]"><Icon size={20} stroke={1.8} /></span><div className="min-w-0"><h2 className="font-medium">{title}</h2>{description && <p className="mt-1 text-sm text-[#787774]">{description}</p>}<p className="mt-2 text-sm font-medium text-[#0f9f8a]">{value}</p></div></section>)}</div></div></AppShell>;
}
