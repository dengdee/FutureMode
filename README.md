# Proximate

## 問題與目標

傳統會議常把重要思考集中在短暫的會議時間內，導致參與者準備不足、資訊分散，會後決策也難以追蹤與延續。無法出席的成員更容易失去發表觀點的機會，團隊知識也會隨著會議結束而逐漸流失。

Proximate 將 AI Agent 整合進完整的會議流程。會前，使用者可與 AI 對話，釐清問題、分析風險並整理成議前文件；會議中，Voice Bot 會像真正的組員一樣參與討論，根據即時逐字稿與團隊脈絡主動提出問題、補充觀點，並在獲得團隊同意後以語音發言，協助成員即時評估選項與做出決策。會後，討論內容會切分為文件 chunks，建立 embedding 並寫入團隊 RAG 記憶，讓後續會議能快速搜尋並延續脈絡。透過這套流程，Proximate 將一次性的會議，轉化為 AI 能持續參與、協助決策，並可累積、搜尋與改善的團隊協作能力。

## 核心功能

- 議前討論：使用者可與個人 AI Agent 對話，釐清問題、風險、反例與待決事項，並整理成議前文件。
- 會議協作：提供會議工作區、議程、參與者、逐字稿、AI 主動提問、投票與共識流程。
- 缺席代理：成員可保存自己的代理重點，經核准後由 AI 產生發言文字並交給 Voice Bot 播放。
- 團隊記憶：文件切成 chunks、建立 embedding 寫入 RAG，支援全文與 hybrid 搜尋。
- 團隊與邀請：建立工作區、管理成員角色，使用站內邀請加入團隊，不依賴 Email 寄送。

## 系統架構

```text
使用者／Google Meet
        │  Next.js Web App + Meet Add-on
        ▼
FastAPI REST / WebSocket API
   ├─ Neon Auth：登入、JWT、session
   ├─ PostgreSQL：團隊、會議、訊息、文件、成員與邀請
   ├─ Gemini：議前回覆、文件整理、embedding
   ├─ RAG：chunks、向量搜尋與團隊記憶
   └─ Meeting BaaS：Google Meet Voice Bot（可選）
        │
        ▼
會前文件 → 會議協作 → 會後 Review／可搜尋記憶
```

前端負責畫面、登入狀態與會議工作區互動；後端負責授權、資料保存、AI 呼叫、文件處理與 RAG。所有需要權限的 API 都使用 Neon Auth Bearer JWT，不信任前端自行送入的身分資訊。

## 使用技術

| 類型 | 技術／服務 | 用途 |
| --- | --- | --- |
| AI 模型 | Gemini Flash Lite、Gemini Embedding | 議前對話、文件整理、向量 embedding |
| 前端 | Next.js、React、TypeScript、Tailwind CSS | Web App、Meet Add-on、響應式介面 |
| 後端 | FastAPI、Python、SQLAlchemy、PostgreSQL | REST/WebSocket API、授權、資料與 RAG |
| 身分驗證 | Neon Auth | Email/password 登入、JWT 與 session |
| 即時／會議 | Google Meet Add-on、Meeting BaaS | 會議嵌入、即時協作與 Voice Bot |
| 影片展示 | Remotion | 2 分鐘作品評選展示影片 |
| Sponsor 技術 | 目前無 | 本作品未使用 Sponsor 提供的技術或服務 |

## 安裝與執行

```bash
git clone https://github.com/dengdee/FutureMode.git
cd FutureMode

# 後端
cd backend
copy .env.example .env
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 前端
cd frontend
npm install
copy .env.example .env
npm run dev
```

瀏覽器開啟 `http://localhost:3000`；後端 API 文件位於 `http://127.0.0.1:8000/docs`。若只要執行展示影片：

```bash
cd video
npm install
npm run render
```

## 作品展示

- 作品展示網址：https://future-mode-proximate-v2.vercel.app/
- 原始碼：https://github.com/dengdee/FutureMode
- 評選影片：[Proximate Showcase](video/out/proximate-showcase.mp4)

## 限制與未來工作

- Gemini 與 Meeting BaaS 需要有效的環境變數與外部服務連線；本機未設定時，相關功能會回傳可理解的錯誤。
- Google Meet Add-on、WebSocket 在正式 Vercel 部署上的長連線與重連策略仍需持續驗證。
- 目前議前文件以字幕與文字介面為主，後續可加入更完整的語音互動、多人即時 presence 與權限細分。
- RAG 搜尋結果會依 embedding provider 與資料量影響，正式上線前需要建立評估資料集與品質監控。

## 第三方服務、資料與素材

- Neon Auth：https://neon.tech/docs/neon-auth —— 登入與 session 服務，依 Neon 使用條款。
- Gemini API：https://ai.google.dev/ —— AI 回覆與 embedding；金鑰只放在本機或部署環境變數，不提交至儲存庫。
- Meeting BaaS：https://www.meetingbaas.com/zh-CN/meeting-bot-api-for-google-meet —— Google Meet Bot 與語音輸出服務。
- Remotion：https://www.remotion.dev/ —— 作品展示影片製作工具，依其授權條款使用。
- 字體：`frontend/public/fonts/NotoSansTC-VF.ttf`，隨專案提供，使用前請依原字體授權條款確認。

## 團隊成員

| 姓名 | 分工 |
| --- | --- |
| fengyenchen（馮妍禎） | 後端 Web：FastAPI REST API、資料庫模型與 migration、JWT 權限驗證、團隊／會議／邀請、議前對話 API。 |
| dengdee（鄧亦宸） | Meeting Bot、TTS：Google Meet Bot、會議中 AI 發言、LLM 文字生成、文字轉語音與語音輸出整合。 |
| fengyenchia（馮妍嘉） | 前端 Web：Next.js Web App、Dashboard、團隊與會議頁面、議前討論介面、RAG 文件流程與 UI/UX。 |
| Yun011017（林芸萱） | 前端 Add-on：Google Meet Add-on iframe、會議中窄版介面、即時狀態與 AI Sidekick 互動。 |

### 團隊協作方式

- 後端 Web 與前端 Web 以 REST API 契約協作，統一使用 Neon Auth Bearer JWT。
- Meeting Bot 與 TTS 將核准的 AI 發言轉成可播放語音，前端 Add-on 顯示同步狀態。
- Web App 與 Add-on 共用會議狀態，但分別提供完整頁面與 Google Meet 內嵌介面。
- 議前對話、文件、embedding 與 RAG 由後端保存，確保團隊記憶不依賴單一瀏覽器。


## License

本專案採用 [MIT License](LICENSE)。第三方服務、字體與素材仍須依各自的授權條款使用。
