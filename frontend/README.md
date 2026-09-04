# Proximate Frontend 開發計畫

本文件只規劃前端工作，不代表功能已實作。每次只執行使用者指定的一個步驟；未經指定不得提前建立頁面、安裝套件、修改後端或串接外部服務。

## 現況盤點

| 項目 | 現況 |
| --- | --- |
| 前端位置 | `frontend/` |
| 框架與語言 | Next.js `16.3.0` App Router、React `19.2.0`、TypeScript `5.9` |
| 套件管理 | npm；已存在 `package-lock.json` |
| 樣式 | Tailwind CSS `4.1`；`app/globals.css` 定義少量 CSS variables |
| UI 元件庫與動效 | 尚未安裝 shadcn/ui、Radix；已安裝 Tabler Icons 與 GSAP／`@gsap/react`，用於導覽與 Sidebar 動效 |
| 狀態管理 | 尚未使用 Zustand、React Context 或其他全域狀態方案 |
| 資料請求 | `lib/api/client.ts` 與 repository 已串接 `/health`、`/meetbot/join` |
| 現有頁面 | `/` 導向 `/dashboard`；Dashboard 顯示 API 狀態與正式資料尚未提供時的空狀態 |
| 已完成功能 | Next.js、TypeScript、ESLint、Tailwind、Tabler Icons、GSAP Sidebar 動效、API Client、Dashboard 健康檢查 UI |
| 尚未完成 | Neon Auth、正式 Meeting CRUD、表單、WebSocket、Google Meet Add-on、音訊、AI、外部服務完整整合 |

### 現有檔案與可沿用基礎

- `app/layout.tsx`：`lang="zh-Hant"`、Metadata 與全域 CSS 入口。
- `app/globals.css`：`--background`、`--foreground`、`--surface`、`--accent`、`--muted` 五個基本色彩 token。
- `app/page.tsx`：可保留為開發期 scaffold；產品首頁日後另建，Dashboard 正式入口固定為 `/dashboard`。
- `tsconfig.json`：已設定 `@/*` 路徑別名。
- `.env.example`：僅有 `NEXT_PUBLIC_API_BASE_URL`；不可在 `NEXT_PUBLIC_` 變數放 API key、Meet／Meeting BaaS token 或任何私人資料。

## 開發步驟進度

| 步驟 | 功能 | 狀態 | 實際完成內容／剩餘工作 |
| --- | --- | --- | --- |
| 01 | 前端基礎與設計語言 | 部分完成 | 已有 Tailwind token、Landing Page 與 `AppShell`；完整 Design System 與所有 route shell 尚未完成 |
| 02 | 路由、版面與導覽骨架 | 已完成 | 已建立所有規劃產品路由的靜態 UI、桌面／手機導覽、會議上下文頁首，以及 loading、error、404 邊界；尚未串接各功能 API |
| 03 | Domain 型別、API Client 與資料狀態 | 已完成（目前 API 範圍） | 已建立 `types/api.ts`、`lib/api/client.ts`、repositories；串接 `/health`、`/meetbot/join`，不使用 Mock Data |
| 04 | 登入狀態、角色與存取邊界 | 尚未執行 | Neon Auth、`/v1/me`、角色與 route guard 尚未實作 |
| 05 | Dashboard 與會議清單 | 部分完成 | Dashboard 已顯示真實 `/health` 結果與 API 未提供時的空狀態；會議清單 API 尚未存在 |
| 06–16 | 建立會議、Prepare、Audio、Add-on、Live、Review、Realtime、測試與部署 | 尚未執行 | 需等待對應後端 API／外部服務契約後依序實作 |

> 狀態只代表 repository 中已完成且可驗證的程式碼。每完成一個步驟，需同步更新本表、步驟內容與驗證結果。

## 已確認的架構決策

1. 正式登入採用 **Neon Auth**；Clerk 不列入目前實作方案。
2. API 正式部署採用 **Vercel**；FastAPI WebSocket 長連線必須先完成 staging 壓力與斷線重連驗證。
3. Dashboard 正式路由為 **`/dashboard`**；產品首頁日後另建立，不與 Dashboard 混用。
4. Google Meet Add-on 入口固定為 **`/meetings/[id]/addon`**。
5. 建立瀏覽器 fallback **`/meetings/[id]/live`**，供無法使用 Add-on 或開發期測試時承載 Live UI。
6. Member 可以修改自己的投票；「稍後」與「忽略」可重新投票。
7. Audio Setup 開始後必須持續收音；Capture Page 保持開啟並顯示連線狀態。背景分頁與裝置休眠仍須實測。
8. 優先採用 `ProductPlanning.md` 已列出的前端套件；未經指定不引入額外套件。

## 修改邊界

### 允許修改的前端目錄

```text
frontend/
├─ app/
├─ components/        # 尚未建立；預計放共用 UI
├─ features/          # 尚未建立；預計放領域功能
├─ lib/               # API client、repositories、formatters
├─ types/             # 尚未建立；預計放前端 domain／API 型別
├─ stores/            # 尚未建立；僅在核准採用狀態管理後建立
├─ public/            # 尚未建立；預計放前端靜態資產
├─ README.md          # 本文件
├─ package.json
├─ package-lock.json
├─ next.config.ts
├─ tsconfig.json
├─ eslint.config.mjs
└─ .env.example
```

### 禁止修改的後端目錄

```text
backend/
├─ app/
├─ tests/
├─ pyproject.toml
├─ uv.lock
├─ .python-version
└─ .env.example
```

本計畫不得修改後端 API、資料庫、Migration、驗證、CORS、部署或測試。現有後端只有 `GET /health`，其餘產品 API 都尚未存在。

### 前後端共用檔案與注意事項

