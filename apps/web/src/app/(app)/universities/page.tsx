"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { universitiesApi, targetsApi, reportsApi, achievementsApi, profileApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { Search, Plus, CheckCircle, Loader2, FileText, Sparkles, SlidersHorizontal } from "lucide-react";
import type { Achievement, CommonAppRecommendation, StudentProfile, TargetUniversity, University } from "@/types";
import { cn } from "@/lib/utils";

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
  { value: "aid_strength", label: "Aid strength" },
  { value: "selectivity_score", label: "Selectivity" },
  { value: "education_years_required", label: "School years required" },
];

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
    queryFn: () => universitiesApi.list(filters),
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
  }, [profile, loadedSavedPrefs]);

  const addTargetMutation = useMutation({
    mutationFn: (universityId: string) => targetsApi.add({ university_id: universityId }),
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

  const groupedRecommendations = useMemo(() => ({
    dream: recommendations.filter((item) => item.category === "dream"),
    target: recommendations.filter((item) => item.category === "target"),
    safe: recommendations.filter((item) => item.category === "safe"),
  }), [recommendations]);

  const handleGenerateReport = async (university: University) => {
    setGeneratingId(university.id);
    try {
      const res = await reportsApi.generate(university.id);
      const reportId = res.data?.data?.id;
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
    <div className="p-8 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Universities</h1>
        <p className="mt-1 text-sm text-slate-500">
          Filter funded options, save preferences, and generate a Common App shortlist from selected achievements.
        </p>
      </div>

      <section className="mb-8 rounded-xl border border-slate-200 bg-white p-5">
        <div className="mb-4 flex items-center gap-2">
          <SlidersHorizontal className="h-4 w-4 text-slate-500" />
          <h2 className="text-sm font-semibold text-slate-900">Sort and filter</h2>
        </div>
        <div className="grid gap-3 md:grid-cols-4">
          <div className="relative md:col-span-2">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              placeholder="Search by university, country, or major..."
              className="pl-9"
              value={filters.search}
              onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))}
            />
          </div>
          <select className="h-9 rounded-md border border-input bg-white px-3 text-sm" value={filters.country} onChange={(event) => setFilters((current) => ({ ...current, country: event.target.value }))}>
            {COUNTRIES.map((country) => <option key={country || "all"} value={country}>{country || "All countries"}</option>)}
          </select>
          <select className="h-9 rounded-md border border-input bg-white px-3 text-sm" value={filters.region} onChange={(event) => setFilters((current) => ({ ...current, region: event.target.value }))}>
            {REGIONS.map((region) => <option key={region || "all"} value={region}>{region || "All regions"}</option>)}
          </select>
          <Input placeholder="Major filter, e.g. CS" value={filters.major} onChange={(event) => setFilters((current) => ({ ...current, major: event.target.value }))} />
          <Input placeholder="Teaching language" value={filters.teaching_language} onChange={(event) => setFilters((current) => ({ ...current, teaching_language: event.target.value }))} />
          <Input type="number" min={10} max={13} placeholder="School years" value={filters.school_years} onChange={(event) => setFilters((current) => ({ ...current, school_years: event.target.value }))} />
          <select className="h-9 rounded-md border border-input bg-white px-3 text-sm" value={filters.aid_type} onChange={(event) => setFilters((current) => ({ ...current, aid_type: event.target.value }))}>
            <option value="">All aid routes</option>
            {Object.entries(AID_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <select className="h-9 rounded-md border border-input bg-white px-3 text-sm" value={filters.sort_by} onChange={(event) => setFilters((current) => ({ ...current, sort_by: event.target.value }))}>
            {SORTS.map((sort) => <option key={sort.value} value={sort.value}>Sort: {sort.label}</option>)}
          </select>
          <select className="h-9 rounded-md border border-input bg-white px-3 text-sm" value={filters.sort_dir} onChange={(event) => setFilters((current) => ({ ...current, sort_dir: event.target.value }))}>
            <option value="asc">Ascending</option>
            <option value="desc">Descending</option>
          </select>
          <label className="flex h-9 items-center gap-2 rounded-md border border-slate-200 px-3 text-sm">
            <input type="checkbox" checked={filters.full_ride_only} onChange={(event) => setFilters((current) => ({ ...current, full_ride_only: event.target.checked }))} />
            Full-ride possible
          </label>
          <label className="flex h-9 items-center gap-2 rounded-md border border-slate-200 px-3 text-sm">
            <input type="checkbox" checked={filters.common_app_only} onChange={(event) => setFilters((current) => ({ ...current, common_app_only: event.target.checked }))} />
            Common App only
          </label>
        </div>
      </section>

      <section className="mb-8 rounded-xl border border-slate-200 bg-white p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Common App top 20 recommender</h2>
            <p className="mt-1 text-xs text-slate-500">
              Gemini will use only the selected top honors, selected top activities, and saved preferences.
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

        <div className="grid gap-4 lg:grid-cols-3">
          <div className="space-y-3">
            <Label>Preferences</Label>
            <Input placeholder="Preferred countries" value={prefs.preferred_countries} onChange={(event) => setPrefs((current) => ({ ...current, preferred_countries: event.target.value }))} />
            <Input placeholder="Preferred regions" value={prefs.preferred_regions} onChange={(event) => setPrefs((current) => ({ ...current, preferred_regions: event.target.value }))} />
            <Input placeholder="Teaching language" value={prefs.teaching_language} onChange={(event) => setPrefs((current) => ({ ...current, teaching_language: event.target.value }))} />
            <Input placeholder="Intended major" value={prefs.intended_major} onChange={(event) => setPrefs((current) => ({ ...current, intended_major: event.target.value }))} />
            <Input type="number" min={10} max={13} placeholder="Years of school completed" value={prefs.school_years} onChange={(event) => setPrefs((current) => ({ ...current, school_years: event.target.value }))} />
            <label className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm">
              <input type="checkbox" checked={prefs.needs_full_ride} onChange={(event) => setPrefs((current) => ({ ...current, needs_full_ride: event.target.checked }))} />
              Need full-ride / full funding route
            </label>
          </div>

          <div>
            <Label>Top honors ({selectedHonorIds.length}/5)</Label>
            <div className="mt-2 max-h-72 space-y-2 overflow-y-auto pr-1">
              {honors.length ? honors.map((honor) => (
                <button key={honor.id} type="button" onClick={() => toggleSelection(honor.id, "honor")} className={cn("w-full rounded-lg border p-3 text-left text-sm", selectedHonorIds.includes(honor.id) ? "border-navy-950 bg-navy-50" : "border-slate-200 hover:border-slate-300")}>
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-medium text-slate-900">{honor.title}</span>
                    <span className="text-xs text-slate-500">{averageAchievementScore(honor) ?? "Pending"}</span>
                  </div>
                  {honor.organization_name && <p className="mt-1 text-xs text-slate-500">{honor.organization_name}</p>}
                </button>
              )) : <p className="text-sm text-slate-500">Add honors in Achievement Vault first.</p>}
            </div>
          </div>

          <div>
            <Label>Top activities ({selectedActivityIds.length}/10)</Label>
            <div className="mt-2 max-h-72 space-y-2 overflow-y-auto pr-1">
              {activities.length ? activities.map((activity) => (
                <button key={activity.id} type="button" onClick={() => toggleSelection(activity.id, "activity")} className={cn("w-full rounded-lg border p-3 text-left text-sm", selectedActivityIds.includes(activity.id) ? "border-navy-950 bg-navy-50" : "border-slate-200 hover:border-slate-300")}>
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-medium text-slate-900">{activity.title}</span>
                    <span className="text-xs text-slate-500">{averageAchievementScore(activity) ?? "Pending"}</span>
                  </div>
                  {activity.organization_name && <p className="mt-1 text-xs text-slate-500">{activity.organization_name}</p>}
                </button>
              )) : <p className="text-sm text-slate-500">Add activities in Achievement Vault first.</p>}
            </div>
          </div>
        </div>

        {!!recommendations.length && (
          <div className="mt-6 grid gap-4 lg:grid-cols-3">
            {(["dream", "target", "safe"] as const).map((category) => (
              <div key={category} className="rounded-lg border border-slate-200 p-4">
                <h3 className="text-sm font-semibold capitalize text-slate-900">{category}</h3>
                <p className="mt-1 text-xs text-slate-500">Relative category, not an admission guarantee.</p>
                <div className="mt-3 space-y-3">
                  {groupedRecommendations[category].map((rec) => (
                    <div key={rec.slug} className="rounded-md bg-slate-50 p-3">
                      <p className="text-sm font-medium text-slate-900">{rec.name}</p>
                      <p className="text-xs text-slate-500">{rec.country}</p>
                      <p className="mt-2 text-xs text-slate-700">{rec.rationale}</p>
                      {rec.aid_notes && <p className="mt-2 text-xs text-emerald-700">{rec.aid_notes}</p>}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {isLoading ? (
        <div className="flex items-center gap-2 text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading universities...
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {universities.map((uni) => {
            const isTarget = targetUniversityIds.has(uni.id);
            const isGenerating = generatingId === uni.id;

            return (
              <div key={uni.id} className={cn("rounded-xl border bg-white p-5 transition-all", isTarget ? "border-navy-300 ring-1 ring-navy-200" : "border-slate-200 hover:border-slate-300")}>
                <div className="mb-3 flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-semibold leading-snug text-slate-900">{uni.name}</h3>
                    <p className="mt-0.5 text-xs text-slate-500">{uni.country}{uni.city ? ` - ${uni.city}` : ""}</p>
                  </div>
                  {isTarget && <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-navy-700" />}
                </div>

                <div className="mb-3 flex flex-wrap gap-2">
                  <span className={cn("inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium", PRESET_COLORS[uni.weight_preset])}>
                    {PRESET_LABELS[uni.weight_preset]}
                  </span>
                  {uni.is_common_app && <Badge variant="outline">Common App</Badge>}
                  {uni.full_ride_possible && <Badge variant="success">Full ride possible</Badge>}
                  {uni.full_tuition_possible && !uni.full_ride_possible && <Badge variant="info">Full tuition possible</Badge>}
                </div>

                {uni.short_description && <p className="mb-3 line-clamp-3 text-xs leading-relaxed text-slate-600">{uni.short_description}</p>}
                <div className="mb-4 space-y-1 text-xs text-slate-500">
                  {uni.aid_type && <p>Aid: {AID_LABELS[uni.aid_type] ?? uni.aid_type}</p>}
                  {uni.education_years_required && <p>School years: {uni.education_years_required}+ expected</p>}
                  {!!uni.teaching_languages?.length && <p>Language: {uni.teaching_languages.join(", ")}</p>}
                  {!!uni.major_strengths?.length && <p className="line-clamp-1">Strong fits: {uni.major_strengths.join(", ")}</p>}
                </div>

                <div className="flex gap-2">
                  {!isTarget ? (
                    <Button size="sm" variant="outline" className="flex-1 gap-1.5 text-xs" onClick={() => addTargetMutation.mutate(uni.id)} disabled={addTargetMutation.isPending}>
                      <Plus className="h-3.5 w-3.5" />
                      Add to targets
                    </Button>
                  ) : (
                    <Button size="sm" className="flex-1 gap-1.5 bg-navy-950 text-xs text-white hover:bg-navy-900" onClick={() => handleGenerateReport(uni)} disabled={isGenerating}>
                      {isGenerating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FileText className="h-3.5 w-3.5" />}
                      {isGenerating ? "Generating..." : "Generate Report"}
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {universities.length === 0 && !isLoading && (
        <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center">
          <p className="text-slate-500">No universities found. Try different filters.</p>
        </div>
      )}
    </div>
  );
}
