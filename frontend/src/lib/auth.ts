const ACCESS_TOKEN_KEY = "rugsignal_access_token";

function readAccessTokenCookie(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const cookieValue = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(`${ACCESS_TOKEN_KEY}=`))
    ?.split("=")
    .slice(1)
    .join("=");

  return cookieValue ? decodeURIComponent(cookieValue) : null;
}

function writeAccessTokenCookie(token: string): void {
  if (typeof window === "undefined") {
    return;
  }

  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${ACCESS_TOKEN_KEY}=${encodeURIComponent(token)}; Path=/; Max-Age=2592000; SameSite=Lax${secure}`;
}

function clearAccessTokenCookie(): void {
  if (typeof window === "undefined") {
    return;
  }

  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${ACCESS_TOKEN_KEY}=; Path=/; Max-Age=0; SameSite=Lax${secure}`;
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const localStorageToken = window.localStorage.getItem(ACCESS_TOKEN_KEY);
  if (localStorageToken) {
    return localStorageToken;
  }

  const cookieToken = readAccessTokenCookie();
  if (cookieToken) {
    window.localStorage.setItem(ACCESS_TOKEN_KEY, cookieToken);
    return cookieToken;
  }

  return null;
}

export function setAccessToken(token: string): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
  writeAccessTokenCookie(token);
}

export function clearAccessToken(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  clearAccessTokenCookie();
}

export function isAuthenticated(): boolean {
  return Boolean(getAccessToken());
}
