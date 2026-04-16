"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, FileSearch, GraduationCap, Loader2, ReceiptText, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { profileApi, reportsApi } from "@/lib/api";
import { cn, formatDate } from "@/lib/utils";
import type { ReportDetail, ReportStatus } from "@/types";

const STATUS_STEPS = {
  pending: [
    "Loading university record",
    "Reading major and funding constraints",
    "Preparing advisor structure",
  ],
  processing: [
    "Matching university with your intended major",
    "Building research-program shortlist",
    "Preparing funding and action plan",
  ],
  completed: [],
  failed: [],
} satisfies Record<ReportStatus, string[]>;

function StatusBadge({ status }: { status: ReportStatus }) {
  const variants = {
    completed: "success",
    pending: "info",
    processing: "info",
    failed: "destructive",
  } as const;

  return <Badge variant={variants[status]}>{status}</Badge>;
}

function InfoCard({
  icon: Icon,
  title,
  children,
}: {
  icon: typeof GraduationCap;
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-2 text-slate-900">
        <Icon className="h-4 w-4 text-navy-700" />
        <h2 className="text-sm font-semibold">{title}</h2>
      </div>
      <div className="mt-4">{children}</div>
    </div>
  );
}

export default function ReportDetailPage({ params }: { params: { id: string } }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["reports", params.id],
    queryFn: () => reportsApi.get(params.id),
  });

  const { data: profileData } = useQuery({
    queryKey: ["profile"],
    queryFn: () => profileApi.get(),
  });

  const report: ReportDetail | undefined = data?.data?.data;
  const profile = profileData?.data?.data?.profile;

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="p-8">
        <p className="text-red-600">Advisor not found or failed to load.</p>
        <Link href="/reports">
          <Button variant="outline" className="mt-4">Back to advisors</Button>
        </Link>
      </div>
    );
  }

  const advisor = report.advisor_snapshot_json;
  const intendedMajor = advisor?.target_major || profile?.intended_major || report.university.major_strengths?.[0] || "your target major";
  const inProgress = report.status === "pending" || report.status === "processing";
  const isLegacyCompletedReport = report.status === "completed" && !advisor;

  return (
    <div className="relative overflow-hidden bg-[#f7f5ef] px-4 py-8 sm:px-6 lg:px-8">
      <div className="absolute inset-x-0 top-0 h-72 bg-[radial-gradient(circle_at_top_left,_rgba(33,39,143,0.14),_transparent_42%),radial-gradient(circle_at_top_right,_rgba(16,185,129,0.08),_transparent_38%)]" />
      <div className="relative mx-auto max-w-6xl">
        <section className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur sm:p-8">
          <Link href="/reports" className="mb-4 inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700">
            <ArrowLeft className="h-4 w-4" />
            Back to advisors
          </Link>

          <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
            <div className="max-w-3xl">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                University advisor
              </p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">
                {report.university.name}
              </h1>
              <p className="mt-3 text-sm leading-relaxed text-slate-500">
                {advisor?.subtitle ?? "This report was generated before versioned advisor snapshots were stored."}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Badge variant="outline">{report.university.country}</Badge>
                <Badge variant="outline">{intendedMajor}</Badge>
                {report.university.full_ride_possible && <Badge variant="success">Full-funding route visible</Badge>}
                {report.university.is_common_app && <Badge variant="info">Common App</Badge>}
              </div>
            </div>

            <div className="rounded-[28px] border border-slate-200 bg-slate-50 px-5 py-4 xl:min-w-[280px]">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Status</p>
                  <p className="mt-1 text-sm font-medium text-slate-900">
                    Built {formatDate(report.created_at)} • v{report.version_number}
                  </p>
                </div>
                <StatusBadge status={report.status} />
              </div>
              <p className="mt-3 text-xs leading-relaxed text-slate-500">
                {advisor?.report_note ?? report.summary_text ?? "This view is intentionally university-first: school, major, funding route, and next moves."}
              </p>
            </div>
          </div>
        </section>

        {inProgress && (
          <section className="mt-6 rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)] backdrop-blur sm:p-8">
            <div className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 animate-spin text-navy-700" />
              <div>
                <h2 className="text-sm font-semibold text-slate-900">Building your university advisor</h2>
                <p className="text-sm text-slate-500">You can see what the app is doing right now.</p>
              </div>
            </div>
            <div className="mt-5 grid gap-3 md:grid-cols-3">
              {STATUS_STEPS[report.status].map((step, index) => (
                <div key={step} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                  <p className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Step {index + 1}</p>
                  <p className="mt-2 text-sm font-medium text-slate-900">{step}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {isLegacyCompletedReport && (
          <section className="mt-6 rounded-[32px] border border-amber-200 bg-amber-50 p-6 text-sm text-amber-800">
            This is a legacy report created before advisor snapshots were stored. Regenerate the advisor from the Universities page to lock a versioned university-specific snapshot.
          </section>
        )}

        {!inProgress && report.status === "completed" && advisor && (
          <>
            <section className="mt-6 grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
              <InfoCard icon={Sparkles} title="What matters for this university">
                <div className="space-y-3">
                  {advisor.focus_areas.map((item) => (
                    <div key={item} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm leading-relaxed text-slate-700">
                      {item}
                    </div>
                  ))}
                </div>
              </InfoCard>

              <InfoCard icon={ReceiptText} title="Funding route for this target">
                <div className="space-y-3">
                  {advisor.funding_plan.map((item) => (
                    <div key={item} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm leading-relaxed text-slate-700">
                      {item}
                    </div>
                  ))}
                </div>
              </InfoCard>
            </section>

            <section className="mt-6 rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)] backdrop-blur sm:p-8">
              <div className="flex items-center gap-2 text-slate-900">
                <FileSearch className="h-4 w-4 text-navy-700" />
                <h2 className="text-lg font-semibold">Research programs to target</h2>
              </div>
              <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-500">
                These are named programs worth prioritizing so the advisor sounds like a real admissions strategy, not a generic dashboard summary.
              </p>

              <div className="mt-5 grid gap-4 lg:grid-cols-2">
                {advisor.research_programs.map((program) => (
                  <div key={program.name} className="rounded-[28px] border border-slate-200 bg-slate-50/80 p-5">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-base font-semibold text-slate-900">{program.name}</h3>
                        <p className="mt-2 text-sm leading-relaxed text-slate-600">{program.why_it_matters}</p>
                      </div>
                      <span
                        className={cn(
                          "inline-flex rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.12em]",
                          program.priority === "full-funding" && "bg-emerald-100 text-emerald-800",
                          program.priority === "scholarship" && "bg-amber-100 text-amber-800",
                          program.priority === "verify" && "bg-slate-200 text-slate-700"
                        )}
                      >
                        {program.priority === "full-funding" ? "Funding first" : program.priority === "scholarship" ? "Scholarship route" : "Verify"}
                      </span>
                    </div>
                    <div className="mt-4 rounded-2xl border border-white bg-white px-4 py-4 text-sm leading-relaxed text-slate-700">
                      {program.funding_note}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="mt-6 rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)] backdrop-blur sm:p-8">
              <div className="flex items-center gap-2 text-slate-900">
                <CheckCircle2 className="h-4 w-4 text-navy-700" />
                <h2 className="text-lg font-semibold">What to do next</h2>
              </div>
              <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                {advisor.action_plan.map((step, index) => (
                  <div key={step.title} className="rounded-[28px] border border-slate-200 bg-slate-50/80 p-5">
                    <p className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Action {index + 1}</p>
                    <h3 className="mt-2 text-sm font-semibold text-slate-900">{step.title}</h3>
                    <p className="mt-3 text-sm leading-relaxed text-slate-600">{step.detail}</p>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}

        {report.status === "failed" && (
          <section className="mt-6 rounded-[32px] border border-red-200 bg-red-50 p-6 text-sm text-red-700">
            The advisor failed to build. Open the university list and generate it again.
          </section>
        )}
      </div>
    </div>
  );
}