| 檔案／設定 | 擁有範圍 | 注意事項 |
| --- | --- | --- |
| 根目錄 `README.md`、`ProductPlanning.md` | 專案共用文件 | 前端改動若使產品契約過期，先提出差異；未經要求不直接改規劃文件。 |
| `frontend/.env.example` | 前端 | 只能加入公開 URL、feature flag 等可公開值；不得加入秘密。 |
| `backend/.env.example` | 後端 | 禁止修改；前端僅可在計畫中列出需要後端提供的設定。 |
| REST／WebSocket schema | 前後端契約 | 目前已存在 `GET /health` 與 `POST /meetbot/join`；其餘產品 API／WebSocket 尚未建立，型別與 repository 只先覆蓋實際 endpoint。 |
| `package.json`／lockfile | 前端 | 只有使用者批准新套件時才可變更。 |

## 目標資訊架構

主導覽只保留四個入口：Dashboard、Meetings、Team Memory、Settings。單一會議是同一個 Meeting Workspace，不把會前、會中、會後拆成互不相干的產品。

```text
/                         # 產品首頁（後續建立）
/dashboard                # Dashboard 正式入口
/sign-in                  # 技術性登入入口
/meetings/new             # 建立會議
/meetings/[id]/prepare    # Meeting Workspace：會前
/meetings/[id]/audio-setup# 技術性收音設定，不列入主導覽
/meetings/[id]/addon      # Google Meet Add-on 窄版 iframe，不列入主導覽
/meetings/[id]/live       # Add-on 不可用時的瀏覽器 fallback／開發期測試頁
/meetings/[id]/review     # Meeting Workspace：會後
/memory                   # Team Memory
/settings                 # Team／Integrations／Privacy 三個 Tabs
```

> [!NOTE]
> `/meetings/[id]/live` 是瀏覽器 fallback 與開發期測試頁；一般使用者優先在 Google Meet 的 `/meetings/[id]/addon` 查看 Live State。兩者共用同一套 Live components 與資料 adapter，不維護兩套產品邏輯。

### Add-on 身分與畫面同步

Meet Add-on 不在 iframe 內重新執行登入。使用者從已登入的 Web App 開啟會議後，前端向後端交換一個綁定 `user_id`、`team_id`、`meeting_id` 的短效 meeting token，再把 token 交給 `/meetings/[id]/addon`。Add-on 以此 token 建立自己的 API／Realtime 連線，token 過期或權限不符時必須顯示重新開啟會議的提示。

同一個使用者的 Web App、瀏覽器 `/live` fallback 與 Meet Add-on 會看到相同的公共 Meeting State，也會看到自己的 Personal Sidekick 對話；其他成員看不到該私人內容。資料與功能元件共用，但版面不必完全相同：Add-on 是窄版 iframe，Web App 是完整工作區。

## 開發原則

- 產品資料優先使用正式 API；後端尚未提供的功能不假造 Mock Data，頁面顯示明確的「尚未提供」狀態。
- 所有正式 API 呼叫集中在 `lib/api/` 與 `lib/data/` repository；不得在頁面元件內散落 fetch 或 endpoint 字串。
- 私人 Sidekick 與公共 Meeting State 必須使用不同資料型別、不同 cache key／事件 channel；前端隱藏不能替代後端權限。
- 所有非同步畫面至少有 loading、success、empty、error、unauthorized 五種狀態；尚未實作的後端能力以明確 placeholder 呈現。
- 首版以繁體中文為預設；字串避免直接散落在複雜元件內，保留日後 i18n 集中化空間。
- 先沿用 Tailwind 與現有 CSS variables。依團隊決策，後續優先安裝並採用規劃文件列出的 shadcn/ui／Radix、Zustand、Axios、React Hook Form／Zod、Tabler Icons、date-fns；不得引入未列出的套件，且每批安裝都要在對應步驟驗證。

## 必要功能開發流程

### 步驟 01｜前端基礎與設計語言

- **目標**：將目前 scaffold 整理為可承載產品頁面的前端基礎，但不建立產品功能。
- **使用者情境**：使用者進入任一頁面時，取得一致的字體、色彩、間距、焦點與基本空白頁狀態。
- **功能內容**：盤點並延用既有 CSS variables；定義 AppShell、頁面容器、標題、卡片、按鈕、輸入欄位、狀態訊息的最小樣式規範。
- **頁面／路由**：`app/layout.tsx`、開發期 `/`。
- **元件規劃**：新增前需先確認是否使用自製 primitive；不安裝 shadcn/ui。
- **狀態管理**：無。
- **資料來源**：靜態內容。
- **API 串接**：無。
- **畫面狀態**：Skeleton、空狀態、錯誤提示與鍵盤 focus 樣式的共用規則。
- **互動細節**：可點擊元素需具 hover、focus-visible、disabled；非按鈕不可假裝成按鈕。
- **響應式需求**：最小寬度、可讀行長、手機安全邊距；不在此步設計單一產品頁。
- **預計異動範圍**：`app/layout.tsx`、`app/globals.css`、未來 `components/ui/`；不動後端。
- **前置條件**：無。
- **驗證方式**：`npm run lint`、`npm run typecheck`、不同 viewport 手動檢視。
- **完成標準**：後續頁面可使用一致 token 與基本 primitive，且沒有額外套件。
- **注意事項**：規劃文件指定的品牌視覺尚未提供，細節列為待確認。

### 步驟 02｜App Shell、主導覽與路由骨架

