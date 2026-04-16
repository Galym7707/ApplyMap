"use client";

import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { profileApi, targetsApi, universitiesApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import type { University } from "@/types";

const TOTAL_STEPS = 6;
const STEP_TITLES = ["Academic context", "Major interests", "Test scores", "Preferences", "Target universities", "All set!"];
const STEP_NOTES = [
  "Anchor the profile to your curriculum and graduation timing.",
  "This drives relevance in ranking and recommendations.",
  "Add only the exams you already have.",
  "These settings power the Common App recommender.",
  "Choose a shortlist to carry into university advisors.",
  "Move into the dashboard and start the workflow.",
];

const CURRICULA = ["NIS Grade 12 Certificate", "NIS Programme (Kazakhstan/Cambridge)", "Kazakhstan National Curriculum", "UNT/ENT preparation track", "IB (International Baccalaureate)", "A-Levels", "AP (Advanced Placement)", "French Baccalaureate", "German Abitur", "CBSE", "IGCSE", "National Curriculum", "Other"];
const COUNTRIES = ["Afghanistan", "Albania", "Algeria", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bangladesh", "Belgium", "Bolivia", "Brazil", "Cambodia", "Cameroon", "Canada", "Chile", "China", "Colombia", "Congo", "Costa Rica", "Croatia", "Cuba", "Czech Republic", "Denmark", "Ecuador", "Egypt", "Ethiopia", "Finland", "France", "Germany", "Ghana", "Greece", "Guatemala", "Honduras", "Hungary", "India", "Indonesia", "Iran", "Iraq", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "South Korea", "Kuwait", "Lebanon", "Malaysia", "Mexico", "Morocco", "Nepal", "Netherlands", "New Zealand", "Nigeria", "Norway", "Pakistan", "Peru", "Philippines", "Poland", "Portugal", "Romania", "Russia", "Saudi Arabia", "Senegal", "Singapore", "South Africa", "Spain", "Sri Lanka", "Sweden", "Switzerland", "Syria", "Taiwan", "Tanzania", "Thailand", "Tunisia", "Turkey", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"];

function csvToArray(value: string) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

export default function OnboardingPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [step, setStep] = useState(1);
  const [selectedTargets, setSelectedTargets] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [loadedProfile, setLoadedProfile] = useState(false);

  const { data: universitiesData, isLoading: isUniversitiesLoading } = useQuery({
    queryKey: ["universities"],
    queryFn: () => universitiesApi.list(),
  });
  const { data: profileData } = useQuery({
    queryKey: ["profile"],
    queryFn: () => profileApi.get(),
  });
  const universities: University[] = universitiesData?.data?.data ?? [];

  const filteredUniversities = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return universities;
    return universities.filter((uni) =>
      [uni.name, uni.country, uni.city, uni.short_description].filter(Boolean).some((value) =>
        String(value).toLowerCase().includes(term)
      )
    );
  }, [search, universities]);

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
      sat_math: "",
      sat_ebrw: "",
      act_score: "",
      ielts_score: "",
      ielts_listening: "",
      ielts_reading: "",
      ielts_writing: "",
      ielts_speaking: "",
      toefl_score: "",
      toefl_reading: "",
      toefl_listening: "",
      toefl_speaking: "",
      toefl_writing: "",
      duolingo_score: "",
      a_level_subjects: "",
      a_level_predicted: "",
      ap_subjects: "",
      ib_predicted_score: "",
      unt_score: "",
      nis_grade12_certificate_gpa: "",
      preferred_countries: "United States, United Arab Emirates, Canada",
      preferred_regions: "USA, Abu Dhabi / UAE, Canada, Hong Kong, Korea, Japan, Europe",
      teaching_language: "English",
      school_years: "11",
      needs_full_ride: true,
    },
  });

  useEffect(() => {
    if (loadedProfile || !profileData?.data?.data) return;
    const { user, profile } = profileData.data.data;
    const saved = profile?.application_preferences_json ?? {};
    form.reset({
      country: user?.country ?? "",
      graduation_year: profile?.graduation_year ? String(profile.graduation_year) : "",
      curriculum: profile?.curriculum ?? "",
      intended_major: profile?.intended_major ?? "",
      sat_score: profile?.sat_score ? String(profile.sat_score) : "",
      sat_math: profile?.sat_math ? String(profile.sat_math) : "",
      sat_ebrw: profile?.sat_ebrw ? String(profile.sat_ebrw) : "",
      act_score: profile?.act_score ? String(profile.act_score) : "",
      ielts_score: profile?.ielts_score ?? "",
      ielts_listening: profile?.ielts_listening ?? "",
      ielts_reading: profile?.ielts_reading ?? "",
      ielts_writing: profile?.ielts_writing ?? "",
      ielts_speaking: profile?.ielts_speaking ?? "",
      toefl_score: profile?.toefl_score ? String(profile.toefl_score) : "",
      toefl_reading: profile?.toefl_reading ? String(profile.toefl_reading) : "",
      toefl_listening: profile?.toefl_listening ? String(profile.toefl_listening) : "",
      toefl_speaking: profile?.toefl_speaking ? String(profile.toefl_speaking) : "",
      toefl_writing: profile?.toefl_writing ? String(profile.toefl_writing) : "",
      duolingo_score: profile?.duolingo_score ? String(profile.duolingo_score) : "",
      a_level_subjects: profile?.a_level_subjects ?? "",
      a_level_predicted: profile?.a_level_predicted ?? "",
      ap_subjects: profile?.ap_subjects ?? "",
      ib_predicted_score: profile?.ib_predicted_score ? String(profile.ib_predicted_score) : "",
      unt_score: profile?.unt_score ? String(profile.unt_score) : "",
      nis_grade12_certificate_gpa: profile?.nis_grade12_certificate_gpa ?? "",
      preferred_countries: Array.isArray(saved.preferred_countries) ? saved.preferred_countries.join(", ") : "United States, United Arab Emirates, Canada",
      preferred_regions: Array.isArray(saved.preferred_regions) ? saved.preferred_regions.join(", ") : "USA, Abu Dhabi / UAE, Canada, Hong Kong, Korea, Japan, Europe",
      teaching_language: typeof saved.teaching_language === "string" ? saved.teaching_language : "English",
      school_years: saved.school_years ? String(saved.school_years) : "11",
      needs_full_ride: typeof saved.needs_full_ride === "boolean" ? saved.needs_full_ride : true,
    });
    setLoadedProfile(true);
  }, [form, loadedProfile, profileData]);

  const handleNext = async () => {
    const values = form.getValues();

    if (step === 1) {
      if (values.country) {
        await profileApi.updateUser({ country: values.country });
        queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      }
      await updateProfileMutation.mutateAsync({
        graduation_year: values.graduation_year ? parseInt(values.graduation_year, 10) : undefined,
        curriculum: values.curriculum || undefined,
      });
    } else if (step === 2) {
      await updateProfileMutation.mutateAsync({ intended_major: values.intended_major || undefined });
    } else if (step === 3) {
      await updateProfileMutation.mutateAsync({
        sat_score: values.sat_score ? parseInt(values.sat_score, 10) : undefined,
        sat_math: values.sat_math ? parseInt(values.sat_math, 10) : undefined,
        sat_ebrw: values.sat_ebrw ? parseInt(values.sat_ebrw, 10) : undefined,
        act_score: values.act_score ? parseInt(values.act_score, 10) : undefined,
        ielts_score: values.ielts_score || undefined,
        ielts_listening: values.ielts_listening || undefined,
        ielts_reading: values.ielts_reading || undefined,
        ielts_writing: values.ielts_writing || undefined,
        ielts_speaking: values.ielts_speaking || undefined,
        toefl_score: values.toefl_score ? parseInt(values.toefl_score, 10) : undefined,
        toefl_reading: values.toefl_reading ? parseInt(values.toefl_reading, 10) : undefined,
        toefl_listening: values.toefl_listening ? parseInt(values.toefl_listening, 10) : undefined,
        toefl_speaking: values.toefl_speaking ? parseInt(values.toefl_speaking, 10) : undefined,
        toefl_writing: values.toefl_writing ? parseInt(values.toefl_writing, 10) : undefined,
        duolingo_score: values.duolingo_score ? parseInt(values.duolingo_score, 10) : undefined,
        a_level_subjects: values.a_level_subjects || undefined,
        a_level_predicted: values.a_level_predicted || undefined,
        ap_subjects: values.ap_subjects || undefined,
        ib_predicted_score: values.ib_predicted_score ? parseInt(values.ib_predicted_score, 10) : undefined,
        unt_score: values.unt_score ? parseInt(values.unt_score, 10) : undefined,
        nis_grade12_certificate_gpa: values.nis_grade12_certificate_gpa || undefined,
      });
    } else if (step === 4) {
      await updateProfileMutation.mutateAsync({
        application_preferences_json: {
          preferred_countries: csvToArray(values.preferred_countries),
          preferred_regions: csvToArray(values.preferred_regions),
          teaching_language: values.teaching_language || undefined,
          school_years: values.school_years ? parseInt(values.school_years, 10) : undefined,
          intended_major: values.intended_major || undefined,
          needs_full_ride: values.needs_full_ride,
        },
      });
    } else if (step === 5) {
      for (const universityId of selectedTargets) {
        try {
          await addTargetMutation.mutateAsync(universityId);
        } catch {}
      }
    }

    if (step < TOTAL_STEPS) {
      setStep((current) => current + 1);
    } else {
      router.push("/dashboard");
    }
  };

  const selectedPreview = universities.filter((uni) => selectedTargets.includes(uni.id));
  const isSaving = updateProfileMutation.isPending || addTargetMutation.isPending;

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#f7f5ef]">
      <div className="absolute inset-x-0 top-0 h-72 bg-[radial-gradient(circle_at_top_left,_rgba(33,39,143,0.16),_transparent_42%),radial-gradient(circle_at_top_right,_rgba(15,118,110,0.12),_transparent_36%)]" />
      <div className="absolute -left-12 top-24 h-56 w-56 rounded-full bg-amber-200/30 blur-3xl" />
      <div className="absolute -right-12 bottom-0 h-72 w-72 rounded-full bg-navy-200/30 blur-3xl" />

      <div className="relative mx-auto flex min-h-screen max-w-7xl flex-col gap-6 px-4 py-8 lg:flex-row lg:px-8 lg:py-10">
        <aside className="lg:w-[320px] lg:shrink-0">
          <div className="rounded-[28px] border border-white/70 bg-white/85 p-6 shadow-[0_18px_60px_rgba(15,23,42,0.08)] backdrop-blur">
            <div className="mb-5 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-navy-950 text-sm font-bold text-white">SL</div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">SourceLock</p>
                <p className="text-sm font-medium text-slate-700">Profile setup</p>
              </div>
            </div>

            <div className="rounded-2xl bg-slate-950 px-5 py-5 text-white">
              <p className="text-xs uppercase tracking-[0.2em] text-white/60">Current step</p>
              <h1 className="mt-3 text-2xl font-semibold">{STEP_TITLES[step - 1]}</h1>
              <p className="mt-2 text-sm leading-relaxed text-white/72">{STEP_NOTES[step - 1]}</p>
              <div className="mt-5">
                <div className="mb-2 flex items-center justify-between text-xs text-white/70">
                  <span>Progress</span>
                  <span>{step}/{TOTAL_STEPS}</span>
                </div>
                <Progress value={(step / TOTAL_STEPS) * 100} className="h-1.5 bg-white/15" />
              </div>
            </div>

            <div className="mt-5 space-y-2">
              {STEP_TITLES.map((title, index) => {
                const stepNumber = index + 1;
                const isActive = stepNumber === step;
                const isComplete = stepNumber < step;
                return (
                  <div key={title} className={cn("flex items-center gap-3 rounded-2xl border px-4 py-3", isActive ? "border-navy-200 bg-navy-50" : isComplete ? "border-emerald-100 bg-emerald-50/70" : "border-slate-200 bg-white")}>
                    <div className={cn("flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold", isActive ? "bg-navy-950 text-white" : isComplete ? "bg-emerald-500 text-white" : "bg-slate-100 text-slate-500")}>
                      {isComplete ? "✓" : stepNumber}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-800">{title}</p>
                      <p className="text-xs text-slate-500">{STEP_NOTES[index]}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </aside>

        <main className="flex-1">
          <div className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur sm:p-8 lg:p-10">
            <div className="mb-8 flex flex-col gap-4 border-b border-slate-100 pb-6 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Step {step} of {TOTAL_STEPS}</p>
                <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">{STEP_TITLES[step - 1]}</h2>
              </div>
              <div className="grid grid-cols-3 gap-3 sm:w-[320px]">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3"><p className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Prefs</p><p className="mt-1 text-lg font-semibold text-slate-900">Saved</p></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3"><p className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Targets</p><p className="mt-1 text-lg font-semibold text-slate-900">{selectedTargets.length}</p></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3"><p className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Ready</p><p className="mt-1 text-lg font-semibold text-slate-900">{Math.round((step / TOTAL_STEPS) * 100)}%</p></div>
              </div>
            </div>

            {step === 1 && (
              <div className="grid gap-5 md:grid-cols-2">
                <div className="space-y-2 md:col-span-2"><p className="text-sm leading-relaxed text-slate-500">We use this context to calibrate fit, shortlist suggestions, and the first report narrative.</p></div>
                <div className="space-y-2">
                  <Label>Country</Label>
                  <select {...form.register("country")} className="flex h-11 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm shadow-sm outline-none transition focus:border-navy-300 focus:ring-2 focus:ring-navy-100">
                    <option value="">Select your country</option>
                    {COUNTRIES.map((country) => <option key={country} value={country}>{country}</option>)}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Graduation year</Label>
                  <Input type="number" min={2024} max={2035} placeholder="2026" className="h-11 rounded-xl" {...form.register("graduation_year")} />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label>Curriculum</Label>
                  <select {...form.register("curriculum")} className="flex h-11 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm shadow-sm outline-none transition focus:border-navy-300 focus:ring-2 focus:ring-navy-100">
                    <option value="">Select your curriculum</option>
                    {CURRICULA.map((curriculum) => <option key={curriculum} value={curriculum}>{curriculum}</option>)}
                  </select>
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-6">
                <p className="text-sm leading-relaxed text-slate-500">This field has outsized impact on recommendation quality, so it is worth setting clearly now.</p>
                <div className="grid gap-4 md:grid-cols-3">
                  {["Computer Science", "Economics", "Mechanical Engineering"].map((suggestion) => (
                    <button key={suggestion} type="button" onClick={() => form.setValue("intended_major", suggestion)} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-left transition hover:border-navy-300 hover:bg-navy-50">
                      <p className="text-xs uppercase tracking-[0.16em] text-slate-400">Quick fill</p>
                      <p className="mt-2 text-sm font-medium text-slate-900">{suggestion}</p>
                    </button>
                  ))}
                </div>
                <div className="space-y-2">
                  <Label>Intended major or field of study</Label>
                  <Input placeholder="e.g. Computer Science, Petroleum Engineering, Economics" className="h-11 rounded-xl" {...form.register("intended_major")} />
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2 md:col-span-2"><p className="text-sm leading-relaxed text-slate-500">These inputs are optional. Skip anything you do not already have.</p></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 md:col-span-2">
                  <Label>SAT</Label>
                  <div className="mt-2 grid gap-3 md:grid-cols-3">
                    <Input type="number" min={400} max={1600} placeholder="Total 1450" className="h-11 rounded-xl" {...form.register("sat_score")} />
                    <Input type="number" min={200} max={800} placeholder="Math 760" className="h-11 rounded-xl" {...form.register("sat_math")} />
                    <Input type="number" min={200} max={800} placeholder="Reading/Writing 690" className="h-11 rounded-xl" {...form.register("sat_ebrw")} />
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><Label>ACT</Label><Input type="number" min={1} max={36} placeholder="32" className="mt-2 h-11 rounded-xl" {...form.register("act_score")} /></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><Label>Duolingo English Test</Label><Input type="number" min={10} max={160} placeholder="135" className="mt-2 h-11 rounded-xl" {...form.register("duolingo_score")} /></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 md:col-span-2">
                  <Label>IELTS</Label>
                  <div className="mt-2 grid gap-3 md:grid-cols-5">
                    <Input placeholder="Overall 7.5" className="h-11 rounded-xl" {...form.register("ielts_score")} />
                    <Input placeholder="Listening" className="h-11 rounded-xl" {...form.register("ielts_listening")} />
                    <Input placeholder="Reading" className="h-11 rounded-xl" {...form.register("ielts_reading")} />
                    <Input placeholder="Writing" className="h-11 rounded-xl" {...form.register("ielts_writing")} />
                    <Input placeholder="Speaking" className="h-11 rounded-xl" {...form.register("ielts_speaking")} />
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 md:col-span-2">
                  <Label>TOEFL iBT</Label>
                  <div className="mt-2 grid gap-3 md:grid-cols-5">
                    <Input type="number" min={0} max={120} placeholder="Total 105" className="h-11 rounded-xl" {...form.register("toefl_score")} />
                    <Input type="number" min={0} max={30} placeholder="Reading" className="h-11 rounded-xl" {...form.register("toefl_reading")} />
                    <Input type="number" min={0} max={30} placeholder="Listening" className="h-11 rounded-xl" {...form.register("toefl_listening")} />
                    <Input type="number" min={0} max={30} placeholder="Speaking" className="h-11 rounded-xl" {...form.register("toefl_speaking")} />
                    <Input type="number" min={0} max={30} placeholder="Writing" className="h-11 rounded-xl" {...form.register("toefl_writing")} />
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><Label>A-Level subjects</Label><Input placeholder="Math A*, Physics A, CS A" className="mt-2 h-11 rounded-xl" {...form.register("a_level_subjects")} /></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><Label>A-Level predicted</Label><Input placeholder="A*A*A" className="mt-2 h-11 rounded-xl" {...form.register("a_level_predicted")} /></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><Label>IB predicted score</Label><Input type="number" min={1} max={45} placeholder="40" className="mt-2 h-11 rounded-xl" {...form.register("ib_predicted_score")} /></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><Label>AP subjects</Label><Input placeholder="Calc BC 5, Physics C 5" className="mt-2 h-11 rounded-xl" {...form.register("ap_subjects")} /></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><Label>UNT / ENT</Label><Input type="number" min={0} placeholder="Score" className="mt-2 h-11 rounded-xl" {...form.register("unt_score")} /></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4"><Label>NIS Grade 12 Certificate</Label><Input placeholder="GPA / predicted result" className="mt-2 h-11 rounded-xl" {...form.register("nis_grade12_certificate_gpa")} /></div>
              </div>
            )}

            {step === 4 && (
              <div className="grid gap-5 xl:grid-cols-[1.4fr_0.9fr]">
                <div className="space-y-5">
                  <div className="space-y-2"><Label>Preferred countries</Label><Input placeholder="United States, Canada, UAE" className="h-11 rounded-xl" {...form.register("preferred_countries")} /></div>
                  <div className="space-y-2"><Label>Preferred regions</Label><Input placeholder="USA, Abu Dhabi / UAE, Canada" className="h-11 rounded-xl" {...form.register("preferred_regions")} /></div>
                  <div className="grid gap-5 md:grid-cols-2">
                    <div className="space-y-2"><Label>Teaching language</Label><Input placeholder="English" className="h-11 rounded-xl" {...form.register("teaching_language")} /></div>
                    <div className="space-y-2"><Label>Years of school completed</Label><Input type="number" min={10} max={13} placeholder="11" className="h-11 rounded-xl" {...form.register("school_years")} /></div>
                  </div>
                </div>
                <div className="rounded-3xl bg-slate-950 p-5 text-white">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/55">Funding posture</p>
                  <h3 className="mt-3 text-xl font-semibold">Tell the recommender how strict to be.</h3>
                  <label className="mt-5 flex items-start gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-4 text-sm leading-relaxed text-white/82">
                    <input type="checkbox" className="mt-1 h-4 w-4 rounded border-white/30" {...form.register("needs_full_ride")} />
                    <span>I need a full-ride or full-funding route. Keep the shortlist anchored to realistic affordability.</span>
                  </label>
                </div>
              </div>
            )}

            {step === 5 && (
              <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
                <div className="rounded-3xl border border-slate-200 bg-slate-50/70 p-4">
                  <div className="mb-3 flex items-end justify-between gap-3">
                    <div><p className="text-sm font-semibold text-slate-900">Available universities</p><p className="text-xs text-slate-500">{filteredUniversities.length} shown</p></div>
                    <div className="w-full max-w-xs"><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by university or country" className="h-11 rounded-xl bg-white" /></div>
                  </div>
                  <div className="max-h-[26rem] space-y-2 overflow-y-auto pr-1">
                    {isUniversitiesLoading ? Array.from({ length: 5 }).map((_, index) => (
                      <div key={index} className="animate-pulse rounded-2xl border border-slate-200 bg-white px-4 py-4"><div className="h-4 w-40 rounded bg-slate-200" /><div className="mt-2 h-3 w-24 rounded bg-slate-100" /></div>
                    )) : filteredUniversities.length ? filteredUniversities.map((university) => {
                      const isSelected = selectedTargets.includes(university.id);
                      return (
                        <button key={university.id} type="button" onClick={() => setSelectedTargets((current) => current.includes(university.id) ? current.filter((id) => id !== university.id) : [...current, university.id])} className={cn("w-full rounded-2xl border px-4 py-4 text-left transition", isSelected ? "border-navy-300 bg-navy-50 shadow-sm" : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50")}>
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="text-sm font-semibold text-slate-900">{university.name}</p>
                              <p className="mt-1 text-xs text-slate-500">{[university.country, university.city].filter(Boolean).join(" • ")}</p>
                              {university.short_description && <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-slate-600">{university.short_description}</p>}
                            </div>
                            <div className={cn("mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2", isSelected ? "border-navy-950 bg-navy-950 text-[10px] text-white" : "border-slate-300 bg-white")}>{isSelected ? "✓" : ""}</div>
                          </div>
                        </button>
                      );
                    }) : <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-4 py-10 text-center text-sm text-slate-500">No universities match this search.</div>}
                  </div>
                </div>

                <div className="rounded-3xl bg-slate-950 p-5 text-white">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/55">Selection summary</p>
                  <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 px-4 py-4">
                    <p className="text-3xl font-semibold">{selectedTargets.length}</p>
                    <p className="mt-1 text-sm text-white/70">universities selected</p>
                  </div>
                  <div className="mt-4 max-h-[18rem] space-y-2 overflow-y-auto pr-1">
                    {selectedPreview.length ? selectedPreview.map((university) => (
                      <div key={university.id} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                        <p className="text-sm font-medium text-white">{university.name}</p>
                        <p className="mt-1 text-xs text-white/60">{university.country}</p>
                      </div>
                    )) : <div className="rounded-2xl border border-dashed border-white/15 px-4 py-8 text-center text-sm text-white/60">Pick a few targets to start the workflow with realistic examples.</div>}
                  </div>
                </div>
              </div>
            )}

            {step === 6 && (
              <div className="space-y-6 py-4 text-center">
                <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-emerald-100 text-4xl">🎯</div>
                <div>
                  <h3 className="text-3xl font-semibold tracking-tight text-slate-900">Profile complete</h3>
              <p className="mx-auto mt-3 max-w-2xl text-sm leading-relaxed text-slate-500">You are ready to move into the dashboard, add achievements, and generate the first university advisor.</p>
                </div>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-5"><p className="text-xs uppercase tracking-[0.16em] text-slate-400">Major</p><p className="mt-2 text-sm font-semibold text-slate-900">{form.getValues("intended_major") || "To be refined"}</p></div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-5"><p className="text-xs uppercase tracking-[0.16em] text-slate-400">Targets</p><p className="mt-2 text-sm font-semibold text-slate-900">{selectedTargets.length} selected</p></div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-5"><p className="text-xs uppercase tracking-[0.16em] text-slate-400">Next step</p><p className="mt-2 text-sm font-semibold text-slate-900">Fill the vault and open advisors</p></div>
                </div>
              </div>
            )}

            <div className="mt-10 flex flex-col gap-3 border-t border-slate-100 pt-6 sm:flex-row sm:items-center sm:justify-between">
              {step > 1 ? <Button variant="outline" onClick={() => setStep((current) => current - 1)}>Back</Button> : <div />}
              <div className="flex flex-col gap-3 sm:flex-row">
                {step < TOTAL_STEPS && <Button variant="ghost" className="text-slate-500 hover:text-slate-700" onClick={() => router.push("/dashboard")}>Skip for now</Button>}
                <Button className="bg-navy-950 text-white hover:bg-navy-900" onClick={handleNext} disabled={isSaving}>
                  {isSaving ? "Saving..." : step === TOTAL_STEPS ? "Go to dashboard" : "Continue"}
                </Button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
