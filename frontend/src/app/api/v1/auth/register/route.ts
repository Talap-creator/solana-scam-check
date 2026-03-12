import { NextRequest, NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/lib/api-base";
import { applySessionCookies, clearSessionCookies } from "@/lib/server-session";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  const body = await request.text();
  const forwardedFor = request.headers.get("x-forwarded-for");
  const userAgent = request.headers.get("user-agent");
  const headers = new Headers({
    "Content-Type": request.headers.get("content-type") ?? "application/json",
    Accept: "application/json",
  });
  if (forwardedFor) {
    headers.set("x-forwarded-for", forwardedFor);
  }
  if (userAgent) {
    headers.set("user-agent", userAgent);
  }
  const upstreamResponse = await fetch(new URL("/api/v1/auth/register", getServerApiBaseUrl()), {
    method: "POST",
    cache: "no-store",
    headers,
    body,
  });

  const payload = await upstreamResponse.text();
  const contentType = upstreamResponse.headers.get("content-type") ?? "application/json";

  if (!upstreamResponse.ok) {
    const errorResponse = new NextResponse(payload, { status: upstreamResponse.status });
    errorResponse.headers.set("content-type", contentType);
    errorResponse.headers.set("Cache-Control", "no-store");
    clearSessionCookies(errorResponse);
    return errorResponse;
  }

  const session = JSON.parse(payload) as { access_token?: string; token_type?: string };
  if (!session.access_token) {
    return NextResponse.json({ detail: "Upstream auth response did not include a session token." }, { status: 502 });
  }

  const response = NextResponse.json({ access_token: "session", token_type: "bearer" }, { status: 201 });
  response.headers.set("Cache-Control", "no-store");
  applySessionCookies(response, session.access_token);
  return response;
}
