export function ProblemSection() {
  const problems = [
    {
      title: "You don't know what to include",
      description:
        "You have 15+ activities and honors. The Common App has space for 10 activities and 5 honors. How do you choose — and for which university specifically?",
    },
    {
      title: "Generic advice doesn't apply to you",
      description:
        "Most guides assume you're American. They don't account for your curriculum, your country's opportunity landscape, or what MIT vs. Yale actually weights differently.",
    },
    {
      title: "AI rewrites invent things",
      description:
        "ChatGPT will confidently write that you 'led a team of 12' when you worked alone. SourceLock only compresses and restructures what you actually did — never invents facts.",
    },
    {
      title: "You can't trust anonymous internet advice",
      description:
        "College Confidential posts and Reddit threads vary wildly in accuracy. SourceLock ties every recommendation to an official source — labeled by tier and source type.",
    },
  ];

  return (
    <section className="border-y border-slate-200 bg-white px-6 py-20">
      <div className="mx-auto max-w-5xl">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold text-slate-900">
            Why the Common App activities section is hard for international students
          </h2>
          <p className="text-slate-500">
            You&rsquo;re not imagining it. The process genuinely has gaps that SourceLock closes.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {problems.map((p, i) => (
            <div
              key={i}
              className="rounded-xl border border-slate-200 bg-slate-50 p-6"
            >
              <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-full bg-navy-950 text-sm font-bold text-white">
                {i + 1}
              </div>
              <h3 className="mb-2 font-semibold text-slate-900">{p.title}</h3>
              <p className="text-sm leading-relaxed text-slate-600">{p.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
