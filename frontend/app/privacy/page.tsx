import Link from "next/link";

export const metadata = {
  title: "隱私權政策｜Proximate",
  description: "Proximate 隱私權政策，說明我們如何處理帳號、會議與 Google 服務資料。",
};

export default function PrivacyPage() {
  return (
    <main className="min-h-screen bg-[#f4f7f6] px-5 py-10 text-[#15201d] sm:px-8 sm:py-16">
      <article className="mx-auto max-w-3xl rounded-2xl border border-[#e6e6e3] bg-white p-6 shadow-sm sm:p-10">
        <Link href="/" className="text-sm font-semibold text-[#0f9f8a] hover:underline">Proximate</Link>
        <h1 className="mt-6 text-3xl font-semibold tracking-tight">隱私權政策</h1>
        <p className="mt-3 text-sm text-[#60706b]">最後更新日期：2026 年 9 月 14 日</p>

        <div className="mt-8 space-y-7 text-sm leading-7 text-[#374741]">
          <section><h2 className="text-lg font-semibold text-[#15201d]">1. 我們提供的服務</h2><p className="mt-2">Proximate 是協助團隊進行會前整理、會中協作與會後回顧的會議工具。</p></section>
          <section><h2 className="text-lg font-semibold text-[#15201d]">2. 我們收集的資料</h2><p className="mt-2">我們可能處理你提供的名稱、Email、工作區與會議資料，以及你在使用會議收音功能時產生的逐字稿與相關文字內容。</p></section>
          <section><h2 className="text-lg font-semibold text-[#15201d]">3. Google 資料的使用</h2><p className="mt-2">若你使用 Google 登入或 Google Meet 整合，我們只會依你授權的範圍使用必要資料，以提供登入、會議辨識與協作功能。我們不會出售 Google 使用者資料，也不會將其用於廣告。</p></section>
          <section><h2 className="text-lg font-semibold text-[#15201d]">4. 收音與逐字稿</h2><p className="mt-2">收音功能只有在你明確授權並開始收音後才會啟用。會議結束或你手動停止收音後，系統會停止擷取；請勿在未取得與會者同意的情況下錄音。</p></section>
          <section><h2 className="text-lg font-semibold text-[#15201d]">5. 保存與安全</h2><p className="mt-2">我們會採取合理的技術與管理措施保護資料，並僅在提供服務所需期間保存資料。你可以透過應用程式中的帳號或工作區功能管理相關內容。</p></section>
          <section><h2 className="text-lg font-semibold text-[#15201d]">6. 政策更新與聯絡</h2><p className="mt-2">我們可能因服務或法規變更更新本政策，更新後會在本頁標示日期。若你對隱私有疑問，請透過 Proximate 應用程式中的支援管道聯絡我們。</p></section>
        </div>
        <p className="mt-10 border-t border-[#ededeb] pt-5 text-sm text-[#60706b]">相關文件：<Link href="/terms" className="text-[#0f9f8a] hover:underline">服務條款</Link></p>
      </article>
    </main>
  );
}
