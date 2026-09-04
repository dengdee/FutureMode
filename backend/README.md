# Proximate Backend 開發流程

本文件是後端開發的執行順序與驗收基準。它根據根目錄的 `ProductPlanning.md` 與目前 `backend/` 程式碼整理而成；本階段只建立規劃，不代表下列功能已完成。

## 目前後端狀態

- 技術：Python 3.12、FastAPI、Pydantic Settings、Uvicorn、HTTPX、pytest、Ruff。
- 套件管理：`uv`，依賴與版本鎖定在 `pyproject.toml`、`uv.lock`。
- 入口：`backend/app/main.py`。
- 設定：`backend/app/config.py`，目前讀取 `backend/.env`。
- 已完成 API：`GET /health`、`POST /meetbot/join`。
- 已完成測試：健康檢查測試。
- 已存在的 Meeting BaaS 實作：`backend/app/meetbot.py` 直接呼叫 Meeting BaaS v2 Bot API，尚未形成完整 adapter、政策驗證、idempotency 或完整錯誤模型。
- 尚未存在：WebSocket room、逐字稿管線、AI runtime、RAG、共識流程、正式 observability 與部署設定。

### 已完成步驟

- **步驟 0**：已確認 Neon Auth、逐人麥克風與 Vercel；分頁音訊列為備援。
- **步驟 1**：已完成設定容錯、CORS allowlist、request ID、統一錯誤回應、`/ready` 與基礎測試。
- **步驟 2**：已完成 SQLAlchemy async engine、asyncpg、Alembic migration 基線與資料庫就緒檢查。
- **步驟 3**：已建立 users、teams、team_members、meetings、meeting_participants、agenda_items ORM 模型與 Alembic migration。
- **步驟 4**：已完成 Neon Auth JWT 驗證、`/me`、使用者設定、團隊列表／成員查詢、團隊建立與角色授權基礎。
- **登入設定**：已提供 `GET /api/v1/auth/config` 與 Neon Auth 人工設定文件；登入／註冊仍由 Neon Auth SDK 負責。
- **步驟 5**：已完成會議建立、列表、單筆查詢、修改、參與者、議程、開始／結束與取消生命週期 API。
- **步驟 6（資料庫部分）**：已建立 `bot_sessions`、`voice_requests` 與非敏感 audit metadata 模型與 Migration；provider adapter 尚未完成。
- **步驟 7（資料庫部分）**：已建立 `meeting_states` 與 `meeting_event_cursors` 模型與 Migration；WebSocket gateway 尚未完成。
- **步驟 8（第一段）**：已建立 `transcripts` 模型、Migration，以及受保護的逐字稿新增／查詢 API；STT provider 與音訊串流尚未接入。
- **步驟 8（第二段）**：已修正每場會議 transcript sequence 唯一約束，並加入 `limit`／`after_sequence` 分頁查詢。
- **步驟 9（第一段）**：已建立 `ai_suggestions`、`suggestion_votes` 模型、Migration、建議列表與投票 API；尚未接入 LLM provider 與 Host 控制流程。
- **步驟 9（第二段）**：已加入 Suggestion 狀態控制與投票結果查詢；LLM provider 尚未接入。
- **步驟 10（第一段）**：已建立私人 Sidekick 訊息模型、Migration 與 user／meeting 隔離的新增／查詢 API；公開貢獻與 Delegate 尚未完成。
- **步驟 11（第一段）**：已建立 Consensus、Feedback、Action Items 模型、Migration，以及基本共識／回饋／行動項目 API；完整確認門檻與版本衝突處理待補。
- **步驟 11（第二段）**：已加入 Feedback 查詢、Consensus 確認，以及 Action Item 更新／刪除 API。
- **步驟 12（第一段）**：已建立 Team Memory 文件與文件切塊模型、Migration，以及 team-scoped 文件／chunk 建立與查詢 API；尚未接入 embedding provider、檔案上傳與 hybrid search。
- **步驟 12（第二段）**：已加入 team-scoped PostgreSQL 全文檢索 API，回傳文件來源、chunk 位置與相關度；尚未接入 embedding provider、pgvector hybrid ranking 與檔案 ingestion。
- **步驟 12（第三段）**：已補齊文件詳情與 chunk metadata 查詢 API，提供來源追溯與 chunk 數量資訊；尚未接入 embedding provider、pgvector hybrid ranking 與檔案 ingestion。
- **步驟 13（第一段）**：已為文件清單、詳情、chunks 與 Memory search 補上明確 OpenAPI response schema；前端可由 `/docs` 取得穩定欄位定義。
- **步驟 13（第二段）**：已為文件與 chunk 建立 API 補上明確建立結果 schema，OpenAPI 回應格式完整一致。
- **步驟 12（第四段）**：已加入純文字 ingestion API、固定大小 chunk 切分，以及文件 version／indexing 狀態欄位；尚未接入檔案儲存、embedding provider 與 pgvector hybrid search。
- **步驟 12（第五段）**：已加入 Embedding provider 的設定欄位與安全範例（預設 OpenAI `text-embedding-3-small`）；尚未執行外部 API 呼叫或建立 vector 欄位。
- **步驟 12（第六段）**：已加入 pgvector embedding 欄位、Migration 與 OpenAI embedding API；文件可透過 embed endpoint 建立向量並標記為 embedded。
- **步驟 12（第七段）**：已加入 Embedding 相似度與全文檢索混合排序 API；未設定 Embedding provider 時保留純全文搜尋並讓 hybrid endpoint 回傳設定錯誤。
- **步驟 12（第八段）**：已加入 Embedding 失敗狀態、錯誤摘要與 retry count；再次呼叫 embed endpoint 可重試既有 chunks。
- **步驟 12（第九段）**：已加入不可變文件版本紀錄、內容 hash 與版本查詢 API；不保存原始全文。
- **步驟 12（第十段）**：已加入 UTF-8 純文字／Markdown 與 PDF multipart upload，限制 5 MB 並沿用既有 ingestion 流程；雲端檔案儲存待後續外部方案確認。
- **步驟 12（第十一段）**：搜尋僅納入 `ready`／`embedded` 文件，排除尚未完成或索引失敗資料；hybrid search 僅使用已建立向量的 `embedded` 文件。
- **步驟 12（第十二段）**：已加入文件 archive lifecycle API；archive 僅標記狀態、不刪除 chunks／vectors，且會被搜尋排除。
- **步驟 12（第十三段）**：Embedding 改為可設定批次處理並限制單文件 chunks 數量，降低 provider 請求大小與成本風險。
- **步驟 12（第十四段）**：已加入 Cloudflare R2 S3-compatible storage adapter 與設定欄位；尚未接到文件 upload API。
- **步驟 12（第十五段）**：文件 upload API 已接入 Cloudflare R2，保存原始檔案並於 document metadata 記錄 storage key；未提供刪除舊檔操作。
- **步驟 12（第十六段）**：已加入 team-scoped R2 預簽名下載 URL API，短效 URL 可供 Web 預覽／下載且不暴露儲存金鑰。
- **步驟 12（第十七段）**：已加入文件刪除 API，先清理 R2 原始檔，再刪除文件及其 chunks／vectors／版本資料；R2 失敗時保留資料庫內容。
- **步驟 12（第十八段）**：已加入 R2 檔案存在性檢查 API，Web 端可確認原始檔是否仍可取用。
- **步驟 12（第十九段）**：文件版本會記錄對應 R2 storage key，版本查詢可追溯各版本原始檔；新增 Migration `0016_version_storage_key`。
- **步驟 12（第二十段）**：全文與 hybrid search 支援 `source_type`、`version` 與 metadata key/value 過濾，便於 Web 端進行版本與來源治理。
- **步驟 12（第二十一段）**：已加入指定文件版本回復 API，從 R2 讀回原始檔並重新 ingestion 產生新版本。
- **步驟 12（第二十二段）**：文件刪除會清理目前文件與所有歷史版本的 R2 原始檔，避免留下孤兒物件。
- **步驟 8（第一段）**：已加入 Groq Whisper STT 音訊轉文字 API，支援 25 MB 上限與 provider 錯誤處理；TTS 沿用 `meetbot.py`／Meeting BaaS，不另接 ElevenLabs。
- **步驟 8（第二段）**：STT 成功後會持久化為 transcript segment，產生 meeting 內 sequence 與 `source=groq`；speaker mapping 與串流仍待後續處理。
- **步驟 8（第三段）**：STT 上傳 API 支援 `speaker_label` 與 `started_at` multipart 欄位，持久化逐人來源與時間；未提供 speaker 時使用 `unknown`。

