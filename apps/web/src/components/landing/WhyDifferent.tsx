import { Check, X } from "lucide-react";

export function WhyDifferent() {
  const comparisons = [
    {
      feature: "Uses the student's real experiences",
      applymap: true,
      genericAi: "sometimes",
      privateConsultant: true,
    },
    {
      feature: "Built for students without expensive private guidance",
      applymap: true,
      genericAi: "partial",
      privateConsultant: false,
    },
    {
      feature: "Separates structure from ghostwriting",
      applymap: true,
      genericAi: false,
      privateConsultant: "sometimes",
    },
    {
      feature: "Keeps university advice tied to current sources",
      applymap: true,
      genericAi: false,
      privateConsultant: "sometimes",
    },
    {
      feature: "International and Kazakhstan context aware",
      applymap: true,
      genericAi: "sometimes",
      privateConsultant: "sometimes",
    },
    {
      feature: "Dream, target, and safe planning with funding realism",
      applymap: true,
      genericAi: "partial",
      privateConsultant: true,
    },
  ];

  const renderCell = (value: boolean | string) => {
    if (value === true) return <Check className="mx-auto h-4 w-4 text-emerald-600" />;
    if (value === false) return <X className="mx-auto h-4 w-4 text-red-400" />;
    return <span className="mx-auto block text-center text-xs font-medium text-amber-600">{value}</span>;
  };

  return (
    <section className="border-y border-slate-200 bg-white px-6 py-20">
      <div className="mx-auto max-w-4xl">
        <div className="mb-12 text-center">
          <h2 className="font-display mb-4 text-3xl font-bold text-slate-900">
            Not a shortcut. A guide.
          </h2>
          <p className="mx-auto max-w-xl text-slate-500">
            ApplyMap does not write a fake persona for the student. It helps them
            understand, structure, and advocate for the facts they already own.
          </p>
        </div>

        <div className="overflow-hidden rounded-xl border border-slate-200">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50">
                <th className="px-5 py-3 text-left text-sm font-medium text-slate-600">Feature</th>
                <th className="px-5 py-3 text-center text-sm font-semibold text-navy-950">ApplyMap</th>
                <th className="px-5 py-3 text-center text-sm font-medium text-slate-500">Generic AI</th>
                <th className="px-5 py-3 text-center text-sm font-medium text-slate-500">Private consultant</th>
              </tr>
            </thead>
            <tbody>
              {comparisons.map((row, index) => (
                <tr
                  key={row.feature}
                  className={`border-b border-slate-100 ${index % 2 === 0 ? "bg-white" : "bg-slate-50/50"}`}
                >
                  <td className="px-5 py-3 text-sm text-slate-700">{row.feature}</td>
                  <td className="px-5 py-3">{renderCell(row.applymap)}</td>
                  <td className="px-5 py-3">{renderCell(row.genericAi)}</td>
                  <td className="px-5 py-3">{renderCell(row.privateConsultant)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
