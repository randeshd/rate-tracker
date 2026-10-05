export const AUTH_COOKIE = "it_session";

/** Cookie value for a given password: a hash, so the password itself is never stored in the browser. */
export async function sessionToken(password: string): Promise<string> {
  const bytes = new TextEncoder().encode(`investment-tracker:${password}`);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, "0")).join("");
}

export function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}
