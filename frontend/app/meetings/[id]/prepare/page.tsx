import { AppShell, MeetingWorkspaceHeader, PlaceholderState } from "../../../../components/app-shell";

export default async function MeetingPreparePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AppShell><MeetingWorkspaceHeader meetingId={id} title="會前準備" /><PlaceholderState title="Prepare 頁面骨架" description="會議 Brief、議程與 Personal Sidekick 將在後續步驟加入。" /></AppShell>;
}
