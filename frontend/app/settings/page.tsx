import { AppShell, PageHeader, PlaceholderState } from "../../components/app-shell";

export default function SettingsPage() {
  return <AppShell><PageHeader eyebrow="Settings" title="設定" description="管理團隊、整合服務與隱私選項。" /><div className="mt-8"><PlaceholderState title="設定頁面骨架" description="Team、Integrations 與 Privacy Tabs 會在後續步驟加入。" /></div></AppShell>;
}
