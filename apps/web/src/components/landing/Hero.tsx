import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, BookOpen, Map, Shield, Star } from "lucide-react";

const profileMoments = [
  {
    rank: 1,
    title: "National Science Olympiad",
    meta: "Leadership, rigor, and national context",
    status: "Clarify impact",
    color: "emerald",
  },
  {
    rank: 2,
    title: "ML Research at Nazarbayev University",
    meta: "Academic direction and evidence",
    status: "Build spike",
    color: "emerald",
  },
  {
    rank: 3,
    title: "Student Council President",
    meta: "Leadership needs concrete outcomes",
    status: "Sharpen",
    color: "amber",
  },
  {
    rank: null,
    title: "Casual Math Tutoring",
    meta: "Useful only if impact is specific",
    status: "Review",
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
    <section className="relative overflow-hidden px-6 pb-16 pt-20">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 45% at 50% 0%, rgba(20, 21, 84, 0.07) 0%, transparent 65%)",
        }}
      />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[#F9F8F6]/60" />

      <div className="relative mx-auto max-w-4xl text-center">
        <div className="mb-7 flex justify-center">
          <div className="inline-flex animate-badge-glow items-center gap-2 rounded-full border border-navy-200 bg-navy-50 px-4 py-1.5 text-sm text-navy-800">
            <Shield className="h-3.5 w-3.5" />
            Accessible admissions guidance for independent students
          </div>
        </div>

        <p className="mb-3 text-sm font-semibold uppercase tracking-widest text-navy-700">
          ApplyMap
        </p>

        <h1 className="font-display mb-6 text-5xl font-bold leading-[1.1] text-slate-900 sm:text-6xl">
          Your hard work deserves{" "}
          <span className="italic text-navy-950">to be seen.</span>
        </h1>

        <p className="mx-auto mb-10 max-w-2xl text-xl leading-relaxed text-slate-600">
          Navigate college admissions with clarity and confidence. ApplyMap helps
          you recognize your strengths, structure your achievements, and discover
          universities that fit, without expensive private consultants.
        </p>

        <div className="flex flex-col items-center gap-3">
          <Link href="/sign-up">
            <Button
              size="xl"
              className="gap-2 bg-navy-950 text-white transition-transform hover:bg-navy-900 active:scale-[0.97]"
            >
              Start Mapping Your Profile <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <Link
            href="#how-it-works"
            className="text-sm text-slate-500 underline underline-offset-2 transition-colors hover:text-navy-700"
          >
            See how it works
          </Link>
        </div>

        <div className="mx-auto mt-16 max-w-xl">
          <div
            className="rotate-[0.5deg] overflow-hidden rounded-2xl border border-slate-200 bg-white ring-1 ring-slate-900/5"
            style={{
              boxShadow:
                "0 20px 60px -10px rgba(20, 21, 84, 0.15), 0 4px 16px -4px rgba(0,0,0,0.08)",
            }}
          >
            <div className="flex items-center justify-between bg-navy-950 px-5 py-3">
              <div className="flex items-center gap-2">
                <div className="flex h-5 w-5 items-center justify-center rounded bg-navy-800">
                  <Map className="h-3 w-3 text-white" />
                </div>
                <span className="text-sm font-semibold text-white">
                  ApplyMap - Guided Profile Map
                </span>
              </div>
              <span className="text-xs text-navy-300">student-owned</span>
            </div>

            <div className="p-5">
              <p className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                What ApplyMap helps you see
              </p>

              <div className="space-y-2">
                {profileMoments.map((item) => (
                  <div
                    key={item.title}
                    className="flex items-center gap-3 rounded-lg bg-slate-50 px-3 py-2.5"
                  >
                    <span className="w-5 shrink-0 text-right text-xs font-bold text-slate-400">
                      {item.rank ? `#${item.rank}` : "--"}
                    </span>
                    <div className="min-w-0 flex-1 text-left">
                      <p className="truncate text-sm font-medium text-slate-900">
                        {item.title}
                      </p>
                      <p className="text-xs text-slate-400">{item.meta}</p>
                    </div>
                    <span
                      className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${statusStyles[item.color]}`}
                    >
                      {item.status}
                    </span>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex items-center gap-1.5 border-t border-slate-100 pt-3">
                <BookOpen className="h-3.5 w-3.5 shrink-0 text-navy-500" />
                <span className="text-xs text-slate-400">
                  Structure real experiences before turning them into applications
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-8 text-sm text-slate-500">
          <div className="flex items-center gap-1.5">
            <div className="flex">
              {[1, 2, 3, 4, 5].map((i) => (
                <Star key={i} className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
              ))}
            </div>
            <span>Built for students navigating without private counselors</span>
          </div>
          <div className="flex items-center gap-1.5">
            <BookOpen className="h-3.5 w-3.5 text-navy-700" />
            <span>Guidance anchored to sources and student-owned facts</span>
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
