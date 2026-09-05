# 站內團隊邀請

不寄送邀請 Email。管理員搜尋並選擇已註冊帳號，邀請綁定本機 `users.id`；使用者登入後可看到待處理邀請，接受後前往團隊。不再使用 Email 或 Email 驗證旗標配對邀請。

| API | 用途 |
| --- | --- |
| POST /api/v1/teams/{team_id}/invitations | Admin 建立邀請，body 為 email、role（admin/member）；後端只接受已註冊帳號。相同待處理邀請重試不重複建立。 |
| GET /api/v1/teams/{team_id}/invitations | Admin 查看邀請狀態與歷史。 |
| DELETE /api/v1/teams/{team_id}/invitations/{id} | Admin 取消待處理邀請。已回覆的邀請不能取消。 |
| GET /api/v1/me/invitations | 查看目前登入者的待處理邀請，包含 id、team_id、team_name、role、status。 |
| POST /api/v1/me/invitations/{id}/accept | 接受邀請並加入團隊；既有成員不會被覆蓋角色。 |
| POST /api/v1/me/invitations/{id}/decline | 拒絕邀請，不建立成員。 |

後端先驗證 JWT 或 session，再以已驗證的 `sub` 對應 `users.external_id`，取得本機 ID 查詢及接受邀請。JWT 缺少 Email claims 或帳號 Email 尚未驗證，不影響此流程；JWT 簽章、issuer、audience、期限檢查仍保留。前端提供的 Email 不作為權限依據，也不需要額外 session Cookie 補齊邀請身分。

建立時帳號不存在回傳 404、已是成員回傳 409、非 Admin 回傳 403。不屬於自己的邀請回傳 404，已取消／反向回覆回傳 409。相同回覆重試安全，接受不覆蓋既有成員角色。

建立邀請範例：`{"email":"person@example.com","role":"member"}`。後端會以完全比對的 Email 找到已註冊帳號，再將邀請綁定其 `users.id`；未註冊回傳 404。絕不回傳帳號搜尋清單。
邀請管理清單新增 `recipient_user_id`、`recipient_name`，舊 `email` 欄位保留但可為 null。收件者需先登入並在設定頁保存 Email，才可被邀請。
接受／拒絕不需要 body，成功回傳 `{"status":"accepted","team_id":"..."}` 或 declined。
前端每 30 秒及視窗重新取得焦點時讀取待處理邀請；非即時推播。

登入後會以已驗證的 name claim 補齊本機缺少的顯示名稱，保留已自訂名稱。當前使用者也會直接使用登入名稱顯示；其他尚未登入同步且缺少名稱的成員顯示「未設定名稱的成員」，不顯示 UUID。

資料庫需套用 0020_in_app_invitations 及 0021_invitation_recipients。若既有 migration 鏈因缺少 0005_transcripts 無法執行，可從 backend 依序執行：

```powershell
uv run python -m scripts.migrate_in_app_invitations
uv run python -m scripts.migrate_invitation_recipients
```

腳本保留邀請紀錄，不改 Alembic 版本；修復 migration 鏈後可安全重跑上述 revision。0021 新增收件人 ID 外鍵、名稱快照及 pending 唯一索引，並允許 email 為空。不把舊 Email 自動對應帳號，以免可修改或未驗證的 Email 造成誤領。舊邀請會在管理清單標示，Admin 請先取消，再搜尋選擇正確帳號重新邀請。

驗收：A 搜尋 B → 選擇 B 的 ID 建立 → B 登入看到邀請 → B 接受並出現在團隊成員清單；C 無法查看或回覆這筆邀請。B 的 JWT 即使只有 sub、iss、aud、exp 也可使用，過期或偽造 JWT 必須拒絕。