## 目前發現的缺口與衝突

1. `MEETING_BAAS_API_KEY` 本機可為空是刻意設計；未設定時呼叫會回傳錯誤，正式環境必須使用 Secret 管理。
2. Neon Auth 後端驗證基礎已完成，包含 issuer／audience／JWKS 設定、`/api/v1/auth/config` 與設定文件；仍需要人工在 Neon Console 建立 Auth、測試帳號並填入 `backend/.env`。
3. 規劃文件建議 `backend/integrations/meetingbaas/`、`voice_bot/`，目前仍以 `backend/app/meetbot.py` 為相容入口；Meeting BaaS adapter、Webhook、retry 與 idempotency 尚未完成。
4. 音訊主要來源已確認採逐人麥克風；分頁音訊僅作備援。瀏覽器權限、同意流程與斷線行為需要前端／瀏覽器實測，後端尚未宣稱完成。
5. API hosting 已選定 Vercel；WebSocket gateway 與 Vercel 長連線能力尚未完成及實測，不預先宣稱已支援。

## 開發順序

每一步都應獨立完成、測試並更新 API 文件；未完成前置條件時不要跳到後續步驟。

### 步驟 0｜後端基線與決策凍結

- **目標**：確認本機啟動方式、目前 API、命名規則、錯誤回應格式與待裁決事項。
- **功能內容**：建立後端模組邊界、API prefix（建議 `/api/v1`）、環境分層（development／test／production）與決策紀錄。
- **預計異動範圍**：`backend/README.md`、`backend/app/` 目錄規則、API 文件；不先改業務程式。
- **資料庫變更**：無。
- **API 規格**：保留 `GET /health`；確認現有 `POST /meetbot/join` 的 request／response 與錯誤格式。
- **前置條件**：無。
- **環境設定**：Python 3.12、uv；確認 `backend/.env` 不進 Git。
- **驗證方式**：`uv sync`、Ruff、pytest、啟動 Uvicorn、呼叫 `/health`；另外測試未設定必要環境變數時的可理解錯誤。
- **完成標準**：決策清單已確認，後續步驟不再自行猜測認證、音訊主要來源與 hosting。
- **注意事項**：不得讀取、輸出或提交現有 `.env` 的真實值。

