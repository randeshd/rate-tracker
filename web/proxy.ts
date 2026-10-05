import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { AUTH_COOKIE, safeEqual, sessionToken } from "./lib/auth";

// Simple password gate: every page except /login needs a valid session cookie.
export async function proxy(request: NextRequest) {
  const password = process.env.SITE_PASSWORD;
  const cookie = request.cookies.get(AUTH_COOKIE)?.value ?? "";
  if (password && safeEqual(cookie, await sessionToken(password))) {
    return NextResponse.next();
  }
  return NextResponse.redirect(new URL("/login", request.url));
}

export const config = {
  matcher: ["/((?!login|_next/static|_next/image|favicon.ico).*)"],
};
