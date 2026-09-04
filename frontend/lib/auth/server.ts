import { createNeonAuth } from "@neondatabase/auth/next/server";

export const auth = createNeonAuth({
  baseUrl: process.env.NEON_AUTH_BASE_URL ?? "",
  cookies: {
    secret: process.env.NEON_AUTH_COOKIE_SECRET ?? "development-only-neon-auth-cookie-secret-32",
    sessionDataTtl: 300,
  },
});
