import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Check } from "lucide-react";

const plans = [
  {
    name: "Free",
    price: "$0",
    description: "Try SourceLock with no commitment.",
    features: [
      "Up to 10 achievements in vault",
      "1 free optimization report",
      "1 university",
      "Rewrite Studio (1 activity)",
      "No credit card required",
    ],
    cta: "Start free",
    href: "/sign-up",
    highlighted: false,
  },
  {
    name: "Single Report",
    price: "$19",
    description: "One university, fully optimized.",
    features: [
      "Unlimited achievements",
      "Full optimization report for 1 university",
      "All 3 rewrite styles",
      "Complete source library",
      "PDF export",
      "Valid for current application cycle",
    ],
    cta: "Get report",
    href: "/sign-up",
    highlighted: true,
  },
  {
    name: "Season Pass",
    price: "$59",
    description: "Applying to multiple schools this cycle.",
    features: [
      "Everything in Single Report",
      "Unlimited universities",
      "Unlimited reports (regenerate anytime)",
      "Priority source updates",
      "Email support",
      "Full application cycle access",
    ],
    cta: "Get Season Pass",
    href: "/sign-up",
    highlighted: false,
  },
];

export function PricingSection() {
  return (
    <section id="pricing" className="border-t border-slate-200 bg-[#F9F8F6] px-6 py-20">
      <div className="mx-auto max-w-5xl">
        <div className="mb-12 text-center">
          <h2 className="font-display mb-4 text-3xl font-bold text-slate-900">Simple, honest pricing</h2>
          <p className="text-slate-500">No subscriptions. No hidden fees. Pay once per cycle.</p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl border p-6 ${
                plan.highlighted
                  ? "border-navy-950 bg-navy-950 text-white shadow-xl"
                  : "border-slate-200 bg-white"
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                  <span className="inline-block animate-badge-float rounded-full bg-amber-400 px-3 py-1 text-xs font-semibold text-navy-950 shadow-sm">
                    Most popular
                  </span>
                </div>
              )}

              <div className="mb-5">
                <h3
                  className={`text-sm font-semibold uppercase tracking-wider ${
                    plan.highlighted ? "text-navy-200" : "text-slate-500"
                  }`}
                >
                  {plan.name}
                </h3>
                <div className="mt-2 flex items-baseline gap-1">
                  <span
                    className={`text-4xl font-bold ${
                      plan.highlighted ? "text-white" : "text-slate-900"
                    }`}
                  >
                    {plan.price}
                  </span>
                </div>
                <p
                  className={`mt-1.5 text-sm ${
                    plan.highlighted ? "text-navy-200" : "text-slate-500"
                  }`}
                >
                  {plan.description}
                </p>
              </div>

              <ul className="mb-6 space-y-2.5">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2.5">
                    <Check
                      className={`mt-0.5 h-4 w-4 shrink-0 ${
                        plan.highlighted ? "text-emerald-400" : "text-emerald-600"
                      }`}
                    />
                    <span
                      className={`text-sm ${
                        plan.highlighted ? "text-navy-100" : "text-slate-600"
                      }`}
                    >
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              <Link href={plan.href}>
                <Button
                  className={`w-full ${
                    plan.highlighted
                      ? "bg-white text-navy-950 hover:bg-navy-50"
                      : "bg-navy-950 text-white hover:bg-navy-900"
                  }`}
                  size="lg"
                >
                  {plan.cta}
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
