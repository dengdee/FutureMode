import { redirect } from "next/navigation";

export default async function WorkspaceMeetingPreparePage({ params }: { params: Promise<{ workspaceId: string; meetingId: string }> }) {
  const { meetingId } = await params;
  redirect(`/meetings/${meetingId}/prepare`);
}
