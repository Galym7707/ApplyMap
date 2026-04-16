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

const SOURCE_LABELS: Record<UniversityAdvisorSource["source_tier"], string> = {
  official: "Official",
  likely_official: "Likely official",
  education_domain: "Education domain",
  third_party: "Third party",
};

export default function AdvisorPage() {
  const [universityName, setUniversityName] = useState("");
  const [intendedMajor, setIntendedMajor] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AdvisorResponse | null>(null);

  const advisorMutation = useMutation({
    mutationFn: () =>
      universitiesApi.advisorPlan({
        university_name: universityName,
        intended_major: intendedMajor || undefined,
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
      setError(detail ?? "Advisor search failed. Check the backend Google Search configuration.");
    },
  });

  return (
    <div className="bg-[#f7f5ef] px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">University advisor</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">Ask about one target school</h1>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-500">
            Get a concise source-backed plan: exams to prioritize, profile moves that matter, low-value activities, and relevant research or summer programs when current sources support them.
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
              <Label>Intended major</Label>
              <Input
                value={intendedMajor}
                onChange={(event) => setIntendedMajor(event.target.value)}
                placeholder="e.g. Computer Science"
                className="h-11 rounded-xl"
              />
            </div>
            <Button
              className="h-11 gap-2 bg-navy-950 text-white hover:bg-navy-900"
              disabled={advisorMutation.isPending || universityName.trim().length < 2}
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
          <div className="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <section className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)]">
              <div className="mb-5 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-navy-700" />
                <h2 className="text-lg font-semibold text-slate-900">Chancellor plan</h2>
              </div>
              <p className="rounded-2xl bg-slate-950 px-5 py-4 text-sm leading-relaxed text-white">
                {result.plan.summary}
              </p>

              <div className="mt-6 grid gap-5 md:grid-cols-2">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Exams to prioritize</h3>
                  <div className="mt-3 space-y-3">
                    {result.plan.exams_to_prioritize.length ? result.plan.exams_to_prioritize.map((item) => (
                      <div key={`${item.exam}-${item.priority}`} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-sm font-medium text-slate-900">{item.exam}</p>
                          <Badge variant={item.priority === "high" ? "success" : item.priority === "medium" ? "warning" : "outline"}>{item.priority}</Badge>
                        </div>
                        <p className="mt-2 text-xs leading-relaxed text-slate-600">{item.why}</p>
                      </div>
                    )) : <p className="text-sm text-slate-500">No exam advice was confirmed from current sources.</p>}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Profile actions</h3>
                  <ul className="mt-3 space-y-2">
                    {result.plan.profile_actions.map((item) => (
                      <li key={item} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">{item}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Low-value activities</h3>
                  <ul className="mt-3 space-y-2">
                    {result.plan.low_value_activities.map((item) => (
                      <li key={item} className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">{item}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Research or summer programs</h3>
                  <div className="mt-3 space-y-3">
                    {result.plan.research_or_summer_programs.length ? result.plan.research_or_summer_programs.map((item) => (
                      <div key={item.name} className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                        <p className="text-sm font-medium text-slate-900">{item.name}</p>
                        <p className="mt-2 text-xs leading-relaxed text-slate-600">{item.why_it_helps}</p>
                        {item.source_url && <a href={item.source_url} target="_blank" rel="noreferrer" className="mt-2 block text-xs text-navy-700 underline underline-offset-2">Source</a>}
                      </div>
                    )) : <p className="text-sm text-slate-500">No programs were confirmed from current sources.</p>}
                  </div>
                </div>
              </div>

              {!!result.plan.source_notes.length && (
                <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                  <h3 className="text-sm font-semibold text-slate-900">Source notes</h3>
                  <ul className="mt-2 space-y-1 text-sm text-slate-600">
                    {result.plan.source_notes.map((note) => <li key={note}>{note}</li>)}
                  </ul>
                </div>
              )}
            </section>

            <section className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)]">
              <h2 className="text-lg font-semibold text-slate-900">Sources checked</h2>
              <p className="mt-2 text-sm text-slate-500">
                Google Custom Search results are classified by domain. Official university pages should carry the most weight.
              </p>
              <div className="mt-5 max-h-[42rem] space-y-3 overflow-y-auto pr-1">
                {result.sources.map((source) => (
                  <a key={source.url} href={source.url} target="_blank" rel="noreferrer" className="block rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 transition hover:border-navy-200 hover:bg-white">
                    <div className="flex items-center justify-between gap-3">
                      <p className="line-clamp-1 text-sm font-medium text-slate-900">{source.title}</p>
                      <Badge variant={source.source_tier === "official" ? "success" : source.source_tier === "third_party" ? "warning" : "info"}>{SOURCE_LABELS[source.source_tier]}</Badge>
                    </div>
                    <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-slate-600">{source.snippet}</p>
                    <p className="mt-2 truncate text-xs text-navy-700">{source.url}</p>
                  </a>
                ))}
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
