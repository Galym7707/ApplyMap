"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Download,
  FileSearch,
  GraduationCap,
  Loader2,
  ReceiptText,
  Shield,
  Sparkles,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { profileApi, reportsApi } from "@/lib/api";
import { cn, formatDate } from "@/lib/utils";
import { toast } from "sonner";
import type {
  Recommendation,
  ReportDetail,
  ReportStatus,
  RewriteVariant,
  SourceReference,
} from "@/types";

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

const REC_TYPE_COLORS = {
  keep: "success",
  rewrite: "warning",
  remove: "destructive",
  merge: "info",
  reorder: "secondary",
} as const;

const CONFIDENCE_COLORS = {
  high: "bg-emerald-100 text-emerald-800",
  medium: "bg-blue-100 text-blue-800",
  low: "bg-slate-100 text-slate-600",
};

function StatusBadge({ status }: { status: ReportStatus }) {
  const variants = {
    completed: "success",
    pending: "info",
    processing: "info",
    failed: "destructive",
  } as const;

  return <Badge variant={variants[status]}>{status}</Badge>;
}

function getRewriteFormat(report: ReportDetail, achievementType: string) {
  const haystack = [report.university.name, report.university.country, report.university.application_system]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  if (haystack.includes("korea") || ["kaist", "unist", "postech", "yonsei"].some((token) => haystack.includes(token))) {
    if (haystack.includes("kaist")) {
      return { label: "KAIST Apply", limit: 200, unit: "English bytes/chars" };
    }
    return { label: "Korean university application", limit: 300, unit: "English bytes/chars" };
  }

  if (achievementType === "honor") {
    return { label: "Common App honor", limit: 100, unit: "chars" };
  }

  return { label: "Common App activity", limit: 150, unit: "chars" };
}

