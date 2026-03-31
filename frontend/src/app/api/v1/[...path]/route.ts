import { NextRequest, NextResponse } from "next/server";
import { getServerApiBaseUrl } from "@/lib/api-base";
import { SESSION_COOKIE_NAME } from "@/lib/session-cookies";
import { clearSessionCookies } from "@/lib/server-session";

export const dynamic = "force-dynamic";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

const FORWARDED_RESPONSE_HEADERS = ["content-type", "retry-after"] as const;

async function proxyApiRequest(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const upstreamUrl = new URL(`/api/v1/${path.join("/")}`, getServerApiBaseUrl());
  upstreamUrl.search = request.nextUrl.search;

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const accept = request.headers.get("accept");
  const forwardedFor = request.headers.get("x-forwarded-for");
  const userAgent = request.headers.get("user-agent");

  if (contentType) {
    headers.set("content-type", contentType);
  }
  if (accept) {
    headers.set("accept", accept);
  }
  if (forwardedFor) {
    headers.set("x-forwarded-for", forwardedFor);
  }
  if (userAgent) {
    headers.set("user-agent", userAgent);
  }

  const sessionToken = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  if (sessionToken) {
    headers.set("authorization", `Bearer ${sessionToken}`);
  }

  const init: RequestInit = {
    method: request.method,
    headers,
    cache: "no-store",
  };

  if (!["GET", "HEAD"].includes(request.method)) {
    const body = await request.text();
    if (body) {
      init.body = body;
    }
  }

  const upstreamResponse = await fetch(upstreamUrl.toString(), init);

  // SSE: stream through without buffering
  const isSSE = upstreamResponse.headers.get("content-type")?.includes("text/event-stream");
  if (isSSE && upstreamResponse.body) {
    const response = new NextResponse(upstreamResponse.body as ReadableStream, {
      status: upstreamResponse.status,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-store",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
      },
    });
    return response;
  }

  const payload = await upstreamResponse.text();
  const response = new NextResponse(payload, { status: upstreamResponse.status });

  for (const headerName of FORWARDED_RESPONSE_HEADERS) {
    const headerValue = upstreamResponse.headers.get(headerName);
    if (headerValue) {
      response.headers.set(headerName, headerValue);
    }
  }
  response.headers.set("Cache-Control", "no-store");

  if (upstreamResponse.status === 401) {
    clearSessionCookies(response);
  }

  return response;
}

export async function GET(request: NextRequest, context: RouteContext) {
  return proxyApiRequest(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxyApiRequest(request, context);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  return proxyApiRequest(request, context);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  return proxyApiRequest(request, context);
}

export async function OPTIONS(request: NextRequest, context: RouteContext) {
  return proxyApiRequest(request, context);
}
