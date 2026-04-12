"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, BookOpen, GraduationCap, FileText, Library, LogOut, Settings
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/vault", label: "Achievement Vault", icon: BookOpen },
  { href: "/universities", label: "Universities", icon: GraduationCap },
  { href: "/reports", label: "My Reports", icon: FileText },
  { href: "/evidence", label: "Evidence Library", icon: Library },
];

export function AppSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="flex h-full w-60 flex-col border-r border-slate-200 bg-white">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2.5 border-b border-slate-200 px-5">
        <div className="flex h-6 w-6 items-center justify-center rounded bg-navy-950">
          <span className="text-[10px] font-bold text-white">SL</span>
        </div>
        <span className="text-sm font-semibold text-slate-900">SourceLock</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors",
                    isActive
                      ? "bg-navy-950 text-white"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-200 p-3">
        <div className="mb-2 flex items-center gap-2.5 px-3 py-1.5">
          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-navy-100 text-navy-900 text-xs font-semibold">
            {user?.full_name?.charAt(0) ?? user?.email?.charAt(0).toUpperCase() ?? "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="truncate text-xs font-medium text-slate-900">
              {user?.full_name ?? "Student"}
            </p>
            <p className="truncate text-xs text-slate-500">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={() => logout()}
          className="flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-sm text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
