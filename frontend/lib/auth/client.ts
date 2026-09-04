"use client";

// Client Components must use the browser-safe Next.js auth entrypoint.
// The installed @neondatabase/auth 0.5 beta exposes this as `next`;
// `next/server` is intentionally kept in lib/auth/server.ts only.
import { createAuthClient } from "@neondatabase/auth/next";

export const authClient = createAuthClient();
