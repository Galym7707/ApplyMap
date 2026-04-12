import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Shield, BookOpen, Star } from "lucide-react";

export function Hero() {
  return (
    <section className="relative overflow-hidden px-6 pt-20 pb-24">
      {/* Subtle background gradient */}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-slate-100/60 to-transparent" />

      <div className="relative mx-auto max-w-4xl text-center">
        {/* Trust badge */}
        <div className="mb-8 flex justify-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-navy-200 bg-navy-50 px-4 py-1.5 text-sm text-navy-800">
            <Shield className="h-3.5 w-3.5" />
            Source-backed guidance for international applicants
          </div>
        </div>

        {/* Headline */}
        <h1 className="mb-6 text-5xl font-bold leading-[1.1] tracking-tight text-slate-900 sm:text-6xl">
          Choose, rank, and rewrite{" "}
          <span className="text-navy-950">your strongest activities</span>{" "}
          for a specific university.
        </h1>

        <p className="mx-auto mb-4 max-w-2xl text-xl leading-relaxed text-slate-600">
          Source-backed guidance from official admissions materials — not fake admission predictions,
          not generic AI rewrites.
        </p>
        <p className="mx-auto mb-10 max-w-xl text-base text-slate-500">
          Built specifically for international applicants navigating the Common App.
        </p>

        {/* CTAs */}
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <Link href="/sign-up">
            <Button size="xl" className="bg-navy-950 text-white hover:bg-navy-900 gap-2">
              Start free <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <Link href="#how-it-works">
            <Button size="xl" variant="outline" className="border-slate-300 text-slate-700">
              See how it works
            </Button>
          </Link>
        </div>

        {/* Social proof */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-8 text-sm text-slate-500">
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
