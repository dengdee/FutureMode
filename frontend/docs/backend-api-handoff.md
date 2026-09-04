# 前後端 API 串接與契約交接表

本文件以目前後端 `http://localhost:8000/openapi.json` 與前端程式為準，供後端確認契約及安排下一階段 API。前端所有請求集中在 `frontend/lib/api/*.ts`，由 Axios client 統一處理 Bearer token、錯誤 envelope 與狀態碼。

## 一、已建立 function 且已呈現在 UI

| API | 前端 function | UI 位置 | 狀態 |
| --- | --- | --- | --- |
| `GET /api/v1/me` | `getCurrentUser` | 保留作後端身分診斷；App Shell／Settings 的名稱改由 Neon Auth session 顯示 | 已封裝，非主要 UI 資料源 |
| `GET /api/v1/teams` | `listTeams` | 團隊頁、建立會議、團隊記憶工作區選擇 | 已串接 |
| `GET /api/v1/teams/{team_id}/members` | `listTeamMembers` | 團隊成員數量、會前準備成員資訊 | 已串接 |
| `GET /api/v1/meetings` | `listMeetings` | Dashboard、團隊頁、團隊記憶會議選擇 | 已串接 |
| `POST /api/v1/meetings` | `createMeeting` | 建立會議頁 | 已串接 |
| `GET /api/v1/meetings/{meeting_id}` | `getMeeting` | 會前準備頁 | 已串接 |
| `PATCH /api/v1/meetings/{meeting_id}` | `updateMeeting` | 修改會議名稱、AI 介入程度 | 已串接 |
| `POST /api/v1/meetings/{meeting_id}/start` | `startMeeting` | 開始會議按鈕 | 已串接 |
| `POST /api/v1/meetings/{meeting_id}/end` | `endMeeting` | 結束會議按鈕 | 已串接 |
| `GET /api/v1/meetings/{meeting_id}/agenda` | `listAgendaItems` | 會前準備議程清單 | 已串接 |
| `POST /api/v1/meetings/{meeting_id}/agenda` | `addAgendaItem` | 新增議程 | 已串接 |
| `PATCH /api/v1/meetings/{meeting_id}/agenda/{item_id}` | `updateAgendaItem` | 修改議程標題、狀態 | 已串接 |
| `DELETE /api/v1/meetings/{meeting_id}/agenda/{item_id}` | `removeAgendaItem` | 刪除議程 | 已串接 |
| `GET /api/v1/meetings/{meeting_id}/participants` | `listParticipants` | 會前準備參與者清單 | 已串接 |
| `PATCH /api/v1/meetings/{meeting_id}/participants/{user_id}` | `updateParticipant` | 更新出席狀態 | 已串接 |
| `DELETE /api/v1/meetings/{meeting_id}/participants/{user_id}` | `removeParticipant` | 移除參與者 | 已串接 |

## 二、已建立 function，但目前沒有 UI 操作

| API | 前端 function | 沒有 UI 的原因 |
| --- | --- | --- |
| `POST /api/v1/meetings/{meeting_id}/participants` | `addParticipant` | 後端要求內部 `user_id` UUID，但 members response 目前只有 `external_id`；前端不能讓使用者輸入或自行產生 UUID |
| `POST /meetbot/join` | `joinMeetingBot` | 目前是未綁定 meeting 的測試 join，缺少 meeting scope、Host 權限、政策／投票核准與穩定 response schema；因此不在正式 Prepare UI 直接觸發 |
| `GET /health` | `getHealth` | 保留給系統診斷；依產品要求已從 Dashboard 移除 |
| `GET /ready` | `getReady` | 保留給系統診斷；依產品要求已從 Dashboard 移除 |

## 三、後端目前完全尚未提供

以下功能目前沒有可供前端串接的正式 endpoint。前端只能保留 UI scaffold、路由與型別規劃，不能自行猜測 API。

| 產品功能 | 預期前端頁面 | 需要後端提供 |
| --- | --- | --- |
| 工作區建立、改名、刪除 | `/workspaces` | workspace CRUD、目前使用者權限 |
| 團隊邀請與成員管理 | `/workspaces/[workspaceId]/members` | invite、resend、remove、role update |
| 團隊共用文件 | `/workspaces/[workspaceId]/memory/shared` | multipart upload、檔案列表、刪除、權限與搜尋 |
| 單次會議文件 | `/workspaces/[workspaceId]/memory/meetings/[meetingId]` | meeting-scoped upload、列表、刪除、權限 |
| Brief | `/meetings/[id]/prepare` | brief 查詢、重新生成、錯誤狀態 |
| Personal Sidekick | `/meetings/[id]/prepare` | 個人訊息、thread、draft、publish |
| Audio Capture | `/meetings/[id]/audio-setup` | session、WebSocket、收音狀態、重連 |
| Live Snapshot | `/meetings/[id]/live`、`addon` | 公開狀態、建議、參與者、政策 |
| Meeting token handoff | `/meetings/[id]/addon` | 短效 token、expiresAt、meeting/user scope |
| AI 建議與投票 | `/meetings/[id]/addon`、`live` | suggestions、support/later/ignore、重投票、門檻結果 |
| Review／Consensus | `/meetings/[id]/review` | 摘要、版本、回覆、衝突與確認狀態 |
| Action Items | `/meetings/[id]/review` | action item CRUD、assignee、狀態與期限 |
| Memory RAG 搜尋 | 團隊記憶 | 搜尋、索引狀態、引用來源 |
| Settings 儲存 | `/settings` | 目前僅顯示 Neon Auth session 的帳號名稱；通知／權限設定 CRUD 待 API；團隊名稱與成員改由 `/workspaces` |

## 四、Participants UUID 契約

目前：

- `GET /api/v1/teams/{team_id}/members` 回傳 `external_id`。
- `POST /api/v1/meetings/{meeting_id}/participants` 要求 `user_id` UUID。
- 前端可以傳「後端提供且已驗證的 UUID」，但不能自行產生 UUID。

請後端擇一：

1. members response 加入 `user_id`；或
2. participants request 改接受 `external_id`，由後端解析 UUID；或
3. 提供 `POST /api/v1/meetings/{meeting_id}/participants/from-team-member`。

並確認重複加入的 `409`、非團隊成員的 `400/403`、可用 role，以及缺席但由個人 Agent 代理時的欄位。

## 五、共用錯誤與認證契約

- 前端預期錯誤 envelope：`{ "error": { "code", "message", "request_id" } }`。
- `401` 顯示「需要驗證身分，請先登入」；`403` 顯示權限不足。
- `/api/v1/*` 由 Axios interceptor 附加 Neon Auth Bearer token。
- Add-on 不重新登入，需使用單一 meeting 的短效 token。

## 六、前端交接問題

1. 工作區建立與邀請的完整 request／response、角色與權限。
2. Participants UUID 方案及新增後 response 是否包含 `display_name`。
3. 文件上傳的 multipart 欄位、大小限制、檔案類型、掃描與儲存狀態。
4. WebSocket URL、事件 envelope、重連與 token 過期行為。
5. Brief、Sidekick、Vote、Review、Memory、Settings 的正式 endpoint、錯誤碼與權限矩陣。
