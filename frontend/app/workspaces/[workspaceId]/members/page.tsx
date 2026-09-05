import { redirect } from "next/navigation";

export default async function WorkspaceMembersPage({ params }: { params: Promise<{ workspaceId: string }> }) {
  await params;
  redirect("/workspaces");
}
