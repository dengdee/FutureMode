import { redirect } from "next/navigation";

export default async function DeprecatedWorkspaceMeetingsPage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = await params;
  redirect(`/workspaces/${workspaceId}`);
}
