import { redirect } from "next/navigation";

export default async function SharedMemoryPage({ params }: { params: Promise<{ workspaceId: string }> }) {
  const { workspaceId } = await params;
  redirect(`/memory?teamId=${workspaceId}&scope=shared`);
}
