const DEFAULT_API_BASE_URL = "https://solana-scam-check.onrender.com";

export function getClientApiBaseUrl(): string {
  return "";
}

export function getServerApiBaseUrl(): string {
  return (
    process.env.FRONTEND_INTERNAL_API_BASE_URL ??
    process.env.API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    DEFAULT_API_BASE_URL
  );
}
