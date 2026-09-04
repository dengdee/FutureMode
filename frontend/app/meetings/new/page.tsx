import { AppShell, PageHeader, PlaceholderState } from "../../../components/app-shell";

export default function NewMeetingPage() {
  return <AppShell><PageHeader eyebrow="Meetings" title="建立會議" description="會議設定表單將在後續步驟加入。" /><div className="mt-8"><PlaceholderState title="會議建立骨架" description="目前先保留路由與頁面容器，尚未連接表單、Mock 資料或 API。" /></div></AppShell>;
}
