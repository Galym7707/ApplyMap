"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { universitiesApi, targetsApi, reportsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { Search, Plus, CheckCircle, Loader2, FileText } from "lucide-react";
import type { University, TargetUniversity } from "@/types";
import { cn } from "@/lib/utils";

const PRESET_LABELS: Record<string, string> = {
  research_heavy: "Research-Heavy",
  leadership_heavy: "Leadership-Heavy",
  balanced_holistic: "Balanced Holistic",
  community_service_heavy: "Community Service",
};

const PRESET_COLORS: Record<string, string> = {
  research_heavy: "bg-blue-100 text-blue-800",
  leadership_heavy: "bg-purple-100 text-purple-800",
  balanced_holistic: "bg-slate-100 text-slate-800",
  community_service_heavy: "bg-emerald-100 text-emerald-800",
};

export default function UniversitiesPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [generatingId, setGeneratingId] = useState<string | null>(null);

  const { data: universitiesData, isLoading } = useQuery({
    queryKey: ["universities", search],
    queryFn: () => universitiesApi.list({ search }),
  });

  const { data: targetsData } = useQuery({
    queryKey: ["targets"],
    queryFn: () => targetsApi.list(),
  });

  const addTargetMutation = useMutation({
    mutationFn: (universityId: string) => targetsApi.add({ university_id: universityId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["targets"] });
      toast.success("University added to targets");
    },
    onError: () => toast.error("Already in targets or error adding"),
  });

  const universities: University[] = universitiesData?.data?.data ?? [];
  const targets: TargetUniversity[] = targetsData?.data?.data ?? [];
  const targetUniversityIds = new Set(targets.map((t) => t.university_id));

  const handleGenerateReport = async (university: University) => {
    setGeneratingId(university.id);
    try {
      const res = await reportsApi.generate(university.id);
      const reportId = res.data?.data?.id;
      toast.success("Report generated");
      if (reportId) {
        router.push(`/reports/${reportId}`);
      } else {
        router.push("/reports");
      }
    } catch {
      toast.error("Failed to generate report. Make sure you have achievements in your vault.");
    } finally {
      setGeneratingId(null);
    }
  };

  return (
    <div className="p-8 max-w-5xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Universities</h1>
        <p className="mt-1 text-sm text-slate-500">
          Select universities to target, then generate source-backed optimization reports.
        </p>
      </div>

      {/* Search */}
      <div className="relative mb-6 max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <Input
          placeholder="Search universities..."
          className="pl-9"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading ? (
        <div className="flex items-center gap-2 text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading universities...
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {universities.map((uni) => {
            const isTarget = targetUniversityIds.has(uni.id);
            const isGenerating = generatingId === uni.id;

            return (
              <div
                key={uni.id}
                className={cn(
                  "rounded-xl border bg-white p-5 transition-all",
                  isTarget ? "border-navy-300 ring-1 ring-navy-200" : "border-slate-200 hover:border-slate-300"
                )}
              >
                {/* Header */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div>
                    <h3 className="font-semibold text-slate-900 text-sm leading-snug">{uni.name}</h3>
                    <p className="text-xs text-slate-500 mt-0.5">{uni.country}</p>
                  </div>
                  {isTarget && (
                    <CheckCircle className="h-4 w-4 text-navy-700 shrink-0 mt-0.5" />
                  )}
                </div>

                {/* Preset badge */}
                <div className="mb-3">
                  <span
                    className={cn(
                      "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
                      PRESET_COLORS[uni.weight_preset]
                    )}
                  >
                    {PRESET_LABELS[uni.weight_preset]}
                  </span>
                </div>

                {/* Description */}
                {uni.short_description && (
                  <p className="text-xs text-slate-600 line-clamp-3 mb-4 leading-relaxed">
                    {uni.short_description}
                  </p>
                )}

                {/* Actions */}
                <div className="flex gap-2">
                  {!isTarget ? (
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1 gap-1.5 text-xs"
                      onClick={() => addTargetMutation.mutate(uni.id)}
                      disabled={addTargetMutation.isPending}
                    >
                      <Plus className="h-3.5 w-3.5" />
                      Add to targets
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      className="flex-1 gap-1.5 text-xs bg-navy-950 text-white hover:bg-navy-900"
                      onClick={() => handleGenerateReport(uni)}
                      disabled={isGenerating}
                    >
                      {isGenerating ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <FileText className="h-3.5 w-3.5" />
                      )}
                      {isGenerating ? "Generating..." : "Generate Report"}
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {universities.length === 0 && !isLoading && (
        <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center">
          <p className="text-slate-500">No universities found. Try a different search term.</p>
        </div>
      )}
    </div>
  );
}
