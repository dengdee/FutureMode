# 前後端 API 串接與契約交接表

本文件以目前後端路由與 `frontend/lib/api` 為準。前端請求統一經 Axios client，攜帶 Neon Auth cookie 與短效 JWT Bearer。

## 已串接且已有 UI

| 領域 | 已接入內容 | 主要 UI |
| --- | --- | --- |
| 身分／團隊 | me、團隊 CRUD、成員列表／角色／移除、邀請寄送 | Settings、`/workspaces` |
| 會議 | 建立／修改／開始／結束／取消、參與者、手動議程 CRUD | `/meetings/new`、Prepare |
| 會後 | transcripts、批次 transcription、consensus／confirm／feedback、action items CRUD | Review、Audio Setup |
| Suggestions | 清單、support／reject／abstain 投票 | Live、Add-on |
| Personal Sidekick | 私訊清單／新增、contribution preview／publish | Add-on |
| 文件 | upload／ingest、list、search、archive、download URL、delete、versions、restore | Team Memory |

## 後端已有、前端仍缺完整操作

| 後端路由 | 前端缺口 |
| --- | --- |
| `POST /api/v1/meetings/{id}/brief` | 尚未建立 Brief API wrapper 與 Prepare／Add-on 顯示、重生成、錯誤狀態 |
| `GET/PATCH /api/v1/meetings/{id}/state` | Live／Add-on 仍使用組合資料，尚未接 snapshot 版本與 CAS 更新 |
| `WS /api/v1/meetings/{id}/events` | 尚未建立認證、cursor、重連、事件去重與 UI reducer |
| `WS /meetbot/ws/audio-in` | Audio Setup 仍是批次 HTTP transcription，沒有串流 audio chunk |
| teams invitations GET／DELETE | 建立時可寄送，但沒有邀請清單、取消／重送 UI |
| documents versions／detail／chunks | 目前只有「還原最新版本」，沒有版本選擇與詳細內容檢視 |
| suggestion votes GET | wrapper 已有，Live／Review 尚未呈現逐人投票明細 |
| action item PATCH | 目前可編輯標題；assignee、due date、狀態欄位 UI 尚未完整 |
| delegates、meetbot join/status/leave/speak | 有 API wrapper，尚無正式 Web App 操作頁與 meeting-scoped 流程 |

## 仍需後端／部署決策

- Add-on 專用 meeting access-token handoff 與 Google Meet manifest／正式部署。
- Realtime 生產 broker、跨程序事件持久化，以及 VAD／streaming STT／meeting-scoped Voice Bot 的正式契約。

## 認證契約

- `/api/v1/*` 由 Axios interceptor 從同源 `/api/auth/token` 取得短效 token，並設定 `Authorization: Bearer ...`；Axios 同時使用 `withCredentials: true` 傳送 Neon Auth cookie。
- 後端錯誤預期為 `{ error: { code, message, request_id } }`；401 顯示需登入，403 顯示權限不足。
- Participants create 使用後端提供的 `user_id` UUID，前端不自行產生 UUID。
