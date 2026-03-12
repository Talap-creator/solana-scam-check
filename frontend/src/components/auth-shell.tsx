"use client";

import Link from "next/link";
import { ReactNode } from "react";

type AuthShellProps = {
  children: ReactNode;
  footerMode: "login" | "register";
  heading: string;
  intro?: ReactNode;
  navLinks: Array<{
    href: string;
    label: string;
  }>;
  primaryAction?: {
    href: string;
    label: string;
  };
  subheading: string;
  variant: "login" | "register";
};

function BrandMark() {
  return (
    <svg aria-hidden="true" className="h-5 w-4" viewBox="0 0 16 20" fill="none">
      <path
        d="M8 1.25 13.5 3v5.04c0 4.09-2.63 7.7-6.5 8.96C3.13 15.74.5 12.13.5 8.04V3L8 1.25Z"
        stroke="currentColor"
        strokeWidth="1.6"
      />
      <path
        d="M8 5.1 10.8 6v2.44c0 2-1.2 3.78-2.8 4.33-1.6-.55-2.8-2.33-2.8-4.33V6L8 5.1Z"
        fill="currentColor"
        opacity="0.3"
      />
    </svg>
  );
}

export function FieldIcon({
  kind,
}: {
  kind: "email" | "password" | "confirm";
}) {
  if (kind === "email") {
    return (
      <svg aria-hidden="true" className="h-[14px] w-[18px]" viewBox="0 0 18 14" fill="none">
        <path
          d="M1.5 1.5h15v11h-15z"
          rx="1.5"
          stroke="currentColor"
          strokeWidth="1.3"
        />
        <path d="m2.6 2.6 6.4 4.6 6.4-4.6" stroke="currentColor" strokeWidth="1.3" />
      </svg>
    );
  }

  if (kind === "password") {
    return (
      <svg aria-hidden="true" className="h-[18px] w-[14px]" viewBox="0 0 14 18" fill="none">
        <path
          d="M3.25 7V5.75a3.75 3.75 0 1 1 7.5 0V7"
          stroke="currentColor"
          strokeWidth="1.3"
        />
        <rect x="1.5" y="7" width="11" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.3" />
        <circle cx="7" cy="11.5" r="1" fill="currentColor" />
      </svg>
    );
  }

  return (
    <svg aria-hidden="true" className="h-[18px] w-[18px]" viewBox="0 0 18 18" fill="none">
      <path
        d="M9 16.5A7.5 7.5 0 1 0 9 1.5a7.5 7.5 0 0 0 0 15Z"
        stroke="currentColor"
        strokeWidth="1.3"
      />
      <path d="m5.75 9 2.1 2.1 4.4-4.4" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  );
}

export function VisibilityIcon({ visible }: { visible: boolean }) {
  if (visible) {
    return (
      <svg aria-hidden="true" className="h-[14px] w-[20px]" viewBox="0 0 20 14" fill="none">
        <path
          d="M1 7s3.2-5 9-5 9 5 9 5-3.2 5-9 5-9-5-9-5Z"
          stroke="currentColor"
          strokeWidth="1.3"
        />
        <circle cx="10" cy="7" r="2.2" stroke="currentColor" strokeWidth="1.3" />
      </svg>
    );
  }

  return (
    <svg aria-hidden="true" className="h-[14px] w-[20px]" viewBox="0 0 20 14" fill="none">
      <path
        d="M1 7s3.2-5 9-5c2.17 0 4.03.7 5.55 1.63M19 7s-3.2 5-9 5c-2.17 0-4.03-.7-5.55-1.63"
        stroke="currentColor"
        strokeWidth="1.3"
      />
      <circle cx="10" cy="7" r="2.2" stroke="currentColor" strokeWidth="1.3" />
      <path d="M2 13 18 1" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  );
}