### 步驟 1｜設定管理、應用程式基礎與錯誤處理

- **目標**：讓服務在 development／test 中可預期啟動，並提供一致的錯誤與日誌邊界。
- **功能內容**：設定 schema、CORS allowlist、request correlation ID、全域 exception handler、健康／ready 檢查、敏感欄位遮罩。
- **預計異動範圍**：`app/config.py`、`app/main.py`、`app/core/`、`app/api/`、`tests/`。
- **資料庫變更**：無。
- **API 規格**：`GET /health`（程序存活）；`GET /ready`（依賴就緒，未接 DB 前可明確回報未啟用）；錯誤統一包含 `code`、`message`、`request_id`，不得包含 stack trace 或機密。
- **前置條件**：步驟 0。
- **環境設定**：`APP_ENV`、`API_HOST`、`API_PORT`、`CORS_ORIGINS`、`LOG_LEVEL`；`MEETING_BAAS_API_KEY` 在本機可為空，呼叫功能時回傳未設定錯誤。
- **驗證方式**：正常啟動、錯誤設定、未知路由、驗證錯誤、CORS、log redaction 測試。
- **完成標準**：所有錯誤有穩定格式，敏感正文不出現在 log，既有 `/health` 行為不退化；`/ready` 能明確標示尚未啟用的依賴。
- **注意事項**：CORS 不可使用 production wildcard；不要在錯誤中回傳 provider 原始 token 或完整 request body。

