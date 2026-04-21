"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { universitiesApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Loader2, Search, Sparkles } from "lucide-react";
import type { UniversityAdvisorPlan, UniversityAdvisorSource } from "@/types";

type AdvisorResponse = {
  university_name: string;
  sources: UniversityAdvisorSource[];
  plan: UniversityAdvisorPlan;
};

export default function AdvisorPage() {
  const [universityName, setUniversityName] = useState("");
  const [intendedMajor, setIntendedMajor] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AdvisorResponse | null>(null);

  const advisorMutation = useMutation({
    mutationFn: () =>
      universitiesApi.advisorPlan({
        university_name: universityName.trim(),
        intended_major: intendedMajor.trim(),
      }),
    onSuccess: (response) => {
      setError(null);
      setResult(response.data?.data ?? null);
    },
    onError: (err: unknown) => {
      const detail =
        typeof err === "object" && err && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null;
      setResult(null);
      setError(detail ?? "Advisor search failed. Check the backend search configuration.");
    },
  });
  const canSearch = universityName.trim().length >= 2 && intendedMajor.trim().length >= 2;

  return (
    <div className="bg-[#f7f5ef] px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">University advisor</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">Ask about one target school</h1>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-500">
            Enter one university and one major. The advisor returns exams, concrete profile moves, low-value work to avoid, and exact programs when sources confirm them.
          </p>
        </div>

        <section className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)]">
          <div className="grid gap-4 lg:grid-cols-[1fr_1fr_auto] lg:items-end">
            <div className="space-y-2">
              <Label>University</Label>
              <Input
                value={universityName}
                onChange={(event) => setUniversityName(event.target.value)}
                placeholder="e.g. NYU Abu Dhabi, University of Toronto, KAIST"
                className="h-11 rounded-xl"
              />
            </div>
            <div className="space-y-2">
              <Label>Intended major *</Label>
              <Input
                value={intendedMajor}
                onChange={(event) => setIntendedMajor(event.target.value)}
                placeholder="e.g. Computer Science"
                className="h-11 rounded-xl"
                required
              />
            </div>
            <Button
              className="h-11 gap-2 bg-navy-950 text-white hover:bg-navy-900"
              disabled={advisorMutation.isPending || !canSearch}
              onClick={() => advisorMutation.mutate()}
            >
              {advisorMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              Search and analyze
            </Button>
          </div>
          {error && (
            <p className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              {error}
            </p>
          )}
        </section>

        {result && (
          <section className="mt-6 rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)]">
            <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-navy-700" />
                <h2 className="text-lg font-semibold text-slate-900">
                  Action plan for {result.university_name}
                </h2>
              </div>
              <Badge variant="info" className="w-fit">
                {intendedMajor.trim()}
              </Badge>
            </div>

            <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
              <div className="min-w-0 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <h3 className="text-sm font-semibold text-slate-900">Exams to prioritize</h3>
                <div className="mt-3 space-y-3">
                  {result.plan.exams_to_prioritize.length ? result.plan.exams_to_prioritize.map((item) => (
                    <div key={`${item.exam}-${item.priority}`} className="min-w-0 rounded-xl border border-slate-200 bg-white px-4 py-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="min-w-0 break-words text-sm font-medium text-slate-900">{item.exam}</p>
                        <Badge variant={item.priority === "high" ? "success" : item.priority === "medium" ? "warning" : "outline"}>{item.priority}</Badge>
                      </div>
                      <p className="mt-2 break-words text-xs leading-relaxed text-slate-600">{item.why}</p>
                    </div>
                  )) : <p className="text-sm text-slate-500">No source-backed exam priority was returned.</p>}
                </div>
              </div>

              <div className="min-w-0 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <h3 className="text-sm font-semibold text-slate-900">Exact programs to target</h3>
                <div className="mt-3 grid gap-3 lg:grid-cols-2">
                  {result.plan.research_or_summer_programs.length ? result.plan.research_or_summer_programs.map((item) => (
                    <div key={item.name} className="min-w-0 rounded-xl border border-slate-200 bg-white px-4 py-3">
                      <p className="break-words text-sm font-medium text-slate-900">{item.name}</p>
                      <p className="mt-2 break-words text-xs leading-relaxed text-slate-600">{item.why_it_helps}</p>
                      {item.source_url && (
                        <a href={item.source_url} target="_blank" rel="noreferrer" className="mt-2 inline-flex text-xs font-medium text-navy-700 underline underline-offset-2">
                          Official page
                        </a>
                      )}
                    </div>
                  )) : (
                    <p className="text-sm text-slate-500">
                      No exact named program was confirmed from the current official sources.
                    </p>
                  )}
                </div>
              </div>

              <div className="min-w-0 rounded-2xl border border-slate-200 bg-white p-4 xl:col-span-2">
                <h3 className="text-sm font-semibold text-slate-900">Profile moves that matter</h3>
                <ul className="mt-3 grid gap-2 md:grid-cols-2">
                  {result.plan.profile_actions.length ? result.plan.profile_actions.map((item) => (
                    <li key={item} className="break-words rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-relaxed text-slate-700">{item}</li>
                  )) : <li className="text-sm text-slate-500">No profile actions were returned.</li>}
                </ul>
              </div>

              <div className="min-w-0 rounded-2xl border border-slate-200 bg-white p-4 xl:col-span-2">
                <h3 className="text-sm font-semibold text-slate-900">Low-value work to avoid</h3>
                <ul className="mt-3 grid gap-2 md:grid-cols-2">
                  {result.plan.low_value_activities.length ? result.plan.low_value_activities.map((item) => (
                    <li key={item} className="break-words rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-relaxed text-slate-700">{item}</li>
                  )) : <li className="text-sm text-slate-500">No low-value activities were flagged.</li>}
                </ul>
              </div>

              {!!result.plan.source_notes.length && (
                <div className="min-w-0 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 xl:col-span-2">
                  <h3 className="text-sm font-semibold text-amber-950">Source limits</h3>
                  <ul className="mt-2 space-y-1 text-sm leading-relaxed text-amber-900">
                    {result.plan.source_notes.map((note) => <li key={note}>{note}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
