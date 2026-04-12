"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { reportsApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn, formatDate } from "@/lib/utils";
import { Shield, AlertTriangle, ArrowLeft, Download, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import type { ReportDetail, Recommendation, RewriteVariant, SourceReference } from "@/types";

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

function RewriteStudio({
  recommendation,
  variants,
}: {
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

  return (
    <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <button
        className="flex w-full items-center justify-between text-sm font-medium text-slate-700"
        onClick={() => setExpanded((e) => !e)}
      >
        Rewrite Studio
        {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
      </button>

      {expanded && (
        <div className="mt-3 space-y-3">
          {/* Style selector */}
          <div className="flex gap-2">
            {myVariants.map((v) => (
              <button
                key={v.style_mode}
                onClick={() => setSelectedStyle(v.style_mode)}
                className={cn(
                  "rounded-md px-3 py-1 text-xs font-medium transition-colors",
                  selectedStyle === v.style_mode
                    ? "bg-navy-950 text-white"
                    : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-100"
                )}
              >
                {v.style_mode.replace("_", " ")}
                {v.is_recommended && (
                  <span className="ml-1 text-amber-400">★</span>
                )}
              </button>
            ))}
          </div>

          {/* Original */}
          <div>
            <p className="mb-1.5 text-xs font-medium text-slate-500 uppercase tracking-wider">Original</p>
            <div className="rounded-md bg-white border border-slate-200 p-3 text-sm text-slate-700">
              {recommendation.achievement.description_raw || (
                <span className="italic text-slate-400">No description provided</span>
              )}
              <div className="mt-1 text-xs text-slate-400">
                {(recommendation.achievement.description_raw?.length ?? 0)} chars
              </div>
            </div>
          </div>

          {/* Rewritten */}
          {selected && (
            <div>
              <p className="mb-1.5 text-xs font-medium text-slate-500 uppercase tracking-wider">
                {selected.style_mode.replace("_", " ")} style
              </p>
              <div className="rounded-md bg-navy-50 border border-navy-200 p-3 text-sm text-navy-900">
                {selected.text}
                <div className="mt-2 flex items-center justify-between text-xs">
                  <span className={cn("font-medium", selected.character_count > 150 ? "text-red-600" : "text-emerald-700")}>
                    {selected.character_count}/150 chars
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
  const sourceRef = source;
  const isOfficial = sourceRef.policy_entry.source_type === "official";

  return (
    <div
      className={cn(
        "rounded-lg border p-4",
        isOfficial
          ? "border-emerald-200 bg-emerald-50"
          : "border-amber-200 bg-amber-50"
      )}
    >
      <div className="flex items-start gap-2.5 mb-2">
        {isOfficial ? (
          <Shield className="h-4 w-4 text-emerald-700 shrink-0 mt-0.5" />
        ) : (
          <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
        )}
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2 mb-0.5">
            <span
              className={cn(
                "text-xs font-semibold",
                isOfficial ? "text-emerald-800" : "text-amber-800"
              )}
            >
              {isOfficial ? "Official" : "Public Example"} — Tier {sourceRef.policy_entry.reliability_tier}
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
            {sourceRef.policy_entry.title}
          </p>
          {sourceRef.policy_entry.source_title && (
            <p className={cn("text-xs mt-0.5", isOfficial ? "text-emerald-700" : "text-amber-700")}>
              {sourceRef.policy_entry.source_title}
            </p>
          )}
        </div>
      </div>
      {sourceRef.policy_entry.excerpt && (
        <blockquote
          className={cn(
            "text-xs italic leading-relaxed border-l-2 pl-3 mt-2",
            isOfficial ? "border-emerald-300 text-emerald-800" : "border-amber-300 text-amber-800"
          )}
        >
          &ldquo;{sourceRef.policy_entry.excerpt}&rdquo;
        </blockquote>
      )}
      {sourceRef.policy_entry.source_url && (
        <a
          href={sourceRef.policy_entry.source_url}
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

export default function ReportDetailPage({ params }: { params: { id: string } }) {
  const [isExporting, setIsExporting] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["reports", params.id],
    queryFn: () => reportsApi.get(params.id),
  });

  const report: ReportDetail | undefined = data?.data?.data;

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const res = await reportsApi.export(params.id);
      const blob = new Blob([JSON.stringify(res.data.data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `sourcelock-report-${params.id}.json`;
      a.click();
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
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="p-8">
        <p className="text-red-600">Report not found or failed to load.</p>
        <Link href="/reports">
          <Button variant="outline" className="mt-4">Back to reports</Button>
        </Link>
      </div>
    );
  }

  const keepRecs = report.recommendations
    .filter((r) => r.recommendation_type === "keep" || r.recommendation_type === "rewrite")
    .sort((a, b) => (a.suggested_rank ?? 999) - (b.suggested_rank ?? 999));

  const removeRecs = report.recommendations.filter(
    (r) => r.recommendation_type === "remove" || r.recommendation_type === "merge"
  );

  const activities = keepRecs.filter((r) => r.achievement.type === "activity");
  const honors = keepRecs.filter((r) => r.achievement.type === "honor");

  const officialSources = report.source_references.filter(
    (s) => s.policy_entry.source_type === "official"
  );
  const publicSources = report.source_references.filter(
    (s) => s.policy_entry.source_type === "public_example"
  );

  return (
    <div className="p-8 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <Link href="/reports" className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 mb-4">
          <ArrowLeft className="h-4 w-4" />
          Back to reports
        </Link>

        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">{report.university.name}</h1>
            <p className="text-sm text-slate-500 mt-1">
              {report.university.country} ·{" "}
              {report.university.weight_preset.replace(/_/g, " ")} profile ·{" "}
              v{report.version_number} · Generated {formatDate(report.created_at)}
            </p>
          </div>
          <div className="flex items-center gap-2">
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
            <Button
              size="sm"
              variant="outline"
              onClick={handleExport}
              disabled={isExporting}
              className="gap-1.5"
            >
              {isExporting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
              Export
            </Button>
          </div>
        </div>

        {report.summary_text && (
          <div className="mt-4 rounded-lg border border-navy-200 bg-navy-50 px-4 py-3 text-sm text-navy-900">
            {report.summary_text}
          </div>
        )}
      </div>

      <Separator className="mb-6" />

      {/* Recommended Honors */}
      {honors.length > 0 && (
        <div className="mb-8">
          <h2 className="mb-4 text-base font-semibold text-slate-900">
            Recommended Honors ({honors.length}/5 spots)
          </h2>
          <div className="space-y-4">
            {honors.map((rec) => (
              <div
                key={rec.id}
                className="rounded-xl border border-slate-200 bg-white p-5"
              >
                <div className="flex items-start gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-navy-950 text-xs font-bold text-white">
                    {rec.suggested_rank}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <h3 className="font-medium text-slate-900 text-sm">{rec.achievement.title}</h3>
                      <Badge variant={REC_TYPE_COLORS[rec.recommendation_type]}>
                        {rec.recommendation_type}
                      </Badge>
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
                      <p className="text-xs text-slate-500 mb-2">{rec.achievement.organization_name}</p>
                    )}
                    {rec.rationale && (
                      <p className="text-sm text-slate-600">{rec.rationale}</p>
                    )}
                    <RewriteStudio recommendation={rec} variants={report.rewrite_variants} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Activities */}
      {activities.length > 0 && (
        <div className="mb-8">
          <h2 className="mb-4 text-base font-semibold text-slate-900">
            Recommended Activities ({activities.length}/10 spots)
          </h2>
          <div className="space-y-4">
            {activities.map((rec) => (
              <div
                key={rec.id}
                className="rounded-xl border border-slate-200 bg-white p-5"
              >
                <div className="flex items-start gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-navy-950 text-xs font-bold text-white">
                    {rec.suggested_rank}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <h3 className="font-medium text-slate-900 text-sm">{rec.achievement.title}</h3>
                      <Badge variant={REC_TYPE_COLORS[rec.recommendation_type]}>
                        {rec.recommendation_type}
                      </Badge>
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
                      <p className="text-xs text-slate-500 mb-2">{rec.achievement.organization_name}</p>
                    )}
                    {rec.rationale && (
                      <p className="text-sm text-slate-600">{rec.rationale}</p>
                    )}
                    <RewriteStudio recommendation={rec} variants={report.rewrite_variants} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Not recommended */}
      {removeRecs.length > 0 && (
        <div className="mb-8">
          <h2 className="mb-4 text-base font-semibold text-slate-900">
            Not recommended for this university
          </h2>
          <div className="space-y-2">
            {removeRecs.map((rec) => (
              <div
                key={rec.id}
                className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 flex items-center justify-between gap-4"
              >
                <div>
                  <p className="text-sm text-slate-600">{rec.achievement.title}</p>
                  {rec.rationale && (
                    <p className="text-xs text-slate-400 mt-0.5">{rec.rationale}</p>
                  )}
                </div>
                <Badge variant={REC_TYPE_COLORS[rec.recommendation_type]}>
                  {rec.recommendation_type}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      <Separator className="mb-6" />

      {/* Sources */}
      <div>
        <h2 className="mb-2 text-base font-semibold text-slate-900">Guidance Sources</h2>
        <p className="mb-4 text-sm text-slate-500">
          Every recommendation is grounded in these sources.
        </p>

        {officialSources.length > 0 && (
          <div className="mb-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Official Sources (Tier A)
            </h3>
            <div className="space-y-3">
              {officialSources.map((s) => (
                <SourceCard key={s.id} source={s} />
              ))}
            </div>
          </div>
        )}

        {publicSources.length > 0 && (
          <div>
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Public Examples (Tier B/C — not official guidance)
            </h3>
            <div className="space-y-3">
              {publicSources.map((s) => (
                <SourceCard key={s.id} source={s} />
              ))}
            </div>
            <p className="mt-3 rounded-md bg-amber-50 border border-amber-100 px-3 py-2 text-xs text-amber-700">
              Public example sources represent patterns observed in community discussions and admitted student profiles.
              They are not official university guidance. Always verify important decisions against official sources.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
