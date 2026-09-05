# 頁面與路由

| 路由 | 使用者位置 | 頁面責任 | 狀態 |
| --- | --- | --- | --- |
| `/` | 瀏覽器 | 產品 Landing Page | 已完成 |
| `/dashboard` | Web App | 跨團隊工作總覽、近期會議、快速建立會議入口 | meetings／teams API 已接；建立會議仍需在表單選擇所屬工作區，不顯示團隊記憶或單一會議共識／行動項目 |
| `/sign-in` | Web App | Neon Auth 登入入口 | 已接 Neon Auth |
| `/sign-up` | Web App | 建立帳號入口 | 已接 Neon Auth |
| `/workspaces` | Web App | 查看團隊、成員與工作區會議；以表格準備邀請名單 | Team／Member／Meeting 讀取 API 已接；建立／邀請寫入 API 待提供 |
| `/meetings/new` | Web App | 從工作區建立會議、設定議程與 AI 政策；Dashboard 快速入口也會導向此頁 | Meeting／Agenda API 已接；統一顯示「團隊 > 建立會議」，有 `teamId` 時會預先選定工作區 |
| `/meetings/[id]/prepare` | Web App | 會議設定、議程、參與者 | 現有 Meeting／Agenda／Participant API 已接；Brief／Sidekick／meeting-scoped Voice Bot 待提供 |
| `/meetings/[id]/audio-setup` | Web App／Capture Page | 收音同意與連線狀態 | UI scaffold；Audio API 待提供 |
| `/meetings/[id]/addon` | Google Meet Meet Add-on | 窄版公共狀態與 Personal Sidekick | 沿用 Neon Auth session；realtime 待提供 |
| `/meetings/[id]/live` | 瀏覽器 fallback | Add-on 不可用時的同一公共狀態 | UI scaffold；realtime 待提供 |
| `/meetings/[id]/review` | Web App | 摘要、逐字稿、共識與行動項目 | 已接 REST API；即時更新待 WebSocket |
| `/memory` | 相容入口 | 舊版團隊記憶頁 | 保留舊連結；正式入口改為 `/workspaces/[workspaceId]/memory/...` |
| `/settings` | Web App | 帳號 | 目前僅顯示 Neon Auth session；通知／安全設定待 API 完成後加入；團隊資訊移至 `/workspaces` |

桌面版使用可收合左側欄，主內容獨立捲動；手機版使用 Drawer。Add-on 不套用完整 App Shell，優先以約 280px 寬度設計。所有頁面使用繁體中文、Noto Sans TC Variable Font、共用 `rounded-primary`／`control-primary` 與 `focus-visible` 樣式。

## 工作區階層路由

正式資訊架構以 `/workspaces/[workspaceId]` 為根：`members` 管理團隊成員，`memory/shared` 管理團隊共用文件，`memory/meetings/[meetingId]` 管理單次會議文件，`meetings/[meetingId]/prepare|live|review` 分別代表會前準備、會議進行與會後回顧。這些新路由目前導向既有頁面，確保舊連結仍可使用；待後端 workspace-scoped API 完成後再移除相容導向。
