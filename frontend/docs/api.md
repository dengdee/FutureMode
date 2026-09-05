# API 串接規則

## 共用設定

- Client：`lib/api/client.ts`，使用 Axios。
- Base URL：`NEXT_PUBLIC_API_BASE_URL`，本機預設 `http://localhost:8000`。
- API function 依功能各自放在 `lib/api/*.ts`，頁面不可直接散落 Axios 呼叫。
- JSON body 才設定 `Content-Type`；GET 只使用 `Accept`，避免不必要的 CORS preflight。
- API key 與第三方 token 只由後端持有；MVP 前端沿用 Neon Auth session，不自行保存長效 token。
- `/api/v1/*` 請求會由 Axios interceptor 讀取 Neon Auth session 的短效 JWT，加入 `Authorization: Bearer <token>`；FastAPI 以 Neon JWKS 驗證，前端不會轉送 httpOnly cookie。
- Next.js adapter 不把 JWT 放在 `getSession()` 回傳的 session object；interceptor 會透過同源 `/api/auth/token` 取得短效 token，再附加 Bearer header。

## 目前已封裝

| 檔案 | Functions | Endpoint |
| --- | --- | --- |
| `system.ts` | `getHealth`, `getReady` | `GET /health`, `GET /ready` |
| `meetbot.ts` | `joinMeetingBot` | `POST /meetbot/join` |
| `me.ts` | `getCurrentUser`, `updateCurrentUser` | `GET/PATCH /api/v1/me` |
| `teams.ts` | 團隊、成員、改名、刪除、邀請 CRUD | `/api/v1/teams...` |
| `meetings.ts` | list／get／create／update／start／end／cancel | `/api/v1/meetings` |
| `participants.ts` | add／list／update／remove | `/api/v1/meetings/{meeting_id}/participants` |
| `agenda.ts` | add／list／update／remove | `/api/v1/meetings/{meeting_id}/agenda` |
| `meeting-features.ts` | 逐字稿轉錄、共識、回饋、行動項目、建議、投票明細、個人訊息與公開預覽／發布 | `/api/v1/meetings/{meeting_id}/...` |
| `documents.ts` | 文件清單、建立、上傳、索引、封存、刪除、下載、版本、chunk、記憶搜尋 | `/api/v1/teams/{team_id}/documents`、`/api/v1/documents/...` |

目前另有 `meetbot.ts`（join、status、leave、speak）與 `delegates.ts`（Delegate profile 建立／列表）。

建立議程與新增參與者的 response 是精簡建立結果，分別為 `id/meeting_id/position` 與 `meeting_id/user_id/role`；完整欄位需再呼叫列表 API 取得，前端型別已按此區分。

## 畫面接入狀態

| Endpoint 群組 | Web App 使用位置 | 狀態 |
| --- | --- | --- |
| health／ready | 系統診斷工具 | API function 保留；Dashboard 不再顯示健康檢查 |
| me | Settings 個人資料表單 | 已接入讀取／更新；登入身分由 Neon Auth 顯示 |
| teams／members | 工作區清單、成員顯示、建立會議的工作區選擇 | 已接入 |
| meetings | Dashboard 總覽、團隊頁、建立會議、會前準備 | 已接入 |
| agenda | 建立會議、會前準備的新增／修改／刪除／狀態更新 | 已接入 |
| participants | 會前準備的讀取／加入／出席狀態更新／移除 | 已接入 |
| meeting features | Review 結論、逐字稿、回饋、行動項目與 suggestions | 已接入 Web App／Live／Add-on |
| documents | Team Memory 清單、拖曳上傳、搜尋與生命週期操作 | 已接入 |
| meetbot/join | API function 保留供整合測試；正式 Prepare UI 不直接觸發 | 已封裝，產品操作待 meeting-scoped contract |

## 目前限制

- 成員 API 已提供 `user_id`，前端可安全加入會議參與者。
- Live 音訊串流與 WebSocket 事件尚待後端 realtime gateway；Audio Setup 已接入批次 `/transcription`，Voice Bot 保留 join/status/leave/speak function。
- 單次會議文件透過 `metadata.meeting_id` 綁定會議；上傳限制 PDF／TXT。
