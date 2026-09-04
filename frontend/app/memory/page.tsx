import { AppShell, PageHeader, PlaceholderState } from "../../components/app-shell";

export default function MemoryPage() {
  return <AppShell><PageHeader eyebrow="Team Memory" title="團隊記憶" description="集中查看團隊的決策與脈絡。" /><div className="mt-8"><PlaceholderState title="Team Memory 尚未開放" description="這是產品路由骨架；資料與搜尋功能會在後續步驟加入。" /></div></AppShell>;
}
