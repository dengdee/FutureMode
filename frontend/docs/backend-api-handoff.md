# 前端提供給後端的 API 契約確認

## 目的

前端已封裝 `POST /api/v1/meetings/{meeting_id}/participants`，但會前準備頁目前無法安全提供新增參與者操作，因為成員清單與新增 API 使用不同識別碼。

## 目前契約

`GET /api/v1/teams/{team_id}/members` 目前回傳：

```json
{"members":[{"external_id":"neon-user-or-provider-id","display_name":"使用者名稱","role":"member"}]}
```

`POST /api/v1/meetings/{meeting_id}/participants` 目前要求：

```json
{"user_id":"資料庫 users.id UUID","role":"participant"}
```

`user_id` 必須是資料庫既有使用者 UUID，不是前端可以任意產生的值。前端自行產生 UUID 會找不到對應的 `users`／`team_members` 紀錄。

## 「前端可以自己傳 UUID」的正確定義

如果後端的意思是前端可以把 UUID 放進 request，該 UUID 必須由後端 API 回傳，且已確認屬於目前團隊成員。前端不應自行產生或猜測 UUID。

## 建議方案

### A. 在 team member response 加入 `user_id`（建議）

```json
{"members":[{"user_id":"uuid","external_id":"provider-id","display_name":"使用者名稱","role":"member"}]}
```

前端以 `user_id` 作為選取值，只放入 API request，不直接顯示給使用者。

### B. participants endpoint 接受 `external_id`

```json
{"external_id":"provider-id","role":"participant"}
```

後端負責解析 UUID，並驗證使用者屬於會議所在團隊。

### C. 提供語意化 endpoint

```http
POST /api/v1/meetings/{meeting_id}/participants/from-team-member
```

```json
{"external_id":"provider-id","role":"participant"}
```

## 請後端一併確認

- 重複加入回傳 `409` 與穩定錯誤碼。
- 非團隊成員回傳 `400` 或 `403`，並維持統一錯誤格式。
- response 是否補回 `display_name` 與 `external_id`。
- `role` 可用值，以及缺席但由個人 Agent 代理時是否需要額外欄位。
- 更新／移除 participant 是否仍使用內部 `user_id`。

## 前端目前處理

- 已完成 participants API function：新增、列表、更新、移除。
- UI 已顯示既有參與者，可更新出席狀態與移除。
- 契約確認前，不顯示手動 UUID 欄位，也不自行產生 UUID。
