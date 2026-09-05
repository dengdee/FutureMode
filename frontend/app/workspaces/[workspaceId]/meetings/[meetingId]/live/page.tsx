import { redirect } from "next/navigation";

export default async function WorkspaceMeetingLivePage({ params }: { params: Promise<{ workspaceId: string; meetingId: string }> }) {
  const { meetingId } = await params;
  redirect(`/meetings/${meetingId}/live`);
}
