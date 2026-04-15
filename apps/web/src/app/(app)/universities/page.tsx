"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { achievementsApi, profileApi, reportsApi, targetsApi, universitiesApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { useRouter } from "next/navigation";
import { CheckCircle, FileText, Loader2, Plus, Search, SlidersHorizontal, Sparkles } from "lucide-react";
import { toast } from "sonner";
import type { Achievement, CommonAppRecommendation, StudentProfile, TargetUniversity, University } from "@/types";

const PRESET_LABELS: Record<string, string> = {
  research_heavy: "Research-heavy",
  leadership_heavy: "Leadership-heavy",
  balanced_holistic: "Balanced holistic",
  community_service_heavy: "Community service",
};

const PRESET_COLORS: Record<string, string> = {
  research_heavy: "bg-blue-100 text-blue-800",
  leadership_heavy: "bg-amber-100 text-amber-800",
  balanced_holistic: "bg-slate-100 text-slate-800",
  community_service_heavy: "bg-emerald-100 text-emerald-800",
};

const AID_LABELS: Record<string, string> = {
  need_blind_full_need: "Need-blind full need",
  need_aware_full_need: "Need-aware full need",
  need_based_possible: "Need-based possible",
  merit_full_ride_possible: "Merit full ride possible",
  merit_full_tuition_possible: "Merit full tuition possible",
  need_and_merit_full_ride_possible: "Need + merit full ride possible",
  government_full_funding_possible: "Government full funding route",
  partial_scholarship_possible: "Partial scholarship",
};

const COUNTRIES = ["", "United States", "United Arab Emirates", "Hong Kong", "South Korea", "Japan", "Canada", "France", "Italy", "Hungary"];
const REGIONS = ["", "USA", "Abu Dhabi / UAE", "Hong Kong", "Korea", "Japan", "Canada", "Europe"];
const SORTS = [
  { value: "name", label: "Name" },
  { value: "aid_type", label: "Need policy" },
  { value: "aid_strength", label: "Aid strength" },
  { value: "selectivity_score", label: "Selectivity" },
  { value: "education_years_required", label: "School years required" },
];

const FIT_CATEGORY_LABELS = {
  dream: "Dream",
  target: "Target",
  safe: "Safe",
} as const;

function csvToArray(value: string) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function averageAchievementScore(achievement: Achievement) {
  const scores = [
    achievement.major_relevance_score,
    achievement.selectivity_score,
    achievement.continuity_score,
    achievement.distinctiveness_score,
  ].filter((score): score is number => typeof score === "number");

  if (!scores.length) return null;
  return Math.round((scores.reduce((sum, score) => sum + score, 0) / scores.length) * 10) / 10;
}

function SelectionColumn({
  title,
  count,
  limit,
  items,
  selectedIds,
  onToggle,
  emptyText,
}: {
  title: string;
  count: number;
  limit: number;
  items: Achievement[];
  selectedIds: string[];
  onToggle: (id: string) => void;
  emptyText: string;
}) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <Label className="text-sm font-semibold text-slate-900">{title}</Label>
        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
          {count}/{limit}
        </span>
      </div>

      <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
        {items.length ? (
          items.map((item) => {
            const isSelected = selectedIds.includes(item.id);
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onToggle(item.id)}
                className={cn(
                  "w-full rounded-2xl border p-3 text-left transition",
                  isSelected
                    ? "border-navy-300 bg-navy-50 shadow-sm"
                    : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-slate-900">{item.title}</p>
                    {item.organization_name && (
                      <p className="mt-1 text-xs text-slate-500">{item.organization_name}</p>
                    )}
                  </div>
                  <div className="text-xs font-medium text-slate-500">
                    {averageAchievementScore(item) ?? "Pending"}
                  </div>
                </div>
              </button>
            );
          })
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-500">
            {emptyText}
          </div>
        )}
      </div>
    </div>
  );
}