- **目標**：建立四個主入口與技術路由的檔案骨架，避免日後頁面架構分散。
- **使用者情境**：登入後可從固定導覽前往 Dashboard、Meetings、Memory、Settings；進入會議後保留會議上下文。
- **功能內容**：已完成 App Shell、桌面收合側欄、手機 Drawer 導覽、頁面 title、麵包屑／返回 Meetings、所有規劃 route 的靜態 UI，以及 route-level `loading`、`error`、`not-found` 邊界。
- **頁面／路由**：`/dashboard`、`/meetings/new`、`/meetings/[id]/prepare`、`/meetings/[id]/review`、`/memory`、`/settings`；`/sign-in`、`/meetings/[id]/audio-setup`、`/meetings/[id]/addon`、`/meetings/[id]/live` 只建立技術性或會議上下文殼。
- **元件規劃**：`AppShell`、`MainNav`、`MobileNav`、`PageHeader`、`MeetingWorkspaceHeader`、共用狀態畫面。
- **狀態管理**：目前路徑與暫存 navigation state；不建立全域 store。
- **資料來源**：靜態 route metadata 與展示內容；不在本步假造 API 回應。
- **API 串接**：無。
- **畫面狀態**：404、載入骨架、route error、未登入 placeholder。
- **互動細節**：目前頁面高亮、手機選單可用 Esc 關閉、焦點回復。
- **響應式需求**：桌面側欄或頂欄與手機 drawer／底部導覽二擇一，依設計決定；Add-on route 不套用完整 App Shell。
- **預計異動範圍**：`app/`、`components/layout/`、`components/ui/`。
- **前置條件**：步驟 01。
- **驗證方式**：逐路由直接開啟、鍵盤導覽、桌面／平板／手機 viewport。
- **完成標準**：已完成。所有計畫路由均有可辨識的 UI 殼；主導覽只顯示四個產品入口，Dashboard 固定為 `/dashboard`，Add-on route 不套用完整 App Shell。
- **注意事項**：產品首頁 `/` 日後另行設計；不可在此步假設登入完成。

### 步驟 03｜前端 domain 型別、API Client 與資料狀態

- **目標**：在 UI 開發前建立正式 API Client 與可替換的資料邊界，讓頁面不直接處理 fetch 細節。
- **使用者情境**：開發者可透過正式 API 取得服務狀態並建立 Meeting BaaS Bot；API 尚未提供的產品資料暫不在本步假造。
- **功能內容**：定義目前後端已提供的 `HealthResponse`、`JoinMeetingRequest`、`MeetingBotResponse`、`ApiError`；建立 API Client 與 repository 邊界。
- **頁面／路由**：無特定路由，供全站使用。
- **元件規劃**：無產品元件；可沿用共用 `DataState` 顯示正式 API 的載入、空資料與錯誤狀態。
- **狀態管理**：先以 React state／async function 介面；是否採 Zustand 待批准。
- **資料來源**：正式後端 API；目前僅有 `/health` 與 `/meetbot/join`，不建立 Mock Data。
- **API 串接**：`GET /health`、`POST /meetbot/join`；其他產品 endpoint 等後端提供後再加入 repository。
- **畫面狀態**：loading、成功、空回應、網路錯誤、HTTP 錯誤；尚無正式登入／權限 endpoint，暫不宣稱 unauthorized 已完成。
- **互動細節**：API 錯誤需轉為可讀訊息；API key 僅留在後端，前端不可接觸。
- **響應式需求**：無。
- **預計異動範圍**：`types/`、`lib/data/`、`lib/mocks/`、必要的環境 feature flag 文件。
- **前置條件**：步驟 01。
- **驗證方式**：TypeScript typecheck；以 fixture 驗證不同狀態可被頁面讀取。
- **完成標準**：頁面與元件只透過 repository 取得資料；不 import fixture，也不呼叫尚未存在的 endpoint。
- **注意事項**：資料欄位是前端契約草案，須由後端確認；不得把私訊與公共資料放入同一個型別或 cache key。

### 步驟 04｜登入狀態、角色與前端存取邊界

- **目標**：建立前端可測試的匿名、Member、Host、Admin、Absent Owner 狀態與路由保護外觀。
- **使用者情境**：未登入者看見登入入口；Member 看見自己的 Sidekick；Host 才看見主持控制；Admin 才可開啟 Settings 管理 Tabs。
- **功能內容**：Auth adapter、session loading、`RequireAuth`／`RequireRole` UI 邊界、403／登入導向、角色 fixture。
- **頁面／路由**：`/sign-in`、所有主路由與 `/meetings/[id]/addon`。
- **元件規劃**：`AuthGate`、`RoleGate`、`UnauthorizedState`、`SessionMenu`。
- **狀態管理**：目前使用者、團隊、角色與 session status；正式 Auth SDK 選定後再封裝於 adapter。
- **資料來源**：Neon Auth；目前後端尚未提供登入／session endpoint，因此本步尚未實作。
- **API 串接**：預期 `GET /v1/me` → `{ id, name, avatarUrl, activeTeamId, roles }`；另需 `POST /v1/meetings/:id/access-token` 取得短效 meeting token。正式 token transport、過期時間與 refresh 行為待後端確認。
- **畫面狀態**：checking session、signed out、forbidden、session expired、切換團隊失敗。
- **互動細節**：登入後回到原始目的地；角色不足顯示原因，不只隱藏按鈕。
- **響應式需求**：登入頁、使用者選單與無權限畫面可在手機閱讀。
- **預計異動範圍**：`app/sign-in/`、`components/auth/`、`lib/auth/`、`types/`。
- **前置條件**：步驟 02、03。
- **驗證方式**：切換所有角色 fixture；嘗試直接輸入受限 URL；鍵盤操作登入 UI。
- **完成標準**：前端依角色正確顯示功能，但不宣稱能取代後端授權。
- **注意事項**：正式登入已選 Neon Auth；仍需確認 Neon Auth 的前端 SDK、callback、session refresh 與 Vercel 環境設定後，才能安裝或實作真登入。

### 步驟 05｜Dashboard 與會議清單

