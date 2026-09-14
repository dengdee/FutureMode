import Link from "next/link";

export const metadata = {
  title: "支援中心｜Proximate",
  description: "Proximate 支援中心，說明如何停止使用、解除安裝 Google Meet Add-on 與撤銷授權。",
};

export default function SupportPage() {
  return (
    <main className="min-h-screen bg-[#f4f7f6] px-5 py-10 text-[#15201d] sm:px-8 sm:py-16">
      <article className="mx-auto max-w-3xl rounded-2xl border border-[#e6e6e3] bg-white p-6 shadow-sm sm:p-10">
        <Link href="/" className="text-sm font-semibold text-[#0f9f8a] hover:underline">Proximate</Link>
        <p className="mt-6 text-sm font-semibold uppercase tracking-[0.18em] text-[#0f9f8a]">Support</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight">支援中心</h1>
        <p className="mt-3 text-sm leading-6 text-[#60706b]">在這裡查看如何停止使用 Proximate、解除 Google Meet Add-on，或處理帳號授權。</p>

        <div className="mt-8 space-y-7 text-sm leading-7 text-[#374741]">
          <section>
            <h2 className="text-lg font-semibold text-[#15201d]">停止使用 Proximate</h2>
            <p className="mt-2">你可以停止登入與使用 Proximate。若要移除已建立的會議資料或工作區內容，請先在應用程式內完成必要的資料管理，再停止使用帳號。</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-[#15201d]">解除安裝 Google Meet Add-on</h2>
            <p className="mt-2">在 Google Meet 開啟「活動」面板，找到 Proximate 後開啟外掛選單，選擇移除或解除安裝。若由 Google Workspace 管理員部署，請聯絡管理員協助從組織中移除。</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-[#15201d]">撤銷 Google 授權</h2>
            <p className="mt-2">前往 Google 帳戶的第三方連線管理頁面，找到 Proximate 並選擇移除存取權。撤銷授權後，下一次使用需要重新完成授權。</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-[#15201d]">收音與會議資料</h2>
            <p className="mt-2">收音只會在你明確授權並開始收音後啟用。你可以在會議頁停止收音；會議結束時系統也會停止收音。請在錄音前取得所有與會者的同意。</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-[#15201d]">需要協助</h2>
            <p className="mt-2">若遇到登入、安裝、解除安裝或資料處理問題，請透過 Proximate 應用程式中的支援管道聯絡我們，並提供發生問題的頁面與時間；請勿在訊息中提供密碼或存取金鑰。</p>
          </section>
        </div>

        <p className="mt-10 border-t border-[#ededeb] pt-5 text-sm text-[#60706b]">
          相關文件： <Link href="/privacy" className="text-[#0f9f8a] hover:underline">隱私權政策</Link> · <Link href="/terms" className="text-[#0f9f8a] hover:underline">服務條款</Link>
        </p>
      </article>
    </main>
  );
}
