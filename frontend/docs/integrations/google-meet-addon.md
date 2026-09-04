# Google Meet Add-on 前端設定

## 使用方式

Add-on iframe 入口固定為 `/meetings/[id]/addon`，不在 iframe 內重新登入，也不把長效 session 或 API key 放進 URL。Web App 先取得綁定 user／team／meeting 的短效 token，再交給 Add-on 建立連線。

## 需要人工設定的項目

1. Google Cloud 專案擁有者建立 Google Workspace Add-on manifest。
2. 設定 development deployment，並將 Vercel Preview／正式 URL 列入允許來源。
3. 設定 Meet context、SSO／OAuth 與同網域測試帳號；實際欄位依 Google Workspace 官方文件確認。
4. 以測試帳號在 Google Meet 開啟 Add-on，確認窄版 URL 可載入、token 過期可顯示重新開啟提示。

Manifest、OAuth secret、短效 token 簽發與撤銷由後端／Google Cloud 管理；前端只負責 route UI 與連線狀態。
