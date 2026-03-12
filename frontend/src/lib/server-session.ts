import { NextResponse } from "next/server";
import { AUTH_HINT_COOKIE_NAME, SESSION_COOKIE_MAX_AGE, SESSION_COOKIE_NAME } from "@/lib/session-cookies";

function secureCookie() {
  return process.env.NODE_ENV === "production";
}

export function applySessionCookies(response: NextResponse, token: string) {
  response.cookies.set({
    name: SESSION_COOKIE_NAME,
    value: token,
    httpOnly: true,
    sameSite: "lax",
    secure: secureCookie(),
    path: "/",
    maxAge: SESSION_COOKIE_MAX_AGE,
  });
  response.cookies.set({
    name: AUTH_HINT_COOKIE_NAME,
    value: "1",
    httpOnly: false,
    sameSite: "lax",
    secure: secureCookie(),
    path: "/",
    maxAge: SESSION_COOKIE_MAX_AGE,
  });
}

export function clearSessionCookies(response: NextResponse) {
  response.cookies.set({
    name: SESSION_COOKIE_NAME,
    value: "",
    httpOnly: true,
    sameSite: "lax",
    secure: secureCookie(),
    path: "/",
    maxAge: 0,
  });
  response.cookies.set({
    name: AUTH_HINT_COOKIE_NAME,
    value: "",
    httpOnly: false,
    sameSite: "lax",
    secure: secureCookie(),
    path: "/",
    maxAge: 0,
  });
}
