import { Badge } from "@/components/ui/badge";
import { Shield, BookOpen, AlertTriangle } from "lucide-react";

export function ReportPreview() {
  return (
    <section className="px-6 py-20 bg-[#F9F8F6]">
      <div className="mx-auto max-w-5xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold text-slate-900">What a report looks like</h2>
          <p className="text-slate-500">
            Every recommendation comes with a rationale and a source. No guesswork.
          </p>
        </div>

        {/* Mock report card */}
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-lg">
          {/* Header */}
          <div className="border-b border-slate-200 bg-navy-950 px-6 py-5 text-white">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-navy-200">Optimization Report</p>
                <h3 className="text-lg font-semibold">MIT — Research-Heavy Profile</h3>
              </div>
              <Badge className="bg-emerald-500 text-white border-0">Completed</Badge>
            </div>
            <p className="mt-2 text-sm text-navy-200/80">
              Recommended: 8 activities, 3 honors · Generated Apr 2024
            </p>
          </div>

          <div className="p-6">
            {/* Recommended activities */}
            <div className="mb-6">
              <h4 className="mb-4 text-xs font-semibold uppercase tracking-widest text-slate-500">
                Top Recommended Activities
              </h4>
              <div className="space-y-3">
                {[
                  {
                    rank: 1,
                    title: "Independent Protein Folding Research",
                    org: "Self-directed / MIT PRIMES mentor",
                    confidence: "high",
                    type: "keep",
                    rationale: "Multi-year research with documented output aligns directly with MIT's research-heavy criteria.",
                  },
                  {
                    rank: 2,
                    title: "National Math Olympiad Team Captain",
                    org: "Ministry of Education, Country X",
                    confidence: "high",
                    type: "keep",
                    rationale: "National-level, leadership role, multi-year — matches all top weight factors.",
                  },
                  {
                    rank: 3,
                    title: "Competitive Programming (Codeforces Expert)",
                    org: "Individual / School Team",
                    confidence: "medium",
                    type: "rewrite",
                    rationale: "Strong selectivity signal. Description needs specificity — use Rewrite Studio.",
                  },
                ].map((item) => (
                  <div
                    key={item.rank}
                    className="flex items-start gap-4 rounded-lg border border-slate-100 bg-slate-50 p-4"
                  >
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-navy-950 text-xs font-bold text-white">
                      {item.rank}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <span className="font-medium text-slate-900 text-sm">{item.title}</span>
                        <Badge
                          variant={item.type === "keep" ? "success" : "warning"}
                          className="text-xs"
                        >
                          {item.type === "keep" ? "Keep" : "Rewrite"}
                        </Badge>
                        <Badge
                          variant={item.confidence === "high" ? "navy" : "info"}
                          className="text-xs"
                        >
                          {item.confidence} confidence
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-500 mb-1">{item.org}</p>
                      <p className="text-xs text-slate-600">{item.rationale}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Source cards */}
            <div>
              <h4 className="mb-4 text-xs font-semibold uppercase tracking-widest text-slate-500">
                Guidance Sources Used
              </h4>
              <div className="space-y-2">
                <div className="flex items-start gap-3 rounded-lg border border-emerald-100 bg-emerald-50 p-3">
                  <Shield className="h-4 w-4 text-emerald-700 mt-0.5 shrink-0" />
                  <div>
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-xs font-semibold text-emerald-800">Official — Tier A</span>
                    </div>
                    <p className="text-xs text-emerald-900 font-medium">MIT Admissions — What We Look For</p>
                    <p className="text-xs text-emerald-700 mt-0.5">
                      &ldquo;We look for students who pursue their interests with genuine depth rather than breadth for its own sake.&rdquo;
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-lg border border-amber-100 bg-amber-50 p-3">
                  <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
                  <div>
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-xs font-semibold text-amber-800">Public Example — Tier B</span>
                      <span className="text-xs text-amber-600">(not official guidance)</span>
                    </div>
                    <p className="text-xs text-amber-900 font-medium">MIT Community Blog — Admissions Reader Notes</p>
                    <p className="text-xs text-amber-700 mt-0.5">
                      Aggregated patterns from admitted students listing science research activities.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
