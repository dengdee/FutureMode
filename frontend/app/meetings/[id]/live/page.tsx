import { IconExternalLink, IconRefresh } from "@tabler/icons-react";
import Link from "next/link";
import { AppShell } from "../../../../components/app-shell";
import { MeetingWorkspaceHeader } from "../../../../components/meeting-workspace-header";

export default async function LivePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AppShell><MeetingWorkspaceHeader meetingId={id} phase="live" /><div className="mt-7 grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]"><section className="rounded-2xl border border-[#e6e6e3] bg-white p-6"><p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#2f6f5e]">Browser fallback</p><h2 className="mt-2 text-2xl font-semibold">在瀏覽器查看會議即時狀態</h2><p className="mt-3 max-w-xl text-sm leading-6 text-[#787774]">無法開啟 Google Meet Add-on 時，可在這裡查看相同的公開資訊與 AI 建議。此頁不會重新登入 Add-on。</p><div className="mt-7 rounded-xl border border-dashed border-[#d8d8d5] bg-[#f7f7f5] px-5 py-12 text-center"><p className="font-medium">正在等待即時會議資料</p><p className="mt-2 text-sm text-[#787774]">正式 WebSocket 與 meeting token 完成後，此區將自動更新。</p><button className="mt-5 inline-flex items-center gap-2 rounded-lg border border-[#d8d8d5] bg-white px-4 py-2 text-sm font-medium"><IconRefresh size={17} />重新整理狀態</button></div></section><aside className="rounded-2xl border border-[#e6e6e3] bg-white p-5"><h2 className="font-semibold">返回 Google Meet</h2><p className="mt-2 text-sm leading-6 text-[#787774]">建議保持 Google Meet 與 Capture Page 開啟，以維持會議與收音流程。</p><Link href={`/meetings/${id}/audio-setup`} className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#2f6f5e]">查看 Capture 狀態 <IconExternalLink size={16} /></Link></aside></div></AppShell>;
}
