"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { profileApi, universitiesApi, targetsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import type { University } from "@/types";

const TOTAL_STEPS = 5;

const CURRICULA = ["NIS Programme (Kazakhstan/Cambridge)", "Kazakhstan National Curriculum", "UNT/ENT preparation track", "MESK / NIS Selection Exam", "IB (International Baccalaureate)", "A-Levels", "AP (Advanced Placement)", "French Baccalaureate", "German Abitur", "CBSE", "IGCSE", "National Curriculum", "Other"];
const COUNTRIES = ["Afghanistan", "Albania", "Algeria", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bangladesh", "Belgium", "Bolivia", "Brazil", "Cambodia", "Cameroon", "Canada", "Chile", "China", "Colombia", "Congo", "Costa Rica", "Croatia", "Cuba", "Czech Republic", "Denmark", "Ecuador", "Egypt", "Ethiopia", "Finland", "France", "Germany", "Ghana", "Greece", "Guatemala", "Honduras", "Hungary", "India", "Indonesia", "Iran", "Iraq", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "South Korea", "Kuwait", "Lebanon", "Malaysia", "Mexico", "Morocco", "Nepal", "Netherlands", "New Zealand", "Nigeria", "Norway", "Pakistan", "Peru", "Philippines", "Poland", "Portugal", "Romania", "Russia", "Saudi Arabia", "Senegal", "Singapore", "South Africa", "Spain", "Sri Lanka", "Sweden", "Switzerland", "Syria", "Taiwan", "Tanzania", "Thailand", "Tunisia", "Turkey", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"];

