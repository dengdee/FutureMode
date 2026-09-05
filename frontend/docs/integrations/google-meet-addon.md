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
3. OAuth consent screen 使用「外部」＋「測試中」模式，不需要先申請正式驗證；在「測試使用者」中加入要試用的 Google 帳號（上限 100 位）。
4. 設定 Meet context、SSO／OAuth 與 development deployment；實際欄位依 Google Workspace 官方文件確認。
5. 以已加入清單的測試帳號在 Google Meet 開啟 Add-on，確認窄版 URL 可載入並能沿用登入 session 呼叫 API。

### 測試模式限制

- 測試帳號才能完成 OAuth 授權；未加入清單的帳號會被拒絕。
- 測試授權通常 7 天後需要重新授權。
- 正式公開給所有 Google 帳號前，才需要處理 OAuth 驗證與可驗證的自有網域。

### 日後新增測試使用者

1. 開啟 Google Cloud Console，切換至 `future-mode` 專案。
2. 進入 **Google Auth Platform → 目標對象**。
3. 在「測試使用者」區塊按 **新增使用者**。
4. 輸入 Google 帳號 Email，按 Enter 逐一加入後按 **Save**。
5. 重新整理頁面，確認帳號出現在測試使用者清單；該帳號之後才能完成 OAuth 授權。

注意：Email 必須確實綁定有效的 Google／Google Workspace／Cloud Identity 帳戶，否則 Google 不會接受儲存。

Manifest、OAuth secret、短效 token 簽發與撤銷由後端／Google Cloud 管理；前端只負責 route UI 與連線狀態。
