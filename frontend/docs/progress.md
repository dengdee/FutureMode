# 前端製作進度

## 已完成

- Next.js 16 App Router、TypeScript、Tailwind CSS 4、Tabler Icons、GSAP 基礎。
- Noto Sans TC 可變字體已套用全站；表單控制項使用共用 `control-primary` 與 `rounded-primary` 樣式。
- Neon Auth 前端骨架已建立：server auth、`/api/auth/[...path]`、`proxy.ts`、登入／註冊 email/password UI。
- Landing Page `/`。
- Dashboard `/dashboard`：工作總覽、我的團隊數、跨團隊近期會議與快速建立會議入口；服務健康檢查、團隊記憶、待確認共識與行動項目不列入跨團隊畫面。
- 會議相關 UI：`/meetings/new`、`prepare`、`audio-setup`、`addon`、`live`、`review`。
- Memory、Settings、Sign-in、loading、error、404 UI。
- Axios 共用 client、錯誤轉換，以及 Neon Auth session JWT 的 Bearer header 注入。
- OpenAPI 現有 REST endpoint 已接至 Web App：system、me、teams、meetings、agenda、participants、Review、文件與 memory search。
- 工作區與建立會議頁改用正式 teams／meetings API；建立後會依序寫入議程。
- 工作區建立對話框可建立團隊；會前準備可從團隊成員加入參與者。
- 會前準備頁可讀取／修改會議、管理議程、更新／移除參與者、開始／結束會議；Voice Bot 目前只保留 API 封裝，不在 UI 直接觸發未受政策控管的 join。

## API 已完成、UI 受契約限制

- 成員 API 已提供 `user_id`，因此參與者可從團隊成員清單安全加入。
- Team／Workspace 的建立、改名、邀請與移除成員沒有後端 endpoint，因此不會以本地假資料模擬寫入。

## 等待後端契約

- Meeting access token handoff、Brief、Personal Sidekick、公開觀點與即時事件流程。
- Audio WebSocket、Live Snapshot、投票、Host policy、WebSocket event。
- Voice Bot meeting-scoped contract 與正式即時 UI。

## 驗證狀態

| 檢查 | 狀態 |
| --- | --- |
| TypeScript `tsc --noEmit` | 通過 |
| ESLint | 尚未驗證（目前 shell 的 `npm` 不在 PATH） |
| `git diff --check` | 通過 |
| Next production build | 受本機 Windows Turbopack 子程序權限阻擋，需在可 spawn 子程序的環境重試 |
