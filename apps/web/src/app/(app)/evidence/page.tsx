"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { universitiesApi } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Shield, AlertTriangle, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import type { University, PolicyEntry } from "@/types";

const TIER_COLORS: Record<string, string> = {
  A: "bg-emerald-100 text-emerald-800 border-emerald-200",
  B: "bg-blue-100 text-blue-800 border-blue-200",
  C: "bg-amber-100 text-amber-800 border-amber-200",
  D: "bg-slate-100 text-slate-600 border-slate-200",
};

interface UniversityWithSources extends University {
  policy_entries?: PolicyEntry[];
}

export default function EvidencePage() {
  const [search, setSearch] = useState("");
  const [selectedUni, setSelectedUni] = useState<string | "all">("all");
  const [selectedType, setSelectedType] = useState<"all" | "official" | "public_example">("all");

  const { data: uniData } = useQuery({
    queryKey: ["universities"],
    queryFn: () => universitiesApi.list(),
  });

  const universities: University[] = uniData?.data?.data ?? [];

  // Fetch sources for each university
  const { data: sourcesData } = useQuery({
    queryKey: ["all-sources"],
    queryFn: async () => {
      const results = await Promise.all(
        universities.map(async (uni) => {
          const res = await universitiesApi.getSources(uni.id);
          return { uni, entries: res.data?.data ?? [] as PolicyEntry[] };
        })
      );
      return results;
    },
    enabled: universities.length > 0,
  });

  const allEntries: Array<{ entry: PolicyEntry; university: University }> =
    (sourcesData ?? []).flatMap(({ uni, entries }) =>
      entries.map((entry: PolicyEntry) => ({ entry, university: uni }))
    );

  const filtered = allEntries.filter(({ entry, university }) => {
    const matchUni = selectedUni === "all" || university.id === selectedUni;
    const matchType = selectedType === "all" || entry.source_type === selectedType;
    const matchSearch =
      !search ||
      entry.title.toLowerCase().includes(search.toLowerCase()) ||
      entry.content.toLowerCase().includes(search.toLowerCase()) ||
      university.name.toLowerCase().includes(search.toLowerCase());
    return matchUni && matchType && matchSearch;
  });

  return (
    <div className="p-8 max-w-5xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Evidence Library</h1>
        <p className="mt-1 text-sm text-slate-500">
          Browse all guidance sources used to generate recommendations.
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-48 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="Search sources..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select
          value={selectedUni}
          onChange={(e) => setSelectedUni(e.target.value)}
          className="flex h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
        >
          <option value="all">All universities</option>
          {universities.map((u) => (
            <option key={u.id} value={u.id}>{u.name}</option>
          ))}
        </select>

        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value as typeof selectedType)}
          className="flex h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
        >
          <option value="all">All types</option>
          <option value="official">Official only</option>
          <option value="public_example">Public examples only</option>
        </select>
      </div>

      <p className="mb-4 text-xs text-slate-400">{filtered.length} sources</p>

      <div className="space-y-4">
        {filtered.map(({ entry, university }) => {
          const isOfficial = entry.source_type === "official";

          return (
            <div
              key={entry.id}
              className={cn(
                "rounded-xl border p-5",
                isOfficial
                  ? "border-emerald-200 bg-emerald-50"
                  : "border-amber-100 bg-amber-50"
              )}
            >
              <div className="flex items-start gap-3">
                {isOfficial ? (
                  <Shield className="h-4 w-4 text-emerald-700 shrink-0 mt-1" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-1" />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1.5">
                    <span className="text-sm font-semibold text-slate-900">{entry.title}</span>
                    <span
                      className={cn(
                        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium",
                        TIER_COLORS[entry.reliability_tier]
                      )}
                    >
                      Tier {entry.reliability_tier}
                    </span>
                    <Badge variant={isOfficial ? "success" : "warning"} className="text-xs">
                      {isOfficial ? "Official" : "Public Example"}
                    </Badge>
                  </div>

                  <p className="text-xs text-slate-500 mb-2">
                    {university.name}
                    {entry.source_title && ` · ${entry.source_title}`}
                  </p>

                  {entry.excerpt && (
                    <blockquote
                      className={cn(
                        "mb-2 border-l-2 pl-3 text-sm italic",
                        isOfficial ? "border-emerald-300 text-emerald-800" : "border-amber-300 text-amber-800"
                      )}
                    >
                      &ldquo;{entry.excerpt}&rdquo;
                    </blockquote>
                  )}

                  <p className="text-sm text-slate-600 leading-relaxed line-clamp-3">
                    {entry.content}
                  </p>

                  {entry.source_url && (
                    <a
                      href={entry.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={cn(
                        "mt-2 block text-xs hover:underline",
                        isOfficial ? "text-emerald-700" : "text-amber-700"
                      )}
                    >
                      View original source →
                    </a>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {filtered.length === 0 && (
          <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center">
            <p className="text-slate-500">No sources match your filters.</p>
          </div>
        )}
      </div>
    </div>
  );
}
