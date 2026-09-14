import Link from "next/link";

export const metadata = {
  title: "服務條款｜Proximate",
  description: "Proximate 服務條款。",
};

export default function TermsPage() {
  return (
    <main className="min-h-screen bg-[#f4f7f6] px-5 py-10 text-[#15201d] sm:px-8 sm:py-16">
      <article className="mx-auto max-w-3xl rounded-2xl border border-[#e6e6e3] bg-white p-6 shadow-sm sm:p-10">
        <Link href="/" className="text-sm font-semibold text-[#0f9f8a] hover:underline">Proximate</Link>
        <h1 className="mt-6 text-3xl font-semibold tracking-tight">服務條款</h1>
        <p className="mt-3 text-sm text-[#60706b]">最後更新日期：2026 年 9 月 14 日</p>

        <div className="mt-8 space-y-7 text-sm leading-7 text-[#374741]">
          <section><h2 className="text-lg font-semibold text-[#15201d]">1. 接受條款</h2><p className="mt-2">使用 Proximate 即表示你同意遵守本服務條款及適用法律。若你不同意，請停止使用本服務。</p></section>
          <section><h2 className="text-lg font-semibold text-[#15201d]">2. 帳號與工作區</h2><p className="mt-2">你應提供正確的帳號資訊並妥善保管登入憑證。你在工作區中的操作與分享內容，應確保已取得必要授權。</p></section>
          <section><h2 className="text-lg font-semibold text-[#15201d]">3. 合法使用</h2><p className="mt-2">不得利用本服務進行違法、侵害他人權利、未經同意錄音、散布惡意程式或干擾服務運作的行為。</p></section>
          <section><h2 className="text-lg font-semibold text-[#15201d]">4. 會議內容</h2><p className="mt-2">你保留對所提交會議內容的權利，並授予 Proximate 在提供、保存及改善相關功能所必要範圍內處理該內容的權利。請勿提交你無權使用的內容。</p></section>
          <section><h2 className="text-lg font-semibold text-[#15201d]">5. 服務變更與中止</h2><p className="mt-2">我們可能因維護、安全或產品調整而變更、暫停或終止部分功能，並會在合理範圍內提供通知。</p></section>
          <section><h2 className="text-lg font-semibold text-[#15201d]">6. 聯絡與條款更新</h2><p className="mt-2">條款更新後會在本頁標示日期。若你對本條款有疑問，請透過 Proximate 應用程式中的支援管道聯絡我們。</p></section>
        </div>
        <p className="mt-10 border-t border-[#ededeb] pt-5 text-sm text-[#60706b]">相關文件：<Link href="/privacy" className="text-[#0f9f8a] hover:underline">隱私權政策</Link></p>
      </article>
    </main>
  );
}
