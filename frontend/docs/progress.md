# 前端製作進度

本表以目前 repository 的 Web App 程式、後端 REST／WebSocket 路由及 `ProductPlanning.md` 為準。REST endpoint 存在不等於已具備規劃中的 AI 或即時產品能力。

## 已完成：可由使用者操作的 Web App

- 團隊入口拆為團隊總覽、成員與邀請、團隊會議、團隊記憶四個子頁；成員角色、移除、邀請清單與取消邀請均可操作。
- 建立會議採「團隊 → 會議資訊 → 議程」流程，提供常用議程範本與手動增修；AI 介入程度改為含說明的低／中／高選項。
- 會前 Prepare 整合會議生命週期、Brief、議程、參與者、Personal Sidekick 的私訊／預覽／公開，以及 Delegate 的立場、限制與 must-raise 設定。
- Dashboard 僅作跨團隊的下一步入口，不混入單一會議的共識或行動項目。
- Review 可建立／確認共識、送出及查看回饋明細；行動項目可編輯名稱、負責人、期限、狀態及刪除。
- Team Memory 支援上傳、搜尋、下載、封存、刪除，並可選擇指定版本還原。
- Settings 可讀取及儲存顯示名稱、Email；所有畫面均避免將內部 UUID 當作使用者可讀資訊。
- Live fallback 讀取 snapshot、連接會議 events WebSocket 並投票 AI suggestions；Add-on 保留窄版的建議與 Sidekick 操作。

## 已有後端資料，但仍缺少完整前端產品流程

- Audio WebSocket：目前 Audio Setup 是批次轉錄，尚未把瀏覽器音訊切 chunk、送 `/meetbot/ws/audio-in`、斷線重連與權限狀態整合成 Capture 流程。
- 即時事件：Live 有基本 WebSocket 訂閱及較新版本覆蓋保護，但沒有 cursor replay、事件 ID 去重、指數退避重連或跨分頁同步。
- Meeting BaaS Bot：後端 join／status／leave／speak 雖有 wrapper，尚未有可安全操作的 meeting-scoped Host 控制頁；因回應 schema、授權與投票政策尚未固定，前端不應假裝已可正式發言。
- Brief：Prepare 可呼叫 `/brief`，但目前後端只以正式 Agenda 組成摘要；尚未依已授權的 Team Memory 文件、歷史決策產出 AI 議程建議或來源引用。
- Delegate：可建立設定，但沒有規劃中的條件觸發、署名舉手卡、有效期間和停用操作。
- Consensus：目前 API 沒有規劃中 required participants、未回覆者、衝突狀態與新版產生完整模型，前端只能呈現既有回饋／確認資料。

## 需要後端契約或部署決策

- Add-on 專用短效 meeting-token handoff、Google Meet manifest／正式部署。
- Realtime 的生產 broker、事件持久化、cursor replay 與跨程序一致性。
- VAD／streaming STT、meeting-scoped Voice Bot 的權限矩陣與正式事件 schema。
- Host、會議政策、required participants 的持久化 schema；目前會議建立 API 沒有這些可儲存欄位。

## 驗證狀態

| 檢查 | 狀態 |
| --- | --- |
| TypeScript `tsc --noEmit` | 通過（2026-09-05） |
| `git diff --check` | 通過（2026-09-05） |
| ESLint | 尚未驗證；本機 npm script 曾卡住 |
| Next production build | 受本機 Windows Turbopack 子程序權限阻擋，需在可 spawn 子程序的環境重試 |
