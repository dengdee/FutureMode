# Neon Auth 前端設定

## 目前狀態

產品正式登入選 Neon Auth；目前已安裝 `@neondatabase/auth`，並建立 server auth、API handler、`proxy.ts` 路由保護，以及 `/sign-in`／`/sign-up` 的 email/password UI。

## 手動設定清單（待確認）

1. 由專案管理者建立 Neon Auth 專案與登入方式。
2. 在 `frontend/.env` 與 Vercel 設定 `NEON_AUTH_BASE_URL`、`NEON_AUTH_COOKIE_SECRET`（至少 32 字元）。
3. 本機啟動後測試 `/sign-up`、`/sign-in`、登出與受保護路由。
4. 登入後以後端 `GET /api/v1/me` 驗證 active team 與角色。
5. FastAPI 需補上 Bearer token 驗證；目前前端 auth cookie 與 API server 的跨服務 token transport 尚待後端確認。

目前未設定 Neon Auth 環境變數時，`proxy.ts` 會暫時放行頁面以支援本機 UI 開發；正式環境必須設定環境變數並啟用驗證。
