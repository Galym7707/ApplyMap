import { Hero } from "@/components/landing/Hero";
import { ProblemSection } from "@/components/landing/ProblemSection";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { WhyDifferent } from "@/components/landing/WhyDifferent";
import { ReportPreview } from "@/components/landing/ReportPreview";
import { TrustSection } from "@/components/landing/TrustSection";
import { PricingSection } from "@/components/landing/PricingSection";
import { FaqSection } from "@/components/landing/FaqSection";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { LandingNav } from "@/components/landing/LandingNav";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#F9F8F6]">
      <LandingNav />
      <main>
        <Hero />
        <ProblemSection />
        <HowItWorks />
        <WhyDifferent />
        <ReportPreview />
        <TrustSection />
        <PricingSection />
        <FaqSection />
      </main>
      <LandingFooter />
    </div>
  );
}
