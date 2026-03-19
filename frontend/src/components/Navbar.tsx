"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Home" },
  { href: "/enroll", label: "New Enrollment" },
  { href: "/status", label: "Check Status" },
  { href: "/mcp-tools", label: "MCP Tools" },
  { href: "/architecture", label: "Architecture" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="border-b border-gray-800 bg-[#0d0d14]">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2.5 text-lg font-bold text-gray-100">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-8 w-8">
            {/* Shield body */}
            <path
              d="M16 3L5 8v7c0 7.73 4.66 14.96 11 17 6.34-2.04 11-9.27 11-17V8L16 3z"
              fill="#22c55e"
              opacity="0.25"
              stroke="#4ade80"
              strokeWidth="1.5"
              strokeLinejoin="round"
            />
            {/* Inner shield highlight */}
            <path
              d="M16 6.5L8 10v5.5c0 5.8 3.4 11.2 8 12.8 4.6-1.6 8-7 8-12.8V10L16 6.5z"
              fill="#22c55e"
              opacity="0.15"
            />
            {/* Heart / benefits icon */}
            <path
              d="M16 22l-1.1-1C11.1 17.7 9 15.8 9 13.5 9 11.6 10.6 10 12.5 10c1.1 0 2.1.5 2.8 1.3L16 12l.7-.7c.7-.8 1.7-1.3 2.8-1.3C21.4 10 23 11.6 23 13.5c0 2.3-2.1 4.2-5.9 7.5L16 22z"
              fill="#4ade80"
            />
          </svg>
          Benefits Platform
        </Link>
        <div className="flex gap-1">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  active
                    ? "bg-green-500/15 text-green-400"
                    : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
