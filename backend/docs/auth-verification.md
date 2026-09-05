# 登入 API 驗證與排錯

## 首次建立團隊

Neon Auth 帳號與應用程式 `users` 是不同資料。`POST /api/v1/teams` 會以已驗證的
subject 對應 `users.external_id`，缺少時建立本機使用者，並建立團隊與 owner 成員。
三項操作在同一筆交易內完成，失敗時全部 rollback。既有使用者的姓名、email 不會被覆寫；
不需要手動插入 users，也不需要新增 migration。此流程不以 email 自動合併帳號。

前端透過同源 `GET /api/auth/token` 取得 JWT，再以 Authorization Bearer 呼叫後端。
`getSession()` 的 session token 與 JWT 不應混用；`withCredentials` 只影響瀏覽器
允許送出的 Cookie，不能跨越 Cookie domain、SameSite 或 Secure 限制。

後端 JWT 驗證設定：

- `NEON_AUTH_BASE_URL`：Neon Auth 專案 URL（包含資料庫與 `/auth` 路徑）。
- `NEON_AUTH_ISSUER`：預期 issuer；空白時使用上述 base URL。
- `NEON_AUTH_AUDIENCE`：預期 audience；空白或舊範例值
  `your-neon-auth-audience` 時使用 base URL，符合 Better Auth 的預設值。
  若服務自訂 audience，必須明確設定，不能直接信任傳入 token 自述的值。
- `NEON_AUTH_JWKS_URL`：該專案公開 JWKS 的完整 HTTPS URL。

僅接受 RS256、ES256、EdDSA；使用受信任設定中的 JWKS 驗證簽章，
並要求 exp、sub、iss、aud。演算法必須與 JWKS key 相符。
不會透過停用 audience 或簽章驗證來通過登入。

舊 opaque session 路徑仍支援 `/get-session`，只轉送 Neon Auth session Cookie。
Neon Auth 連線失敗回傳 503；無效 JWT 回傳 401。後端日誌只列錯誤類型，
不列 token、Cookie 或使用者資料。

## CMD 驗證

```cmd
cd C:\FutureMode\backend
uv run pytest tests/test_jwt_verification.py
uv run pytest
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

前端重新登入後確認 `/api/auth/token`、`/api/v1/me`、`/api/v1/teams`、
`/api/v1/meetings` 的回應。自動化測試使用測試私鑰及模擬 JWKS；
它們驗證認證程式邏輯，不代表已完成真實 Neon Auth 登入與資料庫串接。
