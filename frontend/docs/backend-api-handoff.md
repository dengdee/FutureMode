# 前後端 API 串接與契約交接表

本文件以目前後端 `http://localhost:8000/openapi.json` 與前端程式為準，供後端確認契約及安排下一階段 API。前端所有請求集中在 `frontend/lib/api/*.ts`，由 Axios client 統一處理 Bearer token、錯誤 envelope 與狀態碼。

## 一、已建立 function 且已呈現在 UI

| API | 前端 function | UI 位置 | 狀態 |
| --- | --- | --- | --- |
| `GET/PATCH /api/v1/me` | `getCurrentUser`／`updateCurrentUser` | Settings 個人資料讀取與更新；登入身分仍由 Neon Auth 顯示 | 已串接 |
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

## 二、已建立 function，但目前沒有完整 UI 操作

| API | 前端 function | 沒有 UI 的原因 |
| --- | --- | --- |
| `POST /api/v1/meetings/{meeting_id}/participants` | `addParticipant` | 會前準備已提供成員選擇與加入操作 | 已串接 |
| `POST /meetbot/join` | `joinMeetingBot` | 目前是未綁定 meeting 的測試 join，缺少 meeting scope、Host 權限、政策／投票核准與穩定 response schema；因此不在正式 Prepare UI 直接觸發 |
| `GET /health` | `getHealth` | 保留給系統診斷；依產品要求已從 Dashboard 移除 |
| `GET /ready` | `getReady` | 保留給系統診斷；依產品要求已從 Dashboard 移除 |

## 三、目前尚未接入正式 UI 的後端能力

以下為後端已有 REST endpoint、但前端尚未做完整操作介面的項目；API function 已集中封裝，後續可直接接入。

| 產品功能 | 預期前端頁面 | 需要後端提供 |
| --- | --- | --- |
| 團隊改名、刪除與邀請寄送 | `/workspaces` | 目前前端僅完成建立團隊與成員列表 |
| 團隊邀請與成員管理 | `/workspaces/[workspaceId]/members` | invite、resend、remove、role update |
| 文件刪除、封存、下載與狀態 | `/memory` | 前端目前完成列表、拖曳上傳與搜尋 |
| 單次會議文件 | `/workspaces/[workspaceId]/memory/meetings/[meetingId]` | meeting-scoped upload、列表、刪除、權限 |
| Brief | `/meetings/[id]/prepare` | brief 查詢、重新生成、錯誤狀態 |
| Personal Sidekick | `/meetings/[id]/prepare` | 個人訊息、thread、draft、publish |
| Audio Capture | `/meetings/[id]/audio-setup` | session、WebSocket、收音狀態、重連 |
| Live Snapshot | `/meetings/[id]/live`、`addon` | 公開狀態、建議、參與者、政策 |
| Meeting token handoff | `/meetings/[id]/addon` | 短效 token、expiresAt、meeting/user scope |
| AI 建議與投票 | `/meetings/[id]/addon`、`live` | suggestions、support/later/ignore、重投票、門檻結果 |
| 共識回饋、建議狀態與投票明細 | `/meetings/[id]/review`、`live` | function 已建立，UI 尚未完整呈現 |
| Action Items 編輯、刪除、指派與期限 | `/meetings/[id]/review` | 目前 UI 已可新增與列表 |
| Personal Sidekick 訊息 | `/meetings/[id]/prepare` | 已提供私人訊息儲存操作；publish／預覽仍待補 |
| 會議取消 | `/meetings/[id]/prepare` | 已提供取消操作 |

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
- Add-on 不重新登入：Web App 先完成 Neon Auth，再由後端簽發單一 meeting 的短效 token。

## 六、前端交接問題

1. 工作區建立與邀請的完整 request／response、角色與權限。
2. Participants UUID 方案及新增後 response 是否包含 `display_name`。
3. 文件上傳的 multipart 欄位、大小限制、檔案類型、掃描與儲存狀態。
4. WebSocket URL、事件 envelope、重連與 token 過期行為。
5. WebSocket、Live Snapshot、Meet token handoff 與 meeting-scoped Voice Bot 的正式事件、錯誤碼與權限矩陣。

## 七、Brief／Agent 議程建議需求

目前前端的會議議程以手動新增與編輯為主，現有 Agenda API 僅提供議程 CRUD：

- `GET /api/v1/meetings/{meeting_id}/agenda`
- `POST /api/v1/meetings/{meeting_id}/agenda`
- `PATCH /api/v1/meetings/{meeting_id}/agenda/{item_id}`
- `DELETE /api/v1/meetings/{meeting_id}/agenda/{item_id}`

若產品需要 Agent 自動產生議程或建議討論順序，請後端提供 Brief／AI endpoint，例如：

```text
POST /api/v1/meetings/{meeting_id}/brief
```

建議 response 包含 `suggested_agenda`、`existing_consensus`、`disagreements`、`open_questions` 與 `recommended_order`。Agent 只提供建議，不得直接覆蓋使用者已輸入的議程；由使用者或本場 Host 確認、修改後，再透過正式 Agenda API 寫入。

請後端確認 Brief 的同步／非同步狀態、輸入是否包含 Team Memory 文件、重新產生是否保留版本，以及產生失敗時的錯誤格式。

## 2026-09-05 前端整合更新

目前後端已存在的 REST 已完成前端接入：團隊邀請／成員角色與移除、會議取消、文件封存／下載／刪除／版本還原、逐字稿批次轉錄、Consensus feedback、Suggestion vote 與明細、Action Items CRUD、Personal Sidekick 訊息／預覽／發布、Delegate profiles，以及 Meeting BaaS bot join／status／leave／speak function。

前端仍不假造下列尚不存在或契約未定的能力：meeting access-token handoff、Live Snapshot、intervention policy、Realtime WebSocket、VAD／streaming STT、meeting-scoped Voice Bot。這些需要後端提供正式路由、事件 envelope、權限與錯誤契約後才能接入。
