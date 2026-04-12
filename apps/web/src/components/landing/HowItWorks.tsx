import { Upload, Sliders, FileText } from "lucide-react";

export function HowItWorks() {
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

  return (
    <section id="how-it-works" className="px-6 py-20 bg-[#F9F8F6]">
      <div className="mx-auto max-w-5xl">
        <div className="mb-14 text-center">
          <h2 className="mb-4 text-3xl font-bold text-slate-900">How it works</h2>
          <p className="text-slate-500 max-w-xl mx-auto">
            Three steps. One university at a time. Every recommendation traced back to a source.
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-3">
          {steps.map((step) => {
            const Icon = step.icon;
            return (
              <div key={step.step} className="relative">
                <div className="mb-4 flex items-start gap-4">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-navy-950">
                    <Icon className="h-5 w-5 text-white" />
                  </div>
                  <span className="pt-2 text-2xl font-bold text-slate-200">{step.step}</span>
                </div>
                <h3 className="mb-3 text-lg font-semibold text-slate-900">{step.title}</h3>
                <p className="text-sm leading-relaxed text-slate-600">{step.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
