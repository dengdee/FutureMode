import { AppShell, MeetingWorkspaceHeader, PlaceholderState } from "../../../../components/app-shell";

export default async function MeetingReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AppShell><MeetingWorkspaceHeader meetingId={id} title="會後回顧" /><PlaceholderState title="Review 頁面骨架" description="共識、決策與行動項目將在後續步驟加入。" /></AppShell>;
}
