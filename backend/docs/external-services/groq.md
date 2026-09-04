# Groq Whisper 設定流程

適用步驟：後端步驟 8 的正式 STT 延伸。

1. 建立 Groq development project。
2. 建立 project-scoped API key，設定保守 rate limit。
3. 放入 `backend/.env`：

   ```env
   GROQ_API_KEY=your_development_key
   GROQ_STT_MODEL=whisper-large-v3-turbo
   ```

4. 以已取得同意的繁中測試音訊驗證延遲、格式、大小與錯誤重試。
5. 保存 speaker、sequence、confidence 與 source metadata；預設不保存原始音訊。

額度用盡或 STT 失敗時，改用預先校對的 transcript fixture，不阻塞共識流程。
