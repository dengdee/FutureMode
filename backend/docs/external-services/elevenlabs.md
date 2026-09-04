# ElevenLabs TTS 設定流程

適用步驟：後端步驟 6 的 Voice Bot 語音延伸。

1. 建立 development workspace。
2. 建立限制為文字轉語音的 API key，設定 credit quota。
3. 選擇並記錄繁體中文 voice ID。
4. 放入 `backend/.env`：

   ```env
   ELEVENLABS_API_KEY=your_development_key
   ELEVENLABS_VOICE_ID=your_voice_id
   ```

5. 用固定 approved text 測試音訊格式、字數限制與播放延遲。
6. 只有 Meeting policy 與 vote threshold 通過後才產生 TTS；保存 usage metadata，不保存私人 prompt。

TTS 失敗或額度不足時，保留 approved text 公開卡片，不能假裝 Voice Bot 已播放。
