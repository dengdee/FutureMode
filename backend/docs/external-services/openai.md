# OpenAI 設定流程

適用步驟：後端步驟 9–12。

1. 建立 development project，確認活動額度／billing 與資料使用政策。
2. 建立 server-side API key，記錄建立日期與用途。
3. 將金鑰放入 `backend/.env`：

   ```env
   OPENAI_API_KEY=your_development_key
   OPENAI_MODEL=your_approved_model
   ```

4. 設定每場 meeting 的 request、token、retry 與成本上限。
5. 先用受控 fixture 驗證 structured output，再接真實 transcript。
6. 在 log 只保留 request ID、模型、延遲、token usage 與錯誤類型，不保存 prompt／回應正文。

API key 不可進前端或 `NEXT_PUBLIC_` 變數。模型輸出必須通過 Pydantic schema，失敗時走 fixture／文字卡降級。
