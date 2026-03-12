"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { AuthShell, FieldIcon, VisibilityIcon } from "@/components/auth-shell";
import { setAccessToken } from "@/lib/auth";
import { ApiError, getMe, registerUser } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setPending(true);

    try {
      const data = await registerUser(email, password, "free");
      setAccessToken(data.access_token);
      const profile = await getMe();
      const nextPath =
        typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("next") : null;
      const target =
        nextPath && nextPath.startsWith("/")
          ? nextPath
          : profile.role === "admin"
            ? "/admin"
            : "/dashboard";
      router.push(target);
      router.refresh();
    } catch (submitError) {
      setError(
        submitError instanceof ApiError ? submitError.message : "Unable to create account right now.",
      );
    } finally {
      setPending(false);
    }
  };

  return (
    <AuthShell
      footerMode="register"
      heading="Join SolanaTrust"
      intro={
        <div className="inline-flex items-center gap-2 rounded-full border border-[rgba(37,99,235,0.2)] bg-[rgba(37,99,235,0.1)] px-3 py-1 text-xs font-bold uppercase tracking-[0.16em] text-[#2563eb]">
          <span className="h-2 w-2 rounded-full bg-[#2563eb] opacity-80" />
          Network Status: Secure
        </div>
      }
      navLinks={[]}
      subheading="Get advanced onchain risk alerts and deep token audits."
      variant="register"
    >
      <form className="mt-8 space-y-5" onSubmit={onSubmit}>
        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-slate-300">Email Address</span>
          <span className="relative block">
            <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-slate-500">
              <FieldIcon kind="email" />
            </span>
            <input
              className="h-14 w-full rounded-xl border border-[rgba(37,99,235,0.2)] bg-[rgba(15,23,42,0.5)] pl-[45px] pr-4 text-base text-slate-100 outline-none transition-colors placeholder:text-slate-600 focus:border-[rgba(37,99,235,0.45)]"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="name@example.com"
              required
              type="email"
              value={email}
            />
          </span>
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-slate-300">Password</span>
          <span className="relative block">
            <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-slate-500">
              <FieldIcon kind="password" />
            </span>
            <input
              className="h-14 w-full rounded-xl border border-[rgba(37,99,235,0.2)] bg-[rgba(15,23,42,0.5)] pl-[45px] pr-12 text-base text-slate-100 outline-none transition-colors placeholder:text-slate-600 focus:border-[rgba(37,99,235,0.45)]"
              minLength={12}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
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

        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-slate-300">Confirm Password</span>
          <span className="relative block">
            <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-slate-500">
              <FieldIcon kind="confirm" />
            </span>
            <input
              className="h-14 w-full rounded-xl border border-[rgba(37,99,235,0.2)] bg-[rgba(15,23,42,0.5)] pl-[45px] pr-12 text-base text-slate-100 outline-none transition-colors placeholder:text-slate-600 focus:border-[rgba(37,99,235,0.45)]"
              minLength={12}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="Repeat your password"
              required
              type={showConfirmPassword ? "text" : "password"}
              value={confirmPassword}
            />
            <button
              aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
              className="absolute inset-y-0 right-4 flex items-center text-slate-500 transition-colors hover:text-slate-300"
              onClick={() => setShowConfirmPassword((current) => !current)}
              type="button"
            >
              <VisibilityIcon visible={showConfirmPassword} />
            </button>
          </span>
        </label>

        <button
          className="flex h-14 w-full items-center justify-center gap-2 rounded-xl bg-[#2563eb] text-lg font-bold text-white shadow-[0_10px_24px_rgba(37,99,235,0.28)] transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={pending}
          type="submit"
        >
          <span>{pending ? "Creating Account..." : "Create Account"}</span>
          <span aria-hidden="true" className="text-xl leading-none">
            -&gt;
          </span>
        </button>

        {error ? <p className="text-sm text-[var(--critical)]">{error}</p> : null}
      </form>
    </AuthShell>
  );
}
