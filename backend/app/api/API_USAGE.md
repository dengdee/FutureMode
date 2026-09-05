# Proximate API 用途說明

Base URL：`http://localhost:8000`

除 `/health`、`/ready`、`/api/auth/config` 外，`/api/v1/*` 需要 Neon Auth 驗證。前端請以 Axios `withCredentials: true` 並帶上 `Authorization: Bearer <session.token>`。

## 系統與認證

| Method | Endpoint | 用途 |
|---|---|---|
| GET | `/health` | API 存活檢查 |
| GET | `/ready` | API、資料庫與外部服務就緒狀態 |
| GET | `/api/auth/config` | 取得認證設定 |

## 個人、團隊與成員

| Method | Endpoint | 用途 |
|---|---|---|
| GET/PATCH | `/api/v1/me` | 取得／修改目前使用者 |
| GET/POST | `/api/v1/teams` | 取得／建立團隊 |
| PATCH/DELETE | `/api/v1/teams/{team_id}` | 修改／刪除團隊 |
| GET/PATCH/DELETE | `/api/v1/teams/{team_id}/members[/{user_id}]` | 成員列表、角色修改、移除 |
| GET/POST | `/api/v1/teams/{team_id}/invitations` | Admin 查看／建立站內邀請（不寄送 Email） |
| DELETE | `/api/v1/teams/{team_id}/invitations/{invitation_id}` | 取消邀請 |
| GET | `/api/v1/me/invitations` | 目前登入者查看自己的待處理站內邀請 |
| POST | `/api/v1/me/invitations/{invitation_id}/accept` | 接受邀請並加入團隊 |
| POST | `/api/v1/me/invitations/{invitation_id}/decline` | 拒絕邀請 |

## 會議、參與者與議程

| Method | Endpoint | 用途 |
|---|---|---|
| GET/POST | `/api/v1/meetings` | 查詢／建立會議 |
| GET/PATCH | `/api/v1/meetings/{meeting_id}` | 查詢／修改會議 |
| POST | `/api/v1/meetings/{meeting_id}/start` | 開始會議 |
| POST | `/api/v1/meetings/{meeting_id}/end` | 結束會議 |
| POST | `/api/v1/meetings/{meeting_id}/cancel` | 取消會議 |
| GET/PATCH | `/api/v1/meetings/{meeting_id}/state` | 取得／更新即時狀態 |
| POST | `/api/v1/meetings/{meeting_id}/brief` | 產生會議 Brief／議程建議 |
| GET/POST | `/api/v1/meetings/{meeting_id}/participants` | 參與者列表／新增 |
| PATCH/DELETE | `/api/v1/meetings/{meeting_id}/participants/{user_id}` | 修改／移除參與者 |
| GET/POST | `/api/v1/meetings/{meeting_id}/agenda` | 議程列表／新增 |
| PATCH/DELETE | `/api/v1/meetings/{meeting_id}/agenda/{item_id}` | 修改／刪除議程 |

## 逐字稿、共識與行動項目

| Method | Endpoint | 用途 |
|---|---|---|
| GET | `/api/v1/meetings/{meeting_id}/transcripts` | 查詢逐字稿 |
| POST | `/api/v1/meetings/{meeting_id}/transcription` | 接收逐字稿 |
| POST | `/api/v1/meetings/{meeting_id}/transcripts/backup` | 備份 Meeting BaaS 逐字稿 |
| GET/POST | `/api/v1/meetings/{meeting_id}/consensus` | 查詢／建立共識 |
| GET/POST | `/api/v1/meetings/{meeting_id}/consensus/{version_id}/feedback` | 查詢／提交共識回饋 |
| POST | `/api/v1/meetings/{meeting_id}/consensus/{version_id}/confirm` | 確認共識版本 |
| GET/POST | `/api/v1/meetings/{meeting_id}/action-items` | 查詢／建立行動項目 |
| PATCH/DELETE | `/api/v1/meetings/{meeting_id}/action-items/{item_id}` | 修改／刪除行動項目 |

## 建議、個人訊息與 Team Memory

