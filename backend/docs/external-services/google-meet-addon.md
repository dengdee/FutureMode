# Google Meet Add-on 與 Google Cloud 設定流程

適用步驟：後端步驟 6、7、13；Add-on 前端由另一個工作範圍負責，本文件只記錄後端依賴。

1. 建立獨立 Google Cloud development project。
2. 啟用 Google Workspace Marketplace SDK、Google Workspace Add-ons API，以及實際需要的 Meet／OAuth API。
3. 設定 OAuth consent screen、測試使用者與必要 scopes。
4. 建立 HTTP deployment，指向已部署且可公開存取的 HTTPS Add-on URL。
5. 以 development deployment 安裝，不先建立公開 Marketplace listing。
6. 設定後端允許的 origin、OAuth issuer／audience 與 webhook／callback URL。
7. 驗證 Add-on iframe 的 user／meeting identity 不能取代後端授權；每個 WebSocket room 都要重新驗證。
8. 確認 Google Workspace 管理員政策、測試帳號、OAuth verification 與公開／私人 visibility 的限制。

Meet Add-on UI 不等於即時音訊權限；音訊 Capture Page、Meeting BaaS bot 與後端 WebSocket 必須分開驗證。
