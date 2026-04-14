import { Lock, Eye, Database, Globe } from "lucide-react";

export function TrustSection() {
  const items = [
    {
      icon: Lock,
      title: "Your data is yours",
      description:
        "We do not sell your application data. We do not train models on your submissions. Your achievements, test scores, and personal details stay private.",
    },
    {
      icon: Eye,
      title: "Full source transparency",
      description:
        "Every piece of guidance is labeled: official (Tier A), verified public example (Tier B/C), or community-sourced (Tier D). You always know what you're reading.",
    },
    {
      icon: Database,
      title: "No invented facts",
      description:
        "The Rewrite Studio only compresses and restructures text you've entered. It cannot and does not add claims about your activities that aren't already there.",
    },
    {
      icon: Globe,
      title: "Built for international students",
      description:
        "Context matters. SourceLock recognizes that a student from Nigeria, Vietnam, or Argentina has different access to extracurriculars than a US applicant. Our sources reflect this.",
    },
  ];

  return (
    <section className="border-y border-slate-200 bg-white px-6 py-20">
      <div className="mx-auto max-w-5xl">
        <div className="mb-12 text-center">
          <h2 className="font-display mb-4 text-3xl font-bold text-slate-900">Privacy and transparency</h2>
          <p className="text-slate-500">
            We take both seriously. Here&rsquo;s exactly what we do — and don&rsquo;t do.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {items.map((item, i) => {
            const Icon = item.icon;
            return (
              <div key={i} className="rounded-xl border border-slate-200 bg-slate-50 p-5">
                <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-navy-100">
                  <Icon className="h-5 w-5 text-navy-950" />
                </div>
                <h3 className="mb-2 font-semibold text-slate-900 text-sm">{item.title}</h3>
                <p className="text-xs leading-relaxed text-slate-600">{item.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
