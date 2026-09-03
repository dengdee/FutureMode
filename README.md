# Proximate

Proximate 是一套以「AI 作為另一位組員」為核心的智慧會議協作系統。本 Repository 目前只包含可執行的前後端基礎架構，尚未實作登入、AI、會議流程、資料庫 CRUD 或外部服務整合。

完整產品與技術規劃請見 [`ProductPlanning.md`](ProductPlanning.md)。

## 專案結構

```text
.
├─ frontend/        # Next.js 16.3、React 19、TypeScript、Tailwind CSS
│  ├─ app/           # Dashboard 與 Meeting Workspace routes
│  │  └─ meetings/[id]/addon/ # Google Meet Add-on iframe 入口
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
/meetings/[id]/review        # 會後摘要、逐字稿、決策、行動項目與成員確認
/memory                      # Team Memory
/settings                    # 團隊、整合與隱私設定
```

`/meetings/[id]/addon` 是嵌入 Google Meet 的窄版 iframe；會議中不要求使用者切回完整 Web App。Voice Bot 由後端透過 [Meeting BaaS Google Meet Bot API](https://www.meetingbaas.com/zh-CN/meeting-bot-api-for-google-meet) 加入會議並輸出語音。主要逐人收音仍由 Audio Setup／Capture 流程提供，Meeting BaaS 音訊串流可作為備援。

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
cd /d C:\hackathonProjects\futuremode\backend
copy .env.example .env
```

後端由 `pydantic-settings` 讀取 `backend/.env`。

前端環境變數放在 `frontend/`：

```cmd
cd /d C:\hackathonProjects\futuremode\frontend
copy .env.example .env.local
```

前端在沒有設定時使用安全的本機預設值 `http://localhost:8000`；若要覆寫，請編輯 `frontend/.env.local`：

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

`backend/.env` 與 `frontend/.env.local` 均已被 Git 忽略。不要在 `NEXT_PUBLIC_` 變數中放置機密。

## 前端

```cmd
cd /d C:\hackathonProjects\futuremode\frontend
npm install
npm run dev
```

瀏覽器開啟 `http://localhost:3000`。

檢查指令：

```cmd
cd /d C:\hackathonProjects\futuremode\frontend
npm run lint
npm run typecheck
npm run build
```

## 後端

```cmd
cd /d C:\hackathonProjects\futuremode\backend
uv python install 3.12
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

健康檢查位於 `http://127.0.0.1:8000/health`，API 文件位於 `http://127.0.0.1:8000/docs`。

檢查指令：

```cmd
cd /d C:\hackathonProjects\futuremode\backend
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## 尚待正式開發前確認

- 規劃文件同時出現 Clerk 與 Neon Auth；登入實作前需確定唯一方案。
- 規劃中的 FastAPI WebSocket 若部署於 Vercel，需先驗證長連線支援或調整 API hosting。
- Neon、Google Meet Add-on、Meeting BaaS、OpenAI、Groq、ElevenLabs 與 Sentry 均未建立或連線。
