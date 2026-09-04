import { createNeonAuth } from "@neondatabase/auth/next/server";

export const auth = createNeonAuth({
  // This must be the Neon Auth project URL, never the Next.js app URL.
  // Leaving it empty would otherwise produce confusing 404s from the local app.
  baseUrl: process.env.NEON_AUTH_BASE_URL || "https://configure-neon-auth-url.invalid",
  cookies: {
    secret: process.env.NEON_AUTH_COOKIE_SECRET || "development-only-neon-auth-cookie-secret-32",
    sessionDataTtl: 300,
  },
});