### 步驟 2｜資料庫連線、ORM 與 Migration 基礎

- **目標**：建立 Neon PostgreSQL 的可測試連線與可回溯 migration 流程。
- **功能內容**：SQLAlchemy 2 async engine／session、Alembic、連線池、transaction boundary、test database strategy、pgvector 啟用策略。
- **預計異動範圍**：`app/db/`、`app/models/`、`alembic/`、`alembic.ini`、`tests/`、`pyproject.toml`。
- **資料庫變更**：建立 migration 基線；先不建立完整業務表，或只建立 migration metadata。
- **API 規格**：`GET /ready` 可檢查 DB；無新增業務 API。
- **前置條件**：步驟 1；Neon development database 已人工建立。
- **環境設定**：`DATABASE_URL`（asyncpg／pooler 連線字串）、`DB_POOL_SIZE`、`DB_MAX_OVERFLOW`。
- **驗證方式**：成功／失敗連線、transaction rollback、migration upgrade、空資料庫重建、pytest isolation。
- **完成標準**：新環境可由 lockfile 安裝並執行 migration；不使用 reset 或 rollback 破壞既有資料。
- **注意事項**：連線字串只在後端；migration 必須可審查、不可在啟動時偷偷改 schema。

Migration 指令（在 `backend/` 執行，需先設定 `DATABASE_URL`）：

```cmd
uv run alembic upgrade head
uv run alembic current
```

### 步驟 3｜核心資料模型與第一批 Migration

- **目標**：以最小可用模型支撐團隊、會議與權限範圍。
- **功能內容**：users、teams、team_members、meetings、meeting_participants、agenda items；建立時間、更新時間、狀態與外部 ID 約束。
- **預計異動範圍**：`app/models/`、`app/schemas/`、`app/repositories/`、`alembic/versions/`、`tests/`。
- **資料庫變更**：新增上述資料表、FK、unique／index、UTC timestamp；embedding、transcript 等表留到相依步驟。
- **API 規格**：本步驟可先提供 repository/service 測試；若開放 API，限定為受保護的 read-only schema preview。
- **前置條件**：步驟 2；認證方案可先以測試 principal 代替，但不得把 mock 當正式身份。
- **環境設定**：`DATABASE_URL`。
- **驗證方式**：migration、模型約束、重複 team member、無效 FK、transaction rollback、repository 測試。
- **完成標準**：模型與規劃實體一致，資料庫約束可防止跨 team 連結與孤兒資料。
- **注意事項**：所有查詢必須帶 `team_id`／權限範圍；時間統一 UTC。

### 步驟 4｜身分驗證、團隊與授權

