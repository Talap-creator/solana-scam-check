"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ApiError,
  getPremiumCheckoutSession,
  getUsage,
  type PremiumCheckoutSession,
} from "@/lib/api";

declare global {
  interface Window {
    helioCheckout?: (container: HTMLElement, config: Record<string, unknown>) => void;
  }
}

let helioScriptPromise: Promise<void> | null = null;

function loadHelioCheckoutScript(): Promise<void> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("MoonPay checkout is only available in the browser."));
  }

  if (window.helioCheckout) {
    return Promise.resolve();
  }

  if (helioScriptPromise) {
    return helioScriptPromise;
  }

  helioScriptPromise = new Promise<void>((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>('script[data-helio-checkout="1"]');
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("Unable to load MoonPay checkout.")), {
        once: true,
      });
      return;
    }

    const script = document.createElement("script");
    script.type = "module";
    script.crossOrigin = "anonymous";
    script.src = "https://embed.hel.io/assets/index-v1.js";
    script.dataset.helioCheckout = "1";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Unable to load MoonPay checkout."));
    document.head.appendChild(script);
  });

  return helioScriptPromise;
}

type PremiumCheckoutButtonProps = {
  className: string;
  label?: string;
};

export function PremiumCheckoutButton({
  className,
  label = "Unlock Premium",
}: PremiumCheckoutButtonProps) {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [checkoutSession, setCheckoutSession] = useState<PremiumCheckoutSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !checkoutSession?.paylink_id || !containerRef.current) {
      return;
    }

    let cancelled = false;

    const mountWidget = async () => {
      try {
        await loadHelioCheckoutScript();
        if (cancelled || !containerRef.current || !window.helioCheckout) {
          return;
        }

        containerRef.current.innerHTML = "";
        window.helioCheckout(containerRef.current, {
          paylinkId: checkoutSession.paylink_id,
          paymentType: checkoutSession.payment_type,
          display: "inline",
          theme: { themeMode: "dark" },
          primaryColor: checkoutSession.primary_color,
          neutralColor: checkoutSession.neutral_color,
          backgroundColor: checkoutSession.background_color,
          additionalJSON: checkoutSession.additional_json,
          onSuccess: () => {
            setMessage("Payment received. Waiting for MoonPay confirmation...");
            void pollForUpgrade();
          },
        });
      } catch (mountError) {
        setError(mountError instanceof Error ? mountError.message : "Unable to open MoonPay checkout.");
      }
    };

    const pollForUpgrade = async () => {
      for (let attempt = 0; attempt < 8; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 3000));
        try {
          const usage = await getUsage();
          if (usage.plan === "pro" || usage.plan === "enterprise") {
            setMessage("Premium activated. Refreshing your account limits...");
            window.setTimeout(() => {
              router.refresh();
              window.location.reload();
            }, 800);
            return;
          }
        } catch {}
      }
      setMessage("Payment succeeded. Backend upgrade can take a minute if MoonPay webhook is still processing.");
    };

    void mountWidget();

    return () => {
      cancelled = true;
    };
  }, [checkoutSession, open, router]);

  const onClick = async () => {
    setError(null);
    setMessage(null);
    if (checkoutSession?.available && !checkoutSession.already_active) {
      setOpen(true);
      return;
    }

    setLoading(true);
    try {
      const session = await getPremiumCheckoutSession();
      if (session.already_active) {
        setCheckoutSession(session);
        setMessage("Premium is already active on this account.");
        return;
      }
      if (!session.available || !session.paylink_id) {
        setError("Premium checkout is not configured yet.");
        return;
      }
      setCheckoutSession(session);
      setOpen(true);
    } catch (checkoutError) {
      if (checkoutError instanceof ApiError && checkoutError.status === 401) {
        router.push("/login");
        return;
      }
      setError(checkoutError instanceof Error ? checkoutError.message : "Unable to prepare checkout.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-w-0 flex-col">
      <button
        className={className}
        disabled={loading}
        onClick={() => void onClick()}
        type="button"
      >
        {loading ? "Loading..." : label}
      </button>
      {error ? <p className="mt-2 text-sm text-rose-300">{error}</p> : null}
      {message ? <p className="mt-2 text-sm text-slate-300">{message}</p> : null}

      {open && checkoutSession?.paylink_id ? (
        <div className="fixed inset-0 z-[120] flex items-center justify-center bg-slate-950/80 px-4 py-8 backdrop-blur-sm">
          <div className="w-full max-w-3xl rounded-[28px] border border-[#3b82f6]/20 bg-[linear-gradient(180deg,#0f172a,#020617)] p-6 shadow-[0_40px_120px_rgba(2,6,23,0.65)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.22em] text-[#93c5fd]">
                  MoonPay Commerce
                </p>
                <h3 className="mt-3 text-2xl font-black tracking-tight text-slate-100">
                  Upgrade to Premium
                </h3>
                <p className="mt-2 max-w-xl text-sm leading-6 text-slate-400">
                  Use the same account email at checkout:{" "}
                  <span className="font-semibold text-slate-200">{checkoutSession.email}</span>.
                  Once payment is confirmed, your account switches to Premium and limits increase automatically.
                </p>
              </div>
              <button
                className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm font-semibold text-slate-200 transition hover:bg-white/10"
                onClick={() => setOpen(false)}
                type="button"
              >
                Close
              </button>
            </div>

            <div className="mt-6 rounded-[24px] border border-[#3b82f6]/15 bg-[#020617] p-4">
              <div ref={containerRef} />
            </div>

            <p className="mt-4 text-xs leading-5 text-slate-500">
              If MoonPay confirms the payment but your plan does not update within a minute, the webhook is usually still in flight.
            </p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
