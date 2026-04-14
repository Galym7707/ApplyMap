"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

const faqs = [
  {
    q: "Will this guarantee my admission?",
    a: "No. SourceLock does not predict or guarantee admission outcomes. We provide source-backed guidance on how to present your genuine achievements for a specific university's stated criteria. Admission decisions involve many factors we cannot control.",
  },
  {
    q: "Is this for Common App specifically?",
    a: "Yes. The system is built around Common App activity and honor section formats, including character limits. We plan to support Coalition and QuestBridge in future releases.",
  },
  {
    q: "Can I use this if I'm from outside the US?",
    a: "SourceLock is built specifically for international applicants. The source database includes guidance from universities that explicitly addresses international context, curriculum differences, and opportunity gaps.",
  },
  {
    q: "What universities are supported?",
    a: "Currently: MIT, Harvard, Stanford, Yale, and NYU Abu Dhabi — with more being added monthly. Each has a curated source library drawn from official admissions materials.",
  },
  {
    q: "Will the Rewrite Studio change the facts of what I did?",
    a: "No. The Rewrite Studio only restructures and compresses text you've entered. It cannot and does not add claims about your activities that aren't already there. This is a hard design constraint, not a soft guideline.",
  },
  {
    q: "What does 'Tier A source' mean?",
    a: "Tier A means the guidance comes directly from an official university admissions publication — a webpage, FAQ, or official blog post by admissions staff. Tier B/C are public examples from admitted students or aggregated community patterns, always labeled as such with a disclaimer.",
  },
  {
    q: "How is this different from a college counselor?",
    a: "A good counselor who knows MIT well is excellent — SourceLock doesn't replace that. For students who don't have access to specialized counselors (which describes most international applicants), SourceLock provides the same source-grounded framework at a fraction of the cost.",
  },
];

export function FaqSection() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section id="faq" className="border-t border-slate-200 bg-white px-6 py-20">
      <div className="mx-auto max-w-3xl">
        <div className="mb-12 text-center">
          <h2 className="font-display mb-4 text-3xl font-bold text-slate-900">Frequently asked questions</h2>
        </div>

        <div className="divide-y divide-slate-200">
          {faqs.map((faq, i) => (
            <div key={i}>
              <button
                className="flex w-full items-start justify-between py-5 text-left"
                onClick={() => setOpen(open === i ? null : i)}
              >
                <span className="text-sm font-medium text-slate-900 pr-4">{faq.q}</span>
                <ChevronDown
                  className={cn(
                    "h-4 w-4 shrink-0 text-slate-400 transition-transform",
                    open === i && "rotate-180"
                  )}
                />
              </button>
              {open === i && (
                <div className="pb-5">
                  <p className="text-sm leading-relaxed text-slate-600">{faq.a}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
