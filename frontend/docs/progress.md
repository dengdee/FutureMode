# 前端製作進度

本表以目前 repository 的前端程式與後端已合併的 OpenAPI／WebSocket 路由為準；歷史規劃中的 endpoint 不代表已完成契約。

## 已完成（前端已有 REST 串接與可操作 UI）

- Next.js App Router、TypeScript、Tailwind、共用 App Shell、中文導覽與響應式基礎。
- Neon Auth 登入／註冊、session cookie、`withCredentials`，以及 `/api/v1/*` 的短效 JWT Bearer 注入。
- Dashboard、團隊清單／建立、團隊成員角色修改／移除，以及建立團隊後建立站內邀請（不寄送 Email）。
- 會議建立、修改、開始／結束／取消、參與者管理與手動議程 CRUD。
- Audio Setup 的瀏覽器收音與批次 `POST /api/v1/meetings/{id}/transcription`。
- Review 的逐字稿、Consensus 建立／確認／回饋、Action Items 新增／編輯標題／刪除。
- Live／Add-on 的 suggestions 清單與投票、Personal Sidekick 訊息／預覽／發布。
- Team Memory 文件清單、上傳／ingest、搜尋、封存、下載、刪除與版本還原（目前 UI 還原最新版本）。
- API function 另已封裝 Delegate profiles、Meeting BaaS Bot 與投票明細；尚未都有對應完整頁面。

## 後端已有、前端仍未完成的 UI／adapter

- `GET/PATCH /api/v1/meetings/{id}/state` 與 `WS /api/v1/meetings/{id}/events`：尚未建立前端 snapshot state、cursor、重連、事件去重與狀態更新 hook。
- `POST /api/v1/meetings/{id}/brief`：尚未在 Prepare／Add-on 顯示 Brief、重新生成與錯誤狀態。
- `WS /meetbot/ws/audio-in`：目前只有批次轉錄 UI，尚未做音訊 chunk、重連與權限狀態。
- Delegate profiles、Meeting BaaS bot join/status/leave/speak：有 API wrapper，尚無正式 Web App 操作頁與 meeting-scoped 流程。
- 邀請清單／取消邀請、文件版本選擇／詳細檢視／chunks、Action Item assignee／due date、suggestion vote details 的完整操作 UI 尚未補齊。

## 仍需後端契約或部署決策

- Add-on 專用 meeting access-token handoff、Google Meet manifest／正式部署。
- Realtime 的生產級 broker、事件持久化與跨程序一致性（目前後端是 in-process primitives）。
- VAD／streaming STT、meeting-scoped Voice Bot 的正式事件與權限矩陣。

## 驗證狀態

| 檢查 | 狀態 |
| --- | --- |
| TypeScript `tsc --noEmit` | 通過 |
| ESLint | 尚未驗證（本機 npm script 曾卡住） |
| `git diff --check` | 通過 |
| Next production build | 受本機 Windows Turbopack 子程序權限阻擋，需在可 spawn 子程序的環境重試 |
