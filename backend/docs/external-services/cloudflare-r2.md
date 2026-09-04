# Cloudflare R2 設定流程

## 1. 建立 Bucket

1. 登入 Cloudflare Dashboard。
2. 開啟 **R2 Object Storage**，建立 development bucket。
3. 記下 bucket 名稱與 Cloudflare Account ID。

## 2. 建立 API Token

1. 在 R2 頁面開啟 **Manage R2 API Tokens**。
2. 建立 token，權限選擇該 bucket 的 **Object Read** 與 **Object Write**。
3. 只在建立時保存 Access Key ID 與 Secret Access Key；Secret 遺失時需重新建立 token。

## 3. 設定 backend/.env

```dotenv
R2_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=<ACCESS_KEY_ID>
R2_SECRET_ACCESS_KEY=<SECRET_ACCESS_KEY>
R2_BUCKET_NAME=<BUCKET_NAME>
R2_PRESIGNED_EXPIRY_SECONDS=600
```

金鑰只能放在 `backend/.env` 或部署平台 Secret，不得提交 Git。upload API 會將原始檔案存到 R2，download URL API 只回傳短效預簽名 URL。
