"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { AuthShell, FieldIcon, VisibilityIcon } from "@/components/auth-shell";
import { setAccessToken } from "@/lib/auth";
import { ApiError, getMe, loginUser } from "@/lib/api";
import { APP_TELEGRAM_URL } from "@/lib/plans";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPending(true);
    setError(null);

    try {
      const data = await loginUser(email, password);
      setAccessToken(data.access_token);
      const profile = await getMe();
      router.push(profile.role === "admin" ? "/admin" : "/dashboard");
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof ApiError ? submitError.message : "Unable to login right now.");
    } finally {
      setPending(false);
    }
  };

  return (
    <AuthShell
      footerMode="login"
      heading="Welcome Back"
      navLinks={[
        { href: APP_TELEGRAM_URL, label: "Support" },
      ]}
      subheading="Log in to access your risk intelligence dashboard."
      variant="login"
    >
      <form className="mt-8 space-y-6" onSubmit={onSubmit}>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-300">Email Address</span>
          <span className="relative block">
            <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-slate-500">
              <FieldIcon kind="email" />
            </span>
            <input
              className="h-14 w-full rounded-lg border border-[rgba(59,130,246,0.2)] bg-[rgba(59,130,246,0.05)] pl-[49px] pr-4 text-base text-slate-100 outline-none transition-colors placeholder:text-slate-600 focus:border-[rgba(59,130,246,0.45)]"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="name@company.com"
              required
              type="email"
              value={email}
            />
          </span>
        </label>

        <label className="block">
          <span className="mb-2 flex items-center justify-between text-sm font-medium text-slate-300">
            <span>Password</span>
            <Link className="text-xs font-normal text-[#3b82f6]" href="/register">
              Forgot password?
            </Link>
          </span>
          <span className="relative block">
            <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-slate-500">
              <FieldIcon kind="password" />
            </span>
            <input
              className="h-14 w-full rounded-lg border border-[rgba(59,130,246,0.2)] bg-[rgba(59,130,246,0.05)] px-[49px] text-base text-slate-100 outline-none transition-colors placeholder:text-slate-600 focus:border-[rgba(59,130,246,0.45)]"
              minLength={8}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="password"
              required
              type={showPassword ? "text" : "password"}
              value={password}
            />
            <button
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute inset-y-0 right-4 flex items-center text-slate-500 transition-colors hover:text-slate-300"
              onClick={() => setShowPassword((current) => !current)}
              type="button"
            >
              <VisibilityIcon visible={showPassword} />
            </button>
          </span>
        </label>

        <button
          className="h-14 w-full rounded-lg bg-[#3b82f6] text-base font-bold tracking-[0.02em] text-white shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={pending}
          type="submit"
        >
          {pending ? "Signing In..." : "Sign In to Dashboard"}
        </button>

        {error ? <p className="text-sm text-[var(--critical)]">{error}</p> : null}
      </form>
    </AuthShell>
  );
}