- **目標**：提供登入後的單一入口：近期會議、待確認共識、我的行動項目與建立會議。
- **使用者情境**：Member 進入後找到下一場會議；Host 可建立會議；使用者看到自己待回覆的 Consensus。
- **功能內容**：Meeting list、狀態 badge、日期、參與者摘要、待確認卡、行動項目卡、Empty Dashboard。
- **頁面／路由**：`/dashboard`，連往 `/meetings/new`、`/meetings/[id]/prepare`、`/meetings/[id]/review`。
- **元件規劃**：`MeetingCard`、`MeetingList`、`PendingConsensusList`、`ActionItemList`、`EmptyState`。
- **狀態管理**：頁面資料、篩選／排序的區域狀態。
- **資料來源**：正式 API repository；目前僅能取得 `/health`，會議／共識／行動項目在正式 endpoint 提供前顯示空狀態。
- **API 串接**：`GET /health` 顯示服務連線狀態；預期後續加入 `GET /v1/meetings?scope=upcoming`、`GET /v1/consensus?status=awaiting_response`、`GET /v1/action-items?assignee=me`。
- **畫面狀態**：初次 loading、API 已連線、API 失敗、無會議資料、正式 endpoint 尚未提供。
- **互動細節**：建立會議 CTA、卡片導頁、篩選只影響對應區塊、錯誤可重試。
- **響應式需求**：卡片由多欄縮為單欄；重要 CTA 不被折疊。
- **預計異動範圍**：`app/page.tsx` 或 `app/dashboard/`、`features/dashboard/`、`components/meeting/`。
- **前置條件**：步驟 02–04。
- **驗證方式**：近期／無資料／錯誤／不同角色 fixture；連結與鍵盤 Tab 順序。
- **完成標準**：使用者可看到真實 API 連線狀態，並在會議 endpoint 尚未提供時獲得清楚空狀態與建立會議入口。
- **注意事項**：Meetings 是否需要獨立清單頁待確認；此步不實作後端篩選規則。

### 步驟 06｜建立與編輯會議

- **目標**：完成會議建立流程與會前設定表單的 UI、前端驗證及草稿狀態。
- **使用者情境**：任一團隊成員建立會議，選擇標題、時間、議程、參與者、本場 Host、AI 角色與發言政策。
- **功能內容**：多段表單、議程排序、Host 選擇、參與者選擇、AI 角色切換、門檻／介入程度設定、提交預覽。
- **頁面／路由**：`/meetings/new`；未來可共用於 `/meetings/[id]/prepare` 的設定模式。
- **元件規劃**：`MeetingForm`、`AgendaEditor`、`ParticipantPicker`、`HostSelector`、`AgentRoleSelector`、`InterventionPolicyForm`、`FormErrorSummary`。
- **狀態管理**：表單草稿、dirty、提交中、排序中的區域狀態；採何種表單庫待批准。
- **資料來源**：正式團隊／會議 API；目前後端尚未提供，因此本步尚未實作。
- **API 串接**：預期 `POST /v1/meetings`，request 至少含 `{ title, startsAt, agenda[], participantIds[], hostUserId, enabledRoles[], interventionPolicy }`；response 預期 `{ meeting }`。欄位與門檻規則待後端確認。
- **畫面狀態**：載入成員、空團隊、表單驗證錯誤、送出中、建立成功、建立失敗、無權限建立。
- **互動細節**：即時必填提示、離開未儲存提示、成功後導向 Prepare、不可把私人 Delegate 設定誤當公開會議資料。
- **響應式需求**：議程排序需支援非拖拉備援（上移／下移按鈕）；手機不依賴 hover。
- **預計異動範圍**：`app/meetings/new/`、`features/meetings/setup/`、`components/forms/`、`types/`。
- **前置條件**：步驟 03–05。
- **驗證方式**：有效／無效表單、Member／Host fixture、排序、重新整理草稿的預期行為。
- **完成標準**：正式會議 API 可用時，能建立一場會議並進入 Prepare 頁；所有欄位有明確驗證與錯誤訊息。
- **注意事項**：規劃文件未定義會議建立的正式 request schema、時區規則與角色選項完整列舉，需後端／產品確認。

### 步驟 07｜Meeting Workspace：Prepare 與 Personal Sidekick

- **目標**：讓使用者在會前閱讀 Brief、設定本場內容，並與自己的 Personal Sidekick 延續同一條私人對話。
- **使用者情境**：Member 看見待決問題與分歧，輸入自己的想法，得到整理後的公開草稿，但必須手動確認才可提出。
- **功能內容**：Brief、議程、公開歷史限制、私人對話、草稿預覽、明確「提出觀點」確認；Host 可調整本場 AI 政策。
- **頁面／路由**：`/meetings/[id]/prepare`。
- **元件規劃**：`MeetingWorkspaceHeader`、`BriefPanel`、`AgendaPanel`、`SidekickThread`、`ContributionDraft`、`PublishContributionDialog`、`HostPolicyPanel`。
- **狀態管理**：meeting snapshot、personal thread、輸入草稿、公開確認 dialog、Host policy draft。
- **資料來源**：正式 Meeting、Brief 與 Personal Agent API；目前後端尚未提供，因此本步尚未實作。
- **API 串接**：預期 `GET /v1/meetings/:id`、`GET /v1/meetings/:id/brief`、`GET/POST /v1/meetings/:id/personal-agent/messages`、`POST /v1/meetings/:id/public-contributions`。request／response 與 authorization 均待確認。
- **畫面狀態**：meeting loading、找不到會議、未加入會議、Sidekick thinking、空對話、草稿生成失敗、公開失敗。
- **互動細節**：私訊送出後顯示處理中；公開前顯示將被分享的文字與對象；不可由 UI 自動公開。
- **響應式需求**：桌面可雙欄，手機切換 Brief／Sidekick；聊天輸入保持可用。
- **預計異動範圍**：`app/meetings/[id]/prepare/`、`features/meeting-workspace/`、`features/sidekick/`、`components/meeting/`。
- **前置條件**：步驟 03–06。
- **驗證方式**：Member、Host、未參與者 fixture；私人訊息不出現在公共 panel；公開預覽與取消流程。
- **完成標準**：正式 Meeting／Sidekick API 可用時，同一 meeting 的 thread 可以被讀取、發送、整理與經確認公開。
- **注意事項**：真正的私人隔離必須由後端保證；前端只負責正確的資料邊界與安全提示。

