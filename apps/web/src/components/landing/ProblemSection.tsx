import { Check, X } from "lucide-react";

const pairs = [
  {
    problem: "Private consultants turn admissions know-how into a paid advantage.",
    solution: "ApplyMap turns the same structure into an accessible guided workflow.",
  },
  {
    problem: "Students with real responsibility often do not know how to explain its value.",
    solution: "The platform helps translate jobs, family duties, clubs, and local work into clear application points.",
  },
  {
    problem: "International applicants face unfamiliar formats, constraints, and cultural expectations.",
    solution: "ApplyMap maps school context, exams, funding need, and university fit into one practical plan.",
  },
  {
    problem: "Generic AI tools can replace the student's voice or invent unsupported claims.",
    solution: "ApplyMap uses the student's real facts and keeps guidance source-aware and conservative.",
  },
];

export function ProblemSection() {
  return (
    <section className="border-t border-slate-200 bg-white px-6 py-20">
      <div className="mx-auto max-w-5xl">
        <div className="mb-12 text-center">
          <h2 className="font-display mb-4 text-3xl font-bold text-slate-900">
            The guidance gap decides too much.
          </h2>
          <p className="mx-auto max-w-2xl text-slate-500">
            Many capable students are not missing talent. They are missing the
            specific know-how to present that talent in a system with unwritten rules.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-7">
            <div className="mb-6 flex items-center gap-2.5">
              <div className="h-2 w-2 rounded-full bg-red-400" />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                The gap
              </span>
            </div>
            <ul className="space-y-5">
              {pairs.map((item) => (
                <li key={item.problem} className="flex items-start gap-3">
                  <X className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
                  <span className="text-sm leading-relaxed text-slate-700">{item.problem}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-7">
            <div className="mb-6 flex items-center gap-2.5">
              <div className="h-2 w-2 rounded-full bg-emerald-500" />
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
                With ApplyMap
              </span>
            </div>
            <ul className="space-y-5">
              {pairs.map((item) => (
                <li key={item.solution} className="flex items-start gap-3">
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                  <span className="text-sm leading-relaxed text-emerald-900">{item.solution}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
