import Link from "next/link";
import { Button } from "@/components/ui/button";

export function LandingNav() {
  return (
    <nav className="sticky top-0 z-50 border-b border-slate-200/80 bg-[#F9F8F6]/90 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-navy-950">
            <span className="text-xs font-bold text-white">SL</span>
          </div>
          <span className="text-base font-semibold text-slate-900">SourceLock</span>
        </Link>
        <div className="hidden items-center gap-8 md:flex">
          <Link href="#how-it-works" className="text-sm text-slate-600 hover:text-slate-900 transition-colors">
            How it works
          </Link>
          <Link href="#pricing" className="text-sm text-slate-600 hover:text-slate-900 transition-colors">
            Pricing
          </Link>
          <Link href="#faq" className="text-sm text-slate-600 hover:text-slate-900 transition-colors">
            FAQ
          </Link>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/sign-in">
            <Button variant="ghost" size="sm" className="text-slate-600">
              Sign in
            </Button>
          </Link>
          <Link href="/sign-up">
            <Button size="sm" className="bg-navy-950 text-white hover:bg-navy-900">
              Get started
            </Button>
          </Link>
        </div>
      </div>
    </nav>
  );
}