### 步驟 08｜Audio Setup／Capture 體驗

- **目標**：建立收音前的明確同意、裝置檢查、狀態提示與回到 Meet 的使用流程；不在本步直接做真實串流。
- **使用者情境**：使用者在會議開始前開啟音訊設定、知道收哪些內容、允許麥克風後回到 Google Meet，且能辨識收音是否中斷。
- **功能內容**：同意說明、裝置／權限狀態、開始／停止偵測、背景分頁警告、故障與 fallback transcript 說明。
- **頁面／路由**：`/meetings/[id]/audio-setup`；由 Prepare CTA 開啟，不列入主導覽。
- **元件規劃**：`AudioConsentCard`、`DeviceStatus`、`CaptureStatus`、`AudioTroubleshooting`、`ReturnToMeetLink`。
- **狀態管理**：權限狀態、選定裝置、capture lifecycle、網路／WebSocket status 的 UI state；真實 MediaStream 實作另列後續。
- **資料來源**：瀏覽器 Permissions API 與正式音訊連線狀態；目前後端尚未提供音訊 WebSocket，因此只規劃，不假造串流資料。
- **API 串接**：無正式串流；後續預期 WebSocket handshake `{ meetingId, participantId, sequence }`，binary audio chunk schema 待後端確認。
- **畫面狀態**：unsupported browser、permission prompt、denied、active、stopped、disconnected、reconnecting、fallback。
- **互動細節**：開始與停止需明確；不可暗中收音。開始後 Capture Page 必須保持開啟並持續收音；若頁面被關閉、分頁休眠或 track／WebSocket 中斷，立即顯示停止狀態並提示重新啟動。
- **響應式需求**：手機需提示 Google Meet／瀏覽器限制；核心操作不依賴兩欄布局。
- **預計異動範圍**：`app/meetings/[id]/audio-setup/`、`features/audio-capture/`。
- **前置條件**：步驟 03、07。
- **驗證方式**：瀏覽器 permission、不同瀏覽器 user-agent 提示、開始／停止／斷線 UI。
- **完成標準**：使用者能理解同意範圍、目前狀態與返回 Meet 的下一步；尚未宣稱已收音。
- **注意事項**：`getUserMedia`、VAD、MediaRecorder 與 Audio WebSocket 需在後端 WebSocket 契約與真人同意完成後，另開獨立實作步驟；背景分頁持續收音能力仍需 Chrome／作業系統實測。

### 步驟 09｜Google Meet Add-on：窄版 Live Shell

- **目標**：建立可在一般瀏覽器開發與 Google Meet iframe 使用的窄版會中 UI 結構，不設定或發布 Add-on。
- **使用者情境**：與會者在 Google Meet 右側看到本場 Brief、Live State、Personal Sidekick；Host 額外看見控制區。
- **功能內容**：Add-on 專用 layout、三個 Tab、meeting context loading、iframe 空間限制、private／public 視覺分隔。
- **頁面／路由**：`/meetings/[id]/addon`。
- **元件規劃**：`AddonShell`、`AddonTabs`、`BriefTab`、`LiveStateTab`、`SidekickTab`、`HostControlsTab`、`AddonConnectionStatus`。
- **狀態管理**：active tab、meeting snapshot、使用者角色、Add-on connection UI state。
- **資料來源**：正式 Live Snapshot／Realtime API；目前後端尚未提供，因此只建立規格，不假造會議狀態。
- **API 串接**：先以 `GET /v1/meetings/:id/live-snapshot` 取得公共狀態；Add-on 啟動前使用 `POST /v1/meetings/:id/access-token` 取得短效 token，再建立 WebSocket 或 fallback polling。Google Meet context／manifest 欄位待確認，但不在 iframe 內重新登入。
- **畫面狀態**：iframe 初始 loading、窄版 overflow、未登入、未加入會議、Host controls 隱藏、Add-on 不支援／context 缺失。
- **互動細節**：Tab 支援鍵盤方向鍵或標準 Tab 行為；私人內容要明顯標示「僅你可見」。
- **響應式需求**：以約 280px 寬度優先；不假設可用完整桌面寬度；一般 Web fallback 可擴寬。
- **預計異動範圍**：`app/meetings/[id]/addon/` 或最終確認的 `app/addon/meetings/[id]/`、`features/addon/`、`components/meeting-addon/`。
- **前置條件**：步驟 02–04、07。
- **驗證方式**：以 280px、360px、768px 寬度測試；Member／Host fixture；鍵盤 Tabs；iframe 模擬。
- **完成標準**：不依賴 Meet SDK 也能展示完整窄版會中資訊結構，且不顯示完整 App Shell。
- **注意事項**：Add-on route 固定為 `/meetings/[id]/addon`；不要把 Neon Auth 長效 session 或任何 API key 放入 iframe URL。短效 token 只能用於單一 meeting，且需處理過期、重播與權限錯誤。

### 步驟 10｜Live State、AI 舉手、投票與 Host Controls

