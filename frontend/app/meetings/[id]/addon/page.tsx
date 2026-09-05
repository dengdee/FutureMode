import { AddonShell } from "../../../../components/meeting-addon/addon-shell";

export default async function AddonPage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<{ preview?: string }> }) {
  const { id } = await params;
  const { preview } = await searchParams;
  return <AddonShell meetingId={id} preview={preview === "live"} />;
}