export function AuthShell({
  children,
  footerMode,
  heading,
  intro,
  navLinks,
  primaryAction,
  subheading,
  variant,
}: AuthShellProps) {
  const isRegister = variant === "register";

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#020617] text-slate-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_24%,rgba(37,99,235,0.18),transparent_30%),linear-gradient(180deg,#020617_0%,#081225_46%,#020617_100%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-50 [background-image:linear-gradient(rgba(37,99,235,0.06)_1px,transparent_1px),linear-gradient(90deg,rgba(37,99,235,0.06)_1px,transparent_1px)] [background-size:96px_96px]" />

      <div className="relative flex min-h-screen flex-col">
        <header className={`border-b ${isRegister ? "border-[rgba(37,99,235,0.2)]" : "border-[rgba(59,130,246,0.1)] bg-[rgba(15,23,42,0.55)] backdrop-blur-md"}`}>
          <div className="mx-auto flex h-[65px] w-full max-w-[1280px] items-center justify-between px-4 sm:px-6 lg:px-10 xl:px-40">
            <Link className="flex items-center gap-3 text-slate-100" href="/">
              <span className={`flex h-8 w-8 items-center justify-center ${isRegister ? "" : "rounded bg-[rgba(59,130,246,0.18)]"} text-[#3b82f6]`}>
                <BrandMark />
              </span>
              <span className="text-xl font-bold tracking-[-0.03em]">SolanaTrust</span>
            </Link>

            <nav className="flex items-center gap-6 text-sm text-slate-400">
              {navLinks.map((item) => (
                <Link key={item.href} className="transition-colors hover:text-slate-200" href={item.href}>
                  {item.label}
                </Link>
              ))}
              {primaryAction ? (
                <Link
                  className="rounded-lg border border-[#2563eb] px-4 py-2 font-semibold text-[#2563eb] transition-colors hover:bg-[rgba(37,99,235,0.08)]"
                  href={primaryAction.href}
                >
                  {primaryAction.label}
                </Link>
              ) : null}
            </nav>
          </div>
        </header>

        <section className={`relative flex flex-1 items-center justify-center px-4 sm:px-6 lg:px-8 ${isRegister ? "py-16" : "py-12 md:py-[181px]"}`}>
          <div className={`${isRegister ? "w-full max-w-[480px]" : "w-full max-w-[480px] rounded-xl border border-[rgba(59,130,246,0.1)] bg-[rgba(15,23,42,0.42)] p-8 shadow-[0_25px_50px_-12px_rgba(0,0,0,0.4)] backdrop-blur-xl md:p-[33px]"}`}>
            <div className="space-y-2">
              {intro}
              <h1 className="font-[family:var(--font-display)] text-[42px] font-black tracking-[-0.06em] text-slate-100 md:text-[48px]">
                {heading}
              </h1>
              <p className={`max-w-[420px] ${isRegister ? "text-[18px] leading-[1.62] text-slate-400" : "text-base leading-6 text-slate-400"}`}>
                {subheading}
              </p>
            </div>

            {children}

            {footerMode === "login" ? (
              <div className="mt-8 border-t border-[rgba(59,130,246,0.1)] pt-6 text-center text-sm text-slate-400">
                Don&apos;t have an account?{" "}
                <Link className="font-semibold text-[#3b82f6]" href="/register">
                  Create an account
                </Link>
              </div>
            ) : (
              <>
                <div className="mt-10 text-center text-base text-slate-400">
                  Already have an account?{" "}
                  <Link className="font-medium text-[#2563eb]" href="/login">
                    Log In
                  </Link>
                </div>

                <div className="relative mt-12 flex items-center justify-center">
                  <div className="absolute inset-x-0 h-px bg-[rgba(37,99,235,0.1)]" />
                  <span className="relative bg-[#020617] px-4 text-xs font-bold uppercase tracking-[0.24em] text-slate-500">
                    Enterprise Trust
                  </span>
                </div>

                <div className="mt-12 grid grid-cols-3 gap-4 opacity-50">
                  {["Shielded", "Realtime", "Audited"].map((item) => (
                    <div
                      key={item}
                      className="flex h-[42px] items-center justify-center rounded-lg border border-[rgba(37,99,235,0.1)] text-xs font-semibold uppercase tracking-[0.2em] text-[#38bdf8]"
                    >
                      {item}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </section>

        <footer className={`border-t ${isRegister ? "border-[rgba(37,99,235,0.1)]" : ""}`}>
          <div className={`mx-auto flex w-full max-w-[1280px] flex-col gap-4 px-4 py-6 text-xs text-slate-500 sm:px-6 lg:px-10 ${isRegister ? "lg:flex-row lg:items-center lg:justify-between xl:px-40" : "items-center justify-center text-center"}`}>
            {isRegister ? (
              <>
                <div className="flex flex-wrap items-center justify-center gap-6 lg:justify-start">
                  <span>(c) 2024 SolanaTrust Protocol</span>
                  <span>Terms of Service</span>
                  <span>Privacy Policy</span>
                </div>
                <div className="flex flex-wrap items-center justify-center gap-4 lg:justify-end">
                  <span className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full border border-[#2563eb]" />
                    Mainnet Beta
                  </span>
                  <span>API v2.0.4</span>
                </div>
              </>
            ) : (
              <div className="flex flex-wrap items-center justify-center gap-3">
                <span>(c) 2024 SolanaTrust Intelligence Systems. All rights reserved.</span>
                <span>|</span>
                <span>Terms of Service</span>
                <span>|</span>
                <span>Privacy Policy</span>
              </div>
            )}
          </div>
        </footer>
      </div>
    </main>
  );
}
