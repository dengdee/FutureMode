# 前端製作進度

## 已完成

- Next.js 16 App Router、TypeScript、Tailwind CSS 4、Tabler Icons、GSAP 基礎。
- Noto Sans TC 可變字體已套用全站；表單控制項使用共用 `control-primary` 與 `rounded-primary` 樣式。
- Neon Auth 前端骨架已建立：server auth、`/api/auth/[...path]`、`proxy.ts`、登入／註冊 email/password UI。
- Landing Page `/`。
- Dashboard `/dashboard`：左右分欄、側欄收合、手機 Drawer 與近期會議列表；服務健康檢查不列入產品畫面。
- 會議相關 UI：`/meetings/new`、`prepare`、`audio-setup`、`addon`、`live`、`review`。
- Memory、Settings、Sign-in、loading、error、404 UI。
- Axios 共用 client、錯誤轉換，以及 Neon Auth session JWT 的 Bearer header 注入。
- OpenAPI 現有 REST endpoint 已接至 Web App：system、meetbot、me、teams、meetings、agenda；participants 已接入讀取／更新／移除。
- 工作區與建立會議頁改用正式 teams／meetings API；建立後會依序寫入議程。
- 工作區建立對話框提供表格式邀請成員 UI：可輸入多個 Email、選擇 Member／Owner、增加或移除列；正式送出等待後端契約。
- 會前準備頁可讀取／修改會議、管理議程、更新／移除參與者、開始／結束會議；Voice Bot 目前只保留 API 封裝，不在 UI 直接觸發未受政策控管的 join。

## API 已完成、UI 受契約限制

- `POST /participants` 已封裝，但不顯示手動 UUID 欄位。team members 回傳 `external_id`，participant create 卻要求內部 `user_id` UUID；等待後端提供可安全選取的 member identifier。
- Team／Workspace 的建立、改名、邀請與移除成員沒有後端 endpoint，因此不會以本地假資料模擬寫入。

## 等待後端契約

- Meeting access token handoff、Brief、Personal Sidekick、公開觀點。
- Audio WebSocket、Live Snapshot、投票、Host policy、WebSocket event。
- Review／Consensus／Action Items、Memory search、Settings API。

## 驗證狀態

| 檢查 | 狀態 |
| --- | --- |
| TypeScript `tsc --noEmit` | 通過 |
| ESLint | 通過 |
| `git diff --check` | 通過 |
| Next production build | 受本機 Windows Turbopack 子程序權限阻擋，需在可 spawn 子程序的環境重試 |