- **目標**：在 Add-on 內完成公共會議狀態與受控 AI 介入的互動閉環。
- **使用者情境**：Main Agent 發現風險後顯示「Proximate 想發言」卡；Member 投票支持／稍後／忽略；Host 調整政策、否決或暫停。
- **功能內容**：目前議題、立場、未決問題、暫定決策、Parking Lot、AI suggestion card、票數／門檻、Host policy controls、Voice Bot status。
- **頁面／路由**：`/meetings/[id]/addon` 的 Live State 與 Host Controls tabs。
- **元件規劃**：`MeetingStatePanel`、`AiSuggestionCard`、`VoteControl`、`ThresholdProgress`、`HostPolicyControls`、`ParkingLot`、`VoiceBotStatus`。
- **狀態管理**：meeting snapshot、每張 suggestion 的投票狀態、pending action、Host policy；先以 reducer 或 feature-local state，是否升級 Zustand 待批准。
- **資料來源**：正式 Realtime 與投票 API；目前後端尚未提供，因此本步尚未實作。
- **API 串接**：預期 `POST /v1/meetings/:id/ai-suggestions/:suggestionId/vote` request `{ choice: "support" | "later" | "ignore" }`；Member 可再次呼叫以修改投票；Host 預期 `PATCH /v1/meetings/:id/intervention-policy`；response schema、門檻演算來源待確認。
- **畫面狀態**：無目前議題、無 AI 建議、投票送出中、投票失敗、達門檻、Host 暫停、Voice Bot failed、資料過期。
- **互動細節**：每位使用者每張卡保留一個目前選擇，可在「支持／稍後／忽略」間重新投票；Host 操作應有確認與 audit-friendly feedback；Bot 未成功播放不可顯示為已發言。
- **響應式需求**：卡片單欄、票數文字不可只用顏色、Host controls 在窄版可垂直捲動。
- **預計異動範圍**：`features/live-state/`、`features/intervention/`、`components/meeting-addon/`、Realtime adapter。
- **前置條件**：步驟 03、04、09。
- **驗證方式**：Member／Host fixture、所有票數／門檻情境、錯誤重試、鍵盤投票與屏讀文字。
- **完成標準**：正式 suggestion／vote API 可用時，能完成「AI 建議 → 投票 → 達標／未達標 → 狀態回饋」全流程。
- **注意事項**：Voice Bot 發言與 Meeting BaaS 是後端責任；前端只呈現核准、播放中、完成、失敗事件。

### 步驟 11｜Meeting Workspace：Review 與 Consensus 確認

- **目標**：將摘要、逐字稿、決策、行動項目與逐人確認集中於同一個會後頁面。
- **使用者情境**：會後 Member 閱讀結果並選擇同意、修正或理解不同；未回覆者必須顯示待確認。
- **功能內容**：Review Tabs（Summary、Transcript、Decisions、Actions、Confirmations）、Consensus 狀態、版本比較／歷史入口、修正表單。
- **頁面／路由**：`/meetings/[id]/review`。
- **元件規劃**：`ReviewTabs`、`DecisionCard`、`ActionItemList`、`TranscriptTimeline`、`ConfirmationPanel`、`ConsensusStatusBadge`、`CorrectionForm`。
- **狀態管理**：review snapshot、active tab、confirmation mutation、修正草稿、版本選擇。
- **資料來源**：正式 Review／Consensus API；目前後端尚未提供，因此本步尚未實作。
- **API 串接**：預期 `GET /v1/meetings/:id/review`、`POST /v1/meetings/:id/consensus/:versionId/responses` request `{ status: "agree" | "correction" | "different_understanding", comment? }`；實際版本規則待確認。
- **畫面狀態**：generating、draft、awaiting responses、conflicted、confirmed、無逐字稿、沒有任務、無權限。
- **互動細節**：`confirmed` 不可在有人未回覆時顯示；修正必須保留原版本；行動項目缺 owner／deadline 顯示 incomplete。
- **響應式需求**：長逐字稿可搜尋／捲動；Tabs 在手機可水平捲動或改 selector。
- **預計異動範圍**：`app/meetings/[id]/review/`、`features/review/`、`components/consensus/`。
- **前置條件**：步驟 03、04、06、10。
- **驗證方式**：四種 consensus 狀態、不同回覆、空逐字稿、版本歷史、角色權限 fixture。
- **完成標準**：使用者可理解本場決策、誰尚未確認、下一步負責人與期限。
- **注意事項**：後端如何計算 required participants、逾時封存與版本建立規則尚待確認。

### 步驟 12｜正式 REST／WebSocket adapter 切換

- **目標**：在後端提供並確認契約後，將各 feature 逐項接上正式 REST 與即時事件，而不重寫 UI。
- **使用者情境**：多位使用者在不同 Add-on 實例看到一致的會議狀態；重連後可回到最新 snapshot。
- **功能內容**：API client、request／response validation、error normalization、WebSocket connect／reconnect、`event_id` 去重、snapshot refresh、feature flag 切換。
- **頁面／路由**：Prepare、Audio Setup、Add-on、Review 及 Dashboard。
- **元件規劃**：`ApiErrorState`、`ConnectionStatus`、必要 provider／hook；不得讓元件自己管理 socket 細節。
- **狀態管理**：server snapshot、event cursor、optimistic mutation；選用狀態庫前需明確批准。
- **資料來源**：正式 API；不建立產品 Mock Data，測試改用 API contract test 或明確的錯誤／空資料回應。
- **API 串接**：除各步列出的 REST 外，預期 WebSocket event `{ event_id, meeting_id, timestamp, schema_version, payload }`，至少處理 `transcript:new`、`meeting_state:update`、`ai_suggestion:new`、`ai_suggestion:updated`、`consensus:update`、`participant:update`、`agent:status`、`error`。
- **畫面狀態**：connecting、connected、reconnecting、stale snapshot、server error、schema mismatch、token expired。
- **互動細節**：網路不佳時不可悄悄遺失投票；重試須避免重複提交。
- **響應式需求**：無額外要求，但窄版需看得到連線狀態。
- **預計異動範圍**：`lib/api/`、`lib/realtime/`、`features/*/data.ts`、`types/api.ts`。
- **前置條件**：步驟 03、05–11，以及後端提供契約與測試環境。
- **驗證方式**：正式 API contract、斷線重連、事件重播、兩個瀏覽器視窗同步。
- **完成標準**：UI 元件不需因 API 接入而大幅重寫；連線／錯誤有可理解回饋。
- **注意事項**：目前後端只存在 `/health`，本步不能開始，直到後端人員提供 endpoint、認證與 WebSocket 契約。