- **目標**：驗證外部 session／JWT，並把使用者、團隊與角色權限套用到每個 endpoint。
- **功能內容**：選定 Clerk 或 Neon Auth、token 驗證、principal dependency、team membership、owner／admin／member／host 權限矩陣。
- **預計異動範圍**：`app/auth/`、`app/dependencies/`、`app/services/`、`app/schemas/`、`tests/`。
- **資料庫變更**：補 users external ID、teams、team_members 索引與角色欄位（依步驟 3 調整）。
- **API 規格**：`GET /api/v1/me`、`GET /api/v1/teams`；401 未登入、403 無權限、404 不洩漏資源存在性。
- **前置條件**：步驟 3；完成認證方案裁決。
- **環境設定**：provider issuer／JWKS／audience／client ID；絕不把 client secret 放前端或 log。
- **驗證方式**：有效／過期／錯誤 token、跨 team 存取、角色邊界、host 權限、token rotation。
- **完成標準**：所有受保護 endpoint 都經後端授權，不能只相信前端傳入的 user_id／team_id。
- **注意事項**：Private Sidekick 的隔離必須在 service/repository 層強制，不只靠路由。

### 步驟 5｜會議設定與生命週期 API

- **目標**：完成建立、設定、開始與結束一場會議的核心 REST 流程。
- **功能內容**：標題、時間、議程、參與者、Host、AI 角色、介入程度、Voice policy 與 required participants。
- **預計異動範圍**：`app/api/meetings.py`、`app/services/meeting_service.py`、`app/schemas/meeting.py`、`app/models/`、migration、tests。
- **資料庫變更**：meetings、meeting_participants、agenda items、meeting settings 欄位與狀態索引。
- **API 規格**：`POST /api/v1/meetings`、`GET /api/v1/meetings/{id}`、`PATCH /api/v1/meetings/{id}`、`POST /api/v1/meetings/{id}/start`、`POST /api/v1/meetings/{id}/end`。
- **前置條件**：步驟 4。
- **環境設定**：無新增外部金鑰；時間以 UTC 傳輸與儲存。
- **驗證方式**：schema validation、重複 participant、非成員、非 Host 修改、非法狀態轉換、併發更新。
- **完成標準**：會議狀態轉換與權限可追溯，API schema 與 OpenAPI 一致。
- **注意事項**：Host 是單場設定，不等於永久 team role；不得把 delegate 當成實際投票者。

### 步驟 6｜Meeting BaaS Adapter 與 Voice Bot 政策

- **目標**：將現有 `/meetbot/join` 從直接 HTTP 呼叫提升為可測試、可控權限的 provider adapter。
- **功能內容**：Meeting BaaS client、timeout／retry、provider error mapping、bot lifecycle、webhook signature、idempotency、approved_text immutable version。
- **預計異動範圍**：保留 `app/meetbot.py` 相容路由；新增 `app/integrations/meetingbaas/`、`app/voice_bot/`、schemas、tests。
- **資料庫變更**：bot_sessions、voice_requests、audit metadata；不得保存 API key 或完整私人內容。
- **API 規格**：保留或版本化 `POST /api/v1/meetings/{id}/voice-bot/join`；`POST /.../speak` 只能接收已核准版本；webhook endpoint 驗證簽章。
- **前置條件**：步驟 1、4、5；Meeting BaaS 測試帳號與測試會議連結。
- **環境設定**：`MEETING_BAAS_API_KEY`、`MEETING_BAAS_BASE_URL`、`MEETING_BAAS_WEBHOOK_SECRET`、timeout／用量上限。
- **驗證方式**：mock provider、連線失敗、4xx／5xx、重試、重送 webhook、重複 join、未達政策門檻不得 speak。
- **完成標準**：provider 失敗時回傳可理解錯誤並保留文字卡降級路徑；不會重複建立 Bot 或未授權發言。
- **注意事項**：現有 `POST /meetbot/join` 直接把 provider 原文回傳，後續需改為穩定內部 schema 並遮罩錯誤細節。

### 步驟 7｜Realtime Gateway 與 Meeting State

