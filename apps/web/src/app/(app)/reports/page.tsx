"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, FileText, Loader2 } from "lucide-react";
import { reportsApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";
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
    <div className="max-w-4xl p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">University Advisors</h1>
          <p className="mt-1 text-sm text-slate-500">
            University-first guidance for each target: major fit, funding route, and next steps.
          </p>
        </div>
        <Link href="/universities">
          <Button className="gap-2 bg-navy-950 text-white hover:bg-navy-900">
            <FileText className="h-4 w-4" />
            New advisor
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="flex items-center gap-2 text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading advisors...
        </div>
      ) : reports.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-16 text-center">
          <FileText className="mx-auto mb-3 h-8 w-8 text-slate-300" />
          <p className="mb-1 font-medium text-slate-600">No advisors yet</p>
          <p className="mb-4 text-sm text-slate-500">
            Pick a university and generate your first advisor.
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
              <div className="cursor-pointer rounded-xl border border-slate-200 bg-white p-5 transition-all hover:border-slate-300 hover:shadow-sm">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="mb-1 flex items-center gap-2.5">
                      <h3 className="font-semibold text-slate-900">{report.university.name}</h3>
                      <StatusBadge status={report.status} />
                      <span className="text-xs text-slate-400">v{report.version_number}</span>
                    </div>
                    <p className="text-xs text-slate-500">
                      {report.university.country} • university advisor • Generated {formatDate(report.created_at)}
                    </p>
                  </div>
                  <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-slate-400" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