### 步驟 13｜響應式、無障礙與前端驗收

- **目標**：在核心流程完成後，集中修正響應式、鍵盤操作、狀態可見性與 build 品質。
- **使用者情境**：桌面使用者可操作完整工作區；Meet Add-on 使用者在窄版仍能完成投票與 Sidekick 操作；鍵盤與輔助科技使用者可理解所有狀態。
- **功能內容**：breakpoints、focus management、Dialog focus trap、ARIA label／live region、色彩對比、reduced motion、空／錯誤狀態覆蓋率、效能檢查。
- **頁面／路由**：全部核心路由，優先 `/meetings/[id]/addon`、`/prepare`、`/review`。
- **元件規劃**：調整既有元件；補足 `VisuallyHidden`、`StatusAnnouncer` 等必要 primitive（若無既有替代）。
- **狀態管理**：無新的產品狀態。
- **資料來源**：正式 API contract 與錯誤／空資料回應。
- **API 串接**：無新增 endpoint。
- **畫面狀態**：逐頁檢查 loading、success、empty、error、unauthorized、offline／reconnecting。
- **互動細節**：所有操作可鍵盤完成；錯誤訊息被朗讀；不可只用紅綠色表達投票或確認。
- **響應式需求**：桌面、平板、手機及 Add-on 約 280px 窄版；以真實文字長度測試。
- **預計異動範圍**：既有前端元件、全域樣式、測試設定（若使用者批准）。
- **前置條件**：步驟 05–12 中已完成的功能。
- **驗證方式**：`npm run lint`、`npm run typecheck`、`npm run build`、鍵盤 walkthrough、不同 viewport 手動驗收。
- **完成標準**：核心情境沒有阻塞性 layout、鍵盤或狀態回饋問題。
- **注意事項**：目前沒有前端測試框架；若需要新增 Vitest／Playwright／a11y 工具，必須另行取得套件安裝批准。

## 可選優化

### 步驟 14｜Team Memory 搜尋與 Decision Detail

- **目標**：讓使用者搜尋已確認的歷史決策與來源。
- **使用者情境**：Member 搜尋過去方案限制，從結果打開決策理由與來源會議。
- **功能內容**：搜尋欄、篩選、結果列表、Decision Detail drawer／dialog、來源連結。
- **頁面／路由**：`/memory`；Detail 預設使用 drawer，不另增路由。
- **元件規劃**：`MemorySearch`、`DecisionResultCard`、`DecisionDetailDrawer`、`SourceCitation`。
- **狀態管理**：query、filters、selected decision。
- **資料來源**：正式 RAG API；尚未提供前不實作。
- **API 串接**：預期 `GET /v1/memory/search?q=&type=&teamId=`；response 需包含 ACL 過濾後結果與 citations，待確認。
- **畫面狀態**：空 query、搜尋中、無結果、錯誤、無權限來源。
- **互動細節**：搜尋結果不可露出無權限文件標題或內容。
- **響應式需求**：Detail 在手機改為全螢幕 sheet。
- **預計異動範圍**：`app/memory/`、`features/memory/`。
- **前置條件**：步驟 03、04、11；正式版另需 RAG API。
- **驗證方式**：多權限 fixture、無結果、來源連結。
- **完成標準**：使用者只能看見自己有權查看的決策與來源。
- **注意事項**：ACL 必須由後端保證。

### 步驟 15｜Settings 與整合狀態

- **目標**：用單一 Settings 頁的 Tabs 呈現 Team、Integrations、Privacy，不拆成多個路由。
- **使用者情境**：Admin 檢視成員、外部服務連線狀態與資料保存規則。
- **功能內容**：三個 Tabs、read-only integration status、privacy 說明、Admin gate。
- **頁面／路由**：`/settings`。
- **元件規劃**：`SettingsTabs`、`TeamSettingsPanel`、`IntegrationStatusCard`、`PrivacyPanel`。
- **狀態管理**：active tab、settings snapshot。
- **資料來源**：正式設定 API；尚未提供前不實作。
- **API 串接**：預期 `GET/PATCH /v1/settings/team`、`GET /v1/integrations`、`GET/PATCH /v1/settings/privacy`，皆待確認。
- **畫面狀態**：Member forbidden、未連線、connecting、設定儲存中、失敗。
- **互動細節**：API key 不在前端輸入或顯示；若未來需要 OAuth，前端只啟動後端授權流程。
- **響應式需求**：Tabs 在手機可捲動或改 dropdown。
- **預計異動範圍**：`app/settings/`、`features/settings/`。
- **前置條件**：步驟 03、04。
- **驗證方式**：Admin／Member fixture、所有 integration status。
- **完成標準**：設定 UI 不洩漏秘密，且角色顯示正確。
- **注意事項**：資料保留、成員管理與外部整合的後端規則未定，不自行決定。

### 步驟 16｜外部服務前端設定文件與部署前檢查

