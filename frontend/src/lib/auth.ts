import { AUTH_HINT_COOKIE_NAME } from "@/lib/session-cookies";

function readCookie(name: string): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const cookieValue = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(`${name}=`))
    ?.split("=")
    .slice(1)
    .join("=");

  return cookieValue ? decodeURIComponent(cookieValue) : null;
}

function writeHintCookie(value: string): void {
  if (typeof window === "undefined") {
    return;
  }

  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${AUTH_HINT_COOKIE_NAME}=${encodeURIComponent(value)}; Path=/; Max-Age=604800; SameSite=Lax${secure}`;
}

function clearHintCookie(): void {
  if (typeof window === "undefined") {
    return;
  }

  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${AUTH_HINT_COOKIE_NAME}=; Path=/; Max-Age=0; SameSite=Lax${secure}`;
}

export function getAccessToken(): string | null {
  return readCookie(AUTH_HINT_COOKIE_NAME);
}

export function setAccessToken(token: string): void {
  void token;
  writeHintCookie("1");
}

export function clearAccessToken(): void {
  clearHintCookie();
}

export function isAuthenticated(): boolean {
  return Boolean(getAccessToken());
}
