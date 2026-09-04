# 前端製作進度

## 已完成

- Next.js 16 App Router、TypeScript、Tailwind CSS 4、Tabler Icons、GSAP 基礎。
- Landing Page `/`。
- Dashboard `/dashboard`：左右分欄、側欄收合、手機 Drawer、服務健康檢查與近期會議列表。
- 會議相關 UI：`/meetings/new`、`prepare`、`audio-setup`、`addon`、`live`、`review`。
- Memory、Settings、Sign-in、loading、error、404 UI。
- Axios 共用 client 與錯誤轉換。
- OpenAPI 現有 REST endpoint 的功能封裝：system、meetbot、me、teams、meetings、participants、agenda。

## API 已完成、UI 尚待接入

- 建立 Meeting 表單已送出 `createMeeting`，成功後導向 Prepare；更新表單與議程／參與者完整編輯尚未完成。
- 參與者與議程 API 已封裝，但尚未在 Prepare／建立會議頁完成完整互動。
- `getCurrentUser`、團隊與成員 API 已封裝，Neon Auth session 與 route guard 尚未完成。

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
