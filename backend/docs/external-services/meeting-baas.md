# Meeting BaaS 設定流程

適用步驟：後端步驟 6。Repository 目前已有 `POST /meetbot/join` 初步整合。

1. 建立 Meeting BaaS development account／workspace。
2. 確認 Google Meet bot、speaking、webhook／streaming 能力與方案額度。
3. 建立 development API key，若平台支援，限制權限與 IP；完整金鑰只保存一次。
4. 建立測試 Google Meet 連結，取得參與者對錄音、轉錄與 AI 發言的同意。
5. 在 `backend/.env` 設定：

   ```env
   MEETING_BAAS_API_KEY=your_development_key
   MEETING_BAAS_BASE_URL=https://api.meetingbaas.com
   MEETING_BAAS_WEBHOOK_SECRET=your_webhook_secret
   ```

6. 先用固定 `meeting_url` 測試 join、leave、webhook signature 與重複請求。
7. 再接 `approved_text` immutable version；未通過政策／投票門檻不得呼叫 speak。
8. 记录 bot lifecycle、provider request ID、狀態與費用 metadata，不記錄 API key 或私人正文。

任何 provider 失敗都必須回退為公開文字卡片；不能把失敗標示為已發言。
