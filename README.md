# Proximate

Proximate 是一套以「AI 作為另一位組員」為核心的智慧會議協作系統。本 Repository 目前只包含可執行的前後端基礎架構，尚未實作登入、AI、會議流程、資料庫 CRUD 或外部服務整合。

完整產品與技術規劃請見 [`ProductPlanning.md`](ProductPlanning.md)。

## 專案結構

```text
.
├─ frontend/        # Next.js 16.3、React 19、TypeScript、Tailwind CSS
│  ├─ app/           # Dashboard 與 Meeting Workspace routes
│  │  ├─ meetings/[id]/addon/ # Google Meet Add-on iframe 入口
│  │  └─ meetings/[id]/live/  # 瀏覽器 fallback／開發期 Live UI
│  └─ .env.example  # 前端環境變數範例
├─ backend/         # FastAPI、Pydantic settings、pytest、Ruff
│  ├─ app/           # API 與服務模組
│  ├─ integrations/meetingbaas/ # Meeting BaaS Google Meet Bot API
│  ├─ voice_bot/     # 發言政策與 Voice Bot lifecycle
│  └─ .env.example   # 後端環境變數範例
├─ integrations/
│  └─ google-meet/   # Meet Add-on deployment 與整合設定
└─ ProductPlanning.md
```

前端與後端彼此獨立，不直接引用對方的內部程式碼。

## 前端資訊架構

每場會議使用同一個 Meeting Workspace，依階段分為：

```text
/dashboard
/meetings/new
/meetings/[id]/prepare       # 會前 Brief、議程、AI 角色與 Personal Agent
/meetings/[id]/audio-setup   # 啟動麥克風／分頁音訊後回到 Google Meet
/meetings/[id]/addon         # Google Meet Add-on：Brief、Live State、Sidekick、Host Controls
/meetings/[id]/live          # Add-on 不可用時的瀏覽器 fallback／開發期測試頁
/meetings/[id]/review        # 會後摘要、逐字稿、決策、行動項目與成員確認
/memory                      # Team Memory
/settings                    # 團隊、整合與隱私設定
```

`/meetings/[id]/addon` 是嵌入 Google Meet 的窄版 iframe；會議中不要求使用者切回完整 Web App。Voice Bot 由後端透過 [Meeting BaaS Google Meet Bot API](https://www.meetingbaas.com/zh-CN/meeting-bot-api-for-google-meet) 加入會議並輸出語音。主要逐人收音仍由 Audio Setup／Capture 流程提供，Meeting BaaS 音訊串流可作為備援。

Add-on 不在 iframe 內重新登入。已登入的 Web App 會向後端取得綁定使用者與會議的短效 meeting token，交給 `/meetings/[id]/addon` 建立連線。Web App、`/meetings/[id]/live` 與 Add-on 共用同一份公共 Meeting State；同一使用者也能看到自己的 Personal Sidekick，但 Add-on 只使用窄版版面，不會把長效 session 或 API key 放入 iframe。

## Voice Bot 整合

Proximate 不自行維護 Google 帳號登入或瀏覽器自動化。後端透過 Meeting BaaS 建立與管理 Google Meet Bot，只有在會議政策允許且投票達到門檻後，才傳送 `approved_text` 要求 Bot 播放語音。Meeting BaaS 的 API、Webhook、串流能力與用量限制，應以其[官方文件](https://www.meetingbaas.com/zh-CN/meeting-bot-api-for-google-meet)為準。

主要流程：

```text
Capture Page → WebSocket → STT → OpenAI
→ 結構化 approved_text → ElevenLabs TTS
→ Meeting BaaS Voice Bot → Google Meet 語音輸出
```

Meeting BaaS 的會議音訊／逐字稿串流可作為 Capture Page 失敗時的備援輸入。若 API、語音輸出或用量額度不可用，系統回退為 Meet Add-on 公開文字卡片，不中斷會議紀錄與共識流程。

## 環境需求

- Node.js 24.13.1（建議依 `.node-version`）
- npm 11 或相容版本
- uv 0.11 或相容版本
- Python 3.12（由 uv 自動安裝與管理）

## 環境變數

後端環境變數放在 `backend/`：

```cmd
cd backend
copy .env.example .env
```

後端由 `pydantic-settings` 讀取 `backend/.env`。

前端環境變數放在 `frontend/`：

```cmd
cd frontend
copy .env.example .env.local
```

前端在沒有設定時使用安全的本機預設值 `http://localhost:8000`；若要覆寫，請編輯 `frontend/.env.local`：

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

`backend/.env` 與 `frontend/.env.local` 均已被 Git 忽略。不要在 `NEXT_PUBLIC_` 變數中放置機密。

## 前端

```cmd
cd frontend
npm install
npm run dev
```

瀏覽器開啟 `http://localhost:3000`。

檢查指令：

```cmd
cd frontend
npm run lint
npm run typecheck
npm run build
```

## 後端

```cmd
cd backend
uv python install 3.12
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

健康檢查位於 `http://127.0.0.1:8000/health`，API 文件位於 `http://127.0.0.1:8000/docs`。

檢查指令：

```cmd
cd backend
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## 已採用的產品決策

- 正式登入採 **Neon Auth**；Dashboard 使用 `/dashboard`，產品首頁日後另建。
- Web App 與 FastAPI API 正式部署目標為 **Vercel**；FastAPI WebSocket 長連線需先完成部署驗證。
- Google Meet 會中介面採 Meet Add-on `/meetings/[id]/addon`，並保留瀏覽器 fallback `/meetings/[id]/live`。
- Audio Setup 開始後需持續收音；Capture Page 保持開啟並回報 track／WebSocket 中斷。
- Member 可在每張 AI 發言卡重新投票；「稍後／忽略」不是永久終止狀態。
- 前端優先採用 ProductPlanning.md 列出的套件；安裝前仍需逐批驗證相容性。

## 尚待正式開發前確認

- FastAPI WebSocket 在 Vercel 的長連線、timeout、重連與替代部署方案。
- Neon Auth、Google Meet Add-on、Meeting BaaS、OpenAI、Groq、ElevenLabs 與 Sentry 的帳號、金鑰及 development deployment 尚未建立或連線。