- **目標**：建立已驗證、可重連、事件去重的會議即時通道。
- **功能內容**：WebSocket room、snapshot、cursor replay、event ID、schema version、monotonic state version、participant presence。
- **預計異動範圍**：`app/websocket/`、`app/realtime/`、`app/schemas/events.py`、models、tests。
- **資料庫變更**：meeting_states、event cursor／audit metadata；是否保存完整 event log 待確認。
- **API 規格**：`GET /api/v1/meetings/{id}/state`；`WS /api/v1/meetings/{id}/events`；事件包含 `event_id`、`meeting_id`、`timestamp`、`schema_version`、`payload`。
- **前置條件**：步驟 4、5；WebSocket hosting 方案確認。
- **環境設定**：Redis／ARQ 是否納入 MVP 待確認；若多 instance，需 pub/sub。
- **驗證方式**：認證、跨 room、斷線重連、舊 cursor、重複 event、舊 state version、多人同時更新。
- **完成標準**：不遺失或重複套用事件；私人事件只送給本人，公共事件才廣播 room。
- **注意事項**：不要把 chain-of-thought 或私人 prompt 放進事件 payload。

### 步驟 8｜逐字稿接收與 Speech Pipeline 邊界

- **目標**：先支援受控 fixture，再建立可替換的 STT／音訊輸入 adapter。
- **功能內容**：transcript schema、speaker mapping、sequence、時間校正、fixture replay；後續才接 VAD、Groq Whisper 或 Meeting BaaS stream。
- **預計異動範圍**：`app/speech/`、`app/adapters/stt/`、`app/api/transcripts.py`、models、migration、tests。
- **資料庫變更**：transcripts、segment sequence／confidence／source 欄位；原始音訊預設不保存。
- **API 規格**：`POST /api/v1/meetings/{id}/transcripts`（受保護 ingestion）；`GET /api/v1/meetings/{id}/transcripts`；必要欄位含 speaker、started_at、ended_at、text、source。
- **前置條件**：步驟 5、7；先決定分頁音訊或逐人麥克風主方案。
- **環境設定**：fixture 模式不需金鑰；正式候選為 `GROQ_API_KEY`、`GROQ_STT_MODEL`。
- **驗證方式**：schema、sequence 去重、錯誤 speaker、斷線、未授權私人音訊、fixture replay。
- **完成標準**：逐字稿可推動公共 state，且私人 Sidekick 音訊不會進公共 transcript。
- **注意事項**：不得承諾高精度聲紋辨識；所有輸入來源與同意狀態都要可追溯。

### 步驟 9｜OpenAI Adapter、Meeting State 與 AI 舉手

- **目標**：以 structured output 建立可驗證的 Main Agent 與 Intervention Engine。
- **功能內容**：LLM adapter、prompt/schema version、增量 state、relevance／novelty／importance／urgency／confidence 評分、冷卻與上限。
- **預計異動範圍**：`app/adapters/llm/`、`app/agents/`、`app/intervention/`、schemas、services、tests。
- **資料庫變更**：ai_suggestions、suggestion_votes、meeting_states；保存分數、來源、狀態與處理結果，不保存 chain-of-thought。
- **API 規格**：`GET /api/v1/meetings/{id}/suggestions`、`POST /api/v1/meetings/{id}/suggestions/{suggestion_id}/vote`、Host 控制 endpoint；公共更新走 WebSocket。
- **前置條件**：步驟 7、8；OpenAI development project／key。
- **環境設定**：`OPENAI_API_KEY`、`OPENAI_MODEL`、每場 token／call budget。
- **驗證方式**：schema invalid、timeout、低信心、重複建議、舊 state version、prompt injection fixture、權限測試。
- **完成標準**：模型失敗時仍可用 deterministic fixture；AI 只能舉手，不可自行投票或直接發言。
- **注意事項**：檢索內容視為資料；任何 AI 輸出都必須經 Pydantic 驗證與真人政策控制。

### 步驟 10｜Personal Sidekick、公開貢獻與 Delegate 邊界

