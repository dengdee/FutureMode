# API 串接規則

## 共用設定

- Client：`lib/api/client.ts`，使用 Axios。
- Base URL：`NEXT_PUBLIC_API_BASE_URL`，本機預設 `http://localhost:8000`。
- API function 依功能各自放在 `lib/api/*.ts`，頁面不可直接散落 Axios 呼叫。
- JSON body 才設定 `Content-Type`；GET 只使用 `Accept`，避免不必要的 CORS preflight。
- API key 與第三方 token 只由後端持有；前端只接收可公開的 response 或短效 meeting token。

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

## 尚未有後端 endpoint

Access token、Brief、Sidekick、Live Snapshot、vote、Review、Consensus、Memory、Settings 與 WebSocket 都不可由前端自行猜測。接入前需取得 request／response、錯誤碼、權限、token expiry 與事件 envelope。
