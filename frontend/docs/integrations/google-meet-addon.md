# Google Meet Add-on 前端設定

## 使用方式

Add-on iframe 入口固定為 `/meetings/[id]/addon`。使用者仍在 Web App 以 Neon Auth 登入；Add-on 不重複顯示登入頁，也不把長效 session 或 API key 放進 URL。Web App 登入後向後端取得綁定 user／team／meeting 的短效 meeting token，再交給 Add-on 建立連線。

## Token 與登入邊界

- Neon Auth session JWT：證明使用者已登入，供 Web App 呼叫 `/api/v1/*` REST API。
- Meeting token：由後端針對單一會議簽發的短效、限 scope token，只能讀取該 user／team／meeting 的 Add-on 公開狀態與即時連線。
- Add-on 理論上可以嵌入登入頁，但 iframe 內重新登入會造成 cookie、redirect、第三方儲存限制，也會讓使用者重複登入；因此產品流程採「Web App 登入 → 開啟 Meet Add-on → handoff 短效 meeting token」。
- Token 不放在可分享的長效 URL；過期時由 Add-on 顯示重新從 Web App 開啟的提示。

## 需要人工設定的項目

1. Google Cloud 專案擁有者建立 Google Workspace Add-on manifest。
2. 設定 development deployment，並將 Vercel Preview／正式 URL 列入允許來源。
3. 設定 Meet context、SSO／OAuth 與同網域測試帳號；實際欄位依 Google Workspace 官方文件確認。
4. 以測試帳號在 Google Meet 開啟 Add-on，確認窄版 URL 可載入、token 過期可顯示重新開啟提示。

Manifest、OAuth secret、短效 token 簽發與撤銷由後端／Google Cloud 管理；前端只負責 route UI 與連線狀態。
