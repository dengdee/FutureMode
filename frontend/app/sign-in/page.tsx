import { AppShell, PageHeader, PlaceholderState } from "../../components/app-shell";

export default function SignInPage() {
  return <AppShell><PageHeader eyebrow="Account" title="登入" description="正式登入流程尚未啟用。" /><div className="mt-8"><PlaceholderState title="未登入 placeholder" description="這裡只保留技術入口，不連接 Auth SDK 或建立 session。" /></div></AppShell>;
}
