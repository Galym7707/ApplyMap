"use client";

import { useState, useEffect, useMemo, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { achievementsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  AllAchievementsPanel,
  type ClarificationAnswers,
  type ImportProgressState,
} from "@/components/vault/AllAchievementsPanel";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Plus, Pencil, Trash2, AlertTriangle, CheckCircle, Info, GripVertical, Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import type { Achievement, AchievementImportResult } from "@/types";

const ACTIVITY_ORDER_STORAGE_KEY = "sourcelock_activity_order";
const SHORTLIST_FORMAT_VERSION = "common-app-fields-v3";
const IMPORT_ANALYSIS_STORAGE_KEY = "applymap_all_import_analysis_v3";
const IMPORT_ANALYSIS_SIGNATURE_STORAGE_KEY = "applymap_all_import_analysis_signature_v3";
const AUTO_SHORTLIST_SIGNATURE_STORAGE_KEY = "applymap_auto_shortlist_signature_v3";
const TEXT_PREVIEW_EXTENSIONS = new Set(["txt", "md", "csv", "json"]);
const DEFAULT_IMPORT_WORD_LIMIT = 22;

// ─── Form schema ────────────────────────────────────────────────────────────

const achievementSchema = z.object({
  type: z.enum(["activity", "honor"]),
  title: z.string().min(1, "Title is required").max(500),
  organization_name: z.string().optional(),
  role_title: z.string().optional(),
  description_raw: z.string().optional(),
  category: z.string().optional(),
  start_date: z.string().optional(),
  end_date: z.string().optional(),
  hours_per_week: z.string().optional(),
  weeks_per_year: z.string().optional(),
  impact_scope: z
    .enum(["school", "local", "regional", "national", "international", "family", "personal", ""])
    .optional(),
  leadership_level: z.enum(["none", "member", "lead", "founder", "captain", ""]).optional(),
});
type FormData = z.infer<typeof achievementSchema>;

// ─── Status helpers ──────────────────────────────────────────────────────────

const SCORE_FIELDS: { key: keyof Achievement; label: string }[] = [
  { key: "major_relevance_score", label: "Major relevance" },
  { key: "selectivity_score", label: "Selectivity" },
  { key: "continuity_score", label: "Continuity" },
  { key: "distinctiveness_score", label: "Distinctiveness" },
];

function hasChancellorScores(achievement: Achievement) {
  return SCORE_FIELDS.every((field) => typeof achievement[field.key] === "number");
}

function formatFileSize(bytes: number) {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

async function getLocalSourcePreview(file: File) {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  if (!TEXT_PREVIEW_EXTENSIONS.has(extension)) return [];

  const text = await file.text();
  return text
    .split(/\r?\n|[\u2022*]\s+/)
    .map((line) => line.replace(/\s+/g, " ").trim())
    .filter((line) => line.length > 18)
    .slice(0, 5)
    .map((line) => (line.length > 220 ? `${line.slice(0, 217)}...` : line));
}

function getStatus(achievement: Achievement) {
  const desc = achievement.description_raw ?? "";
  if (achievement.truth_risk_flag) {
    return {
      label: "Review Needed",
      variant: "destructive" as const,
      icon: AlertTriangle,
      reason:
        "The Chancellor found an unsupported, conflicting, or unclear claim. Add evidence or clarify dates, award level, scope, hours, or results.",
    };
  }
  if (desc.length < 30) {
    return {
      label: "Needs Detail",
      variant: "warning" as const,
      icon: Info,
      reason: "The description is too short to judge impact. Add what you did, scale, outcome, and time commitment.",
    };
  }
  if (!hasChancellorScores(achievement)) {
    return {
      label: "Analysis Pending",
      variant: "info" as const,
      icon: Sparkles,
      reason: "The Chancellor has not scored this achievement yet.",
    };
  }
  return {
    label: "Strong",
    variant: "success" as const,
    icon: CheckCircle,
    reason: "The entry has enough detail for the current Chancellor scoring pass.",
  };
}

// ─── Score bar ───────────────────────────────────────────────────────────────

function ScoreBar({ label, value }: { label: string; value?: number | null }) {
  const pct = value != null ? Math.min((value / 10) * 100, 100) : 0;
  const fillClass =
    value == null
      ? ""
      : value >= 7
      ? "bg-emerald-500"
      : value >= 4
      ? "bg-amber-400"
      : "bg-red-400";

  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <span className="text-[10px] leading-none text-slate-400">{label}</span>
        <span className="text-[10px] font-medium tabular-nums text-slate-500">
          {value != null ? value.toFixed(1).replace(/\.0$/, "") : "Pending"}
        </span>
      </div>
      <div className="h-1 w-full rounded-full bg-slate-100">
        {value != null && (
          <div
            className={`h-1 rounded-full transition-all duration-300 ${fillClass}`}
            style={{ width: `${pct}%` }}
          />
        )}
      </div>
    </div>
  );
}

// ─── Empty vault state ───────────────────────────────────────────────────────

function EmptyVaultState({
  type,
  onAdd,
}: {
  type: "activity" | "honor";
  onAdd: () => void;
}) {
  return (
    <div className="flex flex-col items-center rounded-2xl border-2 border-dashed border-slate-200 bg-white px-10 py-14 text-center">
      {/* Vault door illustration */}
      <svg width="64" height="72" viewBox="0 0 64 72" fill="none" aria-hidden="true">
        <rect x="8" y="8" width="48" height="56" rx="6" fill="#F8FAFC" stroke="#CBD5E1" strokeWidth="1.5" />
        <circle cx="17" cy="22" r="3" fill="#E2E8F0" />
        <circle cx="17" cy="50" r="3" fill="#E2E8F0" />
        <circle cx="36" cy="36" r="10" fill="white" stroke="#CBD5E1" strokeWidth="1.5" />
        <circle cx="36" cy="36" r="4" fill="#E2E8F0" />
        <line x1="36" y1="26" x2="36" y2="30" stroke="#CBD5E1" strokeWidth="1.5" />
        <line x1="36" y1="42" x2="36" y2="46" stroke="#CBD5E1" strokeWidth="1.5" />
        <line x1="26" y1="36" x2="30" y2="36" stroke="#CBD5E1" strokeWidth="1.5" />
        <line x1="42" y1="36" x2="46" y2="36" stroke="#CBD5E1" strokeWidth="1.5" />
        <rect x="49" y="33" width="7" height="6" rx="2" fill="#E2E8F0" />
      </svg>

      <h3 className="mt-5 text-sm font-semibold text-slate-700">
        {type === "activity" ? "Your activity vault is empty" : "No honors added yet"}
      </h3>
      <p className="mt-1.5 max-w-xs text-xs leading-relaxed text-slate-400">
        {type === "activity"
          ? "Add clubs, research, jobs, competitions — anything you've done outside class."
          : "Add academic prizes, scholarships, and awards you've received."}
      </p>
      <Button
        size="sm"
        className="mt-6 gap-1.5 bg-navy-950 text-white hover:bg-navy-900"
        onClick={onAdd}
      >
        <Plus className="h-3.5 w-3.5" />
        Add {type === "activity" ? "first activity" : "first honor"}
      </Button>
    </div>
  );
}

// ─── Achievement modal ───────────────────────────────────────────────────────

function AchievementModal({
  open,
  onClose,
  defaultType,
  editing,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  defaultType: "activity" | "honor";
  editing?: Achievement;
  onSaved: () => void;
}) {
  const queryClient = useQueryClient();

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(achievementSchema),
    defaultValues: editing
      ? {
          ...editing,
          hours_per_week: editing.hours_per_week?.toString() ?? "",
          weeks_per_year: editing.weeks_per_year?.toString() ?? "",
          start_date: editing.start_date ?? "",
          end_date: editing.end_date ?? "",
          impact_scope: editing.impact_scope ?? "",
          leadership_level: editing.leadership_level ?? "",
        }
      : { type: defaultType, impact_scope: "", leadership_level: "" },
  });

  useEffect(() => {
    reset(
      editing
        ? {
            ...editing,
            hours_per_week: editing.hours_per_week?.toString() ?? "",
            weeks_per_year: editing.weeks_per_year?.toString() ?? "",
            start_date: editing.start_date ?? "",
            end_date: editing.end_date ?? "",
            impact_scope: editing.impact_scope ?? "",
            leadership_level: editing.leadership_level ?? "",
          }
        : { type: defaultType, impact_scope: "", leadership_level: "" }
    );
  }, [defaultType, editing, reset]);

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => achievementsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
      onSaved();
      toast.success("Achievement added");
      onClose();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      achievementsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
      onSaved();
      toast.success("Achievement updated");
      onClose();
    },
  });

  const onSubmit = (raw: FormData) => {
    const data: Record<string, unknown> = {
      ...raw,
      hours_per_week: raw.hours_per_week ? parseFloat(raw.hours_per_week) : undefined,
      weeks_per_year: raw.weeks_per_year ? parseInt(raw.weeks_per_year, 10) : undefined,
      start_date: raw.start_date || undefined,
      end_date: raw.end_date || undefined,
      impact_scope: raw.impact_scope || undefined,
      leadership_level: raw.leadership_level || undefined,
    };
    if (editing) {
      updateMutation.mutate({ id: editing.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={(nextOpen) => !nextOpen && onClose()}>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{editing ? "Edit achievement" : "Add achievement"}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-2">
          <input type="hidden" {...register("type")} />

          <div className="space-y-1.5">
            <Label>Title *</Label>
            <Input placeholder="e.g. National Math Olympiad Finalist" {...register("title")} />
            {errors.title && <p className="text-xs text-red-600">{errors.title.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Organization</Label>
              <Input placeholder="e.g. Ministry of Education" {...register("organization_name")} />
            </div>
            <div className="space-y-1.5">
              <Label>Your role / title</Label>
              <Input placeholder="e.g. Team Captain" {...register("role_title")} />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Description (use your own words)</Label>
            <Textarea
              rows={3}
              placeholder="Describe what you did, your responsibilities, and impact..."
              {...register("description_raw")}
            />
          </div>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
            <div className="space-y-1.5">
              <Label>Category</Label>
              <Input placeholder="Science / Arts / Service" {...register("category")} />
            </div>
            <div className="space-y-1.5">
              <Label>Start date</Label>
              <Input type="date" {...register("start_date")} />
            </div>
            <div className="space-y-1.5">
              <Label>End date</Label>
              <Input type="date" {...register("end_date")} />
            </div>
            <div className="space-y-1.5">
              <Label>Hrs/week</Label>
              <Input type="number" step="0.5" placeholder="5" {...register("hours_per_week")} />
            </div>
            <div className="space-y-1.5">
              <Label>Wks/year</Label>
              <Input type="number" placeholder="40" {...register("weeks_per_year")} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Impact scope</Label>
              <select
                {...register("impact_scope")}
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
              >
                <option value="">Select scope</option>
                {["school", "local", "regional", "national", "international", "family", "personal"].map(
                  (s) => <option key={s} value={s}>{s}</option>
                )}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label>Leadership level</Label>
              <select
                {...register("leadership_level")}
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm"
              >
                <option value="">Select level</option>
                {["none", "member", "lead", "captain", "founder"].map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-blue-950">
            <div className="flex gap-2">
              <Sparkles className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p className="font-medium">Chancellor analysis runs after saving.</p>
                <p className="mt-1 text-xs text-blue-800">
                  The app will estimate major relevance, selectivity, continuity, and
                  distinctiveness from your achievement details.
                </p>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isPending}
              className="bg-navy-950 text-white hover:bg-navy-900"
            >
              {isPending ? "Saving…" : editing ? "Save changes" : "Add achievement"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ─── Achievement card ────────────────────────────────────────────────────────

function AchievementCard({
  achievement,
  rank,
  onEdit,
  onDelete,
  isDragging = false,
  isDragOver = false,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDrop,
}: {
  achievement: Achievement;
  rank?: number;
  onEdit: () => void;
  onDelete: () => void;
  isDragging?: boolean;
  isDragOver?: boolean;
  onDragStart?: () => void;
  onDragEnd?: () => void;
  onDragOver?: (e: React.DragEvent) => void;
  onDrop?: (e: React.DragEvent) => void;
}) {
  const status = getStatus(achievement);
  const StatusIcon = status.icon;

  const borderAccent =
    status.variant === "success"
      ? "border-l-emerald-500"
      : status.variant === "warning"
      ? "border-l-amber-400"
      : status.variant === "info"
      ? "border-l-blue-400"
      : "border-l-red-400";

  return (
    <div
      draggable={!!onDragStart}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onDragOver={onDragOver}
      onDrop={onDrop}
      className={cn(
        "rounded-xl border border-l-4 bg-white p-4 transition-all",
        borderAccent,
        "border-slate-200",
        isDragging && "opacity-40 scale-[0.98]",
        isDragOver && "ring-2 ring-navy-200 ring-offset-1",
        onDragStart && "cursor-grab active:cursor-grabbing"
      )}
    >
      <div className="flex items-start gap-3">
        {/* Rank + drag handle */}
        {rank != null && (
          <div className="flex shrink-0 flex-col items-center gap-0.5 pt-0.5">
            <span className="text-[10px] font-bold text-slate-400">#{rank}</span>
            <GripVertical className="h-3.5 w-3.5 text-slate-300" />
          </div>
        )}

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="mb-1 flex flex-wrap items-center gap-2">
            <h3 className="truncate text-sm font-medium text-slate-900">{achievement.title}</h3>
            <span className="group/status relative inline-flex">
              <Badge
                variant={status.variant}
                className="flex cursor-help items-center gap-1 text-xs"
                tabIndex={0}
              >
                <StatusIcon className="h-3 w-3" />
                {status.label}
              </Badge>
              <span className="pointer-events-none absolute left-0 top-full z-30 mt-2 w-72 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs leading-relaxed text-slate-700 opacity-0 shadow-lg transition-opacity group-hover/status:opacity-100 group-focus-within/status:opacity-100">
                {status.reason}
              </span>
            </span>
          </div>

          {achievement.organization_name && (
            <p className="text-xs text-slate-500 mb-1">{achievement.organization_name}</p>
          )}
          {achievement.description_raw && (
            <p className="text-xs text-slate-600 line-clamp-2">{achievement.description_raw}</p>
          )}

          {/* Meta tags */}
          <div className="mt-1.5 flex flex-wrap gap-2 text-xs text-slate-400">
            {achievement.impact_scope && <span>Scope: {achievement.impact_scope}</span>}
            {achievement.leadership_level && (
              <span>· Leadership: {achievement.leadership_level}</span>
            )}
            {achievement.hours_per_week && <span>· {achievement.hours_per_week}h/wk</span>}
            {achievement.category && <span>· {achievement.category}</span>}
          </div>

          <div className="mt-3 border-t border-slate-100 pt-3">
            <div className="mb-3 flex items-center gap-1.5 text-xs font-medium text-slate-700">
              <Sparkles className="h-3.5 w-3.5 text-blue-600" />
              Chancellor analysis
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-2">
              {SCORE_FIELDS.map((field) => (
                <ScoreBar
                  key={field.key}
                  label={field.label}
                  value={achievement[field.key] as number | null | undefined}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex shrink-0 items-center gap-1">
          <Button size="icon" variant="ghost" className="h-7 w-7" onClick={onEdit}>
            <Pencil className="h-3.5 w-3.5" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7 text-red-400 hover:bg-red-50 hover:text-red-600"
            onClick={onDelete}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
}

// ─── Vault page ──────────────────────────────────────────────────────────────

export default function VaultPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Achievement | undefined>();
  const [defaultType, setDefaultType] = useState<"activity" | "honor">("activity");
  const [allImportResult, setAllImportResult] = useState<AchievementImportResult | null>(null);
  const [importProgress, setImportProgress] = useState<ImportProgressState | null>(null);
  const [lastImportFile, setLastImportFile] = useState<File | null>(null);
  const [clarificationAnswers, setClarificationAnswers] = useState<ClarificationAnswers>({});
  const [hasLoadedStoredAnalysis, setHasLoadedStoredAnalysis] = useState(false);

  // Drag state
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);

  const [activityOrder, setActivityOrder] = useState<string[]>([]);

  const { data, isLoading } = useQuery({
    queryKey: ["achievements"],
    queryFn: () => achievementsApi.list(),
  });

  const achievements: Achievement[] = data?.data?.data ?? [];
  const activities = achievements.filter((a) => a.type === "activity");
  const honors = achievements.filter((a) => a.type === "honor");
  const vaultSignature = useMemo(
    () =>
      [
        SHORTLIST_FORMAT_VERSION,
        ...achievements
          .map((achievement) => `${achievement.id}:${achievement.updated_at}`)
          .sort(),
      ].join("|"),
    [achievements]
  );

  const clearImportAnalysis = () => {
    setAllImportResult(null);
    setImportProgress(null);
    setLastImportFile(null);
    setClarificationAnswers({});
    try {
      localStorage.removeItem(IMPORT_ANALYSIS_STORAGE_KEY);
      localStorage.removeItem(IMPORT_ANALYSIS_SIGNATURE_STORAGE_KEY);
      localStorage.removeItem("applymap_all_import_analysis");
      localStorage.removeItem("applymap_all_import_analysis_signature");
      sessionStorage.removeItem(AUTO_SHORTLIST_SIGNATURE_STORAGE_KEY);
      sessionStorage.removeItem("applymap_auto_shortlist_signature");
    } catch {}
  };

  const deleteMutation = useMutation({
    mutationFn: (id: string) => achievementsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
      clearImportAnalysis();
      toast.success("Achievement deleted");
    },
  });

  const clearTypeMutation = useMutation({
    mutationFn: async ({ ids }: { type: "activity" | "honor"; ids: string[] }) => {
      await Promise.all(ids.map((id) => achievementsApi.delete(id)));
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
      clearImportAnalysis();
      toast.success(
        variables.type === "activity" ? "All activities cleared" : "All honors cleared"
      );
    },
    onError: () => {
      toast.error("Could not clear all items. Try again.");
    },
  });

  const importMutation = useMutation({
    mutationFn: ({
      file,
      limit,
      answers,
      previousImportIds,
    }: {
      file: File;
      limit: number;
      answers?: ClarificationAnswers;
      previousImportIds?: string[];
    }) =>
      achievementsApi.importAll(file, limit, {
        clarificationAnswers: answers,
        previousImportIds,
      }),
    onSuccess: (response) => {
      const result = response.data.data as AchievementImportResult;
      setAllImportResult(result);
      setImportProgress((current) =>
        current ? { ...current, currentStepIndex: 5 } : current
      );

      try {
        localStorage.setItem(IMPORT_ANALYSIS_STORAGE_KEY, JSON.stringify(result));
        localStorage.removeItem(IMPORT_ANALYSIS_SIGNATURE_STORAGE_KEY);
      } catch {}

      const reorderedActivityIds = [
        ...result.top_activities.map((item) => item.achievement_id),
        ...result.imported_achievements
          .filter((achievement) => achievement.type === "activity")
          .map((achievement) => achievement.id),
        ...activities.map((achievement) => achievement.id),
      ];
      saveOrder(Array.from(new Set(reorderedActivityIds)));

      queryClient.invalidateQueries({ queryKey: ["achievements"] });
      toast.success(`Imported ${result.imported_count} achievements and built a shortlist`);
    },
    onError: (error: unknown) => {
      setImportProgress((current) =>
        current ? { ...current, currentStepIndex: 3 } : current
      );
      const detail =
        typeof error === "object" &&
        error &&
        "response" in error &&
        typeof (error as { response?: { data?: { detail?: string } } }).response?.data?.detail === "string"
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : "Import failed because the server connection dropped. Try a smaller text-based PDF, DOCX, TXT, MD, CSV, or JSON file; scanned image PDFs are not supported yet.";
      toast.error(detail);
    },
  });

  const shortlistMutation = useMutation({
    mutationFn: (limit: number) => achievementsApi.shortlist(limit),
    onSuccess: (response) => {
      const result = response.data.data as AchievementImportResult;
      setAllImportResult(result);
      setImportProgress((current) =>
        current ? { ...current, currentStepIndex: 5 } : current
      );

      try {
        localStorage.setItem(IMPORT_ANALYSIS_STORAGE_KEY, JSON.stringify(result));
        localStorage.setItem(IMPORT_ANALYSIS_SIGNATURE_STORAGE_KEY, vaultSignature);
      } catch {}

      const reorderedActivityIds = [
        ...result.top_activities.map((item) => item.achievement_id),
        ...result.imported_achievements
          .filter((achievement) => achievement.type === "activity")
          .map((achievement) => achievement.id),
        ...activities.map((achievement) => achievement.id),
      ];
      saveOrder(Array.from(new Set(reorderedActivityIds)));

      toast.success("Built a Common App shortlist from your current vault");
    },
    onError: (error: unknown) => {
      setImportProgress((current) =>
        current ? { ...current, currentStepIndex: 3 } : current
      );
      const detail =
        typeof error === "object" &&
        error &&
        "response" in error &&
        typeof (error as { response?: { data?: { detail?: string } } }).response?.data?.detail === "string"
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : "Could not build a shortlist from the current vault.";
      toast.error(detail);
    },
  });

  const isAnalyzing = importMutation.isPending || shortlistMutation.isPending;

  useEffect(() => {
    if (!isAnalyzing) return;

    const interval = window.setInterval(() => {
      setImportProgress((current) => {
        if (!current) return current;
        return {
          ...current,
          currentStepIndex: Math.min(current.currentStepIndex + 1, 4),
        };
      });
    }, 1800);

    return () => window.clearInterval(interval);
  }, [isAnalyzing]);

  // Load order from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(ACTIVITY_ORDER_STORAGE_KEY);
      if (stored) setActivityOrder(JSON.parse(stored));
    } catch {}

    try {
      const storedAnalysis = localStorage.getItem(IMPORT_ANALYSIS_STORAGE_KEY);
      if (storedAnalysis) {
        setAllImportResult(JSON.parse(storedAnalysis) as AchievementImportResult);
      }
    } catch {}
    setHasLoadedStoredAnalysis(true);
  }, []);

  // Keep order in sync: new items appended, deleted items removed
  useEffect(() => {
    if (activities.length === 0) return;
    setActivityOrder((prev) => {
      const ids = new Set(activities.map((a) => a.id));
      const kept = prev.filter((id) => ids.has(id));
      const added = activities.filter((a) => !prev.includes(a.id)).map((a) => a.id);
      return [...kept, ...added];
    });
  }, [activities]);

  useEffect(() => {
    if (
      !hasLoadedStoredAnalysis ||
      !vaultSignature ||
      !allImportResult ||
      allImportResult.file_name !== "Current Vault"
    ) {
      return;
    }

    try {
      const storedSignature = localStorage.getItem(IMPORT_ANALYSIS_SIGNATURE_STORAGE_KEY);
      if (storedSignature && storedSignature !== vaultSignature) {
        clearImportAnalysis();
      }
    } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasLoadedStoredAnalysis, vaultSignature, allImportResult]);

  const sortedActivities = useMemo(() => {
    if (activityOrder.length === 0) return activities;
    return [...activities].sort((a, b) => {
      const ai = activityOrder.indexOf(a.id);
      const bi = activityOrder.indexOf(b.id);
      if (ai === -1 && bi === -1) return 0;
      if (ai === -1) return 1;
      if (bi === -1) return -1;
      return ai - bi;
    });
  }, [activities, activityOrder]);

  const saveOrder = (newOrder: string[]) => {
    setActivityOrder(newOrder);
    try {
      localStorage.setItem(ACTIVITY_ORDER_STORAGE_KEY, JSON.stringify(newOrder));
    } catch {}
  };

  const handleDragStart = (id: string) => setDraggingId(id);
  const handleDragEnd = () => { setDraggingId(null); setDragOverId(null); };
  const handleDragOver = (e: React.DragEvent, id: string) => {
    e.preventDefault();
    if (id !== draggingId) setDragOverId(id);
  };
  const handleDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault();
    if (!draggingId || draggingId === targetId) { handleDragEnd(); return; }
    const newOrder = [...activityOrder];
    const from = newOrder.indexOf(draggingId);
    const to = newOrder.indexOf(targetId);
    if (from !== -1 && to !== -1) {
      newOrder.splice(from, 1);
      newOrder.splice(to, 0, draggingId);
      saveOrder(newOrder);
      clearImportAnalysis();
    }
    handleDragEnd();
  };

  const handleAdd = (type: "activity" | "honor") => {
    setEditing(undefined);
    setDefaultType(type);
    setModalOpen(true);
  };
  const handleEdit = (a: Achievement) => {
    setEditing(a);
    setDefaultType(a.type);
    setModalOpen(true);
  };

  const handleClearAll = (type: "activity" | "honor") => {
    const items = type === "activity" ? activities : honors;
    if (items.length === 0) return;

    const confirmed = window.confirm(
      type === "activity"
        ? `Delete all ${items.length} activities from your vault?`
        : `Delete all ${items.length} honors from your vault?`
    );
    if (!confirmed) return;

    clearTypeMutation.mutate({
      type,
      ids: items.map((item) => item.id),
    });
  };

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const trimmedClarificationAnswers = (): ClarificationAnswers =>
    Object.fromEntries(
      Object.entries(clarificationAnswers)
        .map(([key, value]) => [key, value.trim()])
        .filter(([, value]) => value.length > 0)
    );

  const handleImportFile = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    const sourcePreview = await getLocalSourcePreview(file).catch(() => []);
    setLastImportFile(file);
    setClarificationAnswers({});
    setAllImportResult(null);
    setImportProgress({
      fileName: file.name,
      fileSizeLabel: formatFileSize(file.size),
      currentStepIndex: 0,
      sourcePreview,
    });

    importMutation.mutate({ file, limit: DEFAULT_IMPORT_WORD_LIMIT });
  };

  const handleClarificationAnswerChange = (key: string, value: string) => {
    setClarificationAnswers((current) => ({
      ...current,
      [key]: value,
    }));
  };

  const handleReanalyze = () => {
    if (!lastImportFile) {
      toast.error("Upload the original file again before reanalysis.");
      return;
    }

    const answers = trimmedClarificationAnswers();
    if (Object.keys(answers).length === 0) {
      toast.error("Answer at least one missing detail before reanalysis.");
      return;
    }

    setAllImportResult(null);
    setImportProgress({
      fileName: lastImportFile.name,
      fileSizeLabel: formatFileSize(lastImportFile.size),
      currentStepIndex: 0,
      sourcePreview: importProgress?.sourcePreview ?? [],
    });

    importMutation.mutate({
      file: lastImportFile,
      limit: DEFAULT_IMPORT_WORD_LIMIT,
      answers,
      previousImportIds: allImportResult?.imported_achievements.map((achievement) => achievement.id) ?? [],
    });
  };

  const handleBuildFromVault = () => {
    if (achievements.length === 0) {
      toast.error("Add at least one achievement before building a shortlist.");
      return;
    }

    setLastImportFile(null);
    setClarificationAnswers({});
    setAllImportResult(null);
    setImportProgress({
      fileName: "Current Vault",
      fileSizeLabel: `${achievements.length} saved items`,
      currentStepIndex: 0,
      sourcePreview: achievements
        .map((achievement) =>
          [achievement.title, achievement.organization_name, achievement.description_raw]
            .filter(Boolean)
            .join(" - ")
        )
        .filter(Boolean)
        .slice(0, 6),
    });

    shortlistMutation.mutate(DEFAULT_IMPORT_WORD_LIMIT);
  };

  useEffect(() => {
    if (
      !hasLoadedStoredAnalysis ||
      !vaultSignature ||
      allImportResult ||
      isAnalyzing ||
      achievements.length === 0
    ) {
      return;
    }

    try {
      if (sessionStorage.getItem(AUTO_SHORTLIST_SIGNATURE_STORAGE_KEY) === vaultSignature) {
        return;
      }
      sessionStorage.setItem(AUTO_SHORTLIST_SIGNATURE_STORAGE_KEY, vaultSignature);
    } catch {}

    handleBuildFromVault();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasLoadedStoredAnalysis, vaultSignature, allImportResult, isAnalyzing, achievements.length]);

  return (
    <div className="w-full max-w-none p-6 lg:p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Achievement Vault</h1>
          <p className="mt-1 text-sm text-slate-500">
            {activities.length} activities · {honors.length} honors
          </p>
        </div>
      </div>

      <Tabs defaultValue="all">
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.md,.csv,.json,.pdf,.docx,text/plain,text/markdown,text/csv,application/json,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="hidden"
          onChange={handleImportFile}
        />

        <div className="mb-4 flex items-center justify-between">
          <TabsList>
            <TabsTrigger value="all" className="gap-2">
              All
              <span className="rounded-full bg-navy-100 px-2 py-0.5 text-[10px] font-semibold text-navy-800">
                {achievements.length}
              </span>
            </TabsTrigger>
            <TabsTrigger value="activities" className="gap-2">
              Activities
              <span className="rounded-full bg-navy-100 px-2 py-0.5 text-[10px] font-semibold text-navy-800">
                {activities.length}
              </span>
            </TabsTrigger>
            <TabsTrigger value="honors" className="gap-2">
              Honors
              <span className="rounded-full bg-navy-100 px-2 py-0.5 text-[10px] font-semibold text-navy-800">
                {honors.length}
              </span>
            </TabsTrigger>
          </TabsList>

          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleAdd("honor")}
              className="gap-1.5"
            >
              <Plus className="h-3.5 w-3.5" /> Add honor
            </Button>
            <Button
              size="sm"
              className="gap-1.5 bg-navy-950 text-white hover:bg-navy-900"
              onClick={() => handleAdd("activity")}
            >
              <Plus className="h-3.5 w-3.5" /> Add activity
            </Button>
          </div>
        </div>

        <TabsContent value="all">
          <AllAchievementsPanel
            result={allImportResult}
            onUploadClick={handleImportClick}
            onBuildFromVault={handleBuildFromVault}
            onReanalyze={handleReanalyze}
            onClear={clearImportAnalysis}
            isImporting={importMutation.isPending}
            isBuildingFromVault={shortlistMutation.isPending}
            importProgress={importProgress}
            clarificationAnswers={clarificationAnswers}
            onClarificationAnswerChange={handleClarificationAnswerChange}
            canReanalyze={!!lastImportFile}
            achievementCount={achievements.length}
            activityCount={activities.length}
            honorCount={honors.length}
          />
        </TabsContent>

        {/* Activities tab */}
        <TabsContent value="activities">
          {isLoading ? (
            <div className="space-y-2.5">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="rounded-xl border border-slate-100 bg-white p-4">
                  <div className="flex items-start gap-3">
                    <Skeleton className="h-5 w-5 rounded-full shrink-0" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-48" />
                      <Skeleton className="h-3 w-32" />
                      <div className="grid grid-cols-4 gap-1.5 pt-1">
                        {Array.from({ length: 4 }).map((_, j) => (
                          <Skeleton key={j} className="h-1 w-full rounded-full" />
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : activities.length === 0 ? (
            <EmptyVaultState type="activity" onAdd={() => handleAdd("activity")} />
          ) : (
            <>
              <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-xs text-slate-400">
                Drag to reorder · Common App shows activities in this order
              </p>
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full gap-1.5 border-red-200 text-red-600 hover:bg-red-50 sm:w-auto"
                  onClick={() => handleClearAll("activity")}
                  disabled={clearTypeMutation.isPending}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Clear all activities
                </Button>
              </div>
              <div className="space-y-2.5">
                {sortedActivities.map((a, i) => (
                  <AchievementCard
                    key={a.id}
                    achievement={a}
                    rank={i + 1}
                    onEdit={() => handleEdit(a)}
                    onDelete={() => deleteMutation.mutate(a.id)}
                    isDragging={draggingId === a.id}
                    isDragOver={dragOverId === a.id}
                    onDragStart={() => handleDragStart(a.id)}
                    onDragEnd={handleDragEnd}
                    onDragOver={(e) => handleDragOver(e, a.id)}
                    onDrop={(e) => handleDrop(e, a.id)}
                  />
                ))}
              </div>
            </>
          )}
        </TabsContent>

        {/* Honors tab */}
        <TabsContent value="honors">
          {isLoading ? (
            <div className="space-y-2.5">
              {Array.from({ length: 2 }).map((_, i) => (
                <div key={i} className="rounded-xl border border-slate-100 bg-white p-4">
                  <div className="flex items-start gap-3">
                    <Skeleton className="h-5 w-5 rounded-full shrink-0" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-40" />
                      <Skeleton className="h-3 w-24" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : honors.length === 0 ? (
            <EmptyVaultState type="honor" onAdd={() => handleAdd("honor")} />
          ) : (
            <>
              <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-xs text-slate-400">
                  Academic honors stored in your vault
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full gap-1.5 border-red-200 text-red-600 hover:bg-red-50 sm:w-auto"
                  onClick={() => handleClearAll("honor")}
                  disabled={clearTypeMutation.isPending}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Clear all honors
                </Button>
              </div>
            <div className="space-y-2.5">
              {honors.map((a) => (
                <AchievementCard
                  key={a.id}
                  achievement={a}
                  onEdit={() => handleEdit(a)}
                  onDelete={() => deleteMutation.mutate(a.id)}
                />
              ))}
            </div>
            </>
          )}
        </TabsContent>
      </Tabs>

      <AchievementModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        defaultType={defaultType}
        editing={editing}
        onSaved={clearImportAnalysis}
      />
    </div>
  );
}
