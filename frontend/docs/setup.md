# 本機開發

## 啟動

```powershell
cd C:\hackathonProjects\futuremode\frontend
npm install
npm run dev
```

後端另於 `backend/` 啟動。前端 API URL 由 `.env.local` 的 `NEXT_PUBLIC_API_BASE_URL` 指向，例如 `http://localhost:8000`。

## 驗證

```powershell
npm run typecheck
npm run lint
npm run build
```

可在 `http://localhost:8000/docs` 查看後端 Swagger；前端 Dashboard 的服務狀態會呼叫 `GET /health`。

## 環境變數規則

目前前端只需要公開的 `NEXT_PUBLIC_API_BASE_URL`。不要把 API key、Auth secret、Meeting BaaS token、OpenAI／ElevenLabs／Groq key 放入 `NEXT_PUBLIC_*`。
