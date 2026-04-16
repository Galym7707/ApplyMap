import { Fragment } from "react";
import { ArrowRight, FileText, Map, Search, Upload } from "lucide-react";

const steps = [
  {
    icon: Upload,
    step: "01",
    title: "Map your real experiences",
    description:
      "Add activities, honors, work, family responsibilities, and school context. ApplyMap helps identify what each experience actually proves.",
  },
  {
    icon: Map,
    step: "02",
    title: "Structure the application chaos",
    description:
      "Organize your profile around fit, impact, selectivity, continuity, funding need, and the formats universities expect.",
  },
  {
    icon: Search,
    step: "03",
    title: "Find realistic university paths",
    description:
      "Use saved preferences and source-backed search to compare dream, target, and safe options without pretending admission or aid is guaranteed.",
  },
  {
    icon: FileText,
    step: "04",
    title: "Act with a clear plan",
    description:
      "Get concise guidance on exams, useful profile moves, low-value activities, and next steps tied to the target university.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="border-t border-slate-200 bg-[#F9F8F6] px-6 py-20">
      <div className="mx-auto max-w-6xl">
        <div className="mb-14 text-center">
          <h2 className="font-display mb-4 text-3xl font-bold text-slate-900">How it works</h2>
          <p className="mx-auto max-w-xl text-slate-500">
            A guided software framework for students who have to navigate admissions independently.
          </p>
        </div>

        <div className="flex flex-col gap-4 lg:flex-row lg:items-stretch lg:gap-0">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <Fragment key={step.step}>
                <div className="relative flex-1 overflow-hidden rounded-2xl border border-slate-200 bg-white p-7">
                  <span className="pointer-events-none absolute right-5 top-3 select-none text-7xl font-bold leading-none text-slate-100">
                    {step.step}
                  </span>
                  <div className="relative mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-navy-950">
                    <Icon className="h-5 w-5 text-white" />
                  </div>
                  <h3 className="mb-2.5 text-lg font-semibold text-slate-900">{step.title}</h3>
                  <p className="text-sm leading-relaxed text-slate-600">{step.description}</p>
                </div>

                {index < steps.length - 1 && (
                  <div className="hidden w-10 shrink-0 items-center justify-center lg:flex">
                    <ArrowRight className="h-4 w-4 text-slate-300" />
                  </div>
                )}
              </Fragment>
            );
          })}
        </div>
      </div>
    </section>
  );
}
