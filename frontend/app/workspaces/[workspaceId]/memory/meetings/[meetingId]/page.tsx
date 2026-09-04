import { redirect } from "next/navigation";

export default async function MeetingMemoryPage({ params }: { params: Promise<{ workspaceId: string; meetingId: string }> }) {
  const { workspaceId, meetingId } = await params;
  redirect(`/memory?teamId=${workspaceId}&meetingId=${meetingId}&scope=meeting`);
}
