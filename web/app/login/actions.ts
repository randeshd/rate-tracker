"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AUTH_COOKIE, safeEqual, sessionToken } from "@/lib/auth";

export async function login(_previous: string, formData: FormData): Promise<string> {
  const expected = process.env.SITE_PASSWORD;
  if (!expected) return "No password is configured for this site yet.";
  const given = String(formData.get("password") ?? "");
  const [a, b] = await Promise.all([sessionToken(given), sessionToken(expected)]);
  if (!safeEqual(a, b)) {
    await new Promise((resolve) => setTimeout(resolve, 800)); // slow down guessing
    return "Incorrect password.";
  }
  (await cookies()).set(AUTH_COOKIE, b, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 30,
    path: "/",
  });
  redirect("/");
}
