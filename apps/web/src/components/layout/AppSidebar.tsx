"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  BookOpen,
  GraduationCap,
  FileText,
  Library,
  LogOut,
  Settings,
  Check,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { ApplyMapLogo } from "@/components/brand/ApplyMapLogo";
import { achievementsApi, reportsApi, targetsApi } from "@/lib/api";
import type { Report } from "@/types";

const navItems = [
  {
    href: "/dashboard",
    label: "Dashboard",
    icon: LayoutDashboard,
    tooltip: "Profile completeness, stats, and quick actions",
  },
  {
    href: "/vault",
    label: "Achievement Vault",
    icon: BookOpen,
    tooltip: "Store and manage all your activities and honors",
  },
  {
    href: "/universities",
    label: "Universities",
    icon: GraduationCap,
    tooltip: "Select target schools and generate optimization reports",
  },
  {
    href: "/reports",
    label: "My Reports",
    icon: FileText,
    tooltip: "Ranked recommendations and rewrite variants",
  },
  {
    href: "/evidence",
    label: "Evidence Library",
    icon: Library,
    tooltip: "Browse the official sources behind every recommendation",
  },
];

export function AppSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const { data: achievementsData } = useQuery({
    queryKey: ["achievements"],
    queryFn: () => achievementsApi.list(),
    staleTime: 60_000,
  });
  const { data: targetsData } = useQuery({
    queryKey: ["targets"],
    queryFn: () => targetsApi.list(),
    staleTime: 60_000,
  });
  const { data: reportsData } = useQuery({
    queryKey: ["reports"],
    queryFn: () => reportsApi.list(),
    staleTime: 60_000,
  });

  const achievements = achievementsData?.data?.data ?? [];
  const targets = targetsData?.data?.data ?? [];
  const reports: Report[] = reportsData?.data?.data ?? [];

  const progressSteps = [
    {
      label: "Profile",
      complete: !!(user?.full_name && user?.country),
      href: "/onboarding",
    },
    {
      label: "Vault",
      complete: achievements.length > 0,
      href: "/vault",
    },
    {
      label: "Universities",
      complete: targets.length > 0,
      href: "/universities",
    },
    {
      label: "Report",
      complete: reports.some((r) => r.status === "completed"),
      href: "/reports",
    },
  ];

  const completedCount = progressSteps.filter((s) => s.complete).length;

  return (
    <aside className="flex h-full w-60 flex-col border-r border-slate-200 bg-[#F9F8F6]">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2.5 border-b border-slate-200 px-5">
        <ApplyMapLogo className="h-8" />
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-0.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <li key={item.href} className="group relative">
                <Link
                  href={item.href}
                  className={cn(
                    // base — border-l-2 on all items keeps layout stable (no shift on active)
                    "flex items-center gap-2.5 rounded-md border-l-2 py-2 pl-[10px] pr-3 text-sm transition-all duration-150",
                    isActive
                      ? "border-navy-950 bg-navy-50 font-medium text-navy-900"
                      : "border-transparent text-slate-600 hover:bg-white hover:text-slate-900"
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {item.label}
                </Link>

                {/* Hover tooltip — appears to the right of the sidebar */}
                <div
                  className={cn(
                    "pointer-events-none absolute left-[calc(100%+10px)] top-1/2 z-50 w-52",
                    "-translate-y-1/2 rounded-lg bg-slate-900 px-3 py-2 text-xs leading-snug text-white",
                    "opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100"
                  )}
                >
                  {item.tooltip}
                  {/* Arrow pointing left */}
                  <div className="absolute -left-1.5 top-1/2 -translate-y-1/2 border-4 border-transparent border-r-slate-900" />
                </div>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Progress trail */}
      <div className="border-t border-slate-200 px-5 py-4">
        <div className="mb-3 flex items-center justify-between">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Your progress
          </p>
          <span className={cn(
            "text-[10px] tabular-nums font-semibold",
            completedCount === 4
              ? "text-emerald-600"
              : completedCount > 0
              ? "text-amber-600"
              : "text-slate-400"
          )}>
            {completedCount}/4
          </span>
        </div>
        <div className="space-y-1.5">
          {progressSteps.map((step, i) => (
            <Link
              key={step.label}
              href={step.href}
              className="flex items-center gap-2.5 rounded px-1 py-0.5 transition-colors hover:bg-slate-100"
            >
              {/* Dot + vertical connector */}
              <div className="relative flex shrink-0 flex-col items-center">
                <div
                  className={cn(
                    "h-1.5 w-1.5 rounded-full transition-colors",
                    step.complete ? "bg-emerald-500" : "bg-slate-300"
                  )}
                />
                {/* Connector line below — only between steps */}
                {i < progressSteps.length - 1 && (
                  <div
                    className={cn(
                      "absolute top-1.5 h-[18px] w-px",
                      progressSteps[i + 1].complete
                        ? "bg-emerald-200"
                        : "bg-slate-200"
                    )}
                  />
                )}
              </div>
              <span
                className={cn(
                  "flex-1 text-xs transition-colors",
                  step.complete ? "text-slate-600" : "text-slate-400"
                )}
              >
                {step.label}
              </span>
              {step.complete && (
                <Check className="h-3 w-3 shrink-0 text-emerald-500" />
              )}
            </Link>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-slate-200 p-3">
        {/* User info */}
        <div className="mb-1 flex items-center gap-2.5 px-3 py-1.5">
          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-navy-100 text-xs font-semibold text-navy-900">
            {user?.full_name?.charAt(0) ?? user?.email?.charAt(0).toUpperCase() ?? "U"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-slate-900">
              {user?.full_name ?? "Student"}
            </p>
            <p className="truncate text-xs text-slate-500">{user?.email}</p>
          </div>
        </div>

        {/* Settings */}
        <Link href="/onboarding">
          <button className="flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-sm text-slate-500 transition-colors hover:bg-white hover:text-slate-700">
            <Settings className="h-4 w-4" />
            Settings
          </button>
        </Link>

        {/* Sign out */}
        <button
          onClick={() => logout()}
          className="flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-sm text-slate-500 transition-colors hover:bg-white hover:text-slate-700"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