function RewriteStudio({
  report,
  recommendation,
  variants,
}: {
  report: ReportDetail;
  recommendation: Recommendation;
  variants: RewriteVariant[];
}) {
  const [selectedStyle, setSelectedStyle] = useState(
    variants.find((v) => v.is_recommended)?.style_mode ?? variants[0]?.style_mode
  );
  const [expanded, setExpanded] = useState(false);

  const myVariants = variants.filter((v) => v.achievement_id === recommendation.achievement_id);
  if (myVariants.length === 0) return null;

  const selected = myVariants.find((v) => v.style_mode === selectedStyle) ?? myVariants[0];
  const rewriteFormat = getRewriteFormat(report, recommendation.achievement.type);

  return (
    <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <button
        className="flex w-full items-center justify-between text-sm font-medium text-slate-700"
        onClick={() => setExpanded((current) => !current)}
      >
        Rewrite Studio
        {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
      </button>

      {expanded && (
        <div className="mt-3 space-y-3">
          <div className="flex gap-2">
            {myVariants.map((variant) => (
              <button
                key={variant.style_mode}
                onClick={() => setSelectedStyle(variant.style_mode)}
                className={cn(
                  "rounded-md border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100",
                  selectedStyle === variant.style_mode && "border-navy-950 bg-navy-950 text-white hover:bg-navy-900"
                )}
              >
                {variant.style_mode.replace("_", " ")}
                {variant.is_recommended && (
                  <span className="ml-1 text-amber-500">{selectedStyle === variant.style_mode ? "best" : "recommended"}</span>
                )}
              </button>
            ))}
          </div>

          <div>
            <p className="mb-1.5 text-xs font-medium uppercase tracking-wider text-slate-500">Original</p>
            <div className="rounded-md border border-slate-200 bg-white p-3 text-sm text-slate-700">
              {recommendation.achievement.description_raw || (
                <span className="italic text-slate-400">No description provided</span>
              )}
              <div className="mt-1 text-xs text-slate-400">
                {(recommendation.achievement.description_raw?.length ?? 0)} chars
              </div>
            </div>
          </div>

          {selected && (
            <div>
              <p className="mb-1.5 text-xs font-medium uppercase tracking-wider text-slate-500">
                {selected.style_mode.replace("_", " ")} style
              </p>
              <p className="mb-2 text-xs text-slate-500">Target: {rewriteFormat.label}</p>
              <div className="rounded-md border border-navy-200 bg-navy-50 p-3 text-sm text-navy-900">
                {selected.text}
                <div className="mt-2 flex items-center justify-between text-xs">
                  <span className={cn("font-medium", selected.character_count > rewriteFormat.limit ? "text-red-600" : "text-emerald-700")}>
                    {selected.character_count}/{rewriteFormat.limit} {rewriteFormat.unit}
                  </span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(selected.text);
                      toast.success("Copied to clipboard");
                    }}
                    className="text-navy-700 hover:underline"
                  >
                    Copy
                  </button>
                </div>
              </div>
              {selected.explanation && (
                <p className="mt-1.5 text-xs text-slate-500">{selected.explanation}</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SourceCard({ source }: { source: SourceReference }) {
  const isOfficial = source.policy_entry.source_type === "official";

  return (
    <div
      className={cn(
        "rounded-lg border p-4",
        isOfficial ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50"
      )}
    >
      <div className="mb-2 flex items-start gap-2.5">
        {isOfficial ? (
          <Shield className="mt-0.5 h-4 w-4 shrink-0 text-emerald-700" />
        ) : (
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
        )}
        <div className="flex-1">
          <div className="mb-0.5 flex flex-wrap items-center gap-2">
            <span
              className={cn(
                "text-xs font-semibold",
                isOfficial ? "text-emerald-800" : "text-amber-800"
              )}
            >
              {isOfficial ? "Official" : "Public Example"} — Tier {source.policy_entry.reliability_tier}
            </span>
            {!isOfficial && (
              <span className="text-xs text-amber-600">(not official university guidance)</span>
            )}
          </div>
          <p
            className={cn(
              "text-sm font-medium",
              isOfficial ? "text-emerald-900" : "text-amber-900"
            )}
          >
            {source.policy_entry.title}
          </p>
          {source.policy_entry.source_title && (
            <p className={cn("mt-0.5 text-xs", isOfficial ? "text-emerald-700" : "text-amber-700")}>
              {source.policy_entry.source_title}
            </p>
          )}
        </div>
      </div>
      {source.policy_entry.excerpt && (
        <blockquote
          className={cn(
            "mt-2 border-l-2 pl-3 text-xs italic leading-relaxed",
            isOfficial ? "border-emerald-300 text-emerald-800" : "border-amber-300 text-amber-800"
          )}
        >
          &ldquo;{source.policy_entry.excerpt}&rdquo;
        </blockquote>
      )}
      {source.policy_entry.source_url && (
        <a
          href={source.policy_entry.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className={cn("mt-2 block text-xs hover:underline", isOfficial ? "text-emerald-700" : "text-amber-700")}
        >
          View source →
        </a>
      )}
    </div>
  );
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
  const [isExporting, setIsExporting] = useState(false);

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

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const res = await reportsApi.export(params.id);
      const blob = new Blob([JSON.stringify(res.data.data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `applymap-report-${params.id}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
      toast.success("Report exported");
    } catch {
      toast.error("Export failed");
    } finally {
      setIsExporting(false);
    }
  };

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
  const summaryText = report.summary_text?.trim();
  const intendedMajor = advisor?.target_major || profile?.intended_major || report.university.major_strengths?.[0] || "your target major";
  const inProgress = report.status === "pending" || report.status === "processing";
  const isLegacyCompletedReport = report.status === "completed" && !advisor;
  const keepRecs = report.recommendations
    .filter((rec) => rec.recommendation_type === "keep" || rec.recommendation_type === "rewrite")
    .sort((a, b) => (a.suggested_rank ?? 999) - (b.suggested_rank ?? 999));
  const removeRecs = report.recommendations.filter(
    (rec) => rec.recommendation_type === "remove" || rec.recommendation_type === "merge"
  );
  const activities = keepRecs.filter((rec) => rec.achievement.type === "activity");
  const honors = keepRecs.filter((rec) => rec.achievement.type === "honor");
  const officialSources = report.source_references.filter((source) => source.policy_entry.source_type === "official");
  const publicSources = report.source_references.filter((source) => source.policy_entry.source_type === "public_example");

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
                {advisor?.subtitle ?? summaryText ?? "This report was generated before versioned advisor snapshots were stored."}
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
              <Button
                size="sm"
                variant="outline"
                onClick={handleExport}
                disabled={isExporting}
                className="mt-3 w-full gap-1.5"
              >
                {isExporting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
                Export
              </Button>
              <p className="mt-3 text-xs leading-relaxed text-slate-500">
                {advisor?.report_note ?? summaryText ?? "This view is intentionally university-first: school, major, funding route, and next moves."}
              </p>
            </div>
          </div>
        </section>

        {!!summaryText && (
          <section className="mt-6 rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)] backdrop-blur sm:p-8">
            <div className="flex items-center gap-2 text-slate-900">
              <ReceiptText className="h-4 w-4 text-navy-700" />
              <h2 className="text-lg font-semibold">Stored report summary</h2>
            </div>
            <p className="mt-4 max-w-4xl text-sm leading-relaxed text-slate-600">
              {summaryText}
            </p>
          </section>
        )}

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
          <>
            <section className="mt-6 rounded-[32px] border border-amber-200 bg-amber-50 p-6 text-sm text-amber-800">
              This is a legacy report created before advisor snapshots were stored. Regenerate the advisor from the Universities page to lock a versioned university-specific snapshot.
            </section>

            {honors.length > 0 && (
              <section className="mt-6 rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)] backdrop-blur sm:p-8">
                <h2 className="text-lg font-semibold text-slate-900">Recommended honors</h2>
                <div className="mt-5 space-y-4">
                  {honors.map((rec) => (
                    <div key={rec.id} className="rounded-[28px] border border-slate-200 bg-slate-50/80 p-5">
                      <div className="flex items-start gap-3">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-navy-950 text-xs font-bold text-white">
                          {rec.suggested_rank}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="mb-1 flex flex-wrap items-center gap-2">
                            <h3 className="text-sm font-medium text-slate-900">{rec.achievement.title}</h3>
                            <Badge variant={REC_TYPE_COLORS[rec.recommendation_type]}>{rec.recommendation_type}</Badge>
                            <span
                              className={cn(
                                "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
                                CONFIDENCE_COLORS[rec.confidence_label]
                              )}
                            >
                              {rec.confidence_label} confidence
                            </span>
                          </div>
                          {rec.achievement.organization_name && (
                            <p className="mb-2 text-xs text-slate-500">{rec.achievement.organization_name}</p>
                          )}
                          {rec.rationale && <p className="text-sm text-slate-600">{rec.rationale}</p>}
                          <RewriteStudio report={report} recommendation={rec} variants={report.rewrite_variants} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {activities.length > 0 && (
              <section className="mt-6 rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)] backdrop-blur sm:p-8">
                <h2 className="text-lg font-semibold text-slate-900">Recommended activities</h2>
                <div className="mt-5 space-y-4">
                  {activities.map((rec) => (
                    <div key={rec.id} className="rounded-[28px] border border-slate-200 bg-slate-50/80 p-5">
                      <div className="flex items-start gap-3">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-navy-950 text-xs font-bold text-white">
                          {rec.suggested_rank}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="mb-1 flex flex-wrap items-center gap-2">
                            <h3 className="text-sm font-medium text-slate-900">{rec.achievement.title}</h3>
                            <Badge variant={REC_TYPE_COLORS[rec.recommendation_type]}>{rec.recommendation_type}</Badge>
                            <span
                              className={cn(
                                "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
                                CONFIDENCE_COLORS[rec.confidence_label]
                              )}
                            >
                              {rec.confidence_label} confidence
                            </span>
                          </div>
                          {rec.achievement.organization_name && (
                            <p className="mb-2 text-xs text-slate-500">{rec.achievement.organization_name}</p>
                          )}
                          {rec.rationale && <p className="text-sm text-slate-600">{rec.rationale}</p>}
                          <RewriteStudio report={report} recommendation={rec} variants={report.rewrite_variants} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {removeRecs.length > 0 && (
              <section className="mt-6 rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)] backdrop-blur sm:p-8">
                <h2 className="text-lg font-semibold text-slate-900">Not recommended for this university</h2>
                <div className="mt-5 space-y-2">
                  {removeRecs.map((rec) => (
                    <div
                      key={rec.id}
                      className="flex items-center justify-between gap-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3"
                    >
                      <div>
                        <p className="text-sm text-slate-600">{rec.achievement.title}</p>
                        {rec.rationale && <p className="mt-0.5 text-xs text-slate-400">{rec.rationale}</p>}
                      </div>
                      <Badge variant={REC_TYPE_COLORS[rec.recommendation_type]}>{rec.recommendation_type}</Badge>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {!!(officialSources.length || publicSources.length) && (
              <section className="mt-6 rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)] backdrop-blur sm:p-8">
                <h2 className="text-lg font-semibold text-slate-900">Guidance sources</h2>
                <p className="mt-2 text-sm text-slate-500">Every legacy recommendation is grounded in these sources.</p>

                {officialSources.length > 0 && (
                  <div className="mt-5">
                    <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Official sources (Tier A)
                    </h3>
                    <div className="space-y-3">
                      {officialSources.map((source) => (
                        <SourceCard key={source.id} source={source} />
                      ))}
                    </div>
                  </div>
                )}

                {publicSources.length > 0 && (
                  <div className="mt-5">
                    <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Public examples (Tier B/C)
                    </h3>
                    <div className="space-y-3">
                      {publicSources.map((source) => (
                        <SourceCard key={source.id} source={source} />
                      ))}
                    </div>
                    <p className="mt-3 rounded-md border border-amber-100 bg-amber-50 px-3 py-2 text-xs text-amber-700">
                      Public example sources represent patterns observed in community discussions and admitted student profiles.
                      They are not official university guidance. Always verify important decisions against official sources.
                    </p>
                  </div>
                )}
              </section>
            )}
          </>
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
