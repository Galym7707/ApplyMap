"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { reportsApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";
import { FileText, ArrowRight, Loader2 } from "lucide-react";
import type { Report } from "@/types";

function StatusBadge({ status }: { status: Report["status"] }) {
  const variants = {
    completed: "success",
    pending: "info",
    processing: "info",
    failed: "destructive",
  } as const;
  return <Badge variant={variants[status]}>{status}</Badge>;
}

export default function ReportsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: () => reportsApi.list(),
  });

  const reports: Report[] = data?.data?.data ?? [];

  return (
    <div className="p-8 max-w-4xl">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">My Reports</h1>
          <p className="mt-1 text-sm text-slate-500">
            Optimization reports generated for your target universities.
          </p>
        </div>
        <Link href="/universities">
          <Button className="bg-navy-950 text-white hover:bg-navy-900 gap-2">
            <FileText className="h-4 w-4" />
            New report
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="flex items-center gap-2 text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading reports...
        </div>
      ) : reports.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-16 text-center">
          <FileText className="h-8 w-8 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-600 font-medium mb-1">No reports yet</p>
          <p className="text-slate-500 text-sm mb-4">
            Add achievements to your vault, select a university, and generate your first report.
          </p>
          <Link href="/universities">
            <Button size="sm" className="bg-navy-950 text-white hover:bg-navy-900">
              Go to Universities
            </Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {reports.map((report) => (
            <Link key={report.id} href={`/reports/${report.id}`}>
              <div className="rounded-xl border border-slate-200 bg-white p-5 hover:border-slate-300 hover:shadow-sm transition-all cursor-pointer">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2.5 mb-1">
                      <h3 className="font-semibold text-slate-900">{report.university.name}</h3>
                      <StatusBadge status={report.status} />
                      <span className="text-xs text-slate-400">v{report.version_number}</span>
                    </div>
                    <p className="text-xs text-slate-500">
                      {report.university.country} ·{" "}
                      {report.university.weight_preset.replace(/_/g, " ")} profile ·{" "}
                      Generated {formatDate(report.created_at)}
                    </p>
                    {report.summary_text && (
                      <p className="mt-2 text-sm text-slate-600 line-clamp-2">
                        {report.summary_text}
                      </p>
                    )}
                  </div>
                  <ArrowRight className="h-4 w-4 text-slate-400 shrink-0 mt-1" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
