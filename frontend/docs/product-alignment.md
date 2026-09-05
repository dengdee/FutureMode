# 前端與產品規劃對照

本文件將 `ProductPlanning.md` 的目標使用流程與目前 Web App 對照。畫面已串接 REST 時，仍會明確區分「已可操作」和「尚未具備規劃中的智慧／即時行為」。

## 目前使用流程

```text
Dashboard
  → 團隊清單
    → 團隊總覽
      ├─ 成員與邀請
      ├─ 團隊會議 → 建立會議 → Prepare
      └─ 團隊記憶

Prepare
  → Brief／議程／參與者／Personal Sidekick／Delegate
  → Audio Setup 或 Meet Add-on／Live fallback
  → Review（共識、回饋、行動項目、逐字稿）
```

## 已符合規劃的部分

- 團隊邀請採站內接受／拒絕，不寄送 Email；管理員可查看及取消待處理邀請，成員角色為 Admin／Member。
- Dashboard 僅處理跨團隊「接下來要做什麼」，不把會議內部共識與任務混入總覽。
- 團隊是會議、成員與共用記憶的邊界。團隊子頁採明確按鈕，而非在單一頁塞入所有操作。
- 會議建立使用團隊、名稱、時間、AI 介入程度與議程；AI 介入的低／中／高均有對應文字說明。
- 會前可管理正式 Agenda、參與者、個人私訊與公開前預覽；公開操作必須由本人按下發布。
- Delegate 設定呈現立場、限制與 must-raise，並明確說明不可投票、承諾或替人做決策。
- Review 保留共識版本、成員回饋與行動項目所需的負責人、期限、狀態。
- Team Memory 依團隊／會議範圍管理文件，使用者可選擇還原版本，畫面不暴露 UUID。

## 與規劃不同或尚未完成

| 規劃能力 | 現況 | 差距／原因 |
| --- | --- | --- |
| AI Brief 與議程建議 | Prepare 可呼叫 `/brief`，建立頁有常用議程範本 | 後端目前只根據已存在的 Agenda 回傳摘要，未將已授權文件、歷史決策或 AI 建議寫入獨立草稿。 |
| Personal Sidekick 對談 | 可保存私訊、預覽和發布 | 後端沒有多輪 LLM chat／thread endpoint；目前是受隔離的個人訊息工作區，不宣稱 Agent 已回覆。 |
| Delegate 會中代表 | 可建立事前設定 | 無條件觸發、署名舉手、有效期間或停用 API，尚不能正式代理出席。 |
| 主持人／會議政策 | 能選 AI 介入程度及在現有狀態下開始／結束會議 | Meeting schema 缺少 Host、逐次核准／團隊同意、required participants 的持久欄位。 |
| 即時 Meeting State | Live 可讀 snapshot 和 WebSocket 事件；後端已有 replay、去重、durable events 與 Redis broker | 前端尚未完整串接 cursor replay、去重與重連策略；生產部署仍需驗收。 |
| 聲音與 Voice Bot | Audio Setup 有批次轉錄，後端有 Bot wrapper | 尚未有 streaming audio、VAD、meeting-scoped 授權與可驗證的 Host 控制流程。 |
| Consensus 完成判定 | 可送回饋並確認版本 | 缺少規劃的 awaiting responses、conflicted、required participants 與新版產生模型。 |

## 資訊架構決策

- 使用者看見的是「團隊」；既有 `/workspaces` 僅保留路由相容性，頁面文案不再以工作區作為產品名詞。
- 使用者看見團隊名、會議名、成員顯示名稱和人類可讀的狀態，不看內部 UUID。
- 建立會議成功後直接進入 Prepare；議程可以套用範本並持續手動編輯，直到後端提供可追溯的 AI 議程草稿契約。
- Meet Add-on 是會中的窄版入口；`/live` 是 Add-on 不可用時的瀏覽器 fallback。
