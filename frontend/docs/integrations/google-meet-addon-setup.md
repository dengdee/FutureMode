# Google Meet Add-on 設定文件

## 目前前端網址

- Web App：`https://future-mode.vercel.app`
- 會議 Add-on UI：`https://future-mode.vercel.app/meetings/{meetingId}/addon`
- 瀏覽器 Live fallback：`https://future-mode.vercel.app/meetings/{meetingId}/start/live`

## 目前實作範圍

`/meetings/[id]/addon` 是窄版 Meet iframe UI，包含 Brief、Live State、Personal Sidekick 與 Host 控制。它與 `/meetings/[id]/start/live` 共用會議狀態與 API，但兩者版面不同：Add-on 適合嵌入 Google Meet，Live 是完整瀏覽器頁面。

目前可直接在瀏覽器測試指定會議：

```text
https://future-mode.vercel.app/meetings/{meetingId}/addon
```

`?preview=live` 是開發預覽模式，使用假資料，不代表正式 Meet 連線。

## Google Cloud 設定流程

### 1. 建立或選擇 Google Cloud Project

需要專案擁有者或管理員啟用 Google Workspace Add-ons／Marketplace SDK 相關功能，並設定 OAuth 同意畫面與測試帳號。

### 2. 建立 Meet Add-on manifest

Meet 的 manifest 必須設定固定的 `sidePanelUrl`，並允許 Vercel origin。由於目前 UI 路由需要 `meetingId`，正式 deployment 前仍需提供一個固定 Add-on 入口，接收 Meet context 後再導向對應的 `/meetings/{meetingId}/addon`。

概念設定如下，實際欄位請依 Google Cloud Console 的 manifest 編輯器驗證：

```json
{
  "addOns": {
    "meet": {
      "web": {
        "sidePanelUrl": "https://future-mode.vercel.app/addon",
        "supportsScreenSharing": false,
        "addOnOrigins": [
          "https://future-mode.vercel.app"
        ]
      }
    }
  }
}
```

官方參考：[Meet manifest resource](https://developers.google.com/apps-script/manifest/meet-addons)

### 3. 建立 Development Deployment

在 Google Cloud／Marketplace SDK 建立 HTTP deployment，指定上面的 manifest，並將 `https://future-mode.vercel.app` 列入允許來源。先使用 Development Deployment，不先發布 Marketplace listing。

### 4. 安裝與測試

1. 在 HTTP deployments 對該 deployment 按 **Install**。
2. 使用已列入測試的 Google Workspace 帳號開啟 Google Meet。
3. 在 Meet 的「活動」面板開啟 Proximate。
4. 確認 Add-on iframe 載入，並能取得正確的會議 context。
5. 確認會議 API、投票與即時狀態使用同一個 `meetingId`。

## 尚未完成與必要權限

- 尚未建立 Google Cloud manifest 與 HTTP deployment。
- 尚未建立固定 `/addon` context 入口；目前動態路由只能用指定 meeting ID 直接測試。
- 尚未完成正式 meeting access-token handoff。
- 需要 Google Cloud Project ID，以及具備 Add-ons／Marketplace SDK 權限的帳號。
- 本機目前沒有 `gcloud` CLI 登入環境，因此無法代替帳號完成 Install 或 OAuth 設定。

## 安全邊界

- 不把 Neon Auth 長效 session、API key 或秘密放進 Add-on URL。
- Add-on origin 只允許 `https://future-mode.vercel.app`。
- 每個 meeting 的資料仍需由後端重新驗證使用者權限。
- Add-on iframe 不負責麥克風收音；收音由頂層 Web App Capture Page 處理。
