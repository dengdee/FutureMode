import { redirect } from "next/navigation";

export default async function WorkspaceMeetingReviewPage({ params }: { params: Promise<{ workspaceId: string; meetingId: string }> }) {
  const { meetingId } = await params;
  redirect(`/meetings/${meetingId}/review`);
}
