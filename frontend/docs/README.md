# Proximate 前端文件

這個目錄保存前端開發、API 串接、頁面路由與外部服務設定文件。文件只描述前端責任；後端秘密、資料庫與部署服務端設定不放在這裡。

## 視覺基準

全站使用 `frontend/public/fonts/NotoSansTC-VF.ttf`（Noto Sans TC 可變字重）作為繁體中文與介面字體，透過 `app/globals.css` 的 `@font-face` 載入；元件不得依賴瀏覽器預設控制項樣式。

## 文件索引

| 文件 | 用途 |
| --- | --- |
| [進度表](progress.md) | 已完成、進行中與待後端支援的製作清單 |
| [產品對照](product-alignment.md) | ProductPlanning 與目前 Web App 的符合度、缺口與資訊架構決策 |
| [頁面與路由](routes.md) | URL、頁面責任、共用版面與響應式規則 |
| [API 串接](api.md) | Axios client、功能 API 檔案、目前 OpenAPI 對照 |
| [後端契約確認](backend-api-handoff.md) | Participants UUID 與團隊成員識別碼方案 |
| [本機開發](setup.md) | 啟動、環境變數、檢查與常見問題 |
| [Neon Auth](integrations/neon-auth.md) | 登入服務的前端設定與待確認項目 |
| [Vercel](integrations/vercel.md) | 前端部署與公開環境變數設定 |
| [Google Meet Add-on](integrations/google-meet-addon.md) | Add-on route、manifest 與 development deployment 配合事項 |
| [Meeting BaaS](integrations/meetingbaas.md) | Voice Bot 前後端責任與前端驗證方式 |
| [AI 服務](integrations/ai-providers.md) | OpenAI、ElevenLabs、Groq 的前端邊界 |

## 文件規則

- 先以實際程式碼與 `http://localhost:8000/openapi.json` 為準；規劃中的 endpoint 一律標示「待確認」。
- 不在前端 repository、文件或 `NEXT_PUBLIC_*` 變數放 API key、OAuth secret、Meeting BaaS token、OpenAI／ElevenLabs／Groq key。
- 外部服務若需要手動設定，使用對應 integrations 文件；每次設定都記錄環境、回呼 URL 與驗證結果，但不記錄秘密值。
