import { Check, X } from "lucide-react";

export function WhyDifferent() {
  const comparisons = [
    {
      feature: "Tied to official university sources",
      sourcelock: true,
      chatgpt: false,
      counselor: "sometimes",
    },
    {
      feature: "University-specific weighting",
      sourcelock: true,
      chatgpt: false,
      counselor: "sometimes",
    },
    {
      feature: "Never invents facts",
      sourcelock: true,
      chatgpt: false,
      counselor: true,
    },
    {
      feature: "Source type + reliability labeled",
      sourcelock: true,
      chatgpt: false,
      counselor: false,
    },
    {
      feature: "Common App character limit enforced",
      sourcelock: true,
      chatgpt: false,
      counselor: "sometimes",
    },
    {
      feature: "International context aware",
      sourcelock: true,
      chatgpt: false,
      counselor: "sometimes",
    },
    {
      feature: "Affordable for all income levels",
      sourcelock: true,
      chatgpt: "partial",
      counselor: false,
    },
  ];

  const renderCell = (value: boolean | string) => {
    if (value === true) return <Check className="h-4 w-4 text-emerald-600 mx-auto" />;
    if (value === false) return <X className="h-4 w-4 text-red-400 mx-auto" />;
    return <span className="text-xs text-amber-600 font-medium mx-auto block text-center">Sometimes</span>;
  };

  return (
    <section className="border-y border-slate-200 bg-white px-6 py-20">
      <div className="mx-auto max-w-4xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold text-slate-900">Why not just use ChatGPT?</h2>
          <p className="text-slate-500 max-w-xl mx-auto">
            ChatGPT is a generative model. SourceLock is a guidance system with traceable sources.
            The difference matters when your application is on the line.
          </p>
        </div>

        <div className="overflow-hidden rounded-xl border border-slate-200">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50">
                <th className="px-5 py-3 text-left text-sm font-medium text-slate-600">Feature</th>
                <th className="px-5 py-3 text-center text-sm font-semibold text-navy-950">SourceLock</th>
                <th className="px-5 py-3 text-center text-sm font-medium text-slate-500">ChatGPT</th>
                <th className="px-5 py-3 text-center text-sm font-medium text-slate-500">College Counselor</th>
              </tr>
            </thead>
            <tbody>
              {comparisons.map((row, i) => (
                <tr
                  key={i}
                  className={`border-b border-slate-100 ${i % 2 === 0 ? "bg-white" : "bg-slate-50/50"}`}
                >
                  <td className="px-5 py-3 text-sm text-slate-700">{row.feature}</td>
                  <td className="px-5 py-3">{renderCell(row.sourcelock)}</td>
                  <td className="px-5 py-3">{renderCell(row.chatgpt)}</td>
                  <td className="px-5 py-3">{renderCell(row.counselor)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
