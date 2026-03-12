import type { SVGProps } from "react";

type AppIconName =
  | "shield"
  | "search"
  | "filter"
  | "check"
  | "copy"
  | "bell"
  | "mail"
  | "rss"
  | "terminal"
  | "token"
  | "arrow-right"
  | "document"
  | "verified-user"
  | "star"
  | "star-filled"
  | "share"
  | "analytics"
  | "trending"
  | "code"
  | "groups"
  | "wallet"
  | "rocket"
  | "hub"
  | "history"
  | "control"
  | "holders"
  | "drop"
  | "radar"
  | "chart"
  | "sensors"
  | "arrow-down"
  | "arrow-up"
  | "warning"
  | "info"
  | "priority"
  | "verified"
  | "neutral-face"
  | "happy-face"
  | "sad-face"
  | "hourglass";

type AppIconProps = {
  className?: string;
  name: AppIconName;
};

export function AppIcon({ className, name }: AppIconProps) {
  const props: SVGProps<SVGSVGElement> = {
    className,
    fill: "none",
    stroke: "currentColor",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    strokeWidth: 1.8,
    viewBox: "0 0 24 24",
  };

  switch (name) {
    case "shield":
      return (
        <svg {...props}>
          <path d="M12 3 18.5 5.5v6c0 4.6-2.8 8.6-6.5 10-3.7-1.4-6.5-5.4-6.5-10v-6L12 3Z" />
          <path d="M9.3 10.8c.8-1.7 3.1-2.2 4.5-.8 1.4-1.4 3.7-.9 4.5.8-.7 2.5-2.8 4.5-4.5 5.8-1.7-1.3-3.8-3.3-4.5-5.8Z" />
        </svg>
      );
    case "search":
      return (
        <svg {...props}>
          <circle cx="11" cy="11" r="6" />
          <path d="m20 20-4.2-4.2" />
        </svg>
      );
    case "filter":
      return (
        <svg {...props}>
          <path d="M4 6h16" />
          <path d="M7 12h10" />
          <path d="M10 18h4" />
        </svg>
      );
    case "check":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="8.5" />
          <path d="m8.5 12.2 2.4 2.4 4.7-5.1" />
        </svg>
      );
    case "copy":
      return (
        <svg {...props}>
          <rect x="9" y="9" width="10" height="10" rx="2" />
          <path d="M6 15H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v1" />
        </svg>
      );
    case "bell":
      return (
        <svg {...props}>
          <path d="M8.5 18h7" />
          <path d="M9 18a2.5 2.5 0 0 0 5 0" />
          <path d="M6.5 15.5h11c-1.2-1.2-1.8-2.8-1.8-4.5V10a3.7 3.7 0 1 0-7.4 0v1c0 1.7-.6 3.3-1.8 4.5Z" />
        </svg>
      );
    case "mail":
      return (
        <svg {...props}>
          <path d="M4 7.5 12 13l8-5.5" />
          <rect x="4" y="6" width="16" height="12" rx="2" />
        </svg>
      );
    case "terminal":
      return (
        <svg {...props}>
          <rect x="4" y="5" width="16" height="14" rx="2" />
          <path d="m8 10 2.5 2L8 14.5" />
          <path d="M13 15h3" />
        </svg>
      );
    case "token":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="6.5" />
          <path d="M12 5.5v13" />
          <path d="M5.5 12h13" />
        </svg>
      );
    case "arrow-right":
      return (
        <svg {...props}>
          <path d="M5 12h13" />
          <path d="m13 7 5 5-5 5" />
        </svg>
      );
    case "document":
      return (
        <svg {...props}>
          <path d="M8 4h6l4 4v12H8a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z" />
          <path d="M14 4v4h4" />
          <path d="M10 12h6" />
          <path d="M10 16h4" />
        </svg>
      );
    case "verified-user":
      return (
        <svg {...props}>
          <path d="M12 3 18 5.5v5.6c0 4-2.5 7.6-6 8.9-3.5-1.3-6-4.9-6-8.9V5.5L12 3Z" />
          <path d="m9.5 11.8 1.8 1.8 3.7-4" />
        </svg>
      );
    case "star":
      return (
        <svg {...props}>
          <path d="m12 4 2.3 4.7 5.2.8-3.7 3.7.9 5.3L12 16l-4.7 2.5.9-5.3-3.7-3.7 5.2-.8L12 4Z" />
        </svg>
      );
    case "star-filled":
      return (
        <svg {...props} fill="currentColor" stroke="none">
          <path d="m12 4 2.3 4.7 5.2.8-3.7 3.7.9 5.3L12 16l-4.7 2.5.9-5.3-3.7-3.7 5.2-.8L12 4Z" />
        </svg>
      );
    case "share":
      return (
        <svg {...props}>
          <circle cx="17.5" cy="6.5" r="2" />
          <circle cx="6.5" cy="12" r="2" />
          <circle cx="17.5" cy="17.5" r="2" />
          <path d="m8.3 11 7-3.2" />
          <path d="m8.3 13 7 3.2" />
        </svg>
      );
    case "rss":
      return (
        <svg {...props}>
          <path d="M6 17a1.5 1.5 0 1 0 0 .1Z" />
          <path d="M6 11a7 7 0 0 1 7 7" />
          <path d="M6 6a12 12 0 0 1 12 12" />
        </svg>
      );
    case "analytics":
      return (
        <svg {...props}>
          <path d="M5 18V9" />
          <path d="M12 18V5" />
          <path d="M19 18v-7" />
        </svg>
      );
    case "trending":
      return (
        <svg {...props}>
          <path d="m5 15 5-5 4 4 5-7" />
          <path d="M19 7h-4" />
          <path d="M19 7v4" />
        </svg>
      );
    case "code":
      return (
        <svg {...props}>
          <path d="m9 8-4 4 4 4" />
          <path d="m15 8 4 4-4 4" />
          <path d="m13 6-2 12" />
        </svg>
      );
    case "groups":
      return (
        <svg {...props}>
          <circle cx="9" cy="9" r="2.5" />
          <circle cx="16" cy="9.5" r="2" />
          <path d="M4.5 18c.8-2.2 2.5-3.5 4.5-3.5s3.7 1.3 4.5 3.5" />
          <path d="M14.4 17.5c.4-1.3 1.5-2.2 3-2.5" />
        </svg>
      );
    case "wallet":
      return (
        <svg {...props}>
          <path d="M4 8.5A2.5 2.5 0 0 1 6.5 6H18a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6.5A2.5 2.5 0 0 1 4 15.5v-7Z" />
          <path d="M16 12h4" />
          <circle cx="16" cy="12" r=".8" fill="currentColor" stroke="none" />
        </svg>
      );
    case "rocket":
      return (
        <svg {...props}>
          <path d="M14.5 5.5c2.2-.4 4 .4 4 .4s.8 1.8.4 4L13 15.8l-4.8-4.8 6.3-5.5Z" />
          <path d="M8.2 11 5 14.2" />
          <path d="m9.8 16-1.2 3 3-1.2" />
        </svg>
      );
    case "hub":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="2" />
          <circle cx="6" cy="8" r="1.5" />
          <circle cx="18" cy="8" r="1.5" />
          <circle cx="8" cy="17" r="1.5" />
          <circle cx="16" cy="17" r="1.5" />
          <path d="M10.5 11 7.2 8.8" />
          <path d="m13.5 11 3.3-2.2" />
          <path d="m10.8 13.5-1.8 2.1" />
          <path d="m13.2 13.5 1.8 2.1" />
        </svg>
      );
    case "history":
      return (
        <svg {...props}>
          <path d="M5 12a7 7 0 1 0 2-4.9" />
          <path d="M5 5v4h4" />
          <path d="M12 8.5V12l2.5 1.5" />
        </svg>
      );
    case "control":
      return (
        <svg {...props}>
          <path d="M12 3 18 6v5c0 4-2.4 7.4-6 8.7C8.4 18.4 6 15 6 11V6l6-3Z" />
          <path d="M12 8v5" />
          <path d="M9.5 10.5h5" />
        </svg>
      );
    case "holders":
      return (
        <svg {...props}>
          <circle cx="9" cy="9" r="2.5" />
          <circle cx="16.5" cy="10" r="2" />
          <path d="M4.5 18c.8-2.3 2.7-3.5 4.5-3.5s3.7 1.2 4.5 3.5" />
          <path d="M14.5 17.5c.5-1.5 1.7-2.4 3.2-2.6" />
        </svg>
      );
    case "drop":
      return (
        <svg {...props}>
          <path d="M12 4c3 3.5 5 6.1 5 8.5A5 5 0 0 1 7 12.5C7 10.1 9 7.5 12 4Z" />
        </svg>
      );
    case "radar":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="7.5" />
          <circle cx="12" cy="12" r="3.5" />
          <path d="M12 12 17.5 8.5" />
        </svg>
      );
    case "chart":
      return (
        <svg {...props}>
          <path d="M5 18h14" />
          <path d="M7 16V11" />
          <path d="M12 16V7" />
          <path d="M17 16v-4" />
        </svg>
      );
    case "sensors":
      return (
        <svg {...props}>
          <path d="M12 12v.01" />
          <path d="M9 9a4.2 4.2 0 0 1 6 0" />
          <path d="M6.5 6.5a7.8 7.8 0 0 1 11 0" />
          <path d="M4 4a11.3 11.3 0 0 1 16 0" />
        </svg>
      );
    case "arrow-down":
      return (
        <svg {...props}>
          <path d="M12 5v14" />
          <path d="m7 14 5 5 5-5" />
        </svg>
      );
    case "arrow-up":
      return (
        <svg {...props}>
          <path d="M12 19V5" />
          <path d="m17 10-5-5-5 5" />
        </svg>
      );
    case "warning":
      return (
        <svg {...props}>
          <path d="M12 4 4.5 18h15L12 4Z" />
          <path d="M12 9v4" />
          <path d="M12 16h.01" />
        </svg>
      );
    case "info":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="8.5" />
          <path d="M12 10.5v4.5" />
          <path d="M12 7.8h.01" />
        </svg>
      );
    case "priority":
      return (
        <svg {...props}>
          <path d="M12 5v8" />
          <path d="M12 17h.01" />
          <circle cx="12" cy="12" r="8.5" />
        </svg>
      );
    case "verified":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="8.5" />
          <path d="m8.5 12.2 2.4 2.4 4.7-5.1" />
        </svg>
      );
    case "neutral-face":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="8.5" />
          <path d="M9 15h6" />
          <path d="M9.5 10.2h.01" />
          <path d="M14.5 10.2h.01" />
        </svg>
      );
    case "happy-face":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="8.5" />
          <path d="M8.7 13.5a4 4 0 0 0 6.6 0" />
          <path d="M9.5 10.2h.01" />
          <path d="M14.5 10.2h.01" />
        </svg>
      );
    case "sad-face":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="8.5" />
          <path d="M8.7 15a4 4 0 0 1 6.6 0" />
          <path d="M9.5 10.2h.01" />
          <path d="M14.5 10.2h.01" />
        </svg>
      );
    case "hourglass":
      return (
        <svg {...props}>
          <path d="M7 5h10" />
          <path d="M7 19h10" />
          <path d="M8 5c0 2.5 1.8 4 4 5.5 2.2-1.5 4-3 4-5.5" />
          <path d="M8 19c0-2.5 1.8-4 4-5.5 2.2 1.5 4 3 4 5.5" />
        </svg>
      );
  }
}
