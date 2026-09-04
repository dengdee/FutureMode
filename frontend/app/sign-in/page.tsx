"use client";

import { IconSparkles } from "@tabler/icons-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { authClient, toAuthErrorMessage } from "../../lib/auth/client";

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [error, setError] = useState<string | null>(null); const [loading, setLoading] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setLoading(true); setError(null); try { const result = await authClient.signIn.email({ email, password }); if (result.error) setError(toAuthErrorMessage(result.error, "登入")); else router.push("/dashboard"); } catch (cause) { setError(toAuthErrorMessage(cause, "登入")); } finally { setLoading(false); } }
  return <main className="grid min-h-screen bg-[#fbfbfa] lg:grid-cols-2"><section className="flex flex-col justify-between p-6 sm:p-10"><Link href="/" className="text-lg font-semibold tracking-tight">Proximate</Link><form onSubmit={submit} className="mx-auto w-full max-w-sm"><p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#0f9f8a]">Welcome back</p><h1 className="mt-3 text-3xl font-semibold tracking-tight">登入工作區</h1><p className="mt-3 text-sm leading-6 text-[#787774]">使用 Neon Auth 登入你的 Proximate 帳號。</p><label className="mt-7 block text-sm font-medium">Email<input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="control-primary mt-2" /></label><label className="mt-4 block text-sm font-medium">密碼<input required type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="control-primary mt-2" /></label>{error && <p role="alert" className="mt-4 rounded-primary bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}<button disabled={loading} type="submit" className="mt-6 flex w-full items-center justify-center rounded-primary bg-[#0f9f8a] px-4 py-3 text-sm font-semibold text-white hover:bg-[#0b8978] disabled:opacity-60">{loading ? "登入中…" : "登入"}</button><p className="mt-5 text-center text-sm text-[#787774]">還沒有帳號？ <Link href="/sign-up" className="font-medium text-[#0f9f8a] hover:underline">註冊</Link></p></form><p className="text-xs text-[#9b9b97]">Proximate · thoughtful meetings, together</p></section><aside className="hidden bg-[#0f9f8a] p-10 text-white lg:flex lg:flex-col lg:justify-end"><IconSparkles size={34} /><h2 className="mt-6 max-w-md text-4xl font-semibold leading-tight">讓每個人的思考，在會議裡被看見。</h2><p className="mt-5 max-w-md text-white/70">會前整理、會中提醒、會後確認，保留每次重要決策的脈絡。</p></aside></main>;
}
