# Neon PostgreSQL 設定流程

適用步驟：後端步驟 2、3、12。

1. 在 Neon Console 建立 development project，不要使用 production project 做本機測試。
2. 建立 development branch，記錄 project、branch 與 region。
3. 啟用 PostgreSQL extension 的可行性，確認 pgvector 是否由目前方案支援。
4. 從 Connect 取得 pooled PostgreSQL connection string，僅保存到 `backend/.env`。
5. 設定：

   ```env
   DATABASE_URL=postgresql+asyncpg://...
   ```

6. 後續由 Alembic 執行 migration；不要在應用程式啟動時自動 `create_all`。
7. 建立獨立 test branch 或 test database，測試 migration 與 rollback 邊界。
8. 確認資料保留、branch 休眠、連線上限與計費。

安全要求：connection string 不可進前端、log、Git、Issue 或截圖。刪除資料或 reset branch 前必須人工確認。
