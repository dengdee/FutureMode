# Google Meet Add-on 前端設定

## 使用方式

Add-on iframe 入口固定為 `/meetings/[id]/addon`。使用者在 Web App 以 Neon Auth Email／密碼登入；Add-on 沿用目前登入 session，不重複顯示登入頁，也不把長效 session 或 API key 放進 URL。Add-on 可直接使用現有 Bearer session 呼叫會議 API。

## Token 與登入邊界

- Neon Auth session JWT：證明使用者已登入，供 Web App 呼叫 `/api/v1/*` REST API。
- Meeting token 暫不列入 MVP；未來若需要跨網域或更細的會議 scope，再由後端新增短效 token。
- Add-on 理論上可以嵌入登入頁，但 iframe 內重新登入會造成 cookie、redirect、第三方儲存限制，也會讓使用者重複登入，因此沿用主程式登入狀態。

## 需要人工設定的項目

1. Google Cloud 專案擁有者建立 Google Workspace Add-on manifest。
2. 設定 development deployment，並將 Vercel Preview／正式 URL 列入允許來源。
3. 設定 Meet context、SSO／OAuth 與同網域測試帳號；實際欄位依 Google Workspace 官方文件確認。
4. 以測試帳號在 Google Meet 開啟 Add-on，確認窄版 URL 可載入並能沿用登入 session 呼叫 API。

Manifest、OAuth secret、短效 token 簽發與撤銷由後端／Google Cloud 管理；前端只負責 route UI 與連線狀態。