export default function UniversitiesPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [generatingId, setGeneratingId] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<CommonAppRecommendation[]>([]);
  const [selectedHonorIds, setSelectedHonorIds] = useState<string[]>([]);
  const [selectedActivityIds, setSelectedActivityIds] = useState<string[]>([]);
  const [loadedSavedPrefs, setLoadedSavedPrefs] = useState(false);
  const [filters, setFilters] = useState({
    search: "",
    country: "",
    region: "",
    application_system: "",
    teaching_language: "",
    major: "",
    school_years: "",
    full_ride_only: false,
    common_app_only: false,
    aid_type: "",
    sort_by: "name",
    sort_dir: "asc",
  });
  const [prefs, setPrefs] = useState({
    preferred_countries: "United States, United Arab Emirates, Canada",
    preferred_regions: "USA, Abu Dhabi / UAE, Canada, Hong Kong, Korea, Japan, Europe",
    teaching_language: "English",
    school_years: "11",
    intended_major: "",
    needs_full_ride: true,
  });

  const { data: universitiesData, isLoading } = useQuery({
    queryKey: ["universities", filters],
    queryFn: () =>
      universitiesApi.list({
        ...filters,
        school_years: filters.school_years || undefined,
      }),
  });

  const { data: targetsData } = useQuery({
    queryKey: ["targets"],
    queryFn: () => targetsApi.list(),
  });

  const { data: achievementsData } = useQuery({
    queryKey: ["achievements"],
    queryFn: () => achievementsApi.list(),
  });

  const { data: profileData } = useQuery({
    queryKey: ["profile"],
    queryFn: () => profileApi.get(),
  });

  const profile: StudentProfile | undefined = profileData?.data?.data?.profile;
  const achievements: Achievement[] = achievementsData?.data?.data ?? [];
  const honors = achievements.filter((item) => item.type === "honor");
  const activities = achievements.filter((item) => item.type === "activity");
  const universities: University[] = universitiesData?.data?.data ?? [];
  const targets: TargetUniversity[] = targetsData?.data?.data ?? [];
  const targetUniversityIds = new Set(targets.map((target) => target.university_id));

  useEffect(() => {
    if (!profile || loadedSavedPrefs) return;
    const saved = (profile.application_preferences_json ?? {}) as Record<string, unknown>;
    setPrefs((current) => ({
      ...current,
      preferred_countries: Array.isArray(saved.preferred_countries)
        ? saved.preferred_countries.join(", ")
        : current.preferred_countries,
      preferred_regions: Array.isArray(saved.preferred_regions)
        ? saved.preferred_regions.join(", ")
        : current.preferred_regions,
      teaching_language: typeof saved.teaching_language === "string" ? saved.teaching_language : current.teaching_language,
      school_years: saved.school_years ? String(saved.school_years) : current.school_years,
      intended_major: typeof saved.intended_major === "string" ? saved.intended_major : profile.intended_major ?? "",
      needs_full_ride: typeof saved.needs_full_ride === "boolean" ? saved.needs_full_ride : current.needs_full_ride,
    }));
    setSelectedHonorIds(Array.isArray(saved.top_honor_ids) ? saved.top_honor_ids.map(String).slice(0, 5) : []);
    setSelectedActivityIds(Array.isArray(saved.top_activity_ids) ? saved.top_activity_ids.map(String).slice(0, 10) : []);
    setLoadedSavedPrefs(true);
  }, [loadedSavedPrefs, profile]);

  const groupedRecommendations = useMemo(() => ({
    dream: recommendations.filter((item) => item.category === "dream"),
    target: recommendations.filter((item) => item.category === "target"),
    safe: recommendations.filter((item) => item.category === "safe"),
  }), [recommendations]);
  const targetsByCategory = useMemo(() => ({
    dream: targets.filter((item) => item.fit_category === "dream"),
    target: targets.filter((item) => item.fit_category === "target"),
    safe: targets.filter((item) => item.fit_category === "safe"),
  }), [targets]);

  const addTargetMutation = useMutation({
    mutationFn: ({ universityId, fitCategory }: { universityId: string; fitCategory: "dream" | "target" | "safe" }) =>
      targetsApi.add({ university_id: universityId, fit_category: fitCategory }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["targets"] });
      toast.success("University added to targets");
    },
    onError: () => toast.error("Already in targets or error adding"),
  });

  const recommendMutation = useMutation({
    mutationFn: () =>
      universitiesApi.recommendCommonApp({
        top_honor_ids: selectedHonorIds,
        top_activity_ids: selectedActivityIds,
        preferences: {
          preferred_countries: csvToArray(prefs.preferred_countries),
          preferred_regions: csvToArray(prefs.preferred_regions),
          teaching_language: prefs.teaching_language || undefined,
          school_years: prefs.school_years ? Number(prefs.school_years) : undefined,
          intended_major: prefs.intended_major || profile?.intended_major || undefined,
          needs_full_ride: prefs.needs_full_ride,
          common_app_only: true,
        },
        save_preferences: true,
      }),
    onSuccess: (response) => {
      setRecommendations(response.data?.data?.recommendations ?? []);
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      toast.success("Common App recommendations generated");
    },
    onError: () => toast.error("Select achievements and complete your profile first"),
  });

  const handleGenerateReport = async (university: University) => {
    setGeneratingId(university.id);
    try {
      const res = await reportsApi.generate(university.id);
      const reportId = res.data?.data?.id;
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      toast.success("Report generated");
      router.push(reportId ? `/reports/${reportId}` : "/reports");
    } catch {
      toast.error("Failed to generate report. Make sure you have achievements in your vault.");
    } finally {
      setGeneratingId(null);
    }
  };

  const toggleSelection = (id: string, type: "honor" | "activity") => {
    if (type === "honor") {
      setSelectedHonorIds((current) => {
        if (current.includes(id)) return current.filter((item) => item !== id);
        if (current.length >= 5) {
          toast.error("Common App has 5 honor slots");
          return current;
        }
        return [...current, id];
      });
      return;
    }

    setSelectedActivityIds((current) => {
      if (current.includes(id)) return current.filter((item) => item !== id);
      if (current.length >= 10) {
        toast.error("Common App has 10 activity slots");
        return current;
      }
      return [...current, id];
    });
  };

  return (
    <div className="relative overflow-hidden bg-[#f7f5ef] px-4 py-8 sm:px-6 lg:px-8">
      <div className="absolute inset-x-0 top-0 h-72 bg-[radial-gradient(circle_at_top_left,_rgba(33,39,143,0.14),_transparent_42%),radial-gradient(circle_at_top_right,_rgba(16,185,129,0.08),_transparent_38%)]" />
      <div className="relative mx-auto max-w-7xl">
        <section className="rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur sm:p-8">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-2xl">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                Shortlist workspace
              </p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">
                Universities
              </h1>
              <p className="mt-3 text-sm leading-relaxed text-slate-500">
                Filter funded options, preserve your preferences, generate a Common App shortlist,
                then move the best targets into source-backed optimization reports.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <p className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Targets</p>
                <p className="mt-1 text-2xl font-semibold text-slate-900">{targets.length}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <p className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Visible</p>
                <p className="mt-1 text-2xl font-semibold text-slate-900">{universities.length}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <p className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Honors</p>
                <p className="mt-1 text-2xl font-semibold text-slate-900">{selectedHonorIds.length}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <p className="text-[11px] uppercase tracking-[0.14em] text-slate-400">Activities</p>
                <p className="mt-1 text-2xl font-semibold text-slate-900">{selectedActivityIds.length}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-6 rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)] backdrop-blur sm:p-8">
          <div className="mb-5 flex items-center gap-2">
            <SlidersHorizontal className="h-4 w-4 text-slate-500" />
            <h2 className="text-sm font-semibold text-slate-900">Sort and filter</h2>
          </div>

          <div className="grid gap-3 md:grid-cols-4">
            <div className="relative md:col-span-2">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                placeholder="Search by university, country, or major..."
                className="h-11 rounded-xl pl-9"
                value={filters.search}
                onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))}
              />
            </div>
            <select className="h-11 rounded-xl border border-input bg-white px-3 text-sm" value={filters.country} onChange={(event) => setFilters((current) => ({ ...current, country: event.target.value }))}>
              {COUNTRIES.map((country) => <option key={country || "all"} value={country}>{country || "All countries"}</option>)}
            </select>
            <select className="h-11 rounded-xl border border-input bg-white px-3 text-sm" value={filters.region} onChange={(event) => setFilters((current) => ({ ...current, region: event.target.value }))}>
              {REGIONS.map((region) => <option key={region || "all"} value={region}>{region || "All regions"}</option>)}
            </select>
            <Input className="h-11 rounded-xl" placeholder="Major filter" value={filters.major} onChange={(event) => setFilters((current) => ({ ...current, major: event.target.value }))} />
            <Input className="h-11 rounded-xl" placeholder="Teaching language" value={filters.teaching_language} onChange={(event) => setFilters((current) => ({ ...current, teaching_language: event.target.value }))} />
            <Input className="h-11 rounded-xl" type="number" min={10} max={13} placeholder="School years" value={filters.school_years} onChange={(event) => setFilters((current) => ({ ...current, school_years: event.target.value }))} />
            <select className="h-11 rounded-xl border border-input bg-white px-3 text-sm" value={filters.aid_type} onChange={(event) => setFilters((current) => ({ ...current, aid_type: event.target.value }))}>
              <option value="">All aid routes</option>
              {Object.entries(AID_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
            <select className="h-11 rounded-xl border border-input bg-white px-3 text-sm" value={filters.sort_by} onChange={(event) => setFilters((current) => ({ ...current, sort_by: event.target.value }))}>
              {SORTS.map((sort) => <option key={sort.value} value={sort.value}>Sort: {sort.label}</option>)}
            </select>
            <select className="h-11 rounded-xl border border-input bg-white px-3 text-sm" value={filters.sort_dir} onChange={(event) => setFilters((current) => ({ ...current, sort_dir: event.target.value }))}>
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>
            <label className="flex h-11 items-center gap-2 rounded-xl border border-slate-200 px-3 text-sm">
              <input type="checkbox" checked={filters.full_ride_only} onChange={(event) => setFilters((current) => ({ ...current, full_ride_only: event.target.checked }))} />
              Full-ride possible
            </label>
            <label className="flex h-11 items-center gap-2 rounded-xl border border-slate-200 px-3 text-sm">
              <input type="checkbox" checked={filters.common_app_only} onChange={(event) => setFilters((current) => ({ ...current, common_app_only: event.target.checked }))} />
              Common App only
            </label>
            <label className="flex h-11 items-center gap-2 rounded-xl border border-slate-200 px-3 text-sm">
              <input
                type="checkbox"
                checked={filters.teaching_language.toLowerCase() === "english"}
                onChange={(event) => setFilters((current) => ({ ...current, teaching_language: event.target.checked ? "English" : "" }))}
              />
              English programs
            </label>
          </div>
        </section>

        {!!targets.length && (
          <section className="mt-6 rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)] backdrop-blur sm:p-8">
            <h2 className="text-lg font-semibold text-slate-900">Your university list</h2>
            <p className="mt-2 text-sm text-slate-500">
              Keep your own Dream, Target, and Safe list separate from the AI suggestions.
            </p>
            <div className="mt-5 grid gap-4 lg:grid-cols-3">
              {(["dream", "target", "safe"] as const).map((category) => (
                <div key={category} className="rounded-3xl border border-slate-200 bg-slate-50/70 p-5">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-slate-900">{FIT_CATEGORY_LABELS[category]}</h3>
                    <Badge variant="outline">{targetsByCategory[category].length}</Badge>
                  </div>
                  <div className="mt-4 space-y-2">
                    {targetsByCategory[category].length ? targetsByCategory[category].map((target) => (
                      <div key={target.id} className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                        <p className="text-sm font-medium text-slate-900">{target.university.name}</p>
                        <p className="mt-1 text-xs text-slate-500">{target.university.country}</p>
                      </div>
                    )) : (
                      <p className="rounded-2xl border border-dashed border-slate-200 bg-white px-4 py-6 text-center text-sm text-slate-500">
                        No schools yet.
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="mt-6 rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)] backdrop-blur sm:p-8">
          <div className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div className="max-w-2xl">
              <div className="flex items-center gap-2 text-slate-900">
                <Sparkles className="h-4 w-4 text-navy-700" />
                <h2 className="text-lg font-semibold">Common App top 20 recommender</h2>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-slate-500">
                Use saved preferences plus selected honors and activities to generate a shortlist
                that is filtered for fit and funding reality.
              </p>
            </div>

            <Button
              className="gap-2 bg-navy-950 text-white hover:bg-navy-900"
              disabled={recommendMutation.isPending || (!selectedHonorIds.length && !selectedActivityIds.length)}
              onClick={() => recommendMutation.mutate()}
            >
              {recommendMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Generate Common App top 20
            </Button>
          </div>

          <div className="grid gap-5 xl:grid-cols-[1.05fr_1fr_1fr]">
            <div className="rounded-3xl bg-slate-950 p-5 text-white">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/55">
                Saved preferences
              </p>
              <div className="mt-4 space-y-3">
                <div>
                  <Label className="text-white/80">Preferred countries</Label>
                  <Input className="mt-2 h-11 rounded-xl border-white/10 bg-white/5 text-white placeholder:text-white/35" placeholder="Preferred countries" value={prefs.preferred_countries} onChange={(event) => setPrefs((current) => ({ ...current, preferred_countries: event.target.value }))} />
                </div>
                <div>
                  <Label className="text-white/80">Preferred regions</Label>
                  <Input className="mt-2 h-11 rounded-xl border-white/10 bg-white/5 text-white placeholder:text-white/35" placeholder="Preferred regions" value={prefs.preferred_regions} onChange={(event) => setPrefs((current) => ({ ...current, preferred_regions: event.target.value }))} />
                </div>
                <div>
                  <Label className="text-white/80">Teaching language</Label>
                  <Input className="mt-2 h-11 rounded-xl border-white/10 bg-white/5 text-white placeholder:text-white/35" placeholder="Teaching language" value={prefs.teaching_language} onChange={(event) => setPrefs((current) => ({ ...current, teaching_language: event.target.value }))} />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-white/80">Intended major</Label>
                    <Input className="mt-2 h-11 rounded-xl border-white/10 bg-white/5 text-white placeholder:text-white/35" placeholder="Intended major" value={prefs.intended_major} onChange={(event) => setPrefs((current) => ({ ...current, intended_major: event.target.value }))} />
                  </div>
                  <div>
                    <Label className="text-white/80">School years</Label>
                    <Input className="mt-2 h-11 rounded-xl border-white/10 bg-white/5 text-white placeholder:text-white/35" type="number" min={10} max={13} placeholder="11" value={prefs.school_years} onChange={(event) => setPrefs((current) => ({ ...current, school_years: event.target.value }))} />
                  </div>
                </div>
                <label className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-4 text-sm leading-relaxed text-white/82">
                  <input type="checkbox" className="mt-1" checked={prefs.needs_full_ride} onChange={(event) => setPrefs((current) => ({ ...current, needs_full_ride: event.target.checked }))} />
                  <span>Need full-ride or full-funding route</span>
                </label>
              </div>
            </div>

            <SelectionColumn
              title="Top honors"
              count={selectedHonorIds.length}
              limit={5}
              items={honors}
              selectedIds={selectedHonorIds}
              onToggle={(id) => toggleSelection(id, "honor")}
              emptyText="Add honors in Achievement Vault first."
            />

            <SelectionColumn
              title="Top activities"
              count={selectedActivityIds.length}
              limit={10}
              items={activities}
              selectedIds={selectedActivityIds}
              onToggle={(id) => toggleSelection(id, "activity")}
              emptyText="Add activities in Achievement Vault first."
            />
          </div>

          {!!recommendations.length && (
            <div className="mt-6 grid gap-4 lg:grid-cols-3">
              {(["dream", "target", "safe"] as const).map((category) => (
                <div key={category} className="rounded-3xl border border-slate-200 bg-slate-50/70 p-5">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold capitalize text-slate-900">{category}</h3>
                    <Badge variant="outline">{groupedRecommendations[category].length}</Badge>
                  </div>
                  <p className="mt-2 text-xs leading-relaxed text-slate-500">
                    Relative category only, not an admission or aid guarantee.
                  </p>
                  <div className="mt-4 space-y-3">
                    {groupedRecommendations[category].map((recommendation) => (
                      <div key={recommendation.slug} className="rounded-2xl border border-slate-200 bg-white p-4">
                        <p className="text-sm font-medium text-slate-900">{recommendation.name}</p>
                        <p className="mt-1 text-xs text-slate-500">{recommendation.country}</p>
                        <p className="mt-3 text-xs leading-relaxed text-slate-700">{recommendation.rationale}</p>
                        {recommendation.aid_notes && (
                          <p className="mt-3 text-xs leading-relaxed text-emerald-700">
                            {recommendation.aid_notes}
                          </p>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          className="mt-4 w-full text-xs"
                          disabled={targetUniversityIds.has(recommendation.university_id) || addTargetMutation.isPending}
                          onClick={() => addTargetMutation.mutate({
                            universityId: recommendation.university_id,
                            fitCategory: recommendation.category,
                          })}
                        >
                          {targetUniversityIds.has(recommendation.university_id)
                            ? "Already in your list"
                            : `Add as ${FIT_CATEGORY_LABELS[recommendation.category]}`}
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="mt-6 rounded-[32px] border border-white/70 bg-white/90 p-6 shadow-[0_20px_70px_rgba(15,23,42,0.06)] backdrop-blur sm:p-8">
          {isLoading ? (
            <div className="flex items-center gap-2 text-slate-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading universities...
            </div>
          ) : universities.length ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {universities.map((university) => {
                const isTarget = targetUniversityIds.has(university.id);
                const isGenerating = generatingId === university.id;

                return (
                  <div
                    key={university.id}
                    className={cn(
                      "rounded-3xl border bg-white p-5 transition-all",
                      isTarget
                        ? "border-navy-300 ring-1 ring-navy-200"
                        : "border-slate-200 hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-sm"
                    )}
                  >
                    <div className="mb-4 flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-base font-semibold leading-snug text-slate-900">
                          {university.name}
                        </h3>
                        <p className="mt-1 text-xs text-slate-500">
                          {[university.country, university.city].filter(Boolean).join(" • ")}
                        </p>
                      </div>
                      {isTarget && <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-navy-700" />}
                    </div>

                    <div className="mb-3 flex flex-wrap gap-2">
                      <span className={cn("inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium", PRESET_COLORS[university.weight_preset])}>
                        {PRESET_LABELS[university.weight_preset]}
                      </span>
                      {university.is_common_app && <Badge variant="outline">Common App</Badge>}
                      {university.full_ride_possible && <Badge variant="success">Full ride possible</Badge>}
                      {university.full_tuition_possible && !university.full_ride_possible && <Badge variant="info">Full tuition possible</Badge>}
                    </div>

                    {university.short_description && (
                      <p className="mb-4 line-clamp-3 text-sm leading-relaxed text-slate-600">
                        {university.short_description}
                      </p>
                    )}

                    <div className="mb-5 space-y-1 text-xs text-slate-500">
                      {university.aid_type && <p>Aid: {AID_LABELS[university.aid_type] ?? university.aid_type}</p>}
                      {university.education_years_required && <p>School years: {university.education_years_required}+ expected</p>}
                      {!!university.teaching_languages?.length && <p>Language: {university.teaching_languages.join(", ")}</p>}
                      {!!university.major_strengths?.length && <p className="line-clamp-1">Strong fits: {university.major_strengths.join(", ")}</p>}
                    </div>

                    <div className="flex gap-2">
                      {!isTarget ? (
                        (["dream", "target", "safe"] as const).map((category) => (
                          <Button
                            key={category}
                            size="sm"
                            variant="outline"
                            className="flex-1 gap-1 text-xs"
                            onClick={() => addTargetMutation.mutate({ universityId: university.id, fitCategory: category })}
                            disabled={addTargetMutation.isPending}
                          >
                            <Plus className="h-3.5 w-3.5" />
                            {FIT_CATEGORY_LABELS[category]}
                          </Button>
                        ))
                      ) : (
                        <Button size="sm" className="flex-1 gap-1.5 bg-navy-950 text-xs text-white hover:bg-navy-900" onClick={() => handleGenerateReport(university)} disabled={isGenerating}>
                          {isGenerating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FileText className="h-3.5 w-3.5" />}
                          {isGenerating ? "Generating..." : "Generate Report"}
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="rounded-3xl border border-dashed border-slate-300 p-12 text-center">
              <p className="text-slate-500">No universities found. Try different filters.</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
