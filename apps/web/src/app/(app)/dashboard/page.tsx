"use client";

import Link from "next/link";
import { Fragment } from "react";
import { useQuery } from "@tanstack/react-query";
import { achievementsApi, reportsApi, targetsApi, profileApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/useAuth";
import {
  ArrowRight, Plus, GraduationCap, FileText, BookOpen,
} from "lucide-react";
import { formatDate } from "@/lib/utils";
import type { Achievement, Report, ReportStatus, TargetUniversity } from "@/types";

// ─── Circular Progress Ring ─────────────────────────────────────────────────

function CircleProgress({ value, size = 56, strokeWidth = 3.5 }: {
  value: number;
  size?: number;
  strokeWidth?: number;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
      {/* Track */}
      <circle
        cx={size / 2} cy={size / 2} r={radius}
        fill="none" strokeWidth={strokeWidth}
        className="stroke-slate-100"
      />
      {/* Fill */}
      <circle
        cx={size / 2} cy={size / 2} r={radius}
        fill="none" strokeWidth={strokeWidth}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: "stroke-dashoffset 0.7s ease-out" }}
        className="stroke-navy-950"
      />
    </svg>
  );
}

// ─── Mini Report Status Timeline ────────────────────────────────────────────

function ReportStatusBadge({ status }: { status: ReportStatus }) {
  if (status === "completed") return <Badge variant="success">Completed</Badge>;
  if (status === "failed") return <Badge variant="destructive">Failed</Badge>;

  const stages: ReportStatus[] = ["pending", "processing", "completed"];
  const currentIdx = stages.indexOf(status);

  return (
    <div className="flex items-center gap-1">
      {stages.map((stage, i) => (
        <Fragment key={stage}>
          <div className={
            i < currentIdx
              ? "h-1.5 w-1.5 rounded-full bg-navy-950"
              : i === currentIdx
              ? "h-1.5 w-1.5 rounded-full bg-navy-400 animate-pulse"
              : "h-1.5 w-1.5 rounded-full bg-slate-200"
          } />
          {i < stages.length - 1 && (
            <div className={`h-px w-3 ${i < currentIdx ? "bg-navy-950" : "bg-slate-200"}`} />
          )}
        </Fragment>
      ))}
      <span className="ml-1 text-xs capitalize text-slate-400">{status}</span>
    </div>
  );
}

// ─── Empty Reports Illustration ──────────────────────────────────────────────

function EmptyReports() {
  return (
    <div className="flex flex-col items-center py-8 text-center">
      <svg
        width="56" height="56" viewBox="0 0 56 56" fill="none"
        className="mb-4" aria-hidden="true"
      >
        {/* Document */}
        <rect x="8" y="4" width="30" height="38" rx="3" className="stroke-slate-200" strokeWidth="1.5" fill="white" />
        {/* Fold corner */}
        <path d="M28 4 L38 14 L28 14 Z" className="stroke-slate-200 fill-slate-50" strokeWidth="1.5" />
        {/* Lines */}
        <line x1="14" y1="22" x2="30" y2="22" className="stroke-slate-200" strokeWidth="1.5" strokeLinecap="round" />
        <line x1="14" y1="28" x2="26" y2="28" className="stroke-slate-200" strokeWidth="1.5" strokeLinecap="round" />
        <line x1="14" y1="34" x2="22" y2="34" className="stroke-slate-200" strokeWidth="1.5" strokeLinecap="round" />
        {/* Lock badge */}
        <circle cx="40" cy="42" r="10" fill="white" className="stroke-slate-200" strokeWidth="1.5" />
        <rect x="35.5" y="40.5" width="9" height="7" rx="1.5" className="stroke-slate-400" strokeWidth="1.5" />
        <path d="M37.5 40.5 V38 A2.5 2.5 0 0 1 42.5 38 V40.5" className="stroke-slate-400" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
      <p className="text-sm font-medium text-slate-600">No advisors yet</p>
      <p className="mt-1 text-xs text-slate-400">
        Generate one from the Universities page.
      </p>
      <Link href="/universities" className="mt-4">
        <Button size="sm" variant="outline" className="gap-1.5 text-xs">
          <GraduationCap className="h-3.5 w-3.5" />
          Go to Universities
        </Button>
      </Link>
    </div>
  );
}

// ─── Quick Action Item ────────────────────────────────────────────────────────

