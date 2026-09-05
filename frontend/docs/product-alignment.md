# 前端與產品規劃對照

本文件把 `ProductPlanning.md` 的產品藍圖對照目前 Web App 實作，避免把 UI scaffold 誤認為已完成的產品能力。判定以目前程式碼與 `http://localhost:8000/openapi.json` 為準。

## 已符合

- Landing、Neon Auth 登入／註冊與 session 顯示。
- 工作總覽 `/dashboard`：提供跨團隊導覽、近期會議與快速建立會議入口；團隊記憶從團隊內進入。
- 工作區 `/workspaces`：列出團隊、成員與團隊內會議。
- 建立會議 `/meetings/new`：建立會議與基本議程。
- 會前 `/meetings/[id]/prepare`：讀取／修改會議、議程與現有參與者。
- 團隊記憶 UI：團隊共用文件與單次會議文件分區，支援拖曳選檔。
- `/meetings/[id]/audio-setup`、`addon`、`live`、`review` 路由與基本資訊結構。
- 共用 App Shell、中文導覽、響應式 Drawer、GSAP 進場動畫與一致表單樣式。

## 部分符合

| 規劃能力 | 目前 Web App 狀態 | 缺口 |
| --- | --- | --- |
| 團隊建立／邀請 | 建立工作區對話框與表格 UI | 後端尚無 workspace CRUD／invite endpoint，因此不寫入 |
| 會議參與者 | 可讀取、修改、移除 | 新增仍受後端要求內部 UUID 限制，members API 只有 `external_id` |
| Team Memory／RAG | 有 team／meeting 範圍、拖曳上傳與搜尋 | 已接文件清單、上傳、索引與 hybrid search |
| Personal Sidekick | Add-on 內有版面預覽 | 尚無對話、授權公開與 thread API |
| 會議 Review | 有逐字稿、決策與行動項目操作 | 已接 transcript、consensus、action item API |
| 設定 | 顯示 Neon Auth 登入者資料 | 尚無個人資料更新、通知、隱私與團隊設定 API |

## 尚未實作（需即時後端契約）

議程目前由使用者／Host 手動建立與編輯。未來若後端提供 Brief／AI endpoint，Agent 只能產生建議議程與討論順序，必須由使用者／Host 確認後才寫入正式 Agenda API，不直接覆蓋手動內容。

- Audio WebSocket、Live Snapshot、即時 transcript 與 Meeting State。
- AI suggestion／舉手卡、投票、Host policy 與門檻控制。
- Pre-meeting Brief、Personal Sidekick、Delegate。
- Live WebSocket、音訊串流與 Meet token handoff。
- meeting access-token handoff 與正式 Google Meet Add-on deployment。

## 資訊架構決策

Dashboard 不顯示「待確認共識」或「我的行動項目」。共識與行動項目都屬於單一會議，應在 `/workspaces/[workspaceId]/meetings/[meetingId]/review`（目前由既有 review 頁面相容導向）查看；工作區頁負責團隊、成員與會議入口；Team Memory 負責共用文件與各場會議文件。會議永遠隸屬於團隊，Dashboard 的快速建立只是捷徑，因此建立會議頁統一使用「團隊 > 建立會議」麵包屑。

## 下一個可由前端直接完成的工作

在不新增後端 API 的前提下，前端可先完成：

1. 工作區頁以選定 team 過濾成員與會議，避免跨團隊資料混在一起。
2. 會議建立成功後導向該場 `/prepare`，並顯示明確的成功通知。
3. 會前頁加入既有議程／參與者的載入、錯誤與空狀態提示。
4. 文件拖曳區已接 PDF／TXT 上傳；後續補檔案大小與重複檔案驗證。
