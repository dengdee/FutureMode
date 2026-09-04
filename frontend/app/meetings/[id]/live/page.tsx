import { AppShell, MeetingWorkspaceHeader, PlaceholderState } from "../../../../components/app-shell";

export default async function MeetingLivePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AppShell><MeetingWorkspaceHeader meetingId={id} title="即時會議" /><PlaceholderState title="Live fallback 骨架" description="瀏覽器 fallback 會在後續步驟承載即時會議 UI。" /></AppShell>;
}