- **目標**：建立嚴格的私人資料隔離與明確授權公開流程。
- **功能內容**：私人 thread、公開預覽、本人授權後建立 public contribution；Delegate 只依事前規則建立署名卡。
- **預計異動範圍**：`app/agents/personal/`、`app/delegate/`、schemas、services、models、migration、tests。
- **資料庫變更**：personal_agent_messages、public_contributions、delegate_profiles、版本／有效期間／audit 欄位。
- **API 規格**：`POST/GET /api/v1/meetings/{id}/personal/messages`、`POST /.../personal/contributions/preview`、`POST /.../personal/contributions/publish`、Delegate CRUD／preview。
- **前置條件**：步驟 4、7、9。
- **環境設定**：沿用 OpenAI；Personal agent 的資料範圍與 retention policy 待確認。
- **驗證方式**：A 不可讀 B 私訊、未授權不可公開、公開後保留私人原文、Delegate 越權、過期規則、audit。
- **完成標準**：私人原文與公開稿為不同資料；Main Agent 只能看到已授權 public contribution。
- **注意事項**：Delegate 不得投票、承諾預算、接受任務或產生新決策。

### 步驟 11｜會後 Consensus 與 Action Items

- **目標**：將公共 state 整理成可版本化、逐人確認的共識。
- **功能內容**：決策、理由、否決方案、未決問題、行動項目、required participant feedback、draft／awaiting_responses／conflicted／confirmed。
- **預計異動範圍**：`app/consensus/`、`app/action_items/`、schemas、services、models、migration、tests。
- **資料庫變更**：consensus_versions、consensus_feedback、decisions、action_items；保留版本與來源。
- **API 規格**：`POST /api/v1/meetings/{id}/consensus`、`GET /.../consensus`、`POST /.../consensus/{version}/feedback`、action item CRUD。
- **前置條件**：步驟 5、7、9；逐字稿／state fixture 可重播。
- **環境設定**：OpenAI adapter；無新增外部服務。
- **驗證方式**：未回覆不算同意、衝突產生新版、重複 feedback、非必要成員、來源缺失、confirmed gate。
- **完成標準**：只有所有必要成員回覆且無未解衝突才可 confirmed；確認決策才可進 Team Memory。
- **注意事項**：不得把「沒有人反對」當作全員同意。

### 步驟 12｜Team Memory／RAG 與來源治理（MVP 後段）

- **目標**：在權限先行的前提下，提供可追溯的決策與文件檢索。
- **功能內容**：PDF／純文字 ingestion、chunk、embedding、PostgreSQL FTS＋pgvector hybrid search、來源與版本、ACL。
- **預計異動範圍**：`app/rag/`、`app/adapters/embedding/`、document API、models、migration、workers、tests。
- **資料庫變更**：documents、document_chunks、decisions、embedding vector、ACL／version／effective date。
- **API 規格**：文件上傳、索引狀態、來源查詢、memory search；完整路徑與檔案限制待 API schema 設計時確認。
- **前置條件**：步驟 3、4、9、11；pgvector 與檔案保存方案確認。
- **環境設定**：Embedding provider key、檔案保存 bucket、大小／token／成本上限。
- **驗證方式**：跨 team ACL、過期文件、prompt injection、來源引用、hybrid ranking、刪除衍生索引。
- **完成標準**：先權限過濾再檢索；每項歷史提醒可回到來源；低信心內容以待確認呈現。
- **注意事項**：Notion／Google Drive／Jira 整合列為後續，不應阻塞 MVP。

### 步驟 13｜Observability、API 文件、測試與部署前檢查

