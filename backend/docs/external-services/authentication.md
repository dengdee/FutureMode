# 認證方案設定流程

目前規劃在 Clerk 與 Neon Auth 間尚未裁決；不要同時建立兩套正式認證。

## 裁決前

1. 確認 user、team、role、session 的 source of truth。
2. 確認後端是否驗證 JWT issuer、audience、JWKS，以及 token expiration。
3. 確認開發、staging、production 是否分開 project／application。
4. 確認測試帳號、OAuth redirect URL、登出與帳號刪除流程。

## 選定 provider 後

1. 建立 development application。
2. 設定允許的 redirect／origin，只加入本機與 staging URL。
3. 建立至少一個 host、member 測試帳號。
4. 取得後端需要的 issuer、audience、JWKS／domain 設定；client secret 只放 `backend/.env`。
5. 實作後先測試過期 token、錯誤 token、跨 team 存取與角色邊界。

在方案裁決前，不得開始正式 `/me`、team 或 RBAC API。
