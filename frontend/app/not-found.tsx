import Link from "next/link";

export default function NotFound() {
  return <main className="grid min-h-screen place-items-center bg-[#fbfbfa] p-6 text-center"><div><p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#2f6f5e]">404</p><h1 className="mt-3 text-3xl font-semibold">找不到這個頁面</h1><p className="mt-3 text-sm text-[#787774]">請確認網址，或回到你的會議工作區。</p><Link href="/dashboard" className="mt-6 inline-block rounded-lg bg-[#2f6f5e] px-4 py-2.5 text-sm font-semibold text-white">返回 Dashboard</Link></div></main>;
}
