"use client";

import { IconSparkles } from "@tabler/icons-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { authClient, toAuthErrorMessage } from "../../lib/auth/client";

export default function SignUpPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [registered, setRegistered] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(null);
    const normalizedEmail = email.trim().toLowerCase();
    const normalizedName = name.trim();
    if (!normalizedName) { setError("請輸入名稱。"); return; }
    if (password !== confirmPassword) { setError("兩次輸入的密碼不一致。"); return; }
    if (!/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/[0-9]/.test(password)) {
      setError("密碼至少 8 碼，並包含大小寫英文與數字。"); return;
    }
    setLoading(true);
    try {
      const result = await authClient.signUp.email({ name: normalizedName, email: normalizedEmail, password });
      if (result.error) { setError(toAuthErrorMessage(result.error, "註冊")); return; }
      // Neon Auth may require email verification before creating a session.
      // Do not redirect to a protected page in that case: it looks like signup failed.
      const session = await authClient.getSession();
      if (session.data?.user) router.push("/workspaces");
      else setRegistered(true);
    } catch (cause) { setError(toAuthErrorMessage(cause, "註冊")); }
    finally { setLoading(false); }
  }

  return <main className="grid min-h-screen bg-[#fbfbfa] lg:grid-cols-2"><section className="flex flex-col justify-between p-6 sm:p-10"><Link href="/" className="text-lg font-semibold tracking-tight">Proximate</Link>{registered ? <div className="mx-auto w-full max-w-sm"><p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#0f9f8a]">Almost there</p><h1 className="mt-3 text-3xl font-semibold tracking-tight">請驗證你的 Email</h1><p className="mt-5 leading-7 text-[#787774]">驗證信已寄到 <span className="font-medium text-[#292826]">{email.trim().toLowerCase()}</span>。請完成驗證後再登入 Proximate。</p><Link href="/sign-in" className="mt-7 flex w-full items-center justify-center rounded-primary bg-[#0f9f8a] px-4 py-3 text-sm font-semibold text-white hover:bg-[#0b8978]">前往登入</Link></div> : <form onSubmit={submit} className="mx-auto w-full max-w-sm"><p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#0f9f8a]">Get started</p><h1 className="mt-3 text-3xl font-semibold tracking-tight">註冊</h1><label className="mt-7 block text-sm font-medium">名稱<input required value={name} onChange={(event) => setName(event.target.value)} className="control-primary mt-2" /></label><label className="mt-4 block text-sm font-medium">Email<input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="control-primary mt-2" /></label><label className="mt-4 block text-sm font-medium">密碼<input required minLength={8} type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="control-primary mt-2" aria-describedby="password-hint" /></label><p id="password-hint" className="mt-1 text-xs text-[#787774]">至少 8 碼，包含大小寫英文與數字。</p><label className="mt-4 block text-sm font-medium">確認密碼<input required minLength={8} type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} className="control-primary mt-2" /></label>{error && <p role="alert" className="mt-4 rounded-primary bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}<button disabled={loading} type="submit" className="mt-6 flex w-full items-center justify-center rounded-primary bg-[#0f9f8a] px-4 py-3 text-sm font-semibold text-white hover:bg-[#0b8978] disabled:opacity-60">{loading ? "註冊中…" : "註冊"}</button><p className="mt-5 text-center text-sm text-[#787774]">已經有帳號？ <Link href="/sign-in" className="font-medium text-[#0f9f8a] hover:underline">登入</Link></p></form>}<p className="text-xs text-[#9b9b97]">Proximate · thoughtful meetings, together</p></section><aside className="hidden bg-[#0f9f8a] p-10 text-white lg:flex lg:flex-col lg:justify-end"><IconSparkles size={34} /><h2 className="mt-6 max-w-md text-4xl font-semibold leading-tight">讓團隊的不同觀點，成為更好的決策。</h2><p className="mt-5 max-w-md text-white/70">建立工作區、邀請成員，讓每場會議都有共同脈絡。</p></aside></main>;
}
