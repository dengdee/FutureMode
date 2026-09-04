# Meeting BaaS 前端整合邊界

Meeting BaaS 是後端 Voice Bot 整合，不需要在前端設定 API key。

## 後端負責

- 使用 `POST /meetbot/join` 建立 Bot。
- 管理 Meeting BaaS key、Webhook／音訊串流、Bot lifecycle 與語音播放。
- 在通過會議政策與支持門檻後才讓 Bot 發言。

## 前端負責

- `/meetings/[id]/addon` 與 `/live` 顯示 Bot 狀態：等待、核准、播放中、完成、失敗。
- Bot 失敗時回退為公開文字卡片，不把未知 Meeting BaaS response 欄位當成穩定 UI 契約。
- 等後端提供 lifecycle／status schema 後，再新增對應 API function。
