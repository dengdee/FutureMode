# API 串接規則

## 共用設定

- Client：`lib/api/client.ts`，使用 Axios。
- Base URL：`NEXT_PUBLIC_API_BASE_URL`，本機預設 `http://localhost:8000`。
- API function 依功能各自放在 `lib/api/*.ts`，頁面不可直接散落 Axios 呼叫。
- JSON body 才設定 `Content-Type`；GET 只使用 `Accept`，避免不必要的 CORS preflight。
- API key 與第三方 token 只由後端持有；前端只接收可公開的 response 或短效 meeting token。
- `/api/v1/*` 請求會由 Axios interceptor 讀取 Neon Auth session 的短效 JWT，加入 `Authorization: Bearer <token>`；FastAPI 以 Neon JWKS 驗證，前端不會轉送 httpOnly cookie。

## 目前已封裝

| 檔案 | Functions | Endpoint |
| --- | --- | --- |
| `system.ts` | `getHealth`, `getReady` | `GET /health`, `GET /ready` |
| `meetbot.ts` | `joinMeetingBot` | `POST /meetbot/join` |
| `me.ts` | `getCurrentUser` | `GET /api/v1/me` |
| `teams.ts` | `listTeams`, `listTeamMembers` | `GET /api/v1/teams`, `/teams/{team_id}/members` |
| `meetings.ts` | list／get／create／update／start／end | `/api/v1/meetings` |
| `participants.ts` | add／list／update／remove | `/api/v1/meetings/{meeting_id}/participants` |
| `agenda.ts` | add／list／update／remove | `/api/v1/meetings/{meeting_id}/agenda` |

建立議程與新增參與者的 response 是精簡建立結果，分別為 `id/meeting_id/position` 與 `meeting_id/user_id/role`；完整欄位需再呼叫列表 API 取得，前端型別已按此區分。

## 畫面接入狀態

| Endpoint 群組 | Web App 使用位置 | 狀態 |
| --- | --- | --- |
| health／ready | 系統診斷工具 | API function 保留；Dashboard 不再顯示健康檢查 |
| me | App Shell 身分區 | 已接入 |
| teams／members | 工作區清單、成員顯示、建立會議的工作區選擇 | 已接入 |
| meetings | Dashboard、工作區、建立會議、會前準備 | 已接入 |
| agenda | 建立會議、會前準備的新增／修改／刪除／狀態更新 | 已接入 |
| participants | 會前準備的讀取／出席狀態更新／移除 | 已接入（新增受下列契約缺口阻擋） |
| meetbot/join | API function 保留供整合測試；正式 Prepare UI 不直接觸發 | 已封裝，產品操作待 meeting-scoped contract |

## 已知後端契約缺口

`GET /api/v1/teams/{team_id}/members` 回傳 `external_id`，但 `POST /api/v1/meetings/{meeting_id}/participants` 要求資料庫內部 `user_id` UUID。為避免讓使用者輸入 UUID，前端不會顯示新增參與者控制項。後端應擇一調整：

1. 在 team member response 加入可用於 participant API 的 `user_id`；或
2. 將 participant create request 改為接受 `external_id`；或
3. 提供「由 team member 加入會議」endpoint。

## 尚未有後端 endpoint

Brief、Sidekick、Live Snapshot、vote、Review、Consensus、Memory、Settings 與 WebSocket 都不可由前端自行猜測。接入前需取得 request／response、錯誤碼、權限與事件 envelope。

工作區建立與成員邀請同樣尚未有寫入 endpoint。Memory 的團隊共用文件與單次會議文件目前是 UI 範圍選擇；單次會議文件必須先選定特定會議，正式檔案上傳與依 meeting 保存仍等待後端 API。
