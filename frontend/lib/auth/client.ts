"use client";

// Client Components must use the browser-safe Next.js auth entrypoint.
// The installed @neondatabase/auth 0.5 beta exposes this as `next`;
// `next/server` is intentionally kept in lib/auth/server.ts only.
import { createAuthClient } from "@neondatabase/auth/next";

export const authClient = createAuthClient();

/** Convert provider/network errors into actionable UI copy without leaking gateway details. */
export function toAuthErrorMessage(error: unknown, action: "登入" | "註冊") {
  const message = error instanceof Error ? error.message : typeof error === "object" && error && "message" in error ? String(error.message) : "";
  if (/\b(502|503|504)\b|bad gateway|gateway timeout|failed to fetch|network/i.test(message)) {
    return `${action}服務暫時無法連線，請稍後再試；若持續發生，請確認 Neon Auth 設定。`;
  }
  if (/\b404\b|not found/i.test(message)) return "登入服務尚未完成設定，請聯絡管理員確認 Neon Auth URL。";
  if (/invalid|incorrect|credential|password|email/i.test(message)) return action === "登入" ? "Email 或密碼不正確，請重新確認。" : "Email 或註冊資料格式不正確，請重新確認。";
  return `${action}失敗，請稍後再試。`;
}
