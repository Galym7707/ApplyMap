import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, Shield, BookOpen, Star, Lock } from "lucide-react";

const mockRecommendations = [
  {
    rank: 1,
    title: "National Science Olympiad",
    meta: "Team Captain · 8h/wk · National scope",
    status: "Keep",
    color: "emerald",
  },
  {
    rank: 2,
    title: "ML Research — Nazarbayev University",
    meta: "Research Assistant · 12h/wk",
    status: "Keep",
    color: "emerald",
  },
  {
    rank: 3,
    title: "Student Council President",
    meta: "Description needs strengthening",
    status: "Rewrite",
    color: "amber",
  },
  {
    rank: null,
    title: "Casual Math Tutoring",
    meta: "Low relevance for research profile",
    status: "Remove",
    color: "red",
  },
];

const statusStyles: Record<string, string> = {
  emerald: "bg-emerald-50 text-emerald-700",
  amber: "bg-amber-50 text-amber-700",
  red: "bg-red-50 text-red-600",
};

export function Hero() {
  return (
    <section className="relative overflow-hidden px-6 pt-20 pb-16">
      {/* Radial navy tint at top center */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 45% at 50% 0%, rgba(20, 21, 84, 0.07) 0%, transparent 65%)",
        }}
      />
      {/* Fade to page background at bottom */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#F9F8F6]/60" />

      <div className="relative mx-auto max-w-4xl text-center">
        {/* Animated trust badge */}
        <div className="mb-7 flex justify-center">
          <div className="inline-flex animate-badge-glow items-center gap-2 rounded-full border border-navy-200 bg-navy-50 px-4 py-1.5 text-sm text-navy-800">
            <Shield className="h-3.5 w-3.5" />
            Source-backed guidance for international applicants
          </div>
        </div>

        {/* Eyebrow */}
        <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-navy-700">
          Common App Optimization
        </p>

        {/* Headline — short and punchy, 2 visual lines */}
        <h1 className="font-display mb-6 text-5xl font-bold leading-[1.1] text-slate-900 sm:text-6xl">
          Your strongest activities,{" "}
          <span className="italic text-navy-950">ranked for each university.</span>
        </h1>

        <p className="mx-auto mb-10 max-w-2xl text-xl leading-relaxed text-slate-600">
          Source-backed guidance from official admissions materials — not AI
          guesswork, not generic advice. Built for international Common App
          applicants.
        </p>

        {/* CTAs — primary dominant, ghost link stacked below */}
        <div className="flex flex-col items-center gap-3">
          <Link href="/sign-up">
            <Button
              size="xl"
              className="bg-navy-950 text-white hover:bg-navy-900 gap-2 active:scale-[0.97] transition-transform"
            >
              Start free <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <Link
            href="#how-it-works"
            className="text-sm text-slate-500 hover:text-navy-700 transition-colors underline underline-offset-2"
          >
            See how it works
          </Link>
        </div>

        {/* Product mockup */}
        <div className="mt-16 mx-auto max-w-xl">
          <div
            className="rotate-[0.5deg] rounded-2xl border border-slate-200 bg-white overflow-hidden ring-1 ring-slate-900/5"
            style={{
              boxShadow:
                "0 20px 60px -10px rgba(20, 21, 84, 0.15), 0 4px 16px -4px rgba(0,0,0,0.08)",
            }}
          >
            {/* Report header bar */}
            <div className="flex items-center justify-between bg-navy-950 px-5 py-3">
              <div className="flex items-center gap-2">
                <div className="flex h-5 w-5 items-center justify-center rounded bg-navy-800">
                  <Lock className="h-3 w-3 text-white" />
                </div>
                <span className="text-sm font-semibold text-white">
                  MIT · Research-Heavy Profile
                </span>
              </div>
              <span className="text-xs text-navy-300">v1 · Apr 2026</span>
            </div>

            {/* Report body */}
            <div className="p-5">
              <p className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                Recommended Activities
              </p>

              <div className="space-y-2">
                {mockRecommendations.map((rec, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 rounded-lg bg-slate-50 px-3 py-2.5"
                  >
                    <span className="w-5 shrink-0 text-right text-xs font-bold text-slate-400">
                      {rec.rank ? `#${rec.rank}` : "—"}
                    </span>
                    <div className="flex-1 min-w-0 text-left">
                      <p className="truncate text-sm font-medium text-slate-900">
                        {rec.title}
                      </p>
                      <p className="text-xs text-slate-400">{rec.meta}</p>
                    </div>
                    <span
                      className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${statusStyles[rec.color]}`}
                    >
                      {rec.status}
                    </span>
                  </div>
                ))}
              </div>

              {/* Source footer */}
              <div className="mt-4 flex items-center gap-1.5 border-t border-slate-100 pt-3">
                <BookOpen className="h-3.5 w-3.5 shrink-0 text-navy-500" />
                <span className="text-xs text-slate-400">
                  3 recommendations tied to official MIT admissions materials
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Social proof */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-8 text-sm text-slate-500">
          <div className="flex items-center gap-1.5">
            <div className="flex">
              {[1, 2, 3, 4, 5].map((i) => (
                <Star key={i} className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
              ))}
            </div>
            <span>Trusted by students from 40+ countries</span>
          </div>
          <div className="flex items-center gap-1.5">
            <BookOpen className="h-3.5 w-3.5 text-navy-700" />
            <span>Every recommendation tied to an official source</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Shield className="h-3.5 w-3.5 text-emerald-600" />
            <span>No personal data sold, ever</span>
          </div>
        </div>
      </div>
    </section>
  );
}
