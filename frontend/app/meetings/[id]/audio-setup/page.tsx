import { AppShell, MeetingWorkspaceHeader, PlaceholderState } from "../../../../components/app-shell";

export default async function AudioSetupPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AppShell><MeetingWorkspaceHeader meetingId={id} title="收音設定" /><PlaceholderState title="Audio Setup 技術骨架" description="收音與連線狀態會在後續步驟加入。" /></AppShell>;
}