export default function OnboardingPage() {
  const [step, setStep] = useState(1);
  const router = useRouter();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [selectedTargets, setSelectedTargets] = useState<string[]>([]);

  const { data: universitiesData } = useQuery({
    queryKey: ["universities"],
    queryFn: () => universitiesApi.list(),
  });
  const universities: University[] = universitiesData?.data?.data ?? [];

  const updateProfileMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => profileApi.update(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["profile"] }),
  });

  const addTargetMutation = useMutation({
    mutationFn: (universityId: string) => targetsApi.add({ university_id: universityId }),
  });

  const form = useForm({
    defaultValues: {
      country: "",
      graduation_year: "",
      curriculum: "",
      intended_major: "",
      sat_score: "",
      act_score: "",
      ielts_score: "",
      toefl_score: "",
    },
  });

  const progress = ((step - 1) / TOTAL_STEPS) * 100;

  const handleNext = async () => {
    const values = form.getValues();

    if (step === 1) {
      await updateProfileMutation.mutateAsync({
        graduation_year: values.graduation_year ? parseInt(values.graduation_year) : undefined,
        curriculum: values.curriculum || undefined,
      });
    } else if (step === 2) {
      await updateProfileMutation.mutateAsync({
        intended_major: values.intended_major || undefined,
      });
    } else if (step === 3) {
      await updateProfileMutation.mutateAsync({
        sat_score: values.sat_score ? parseInt(values.sat_score) : undefined,
        act_score: values.act_score ? parseInt(values.act_score) : undefined,
        ielts_score: values.ielts_score || undefined,
        toefl_score: values.toefl_score ? parseInt(values.toefl_score) : undefined,
      });
    } else if (step === 4) {
      // Add selected universities
      for (const uid of selectedTargets) {
        try {
          await addTargetMutation.mutateAsync(uid);
        } catch {}
      }
    }

    if (step < TOTAL_STEPS) {
      setStep((s) => s + 1);
    } else {
      router.push("/dashboard");
    }
  };

  const stepTitles = [
    "Academic context",
    "Major interests",
    "Test scores",
    "Target universities",
    "All set!",
  ];

  return (
    <div className="flex min-h-screen items-start justify-center bg-[#F9F8F6] px-4 py-12">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="mb-1 flex items-center justify-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded bg-navy-950">
              <span className="text-xs font-bold text-white">SL</span>
            </div>
            <span className="text-sm font-semibold text-slate-700">SourceLock</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Let&rsquo;s set up your profile</h1>
          <p className="mt-1 text-sm text-slate-500">
            Step {step} of {TOTAL_STEPS} — {stepTitles[step - 1]}
          </p>
        </div>

        {/* Progress */}
        <Progress value={progress} className="mb-8 h-1.5" />

        {/* Step content */}
        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          {step === 1 && (
            <div className="space-y-5">
              <h2 className="text-lg font-semibold text-slate-900">Academic context</h2>
              <div className="space-y-1.5">
                <Label>Country</Label>
                <select
                  {...form.register("country")}
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                >
                  <option value="">Select your country</option>
                  {COUNTRIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label>Graduation year</Label>
                <Input
                  type="number"
                  placeholder="2025"
                  min={2024}
                  max={2030}
                  {...form.register("graduation_year")}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Curriculum</Label>
                <select
                  {...form.register("curriculum")}
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                >
                  <option value="">Select your curriculum</option>
                  {CURRICULA.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-5">
              <h2 className="text-lg font-semibold text-slate-900">What do you want to study?</h2>
              <p className="text-sm text-slate-500">
                This helps us weight your activities by major relevance. You can change it later.
              </p>
              <div className="space-y-1.5">
                <Label>Intended major / field of study</Label>
                <Input
                  placeholder="e.g. Computer Science, Economics, Biology..."
                  {...form.register("intended_major")}
                />
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-5">
              <h2 className="text-lg font-semibold text-slate-900">Test scores (optional)</h2>
              <p className="text-sm text-slate-500">
                All fields are optional. Only fill in scores you actually have.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>SAT</Label>
                  <Input type="number" placeholder="1600" min={400} max={1600} {...form.register("sat_score")} />
                </div>
                <div className="space-y-1.5">
                  <Label>ACT</Label>
                  <Input type="number" placeholder="36" min={1} max={36} {...form.register("act_score")} />
                </div>
                <div className="space-y-1.5">
                  <Label>IELTS</Label>
                  <Input placeholder="7.5" {...form.register("ielts_score")} />
                </div>
                <div className="space-y-1.5">
                  <Label>TOEFL</Label>
                  <Input type="number" placeholder="110" min={0} max={120} {...form.register("toefl_score")} />
                </div>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-5">
              <h2 className="text-lg font-semibold text-slate-900">Select target universities</h2>
              <p className="text-sm text-slate-500">
                Pick the schools you&rsquo;re applying to. You can add or remove later.
              </p>
              <div className="space-y-2">
                {universities.map((uni) => (
                  <button
                    key={uni.id}
                    type="button"
                    onClick={() =>
                      setSelectedTargets((prev) =>
                        prev.includes(uni.id) ? prev.filter((id) => id !== uni.id) : [...prev, uni.id]
                      )
                    }
                    className={cn(
                      "w-full rounded-lg border p-3 text-left transition-colors",
                      selectedTargets.includes(uni.id)
                        ? "border-navy-950 bg-navy-50"
                        : "border-slate-200 hover:border-slate-300"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-slate-900">{uni.name}</p>
                        <p className="text-xs text-slate-500">{uni.country}</p>
                      </div>
                      <div
                        className={cn(
                          "h-4 w-4 rounded-full border-2",
                          selectedTargets.includes(uni.id)
                            ? "border-navy-950 bg-navy-950"
                            : "border-slate-300"
                        )}
                      />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {step === 5 && (
            <div className="py-4 text-center space-y-4">
              <div className="flex justify-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100">
                  <span className="text-3xl">🎯</span>
                </div>
              </div>
              <h2 className="text-xl font-bold text-slate-900">Profile complete!</h2>
              <p className="text-sm text-slate-500">
                Now add your activities and honors to your vault, then generate your first optimization report.
              </p>
            </div>
          )}

          <div className="mt-8 flex justify-between">
            {step > 1 ? (
              <Button variant="outline" onClick={() => setStep((s) => s - 1)}>
                Back
              </Button>
            ) : (
              <div />
            )}
            <Button
              className="bg-navy-950 text-white hover:bg-navy-900"
              onClick={handleNext}
              disabled={updateProfileMutation.isPending}
            >
              {step === TOTAL_STEPS ? "Go to dashboard" : "Continue"}
            </Button>
          </div>
        </div>

        {step < TOTAL_STEPS && (
          <button
            className="mt-4 w-full text-sm text-slate-400 hover:text-slate-600"
            onClick={() => router.push("/dashboard")}
          >
            Skip for now
          </button>
        )}
      </div>
    </div>
  );
}
