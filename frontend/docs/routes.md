# 頁面與路由

| 路由 | 使用者位置 | 頁面責任 | 狀態 |
| --- | --- | --- | --- |
| `/` | 瀏覽器 | 產品 Landing Page | 已完成 |
| `/dashboard` | Web App | 服務狀態、近期會議、建立入口 | 部分接 API |
| `/sign-in` | Web App | Neon Auth 登入入口 | UI 完成，Auth 待接 |
| `/meetings/new` | Web App | 會議基本資料、AI 政策、議程 | UI 完成，送出待接 |
| `/meetings/[id]/prepare` | Web App | Brief、議程、Personal Sidekick | UI scaffold；API 待提供 |
| `/meetings/[id]/audio-setup` | Web App／Capture Page | 收音同意與連線狀態 | UI scaffold；Audio API 待提供 |
| `/meetings/[id]/addon` | Google Meet Meet Add-on | 窄版公共狀態與 Personal Sidekick | UI scaffold；token／realtime 待提供 |
| `/meetings/[id]/live` | 瀏覽器 fallback | Add-on 不可用時的同一公共狀態 | UI scaffold；realtime 待提供 |
| `/meetings/[id]/review` | Web App | 摘要、逐字稿、共識與行動項目 | UI scaffold；Review API 待提供 |
| `/memory` | Web App | 團隊文件與歷史決策 | UI scaffold；RAG API 待提供 |
| `/settings` | Web App | Team／Integrations／Privacy | UI scaffold；Settings API 待提供 |

桌面版使用可收合左側欄，主內容獨立捲動；手機版使用 Drawer。Add-on 不套用完整 App Shell，優先以約 280px 寬度設計。所有頁面使用繁體中文與 `focus-visible` 樣式。
