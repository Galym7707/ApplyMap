import Link from "next/link";

export function LandingFooter() {
  return (
    <footer className="border-t border-slate-200 bg-slate-50 px-6 py-10">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col items-center justify-between gap-6 md:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-navy-950">
              <span className="text-[10px] font-bold text-white">SL</span>
            </div>
            <span className="text-sm font-semibold text-slate-700">SourceLock</span>
          </div>

          <div className="flex items-center gap-6 text-xs text-slate-500">
            <Link href="#" className="hover:text-slate-700">Privacy Policy</Link>
            <Link href="#" className="hover:text-slate-700">Terms of Service</Link>
            <Link href="#faq" className="hover:text-slate-700">FAQ</Link>
            <a href="mailto:hello@sourcelock.app" className="hover:text-slate-700">Contact</a>
          </div>

          <p className="text-xs text-slate-400">
            © {new Date().getFullYear()} SourceLock. Not affiliated with any university.
          </p>
        </div>

        <div className="mt-6 rounded-lg border border-amber-100 bg-amber-50 px-4 py-3 text-xs text-amber-800">
          <strong>Disclaimer:</strong> SourceLock provides informational guidance only. We do not
          guarantee admission outcomes. Public example sources (Tier B/C/D) represent community
          patterns, not official university positions. Always verify important guidance with official
          university admissions materials.
        </div>
      </div>
    </footer>
  );
}
