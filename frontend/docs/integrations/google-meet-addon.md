# Google Meet Add-on 前端設定

## 使用方式

Add-on iframe 入口固定為 `/meetings/[id]/addon`。使用者在 Web App 以 Neon Auth Email／密碼登入；Add-on 沿用目前登入 session，不重複顯示登入頁，也不把長效 session 或 API key 放進 URL。Add-on 可直接使用現有 Bearer session 呼叫會議 API。

## Token 與登入邊界

- Neon Auth session JWT：證明使用者已登入，供 Web App 呼叫 `/api/v1/*` REST API。
- Meeting token 暫不列入 MVP；未來若需要跨網域或更細的會議 scope，再由後端新增短效 token。
- Add-on 理論上可以嵌入登入頁，但 iframe 內重新登入會造成 cookie、redirect、第三方儲存限制，也會讓使用者重複登入，因此沿用主程式登入狀態。

## Google Cloud 設定狀態

以下設定已完成（專案 `future-mode`，project number `446517015863`）：

1. 已啟用 Google Workspace Marketplace SDK 與 Google Workspace Add-ons API。
2. 已建立並安裝 HTTP deployment `future-mode-meet-addon`。
3. Meet `sidePanelUrl` 設為 `https://future-mode-proximate.vercel.app/addon`，允許來源為 `https://future-mode-proximate.vercel.app`。
4. Marketplace 應用程式設為「不公開」、個人＋管理員安裝，並選取 Meet 外掛程式整合。
5. OAuth 使用外部／測試模式；測試帳號可在下方清單管理。

Vercel 尚未部署最新 `/addon` 路由前，開啟 Add-on 可能暫時顯示 404；部署完成後同一網址會自動生效。

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

目前 Google Cloud 已啟用：

- Google Workspace Marketplace SDK（`appsmarket-component.googleapis.com`）
- Google Workspace Add-ons API（`gsuiteaddons.googleapis.com`）

前端現在提供固定的 `/addon` context 入口：它會使用 Meet Add-ons Web SDK 取得目前會議的 `meetingId`，再導向既有的 `/meetings/[id]/addon` 面板；若從一般瀏覽器開啟且沒有 Meet context，會顯示重新從 Meet 活動面板開啟的提示。
