"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { achievementsApi, reportsApi, targetsApi, profileApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useAuth } from "@/hooks/useAuth";
import { BookOpen, FileText, GraduationCap, ArrowRight, Plus } from "lucide-react";
import { formatDate } from "@/lib/utils";
import type { Achievement, Report, TargetUniversity } from "@/types";

function ProfileCompleteness({ user }: { user: { full_name?: string; country?: string } }) {
  const { data: profileData } = useQuery({
    queryKey: ["profile"],
    queryFn: () => profileApi.get(),
  });

  const profile = profileData?.data?.data?.profile;
  const fields = [
    !!user.full_name,
    !!user.country,
    !!profile?.graduation_year,
    !!profile?.curriculum,
    !!profile?.intended_major,
    !!(profile?.sat_score || profile?.act_score || profile?.ielts_score || profile?.toefl_score),
  ];
  const filled = fields.filter(Boolean).length;
  const pct = Math.round((filled / fields.length) * 100);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-slate-500">Profile Completeness</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-between mb-2">
          <span className="text-3xl font-bold text-slate-900">{pct}%</span>
          {pct < 100 && (
            <Link href="/onboarding">
              <Button size="sm" variant="outline" className="text-xs">
                Complete profile
              </Button>
            </Link>
          )}
        </div>
        <Progress value={pct} className="h-1.5" />
        <p className="mt-2 text-xs text-slate-500">{filled} of {fields.length} fields filled in</p>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();

  const { data: achievementsData } = useQuery({
    queryKey: ["achievements"],
    queryFn: () => achievementsApi.list(),
  });

  const { data: reportsData } = useQuery({
    queryKey: ["reports"],
    queryFn: () => reportsApi.list(),
  });

  const { data: targetsData } = useQuery({
    queryKey: ["targets"],
    queryFn: () => targetsApi.list(),
  });

  const achievements: Achievement[] = achievementsData?.data?.data ?? [];
  const reports: Report[] = reportsData?.data?.data ?? [];
  const targets: TargetUniversity[] = targetsData?.data?.data ?? [];

  const activities = achievements.filter((a) => a.type === "activity");
  const honors = achievements.filter((a) => a.type === "honor");
  const recentReports = reports.slice(0, 3);

  return (
    <div className="p-8 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">
          Welcome back{user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}
        </h1>
        <p className="mt-1 text-slate-500">Here&rsquo;s where your application stands.</p>
      </div>

      {/* Stats row */}
      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {user && <ProfileCompleteness user={user} />}

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Achievements</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">{achievements.length}</div>
            <p className="text-xs text-slate-500 mt-1">
              {activities.length} activities · {honors.length} honors
            </p>
            <Link href="/vault" className="mt-3 flex items-center gap-1 text-xs text-navy-700 hover:underline">
              Manage vault <ArrowRight className="h-3 w-3" />
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Target Universities</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">{targets.length}</div>
            <p className="text-xs text-slate-500 mt-1">
              {targets.map((t) => t.university.name.split(" ")[0]).join(", ") || "None selected"}
            </p>
            <Link href="/universities" className="mt-3 flex items-center gap-1 text-xs text-navy-700 hover:underline">
              Add universities <ArrowRight className="h-3 w-3" />
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Reports Generated</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-900">{reports.length}</div>
            <p className="text-xs text-slate-500 mt-1">
              {reports.filter((r) => r.status === "completed").length} completed
            </p>
            <Link href="/reports" className="mt-3 flex items-center gap-1 text-xs text-navy-700 hover:underline">
              View reports <ArrowRight className="h-3 w-3" />
            </Link>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* CTAs */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Quick actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {achievements.length === 0 && (
              <Link href="/vault">
                <div className="flex items-center gap-3 rounded-lg border border-navy-200 bg-navy-50 p-3 hover:bg-navy-100 transition-colors cursor-pointer">
                  <Plus className="h-4 w-4 text-navy-800" />
                  <div>
                    <p className="text-sm font-medium text-navy-900">Add your first achievement</p>
                    <p className="text-xs text-navy-600">Start building your vault</p>
                  </div>
                </div>
              </Link>
            )}
            {achievements.length > 0 && targets.length === 0 && (
              <Link href="/universities">
                <div className="flex items-center gap-3 rounded-lg border border-navy-200 bg-navy-50 p-3 hover:bg-navy-100 transition-colors cursor-pointer">
                  <GraduationCap className="h-4 w-4 text-navy-800" />
                  <div>
                    <p className="text-sm font-medium text-navy-900">Select target universities</p>
                    <p className="text-xs text-navy-600">Unlock personalized reports</p>
                  </div>
                </div>
              </Link>
            )}
            {achievements.length > 0 && targets.length > 0 && (
              <Link href="/universities">
                <div className="flex items-center gap-3 rounded-lg border border-emerald-200 bg-emerald-50 p-3 hover:bg-emerald-100 transition-colors cursor-pointer">
                  <FileText className="h-4 w-4 text-emerald-800" />
                  <div>
                    <p className="text-sm font-medium text-emerald-900">Generate a new report</p>
                    <p className="text-xs text-emerald-600">You have {targets.length} target universities</p>
                  </div>
                </div>
              </Link>
            )}
          </CardContent>
        </Card>

        {/* Recent reports */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Recent reports</CardTitle>
            <Link href="/reports" className="text-xs text-navy-700 hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent>
            {recentReports.length === 0 ? (
              <p className="text-sm text-slate-500">No reports yet. Generate one from the Universities page.</p>
            ) : (
              <ul className="space-y-3">
                {recentReports.map((report) => (
                  <li key={report.id}>
                    <Link href={`/reports/${report.id}`}>
                      <div className="flex items-center justify-between rounded-lg p-3 hover:bg-slate-50 transition-colors">
                        <div>
                          <p className="text-sm font-medium text-slate-900">{report.university.name}</p>
                          <p className="text-xs text-slate-500">{formatDate(report.created_at)}</p>
                        </div>
                        <Badge
                          variant={
                            report.status === "completed"
                              ? "success"
                              : report.status === "failed"
                              ? "destructive"
                              : "info"
                          }
                        >
                          {report.status}
                        </Badge>
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
