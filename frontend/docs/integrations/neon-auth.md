# Neon Auth 前端設定

## 目前狀態

產品正式登入選 Neon Auth；目前已安裝 `@neondatabase/auth`，並建立 server auth、API handler、`proxy.ts` 路由保護，以及 `/sign-in`／`/sign-up` 的 email/password UI。

## 手動設定清單（待確認）

1. 由專案管理者建立 Neon Auth 專案與登入方式。
2. 在 `frontend/.env` 與 Vercel 設定 `NEON_AUTH_BASE_URL`、`NEON_AUTH_COOKIE_SECRET`（至少 32 字元）。
3. 本機啟動後測試 `/sign-up`、`/sign-in`、登出與受保護路由。
4. 登入後以後端 `GET /api/v1/me` 驗證 active team 與角色。
5. 後端已支援 Neon Auth session cookie／JWT 驗證；前端 Axios 使用 `withCredentials: true`，並從同源 `/api/auth/token` 取得短效 token 後附加 `Authorization: Bearer ...`。

驗證時應在瀏覽器 Network 確認 `/api/v1/me`、`/api/v1/teams` 同時帶有 Authorization 與 Neon Auth cookie。若仍回 401，先檢查登入 session、`NEON_AUTH_ISSUER`／`NEON_AUTH_AUDIENCE`／`NEON_AUTH_JWKS_URL` 是否屬於同一 Neon Auth 專案，再檢查後端日誌；不要把 token 或 cookie 貼到文件或聊天紀錄。

目前未設定 Neon Auth 環境變數時，`proxy.ts` 會暫時放行頁面以支援本機 UI 開發；正式環境必須設定環境變數並啟用驗證。

## Client／Server import 邊界

- Client Components（登入、註冊、App Shell 與 API client）只能引用 `lib/auth/client.ts`。該檔案使用目前已安裝版本提供的 `@neondatabase/auth/next` browser-safe client entrypoint。
- App Shell 的顯示名稱直接讀取 `authClient.useSession()` 的 `data.user.name`，缺少名稱時依序 fallback 到 Email 與 `Proximate`；不依賴後端 `/api/v1/me` 提供 username。
- `lib/auth/server.ts` 只能由 `proxy.ts` 與 `app/api/auth/[...path]/route.ts` 引用，使用 `@neondatabase/auth/next/server`；不可從任何標示 `"use client"` 的元件或其相依模組引入。
- 目前套件版本沒有 `@neondatabase/auth/next/client` export；若升級至提供該子路徑的版本，再依官方 API 替換 client entrypoint，不應自行建立同名 alias。

## 本機 404 排查

若 `/api/auth/sign-in/email` 回傳 404，先確認 `frontend/.env` 的 `NEON_AUTH_BASE_URL` 與 `NEON_AUTH_COOKIE_SECRET` 都不是空值，且前者是 Neon Auth 專案 URL（例如 `https://<project>.neon.tech`），不是 `http://localhost:3000`。修改 `.env` 後必須重新啟動 Next dev server；目前執行中的舊 server 不會自動取得新的環境變數。
