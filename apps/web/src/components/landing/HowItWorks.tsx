import { Fragment } from "react";
import { Upload, Sliders, FileText, ArrowRight } from "lucide-react";

const steps = [
  {
    icon: Upload,
    step: "01",
    title: "Import your achievements",
    description:
      "Add all your activities and honors — as many as you have. Include context: hours, scope, your specific role. The more detail, the better the output.",
  },
  {
    icon: Sliders,
    step: "02",
    title: "Select your target university",
    description:
      "Pick from MIT, Harvard, Stanford, Yale, NYU Abu Dhabi, and more. Each has a unique weight profile (research-heavy, leadership-heavy, holistic) drawn from official admissions materials.",
  },
  {
    icon: FileText,
    step: "03",
    title: "Get your source-backed report",
    description:
      "Receive a ranked list of recommended activities and honors, rewrite variants in 3 styles, and full source citations — official documents labeled A-tier, public examples labeled B/C-tier with disclaimers.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="border-t border-slate-200 bg-[#F9F8F6] px-6 py-20">
      <div className="mx-auto max-w-5xl">
        <div className="mb-14 text-center">
          <h2 className="font-display mb-4 text-3xl font-bold text-slate-900">How it works</h2>
          <p className="mx-auto max-w-xl text-slate-500">
            Three steps. One university at a time. Every recommendation traced back to a source.
          </p>
        </div>

        {/* Step cards with arrow connectors */}
        <div className="flex flex-col gap-4 md:flex-row md:items-stretch md:gap-0">
          {steps.map((step, i) => {
            const Icon = step.icon;
            return (
              <Fragment key={step.step}>
                {/* Card */}
                <div className="relative flex-1 overflow-hidden rounded-2xl border border-slate-200 bg-white p-7">
                  {/* Watermark step number */}
                  <span className="pointer-events-none absolute right-5 top-3 select-none text-7xl font-bold leading-none text-slate-100">
                    {step.step}
                  </span>

                  {/* Icon */}
                  <div className="relative mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-navy-950">
                    <Icon className="h-5 w-5 text-white" />
                  </div>

                  <h3 className="mb-2.5 text-lg font-semibold text-slate-900">{step.title}</h3>
                  <p className="text-sm leading-relaxed text-slate-600">{step.description}</p>
                </div>

                {/* Arrow connector — desktop only */}
                {i < steps.length - 1 && (
                  <div className="hidden md:flex md:w-10 md:shrink-0 md:items-center md:justify-center">
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
