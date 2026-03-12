import { NextResponse } from "next/server";
import { clearSessionCookies } from "@/lib/server-session";

export const dynamic = "force-dynamic";

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.headers.set("Cache-Control", "no-store");
  clearSessionCookies(response);
  return response;
}
