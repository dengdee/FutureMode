import { NextResponse, type NextRequest } from "next/server";
import { auth } from "./lib/auth/server";

const protectedPath = /^\/(dashboard|teams|workspaces|memory|settings|meetings)(\/|$)/;

export default async function proxy(request: NextRequest) {
  if (!protectedPath.test(request.nextUrl.pathname)) return NextResponse.next();
  if (!process.env.NEON_AUTH_BASE_URL) return NextResponse.next();
  return auth.middleware({ loginUrl: "/sign-in" })(request);
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico|api/auth).*)"] };
