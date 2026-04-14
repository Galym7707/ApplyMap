import { X, Check } from "lucide-react";

const pairs = [
  {
    problem: "Guess which 10 activities to include out of 15+",
    solution: "Ranked list tailored to each university's stated criteria",
  },
  {
    problem: "Generic advice that ignores your curriculum and country",
    solution: "Weight presets drawn from official admissions materials",
  },
  {
    problem: "AI tools that confidently invent facts about what you did",
    solution: "Rewrites that only restructure text you've actually entered",
  },
  {
    problem: "Reddit and College Confidential vary wildly in accuracy",
    solution: "Every recommendation traced to a labeled, tiered source",
  },
];

export function ProblemSection() {
  return (
    <section className="border-t border-slate-200 bg-white px-6 py-20">
      <div className="mx-auto max-w-5xl">
        <div className="mb-12 text-center">
          <h2 className="font-display mb-4 text-3xl font-bold text-slate-900">
            Why the Common App activities section is hard for international students
          </h2>
          <p className="text-slate-500">
            You&rsquo;re not imagining it. The process genuinely has gaps that ApplyMap closes.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {/* Left: without ApplyMap */}
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-7">
            <div className="mb-6 flex items-center gap-2.5">
              <div className="h-2 w-2 rounded-full bg-red-400" />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Without ApplyMap
              </span>
            </div>
            <ul className="space-y-5">
              {pairs.map((p, i) => (
                <li key={i} className="flex items-start gap-3">
                  <X className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
                  <span className="text-sm leading-relaxed text-slate-700">{p.problem}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Right: with ApplyMap */}
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-7">
            <div className="mb-6 flex items-center gap-2.5">
              <div className="h-2 w-2 rounded-full bg-emerald-500" />
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
                With ApplyMap
              </span>
            </div>
            <ul className="space-y-5">
              {pairs.map((p, i) => (
                <li key={i} className="flex items-start gap-3">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                  <span className="text-sm leading-relaxed text-emerald-900">{p.solution}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
