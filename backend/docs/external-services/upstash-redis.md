# Upstash Redis：Vercel Realtime Broker

步驟 7 使用 Neon PostgreSQL 作為 `meeting_events` durable event log；Upstash Redis 只負責
跨 Vercel Function instance 的即時 fan-out 與 shared presence，不能取代 PostgreSQL replay。

## 設定

在 Upstash 建立 Redis database，取得 TLS Redis URL，並在 Backend 本機環境與 Vercel
Backend Project 設定：

```env
UPSTASH_REDIS_URL=rediss://default:<token>@<host>:6379
REALTIME_REQUIRE_BROKER=true
```

不要使用 REST token 或將 Redis URL 放進 `NEXT_PUBLIC_*` 前端環境變數。

## 驗收

1. 對 Neon 執行 `uv run alembic upgrade head`，確認 `meeting_events` 存在。
2. 在 Vercel staging 用兩個瀏覽器帳號連進同一 meeting；讓兩個 WebSocket 連線落在不同
   Function instance。
3. PATCH state 一次。兩邊都必須只收到一次相同的 `event_id`／`cursor`。
4. 中斷其中一個連線後再重連。snapshot 後應只 replay 未 ACK 的 cursors。
5. 對 private event 驗證指定 user 收到，另一個 user 永遠不會收到或 replay 到該 event。

Redis 若不可用且 `REALTIME_REQUIRE_BROKER=true`，gateway 會以 WebSocket `1013` 拒絕新連線，
避免多人 room 靜默失去同步。