- **目標**：在真正串接前，為每個前端相關外部服務建立獨立設定文件與回退方案。
- **使用者情境**：新前端成員可依文件設定本機與 staging，不會把秘密放進 bundle。
- **功能內容**：文件而非功能實作；設定來源、公開／私密環境變數、callback URL、測試方式、失敗回退、刪除／撤銷流程。
- **頁面／路由**：無。
- **元件規劃**：無。
- **狀態管理**：無。
- **資料來源**：官方文件與團隊確認後的設定值。
- **API 串接**：無。
- **畫面狀態**：無。
- **互動細節**：無。
- **響應式需求**：無。
- **預計異動範圍**：預計新增 `frontend/docs/integrations/` 下的獨立文件；本步前不得建立或填入真實 secret。
- **前置條件**：外部服務、帳號擁有者與部署網址已確認。
- **驗證方式**：每份文件可由另一位成員在無 secret 外洩下完成設定。
- **完成標準**：至少各有一份 Google Meet Add-on、登入服務、Meeting BaaS 前端回呼／狀態、Vercel 前端部署文件；若服務未採用則標示不適用。
- **注意事項**：OpenAI、ElevenLabs、Groq、Neon 與 Meeting BaaS 的機密 key 都屬後端，不得建立前端 key 設定流程；Meet Add-on 的 OAuth／manifest 細節需 Google Cloud 專案擁有者確認。

## 需要後端提供的 API 與契約

目前只有 `GET /health` 可用。以下皆是前端所需的**待確認**契約，不代表既有 API：

| 功能 | 預期 endpoint | 前端最低 response／事件需求 |
| --- | --- | --- |
| 身分與角色 | `GET /v1/me` | `user`、active team、role、session 狀態 |
| Meeting access token | `POST /v1/meetings/:id/access-token` | 短效 token、`expiresAt`、meeting／user scope；供 Add-on 與 `/live` 建立連線 |
| Dashboard | `GET /v1/meetings`、`/v1/consensus`、`/v1/action-items` | 清單、狀態、權限與 pagination |
| 建立會議 | `POST /v1/meetings` | meeting、agenda、participants、host、policy |
| Meeting BaaS Bot | `POST /meetbot/join` | request `{ meeting_url }`；目前回傳 Meeting BaaS 原始 response，Bot lifecycle／status 尚未封裝 |
| Prepare | `GET /v1/meetings/:id`、`/brief` | meeting snapshot、Brief、可讀資料範圍 |
| Personal Sidekick | `GET/POST /v1/meetings/:id/personal-agent/messages` | 私人 thread、message、draft、error；依 user 隔離 |
| 公開觀點 | `POST /v1/meetings/:id/public-contributions` | 送出後的 public contribution；不可回傳私人原文給其他人 |
| Live Snapshot | `GET /v1/meetings/:id/live-snapshot` | meeting state、participants、suggestions、policy |
| 投票／主持控制 | vote endpoint、intervention policy endpoint | 建議卡、本人投票、統計、門檻、Host 狀態 |
| Review／共識 | review endpoint、consensus response endpoint | decisions、actions、transcript、versions、required／pending members |
| Realtime | WebSocket 或等效 | event envelope、認證、重連 cursor、snapshot、錯誤碼 |
| Memory | search endpoint | ACL 過濾後結果、來源 citations |

### 後端現況對前端的直接影響

- `backend/app/main.py` 尚未加入 CORS middleware；前端從 `localhost:3000` 呼叫後端前，需先確認跨來源請求策略。
- `backend/app/config.py` 的 `cors_origins` 目前只是設定欄位，尚未實際套用；前端不可假設正式環境已能跨來源呼叫。
- `/meetbot/join` 直接轉發 Meeting BaaS response，沒有穩定的前端 response schema；前端型別因此保留可擴充欄位，正式 UI 不應依賴未知欄位。
- 後端尚未提供 `/v1/me`、Meeting CRUD、Access Token、Live Snapshot、投票、Review 或 WebSocket；對應前端步驟維持未完成。

## 待確認問題與衝突

1. Meeting 建立 request 的完整欄位、時區、議程排序與 Host 轉交規則為何？
2. Member 重投票時，誰計算在線人數與支持比例；門檻是否依即時在線成員變動？
3. Audio Setup 持續收音的 MVP 瀏覽器／裝置支援範圍，以及背景分頁休眠時的產品行為為何？
4. Google Meet Add-on 的 context、manifest、development deployment、同網域測試帳號，以及短效 meeting token 的簽發與撤銷責任由誰設定？
5. Meeting BaaS 是否支援目前所需的 Google Meet speaking／自訂音訊輸入，以及狀態 webhook？
6. Review 的 required participants、逾時、conflicted、confirmed 與版本建立規則為何？
7. Vercel 上 FastAPI WebSocket 的長連線、timeout、重連與必要替代部署方案為何？

## 主要風險

- 目前後端僅有健康檢查與 Meeting BaaS join API；其他前端產品功能必須等待正式契約，不以假資料冒充完成。
- 私人 Sidekick 的安全不能只靠前端：必須等待後端 user／team／meeting ACL。
- Meet Add-on 與 Audio Capture 是兩種不同瀏覽器情境；Add-on iframe 不應自行假設可取得麥克風。
- Meeting BaaS、Google Meet、STT 與 TTS 整合皆可能受帳號、額度、部署 URL 與平台政策影響；核心 Demo 必須保留文字卡回退。
- 規劃文件列出 shadcn/ui、Zustand、Axios 等套件，但現有 `package.json` 未安裝；在未批准前只能使用現有 React、Next.js、Tailwind 能力。

## 建議從哪一步開始

建議先執行 **步驟 01｜前端基礎與設計語言**。它不依賴後端或外部帳號，且會為後續所有頁面建立一致的可用性與樣式基礎。

完成本文件後停止，等待使用者指定下一個步驟。
