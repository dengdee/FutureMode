import { MeetingWorkspaceHeader, PlaceholderState } from "../../../../components/app-shell";

export default async function MeetingAddonPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <div className="min-h-screen bg-[var(--background)] p-4 text-[var(--foreground)]"><MeetingWorkspaceHeader meetingId={id} title="Meet Add-on" /><PlaceholderState title="Add-on 窄版骨架" description="此路由不套用完整 App Shell；短效 meeting token 與 Meet SDK 尚未接入。" /></div>;
}
