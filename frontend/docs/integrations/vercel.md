# Vercel 前端部署設定

1. 將 repository 匯入 Vercel，Root Directory 設為 `frontend`。
2. Framework 選 Next.js，Build Command 使用 `npm run build`，Install Command 使用 `npm install`。
3. 在 Preview／Production 分別設定 `NEXT_PUBLIC_API_BASE_URL`，指向對應 FastAPI URL。
4. 將部署網址提供給後端設定 CORS、Neon Auth callback 與 Google Meet Add-on allowlist。
5. Deploy 後檢查 `/`、`/dashboard` 與 `/health` 呼叫；不要在 Vercel 前端環境變數放任何 secret。

FastAPI 長連線 WebSocket 是否適合 Vercel 屬後端部署決策；前端只依賴後端提供的公開 HTTPS／WSS URL。
