# AI 服務前端整合邊界

OpenAI、ElevenLabs、Groq 都是後端服務，前端不直接呼叫，也不保存金鑰。

| 服務 | 後端用途 | 前端可見內容 |
| --- | --- | --- |
| OpenAI | Main／Personal Agent、結構化會議狀態 | 經後端驗證的摘要、建議與狀態 |
| ElevenLabs | TTS，供 Voice Bot 使用 | Voice Bot 播放中／完成／失敗狀態 |
| Groq Whisper | STT | 逐字稿與 speaker 狀態（依後端 ACL） |

若後端未提供正式 endpoint，前端不得把 provider key 放在 `.env.local`、`NEXT_PUBLIC_*` 或瀏覽器 Network request。
