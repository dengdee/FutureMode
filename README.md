# Proximate

Proximate 是一套以「AI 作為另一位組員」為核心的智慧會議協作系統。本 Repository 目前只包含可執行的前後端基礎架構，尚未實作登入、AI、會議流程、資料庫 CRUD 或外部服務整合。

完整產品與技術規劃請見 [`ProductPlanning.md`](ProductPlanning.md)。

## 專案結構

```text
.
├─ frontend/        # Next.js 16.3、React 19、TypeScript、Tailwind CSS
├─ backend/         # FastAPI、Pydantic settings、pytest、Ruff
├─ .env.example     # 安全的本機環境變數範例
└─ ProductPlanning.md
```

前端與後端彼此獨立，不直接引用對方的內部程式碼。

## 環境需求

- Node.js 24.13.1（建議依 `.node-version`）
- npm 11 或相容版本
- uv 0.11 或相容版本
- Python 3.12（由 uv 自動安裝與管理）

## 環境變數

複製根目錄的 `.env.example` 為 `.env`：

```powershell
Copy-Item .env.example .env
```

後端由 `pydantic-settings` 讀取根目錄 `.env`。前端在沒有設定時使用安全的本機預設值 `http://localhost:8000`；若要覆寫，請在 `frontend/.env.local` 設定：

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

`.env` 與 `.env.local` 均已被 Git 忽略。不要在 `NEXT_PUBLIC_` 變數中放置機密。

## 前端

```powershell
Set-Location frontend
npm install
npm run dev
```

瀏覽器開啟 `http://localhost:3000`。

檢查指令：

```powershell
npm run lint
npm run typecheck
npm run build
```

## 後端

```powershell
Set-Location backend
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

健康檢查位於 `http://127.0.0.1:8000/health`，API 文件位於 `http://127.0.0.1:8000/docs`。

檢查指令：

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## 尚待正式開發前確認

- 規劃文件同時出現 Clerk 與 Neon Auth；登入實作前需確定唯一方案。
- 規劃中的 FastAPI WebSocket 若部署於 Vercel，需先驗證長連線支援或調整 API hosting。
- Neon、Google Meet Add-on、Meeting BaaS、OpenAI、Groq、ElevenLabs 與 Sentry 均未建立或連線。