- **目標**：讓後端可維運、可審查、可部署，且能定位每個 pipeline 階段。
- **功能內容**：OpenAPI tags／examples、contract tests、integration tests、WebSocket tests、redaction、Sentry、成本與用量 metadata、CI。
- **預計異動範圍**：`app/observability/`、`tests/`、`.github/`、部署設定、API docs；只處理 backend。
- **資料庫變更**：audit_logs、必要 metric／成本欄位；不得保存敏感正文。
- **API 規格**：完整 OpenAPI；`/docs`、`/openapi.json` 的 auth／schema／錯誤案例需可供前端串接。
- **前置條件**：步驟 1–12 中要納入 MVP 的項目均已完成。
- **環境設定**：Sentry DSN、log level、deployment URL、所有正式 provider secrets；全部使用部署平台 Secret。
- **驗證方式**：lint、format、type／schema check、unit、integration、API contract、build、migration dry run、secret scan、staging smoke test。
- **完成標準**：無機密進 Git；健康檢查、API 文件、資料庫 migration、錯誤追蹤與 rollback/runbook 齊全；正式部署前得到人工批准。
- **注意事項**：不在本流程自動部署、不建立付費資源、不執行 destructive migration。

## 必要功能與可選優化

### MVP 必要功能

步驟 0–9、步驟 11，以及步驟 13 的最小測試／文件／安全檢查。步驟 6 的 Voice Bot 必須有文字卡片降級路徑；步驟 8 可先使用受控繁中 fixture。

### 可選或後續功能

- 完整 Team Memory／RAG、embedding 與文件管理（步驟 12）。
- Delegate 完整觸發引擎、匿名貢獻、跨裝置 thread 同步（步驟 10 的延伸）。
- 真實分頁音訊、VAD、Groq streaming STT 與 Meeting BaaS transcript backup（步驟 8 的延伸）。
- Notion、Google Drive、Calendar、Jira、Zoom、Teams 整合。
- 多 instance Redis／ARQ、進階成本控制、Sentry performance tracing。

## 外部服務設定文件

需要人工建立帳號、project、金鑰或 OAuth 的服務，必須在實作該步驟前依個別文件設定。所有金鑰只放 `backend/.env` 或部署平台 Secret，不得提交 Git。

- [Neon PostgreSQL](docs/external-services/neon-postgresql.md)
- [認證方案（Clerk／Neon Auth 待選）](docs/external-services/authentication.md)
- [Meeting BaaS](docs/external-services/meeting-baas.md)
- [OpenAI](docs/external-services/openai.md)
- [Groq Whisper](docs/external-services/groq.md)
- [Cloudflare R2](docs/external-services/cloudflare-r2.md)
- [Sentry](docs/external-services/sentry.md)
- [Google Meet Add-on 與 Google Cloud](docs/external-services/google-meet-addon.md)

## 待確認問題

- 認證採 Clerk 或 Neon Auth？由誰負責 team／role source of truth？
- MVP 的音訊主要來源是分頁音訊還是逐人麥克風？是否保存原始音訊？
- Vercel 是否承載 FastAPI WebSocket，或需獨立 API／realtime hosting？
- Neon branch、pooler、pgvector、檔案保存與 test database 策略。
- Meeting BaaS v2 的 speaking、webhook、transcript 能力與實際計費。
- OpenAI、Groq 的活動額度、模型名稱、資料保留與成本上限。
- Sentry 是否允許接收錯誤 metadata；哪些欄位必須 server-side redaction？

## 可能風險

- 私人 Sidekick 內容誤進公共 state、log、RAG 或 WebSocket broadcast。
- 舊版 Meeting State／LLM 結果覆蓋新版本，造成錯誤決策。
- provider timeout、額度用盡或 WebSocket 斷線使 Demo 中斷。
- AI 將推測標成 confirmed，或 Delegate 超出授權範圍代表本人承諾。
- Migration、embedding、文件刪除未同步清除衍生資料。
- Vercel serverless 與長連線、webhook 可達性、OAuth／Workspace policy 不相容。

## 建議開始步驟

建議從 **步驟 0** 開始，先裁決認證、音訊主來源與 API hosting，再進入 **步驟 1**。目前若要先處理已存在的程式，則應先針對 `POST /meetbot/join` 補 provider mock、錯誤 schema、金鑰設定範例與測試，但這仍屬步驟 0／6 範圍，不應順便實作後續會議或 AI 功能。
