# Neon Auth 前端設定

## 目前狀態

產品正式登入選 Neon Auth；目前前端只有 `/sign-in` UI，尚未安裝或接入 Neon Auth SDK。

## 手動設定清單（待確認）

1. 由專案管理者建立 Neon Auth 專案與登入方式。
2. 確認前端使用的 SDK、登入 callback、session refresh 與 sign-out API。
3. 在本機與 Vercel 設定必要的公開 application URL；secret 由後端／平台管理，不放前端 bundle。
4. 設定允許的本機與正式 callback URL。
5. 登入後以後端 `GET /api/v1/me` 驗證 active team 與角色。

在 SDK、callback 與 token transport 確認前，不要自行建立 Auth provider 或假造登入成功狀態。
