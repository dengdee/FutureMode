# 站內團隊邀請

不寄送邀請 Email。Email 僅用於配對 Neon Auth 登入帳號；使用者在任一登入後頁面可看到待處理邀請，接受後前往團隊。

| API | 用途 |
| --- | --- |
| POST /api/v1/teams/{team_id}/invitations | Admin 建立邀請，body 為 email、role（admin/member）。相同待處理邀請重試不重複建立。 |
| GET /api/v1/teams/{team_id}/invitations | Admin 查看邀請狀態與歷史。 |
| DELETE /api/v1/teams/{team_id}/invitations/{id} | Admin 取消待處理邀請。已回覆的邀請不能取消。 |
| GET /api/v1/me/invitations | 查看目前登入者的待處理邀請，包含 id、team_id、team_name、role、status。 |
| POST /api/v1/me/invitations/{id}/accept | 接受邀請並加入團隊；既有成員不會被覆蓋角色。 |
| POST /api/v1/me/invitations/{id}/decline | 拒絕邀請，不建立成員。 |

收件人以已驗證 token/session 的 email 及 email_verified=true 或 emailVerified=true 配對；不使用可自行修改的本機個人資料 Email 判定權限。未驗證 Email 回傳 403，不屬於自己的邀請回傳 404，已取消／反向回覆回傳 409。相同回覆重試安全。

建立邀請範例：`{"email":"person@example.com","role":"member"}`。
接受／拒絕不需要 body，成功回傳 `{"status":"accepted","team_id":"..."}` 或 declined。
前端每 30 秒及視窗重新取得焦點時讀取待處理邀請；非即時推播。

登入後會以已驗證的 name claim 補齊本機缺少的顯示名稱，保留已自訂名稱。當前使用者也會直接使用登入名稱顯示；其他尚未登入同步且缺少名稱的成員顯示「未設定名稱的成員」，不顯示 UUID。

資料庫需套用 0020_in_app_invitations。若既有 migration 鏈因缺少 0005_transcripts 無法執行，可從 backend 執行 `uv run python -m scripts.migrate_in_app_invitations`；僅更換唯一索引，保留所有邀請紀錄，不改 Alembic 版本。之後修復 migration 鏈可安全重跑 0020。