function QuickActionItem({
  href,
  icon: Icon,
  iconBg,
  iconColor,
  title,
  subtitle,
}: {
  href: string;
  icon: React.ElementType;
  iconBg: string;
  iconColor: string;
  title: string;
  subtitle: string;
}) {
  return (
    <Link href={href}>
      <div className="flex items-center gap-3 rounded-lg border border-slate-100 bg-slate-50 p-3 transition-colors hover:border-slate-200 hover:bg-white cursor-pointer">
        <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${iconBg}`}>
          <Icon className={`h-4 w-4 ${iconColor}`} />
        </div>
        <div>
          <p className="text-sm font-medium text-slate-900">{title}</p>
          <p className="text-xs text-slate-500">{subtitle}</p>
        </div>
        <ArrowRight className="ml-auto h-3.5 w-3.5 shrink-0 text-slate-300" />
      </div>
    </Link>
  );
}

// ─── Dashboard Page ──────────────────────────────────────────────────────────

export default function DashboardPage() {
  const { user } = useAuth();

  const { data: profileData, isLoading: profileLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: () => profileApi.get(),
  });
  const { data: achievementsData, isLoading: achievementsLoading } = useQuery({
    queryKey: ["achievements"],
    queryFn: () => achievementsApi.list(),
  });
  const { data: reportsData, isLoading: reportsLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: () => reportsApi.list(),
  });
  const { data: targetsData, isLoading: targetsLoading } = useQuery({
    queryKey: ["targets"],
    queryFn: () => targetsApi.list(),
  });

  const isLoading = profileLoading || achievementsLoading || reportsLoading || targetsLoading;

  const profile = profileData?.data?.data?.profile;
  const achievements: Achievement[] = achievementsData?.data?.data ?? [];
  const reports: Report[] = reportsData?.data?.data ?? [];
  const targets: TargetUniversity[] = targetsData?.data?.data ?? [];

  const activities = achievements.filter((a) => a.type === "activity");
  const honors = achievements.filter((a) => a.type === "honor");
  const recentReports = reports.slice(0, 3);

  // Profile completeness
  const profileFields = [
    !!user?.full_name,
    !!user?.country,
    !!profile?.graduation_year,
    !!profile?.curriculum,
    !!profile?.intended_major,
    !!(profile?.sat_score || profile?.act_score || profile?.ielts_score || profile?.toefl_score),
  ];
  const filledCount = profileFields.filter(Boolean).length;
  const profilePct = Math.round((filledCount / profileFields.length) * 100);

  // Welcome banner context
  const firstName = user?.full_name?.split(" ")[0];
  let bannerMessage = "Here's where your application stands.";
  let bannerCTA: { href: string; label: string } | null = null;

  if (achievements.length === 0) {
    bannerMessage = "Start by adding your activities and honors to the vault.";
    bannerCTA = { href: "/vault", label: "Add achievements" };
  } else if (targets.length === 0) {
    bannerMessage = "Good start. Select your target universities to unlock advisors.";
    bannerCTA = { href: "/universities", label: "Choose universities" };
  } else if (!reports.some((r) => r.status === "completed")) {
    bannerMessage = "You're ready. Generate your first university advisor.";
    bannerCTA = { href: "/universities", label: "Open advisor" };
  } else {
    const latest = reports.find((r) => r.status === "completed");
    if (latest) {
      bannerMessage = `Your latest ${latest.university.name} advisor is ready to review.`;
      bannerCTA = { href: `/reports/${latest.id}`, label: "View advisor" };
    }
  }

  // Quick action stage
  const quickActions = [];
  if (achievements.length === 0) {
    quickActions.push({
      href: "/vault",
      icon: Plus,
      iconBg: "bg-navy-50",
      iconColor: "text-navy-800",
      title: "Add your first achievement",
      subtitle: "Start building your vault",
    });
  }
  if (achievements.length > 0 && targets.length === 0) {
    quickActions.push({
      href: "/universities",
      icon: GraduationCap,
      iconBg: "bg-amber-50",
      iconColor: "text-amber-700",
      title: "Select target universities",
      subtitle: "Unlock university advisors",
    });
  }
  if (achievements.length > 0 && targets.length > 0) {
    quickActions.push({
      href: "/universities",
      icon: FileText,
      iconBg: "bg-emerald-50",
      iconColor: "text-emerald-700",
      title: "Open a new advisor",
      subtitle: `${targets.length} target ${targets.length === 1 ? "university" : "universities"} ready`,
    });
  }
  if (achievements.length > 0) {
    quickActions.push({
      href: "/vault",
      icon: BookOpen,
      iconBg: "bg-slate-100",
      iconColor: "text-slate-600",
      title: "Manage vault",
      subtitle: `${activities.length} activities · ${honors.length} honors`,
    });
  }

  if (isLoading) {
    return (
      <div className="p-8 max-w-5xl">
        {/* Banner skeleton */}
        <Skeleton className="mb-8 h-24 w-full rounded-2xl" />
        {/* Stat cards skeleton */}
        <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-xl border border-slate-100 bg-white p-5">
              <Skeleton className="mb-3 h-3 w-20" />
              <Skeleton className="mb-2 h-8 w-12" />
              <Skeleton className="h-2.5 w-28" />
            </div>
          ))}
        </div>
        {/* Bottom grid skeleton */}
        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-xl border border-slate-100 bg-white p-5">
            <Skeleton className="mb-4 h-4 w-28" />
            <div className="space-y-3">
              {Array.from({ length: 2 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full rounded-lg" />
              ))}
            </div>
          </div>
          <div className="rounded-xl border border-slate-100 bg-white p-5">
            <Skeleton className="mb-4 h-4 w-28" />
            <div className="space-y-3">
              {Array.from({ length: 2 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full rounded-lg" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl">

      {/* Welcome banner */}
      <div className="relative mb-8 overflow-hidden rounded-2xl border border-slate-200 bg-white px-7 py-6">
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 60% 80% at 100% 50%, rgba(20,21,84,0.04) 0%, transparent 60%)",
          }}
        />
        <div className="relative flex items-center justify-between gap-4">
          <div>
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              {new Date().toLocaleDateString("en-US", {
                weekday: "long",
                month: "long",
                day: "numeric",
              })}
            </p>
            <h1 className="text-2xl font-bold text-slate-900">
              {firstName ? `Welcome back, ${firstName}.` : "Welcome back."}
            </h1>
            <p className="mt-1 text-sm text-slate-500">{bannerMessage}</p>
          </div>
          {bannerCTA && (
            <Link href={bannerCTA.href} className="shrink-0">
              <Button
                size="sm"
                className="gap-1.5 bg-navy-950 text-white hover:bg-navy-900 active:scale-[0.97] transition-transform"
              >
                {bannerCTA.label}
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Stat cards */}
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

        {/* Profile completeness — circular ring */}
        <Card>
          <CardContent className="pt-5">
            <p className="mb-3 text-xs font-medium text-slate-500">Profile</p>
            <div className="flex items-center gap-3">
              <div className="relative shrink-0">
                <CircleProgress value={profilePct} size={52} strokeWidth={4} />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xs font-bold text-slate-900">{profilePct}%</span>
                </div>
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-slate-900">
                  {profilePct < 100
                    ? `${profileFields.length - filledCount} fields left`
                    : "Complete"}
                </p>
                {profilePct < 100 && (
                  <Link
                    href="/onboarding"
                    className="mt-0.5 flex items-center gap-1 text-xs text-navy-700 hover:underline"
                  >
                    Finish setup <ArrowRight className="h-3 w-3" />
                  </Link>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Achievements */}
        <Card>
          <CardContent className="pt-5">
            <p className="mb-3 text-xs font-medium text-slate-500">Achievements</p>
            <div className="text-3xl font-bold tabular-nums text-slate-900">
              {achievements.length}
            </div>
            <p className="mt-1 text-xs text-slate-500">
              {activities.length} activities · {honors.length} honors
            </p>
            {/* Activities-to-10 bar */}
            <div className="mt-2.5">
              <div className="mb-1 flex justify-between text-[10px] text-slate-400">
                <span>Activities</span>
                <span>{Math.min(activities.length, 10)}/10</span>
              </div>
              <div className="h-1 w-full rounded-full bg-slate-100">
                <div
                  className="h-1 rounded-full bg-navy-950 transition-all duration-700"
                  style={{ width: `${Math.min((activities.length / 10) * 100, 100)}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Target universities */}
        <Card>
          <CardContent className="pt-5">
            <p className="mb-3 text-xs font-medium text-slate-500">Target Universities</p>
            <div className="text-3xl font-bold tabular-nums text-slate-900">
              {targets.length}
            </div>
            <p className="mt-1 truncate text-xs text-slate-500">
              {targets.length > 0
                ? targets.map((t) => t.university.name.split(" ")[0]).join(", ")
                : "None selected"}
            </p>
            <Link
              href="/universities"
              className="mt-2.5 flex items-center gap-1 text-xs text-navy-700 hover:underline"
            >
              {targets.length > 0 ? "Manage" : "Add universities"}
              <ArrowRight className="h-3 w-3" />
            </Link>
          </CardContent>
        </Card>

        {/* Reports */}
        <Card>
          <CardContent className="pt-5">
            <p className="mb-3 text-xs font-medium text-slate-500">Advisors Generated</p>
            <div className="text-3xl font-bold tabular-nums text-slate-900">
              {reports.length}
            </div>
            <p className="mt-1 text-xs text-slate-500">
              {reports.filter((r) => r.status === "completed").length} completed
            </p>
            <Link
              href="/reports"
              className="mt-2.5 flex items-center gap-1 text-xs text-navy-700 hover:underline"
            >
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">

        {/* Quick actions */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Quick actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {quickActions.length > 0 ? (
              quickActions.map((action) => (
                <QuickActionItem key={action.href + action.title} {...action} />
              ))
            ) : (
              <p className="text-sm text-slate-500">
                Everything looks good — keep your vault up to date.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Recent reports */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-base">Recent advisors</CardTitle>
            <Link href="/reports" className="text-xs text-navy-700 hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent>
            {recentReports.length === 0 ? (
              <EmptyReports />
            ) : (
              <ul className="space-y-2">
                {recentReports.map((report) => (
                  <li key={report.id}>
                    <Link href={`/reports/${report.id}`}>
                      <div className="flex items-center justify-between rounded-lg p-3 transition-colors hover:bg-slate-50">
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-slate-900">
                            {report.university.name}
                          </p>
                          <p className="text-xs text-slate-400">{formatDate(report.created_at)}</p>
                        </div>
                        <div className="ml-3 shrink-0">
                          <ReportStatusBadge status={report.status} />
                        </div>
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
