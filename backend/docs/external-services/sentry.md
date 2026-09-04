# Sentry 設定流程

適用步驟：後端步驟 13。

1. 建立獨立 development project，production 另建 project 或 environment。
2. 取得 backend DSN，放入 `backend/.env`：

   ```env
   SENTRY_DSN=https://...
   SENTRY_ENVIRONMENT=development
   ```

3. 設定 server-side before-send redaction，移除 transcript、私人 prompt、API key、token、email 與完整 request body。
4. 建立錯誤告警與 retention policy；限制團隊存取權。
5. 用故意失敗的測試事件確認 DSN、遮罩與 request correlation ID。

Sentry 只接收必要 metadata；敏感正文不應因 exception、HTTP client 或 validation error 被上傳。