| Method | Endpoint | 用途 |
|---|---|---|
| GET | `/api/v1/meetings/{meeting_id}/suggestions` | 查詢會議建議 |
| POST | `/api/v1/meetings/{meeting_id}/suggestions/{suggestion_id}/vote` | 對建議投票 |
| PATCH | `/api/v1/meetings/{meeting_id}/suggestions/{suggestion_id}` | 修改建議狀態 |
| GET | `/api/v1/meetings/{meeting_id}/suggestions/{suggestion_id}/votes` | 查詢投票 |
| GET/POST | `/api/v1/meetings/{meeting_id}/personal/messages` | 查詢／建立個人訊息 |
| GET/POST | `/api/v1/meetings/{meeting_id}/preparation/messages` | 查詢／建立議前 AI 對話；建立時由 Gemini 免費額度模型回覆 |
| POST | `/api/v1/meetings/{meeting_id}/personal/contributions/preview` | 預覽個人貢獻 |
| POST | `/api/v1/meetings/{meeting_id}/personal/contributions/publish` | 發布個人貢獻 |
| GET/POST | `/api/v1/teams/{team_id}/documents` | 文件列表／建立文件紀錄 |
| GET | `/api/v1/teams/{team_id}/memory/hybrid-search` | Team Memory 混合搜尋 |
| GET | `/api/v1/documents/{document_id}` | 文件詳細資料 |
| POST | `/api/v1/documents/{document_id}/upload` | 上傳文件並啟動 ingestion |
| GET | `/api/v1/documents/{document_id}/chunks` | 文件切分內容 |
| POST | `/api/v1/documents/{document_id}/archive` | 封存文件 |
| DELETE | `/api/v1/documents/{document_id}` | 刪除文件與 R2 檔案 |
| GET | `/api/v1/documents/{document_id}/download-url` | 取得下載 URL |
| GET | `/api/v1/documents/{document_id}/storage-status` | 檢查 R2 檔案狀態 |
| POST | `/api/v1/documents/{document_id}/embed` | 建立／重建 embedding |

## Meeting Bot 與即時事件

| Method | Endpoint | 用途 |
|---|---|---|
| POST | `/meetbot/join` | Bot 加入會議 |
| GET | `/meetbot/{bot_id}` | 查詢 Bot 狀態 |
| POST | `/meetbot/{bot_id}/leave` | Bot 離開會議 |
| POST | `/meetbot/speak` | Bot 語音輸出 |
| WebSocket | `/meetbot/ws/audio-in` | Bot 音訊輸入串流 |
| WebSocket | `/api/v1/meetings/{meeting_id}/events` | 會議即時事件串流 |

## 常見錯誤

| Status | 意義 |
|---|---|
| 401 | 尚未登入或 token 無效 |
| 403 | 沒有執行此操作的權限 |
| 404 | 找不到資源 |
| 409 | 資源狀態衝突 |
| 422 | 請求欄位驗證失敗 |
| 502 | 外部服務錯誤 |

錯誤回應格式：

```json
{
  "error": {
    "code": "http_error",
    "message": "需要驗證身份",
    "request_id": "request-id"
  }
}
```

登入後建議依序測試：`GET /api/v1/me`、`GET /api/v1/teams`、`GET /api/v1/meetings`、`GET /api/v1/me/invitations`。

站內邀請以選定帳號的 `recipient_user_id` 配對已驗證身分，不依賴 Email claims 或 Email 驗證旗標，不寄送 Email。建立 body：`{"recipient_user_id":"<users/search 回傳的 id>","role":"member"}`。JWT 簽章、issuer、audience、有效期限仍會先驗證。舊 Email 邀請需由管理員取消後重新選擇帳號；資料庫需更新至 0021。完整流程與遷移方式見 [IN_APP_INVITATIONS.md](IN_APP_INVITATIONS.md)。

session Cookie 必須實際送到後端；缺少 Cookie／Email 回傳 403，session 過期或帳號不符回傳 401，上游失敗回傳 503。session 回應即使為 200，Email 未驗證仍回傳 403。測試使用真實簽章 JWT 與模擬 Neon Auth 回應；實際登入仍需確認瀏覽器請求包含 Cookie。
