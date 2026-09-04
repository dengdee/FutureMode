# Neon Auth 設定（後端）

本專案的登入／註冊由 Neon Auth SDK 處理；FastAPI 不保存密碼，也不接收 client secret。後端只驗證前端送來的 Bearer JWT。

## 人工設定步驟

1. 開啟 Neon Console，選擇 Project 與要使用的 Branch。
2. 進入 `Auth > Configuration`，啟用 Neon Auth。
3. 複製 Auth Base URL 與 JWKS URL。
4. 建立測試帳號，完成一次登入。
5. 取得登入後 JWT 的 `iss` 與 `aud`。後端要求 audience 必須設定，不要把完整 Token 貼到公開網站或提交 Git。
6. 將值填入 `backend/.env`：

```env
NEON_AUTH_BASE_URL=https://...
NEON_AUTH_ISSUER=https://...
NEON_AUTH_AUDIENCE=JWT中的aud值
NEON_AUTH_JWKS_URL=https://.../.well-known/jwks.json
```

7. 確認 `CORS_ORIGINS` 包含前端網址，例如 `http://localhost:3000`。
8. 重新啟動後端，呼叫 `GET /api/v1/auth/config` 確認 `configured` 為 `true`。
9. 使用前端取得的 access token 呼叫 `GET /api/v1/me`，確認回傳使用者 subject。

## 安全注意事項

- `backend/.env` 不可提交；只能提交 `.env.example`。
- `NEON_AUTH_JWKS_URL`、issuer 與 base URL 可作為設定資訊，但不要回傳 client secret、cookie secret 或 API key。
- 正式環境請在 Vercel／部署平台 Secret 設定，不要寫入 Repository。
