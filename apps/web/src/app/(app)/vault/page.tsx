"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { achievementsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Plus, Pencil, Trash2, AlertTriangle, CheckCircle, Info, Sparkles } from "lucide-react";
import { toast } from "sonner";
import type { Achievement } from "@/types";

const achievementSchema = z.object({
  type: z.enum(["activity", "honor"]),
  title: z.string().min(1, "Title is required").max(500),
  organization_name: z.string().optional(),
  role_title: z.string().optional(),
  description_raw: z.string().optional(),
  category: z.string().optional(),
  hours_per_week: z.string().optional(),
  weeks_per_year: z.string().optional(),
  impact_scope: z.enum(["school", "local", "regional", "national", "international", "family", "personal", ""]).optional(),
  leadership_level: z.enum(["none", "member", "lead", "founder", "captain", ""]).optional(),
});

type FormData = z.infer<typeof achievementSchema>;

const SCORE_FIELDS: { key: keyof Achievement; label: string }[] = [
  { key: "major_relevance_score", label: "Major relevance" },
  { key: "selectivity_score", label: "Selectivity" },
  { key: "continuity_score", label: "Continuity" },
  { key: "distinctiveness_score", label: "Distinctiveness" },
];

function hasChancellorScores(achievement: Achievement) {
  return SCORE_FIELDS.every((field) => typeof achievement[field.key] === "number");
}

function formatScore(value: Achievement[keyof Achievement]) {
  return typeof value === "number" ? value.toFixed(1).replace(/\.0$/, "") : "Pending";
}

function getStatusBadge(achievement: Achievement) {
  const desc = achievement.description_raw ?? "";

  if (achievement.truth_risk_flag) {
    return { label: "Review Needed", variant: "destructive" as const, icon: AlertTriangle };
  }
  if (desc.length < 30) {
    return { label: "Needs Detail", variant: "warning" as const, icon: Info };
  }
  if (!hasChancellorScores(achievement)) {
    return { label: "Analysis Pending", variant: "info" as const, icon: Sparkles };
  }
  return { label: "Strong", variant: "success" as const, icon: CheckCircle };
}

function AchievementModal({
  open,
  onClose,
  defaultType,
  editing,
}: {
  open: boolean;
  onClose: () => void;
  defaultType: "activity" | "honor";
  editing?: Achievement;
}) {
  const queryClient = useQueryClient();

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(achievementSchema),
    defaultValues: editing
      ? {
          ...editing,
          hours_per_week: editing.hours_per_week?.toString() ?? "",
          weeks_per_year: editing.weeks_per_year?.toString() ?? "",
          impact_scope: editing.impact_scope ?? "",
          leadership_level: editing.leadership_level ?? "",
        }
      : {
          type: defaultType,
          impact_scope: "",
          leadership_level: "",
        },
  });

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => achievementsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
      toast.success("Achievement added");
      onClose();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      achievementsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
      toast.success("Achievement updated");
      onClose();
    },
  });

  const onSubmit = (raw: FormData) => {
    const data: Record<string, unknown> = {
      ...raw,
      hours_per_week: raw.hours_per_week ? parseFloat(raw.hours_per_week) : undefined,
      weeks_per_year: raw.weeks_per_year ? parseInt(raw.weeks_per_year) : undefined,
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
    <Dialog open={open} onOpenChange={() => onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
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
            <Label>Description (raw — use your own words)</Label>
            <Textarea
              rows={3}
              placeholder="Describe what you did, your responsibilities, and impact..."
              {...register("description_raw")}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-1.5">
              <Label>Category</Label>
              <Input placeholder="Science / Arts / Service" {...register("category")} />
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
                {["school", "local", "regional", "national", "international", "family", "personal"].map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
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
                  The app will estimate major relevance, selectivity, continuity, and distinctiveness from your achievement details.
                </p>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={isPending} className="bg-navy-950 text-white hover:bg-navy-900">
              {isPending ? "Saving..." : editing ? "Save changes" : "Add achievement"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function AchievementCard({
  achievement,
  onEdit,
  onDelete,
}: {
  achievement: Achievement;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const status = getStatusBadge(achievement);
  const StatusIcon = status.icon;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 hover:border-slate-300 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h3 className="font-medium text-slate-900 text-sm truncate">{achievement.title}</h3>
            <Badge variant={status.variant} className="flex items-center gap-1 text-xs">
              <StatusIcon className="h-3 w-3" />
              {status.label}
            </Badge>
          </div>
          {achievement.organization_name && (
            <p className="text-xs text-slate-500 mb-1">{achievement.organization_name}</p>
          )}
          {achievement.description_raw && (
            <p className="text-xs text-slate-600 line-clamp-2">{achievement.description_raw}</p>
          )}
          <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-400">
            {achievement.impact_scope && <span>Scope: {achievement.impact_scope}</span>}
            {achievement.leadership_level && <span>· Leadership: {achievement.leadership_level}</span>}
            {achievement.hours_per_week && <span>· {achievement.hours_per_week}h/wk</span>}
            {achievement.category && <span>· {achievement.category}</span>}
          </div>
          <div className="mt-3 border-t border-slate-100 pt-3">
            <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-slate-700">
              <Sparkles className="h-3.5 w-3.5 text-blue-600" />
              Chancellor analysis
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {SCORE_FIELDS.map((field) => {
                const score = achievement[field.key];
                const numericScore = typeof score === "number" ? score : 0;
                return (
                  <div key={field.key} className="space-y-1">
                    <div className="flex items-center justify-between gap-2 text-xs">
                      <span className="text-slate-500">{field.label}</span>
                      <span className="font-medium text-slate-800">{formatScore(score)}</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-blue-600"
                        style={{ width: `${numericScore * 10}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <Button size="icon" variant="ghost" className="h-7 w-7" onClick={onEdit}>
            <Pencil className="h-3.5 w-3.5" />
          </Button>
          <Button size="icon" variant="ghost" className="h-7 w-7 text-red-400 hover:text-red-600 hover:bg-red-50" onClick={onDelete}>
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function VaultPage() {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Achievement | undefined>();
  const [defaultType, setDefaultType] = useState<"activity" | "honor">("activity");

  const { data, isLoading } = useQuery({
    queryKey: ["achievements"],
    queryFn: () => achievementsApi.list(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => achievementsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
      toast.success("Achievement deleted");
    },
  });

  const achievements: Achievement[] = data?.data?.data ?? [];
  const activities = achievements.filter((a) => a.type === "activity");
  const honors = achievements.filter((a) => a.type === "honor");

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

  return (
    <div className="p-8 max-w-4xl">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Achievement Vault</h1>
          <p className="mt-1 text-sm text-slate-500">
            {activities.length} activities · {honors.length} honors
          </p>
        </div>
      </div>

      <Tabs defaultValue="activities">
        <div className="flex items-center justify-between mb-4">
          <TabsList>
            <TabsTrigger value="activities">Activities ({activities.length})</TabsTrigger>
            <TabsTrigger value="honors">Honors ({honors.length})</TabsTrigger>
          </TabsList>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => handleAdd("honor")} className="gap-1.5">
              <Plus className="h-3.5 w-3.5" /> Add honor
            </Button>
            <Button size="sm" className="bg-navy-950 text-white hover:bg-navy-900 gap-1.5" onClick={() => handleAdd("activity")}>
              <Plus className="h-3.5 w-3.5" /> Add activity
            </Button>
          </div>
        </div>

        <TabsContent value="activities">
          {isLoading ? (
            <p className="text-sm text-slate-500">Loading...</p>
          ) : activities.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center">
              <p className="text-slate-500 mb-3">No activities yet.</p>
              <Button size="sm" className="bg-navy-950 text-white" onClick={() => handleAdd("activity")}>
                <Plus className="h-3.5 w-3.5 mr-1.5" /> Add your first activity
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {activities.map((a) => (
                <AchievementCard
                  key={a.id}
                  achievement={a}
                  onEdit={() => handleEdit(a)}
                  onDelete={() => deleteMutation.mutate(a.id)}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="honors">
          {isLoading ? (
            <p className="text-sm text-slate-500">Loading...</p>
          ) : honors.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center">
              <p className="text-slate-500 mb-3">No honors yet.</p>
              <Button size="sm" className="bg-navy-950 text-white" onClick={() => handleAdd("honor")}>
                <Plus className="h-3.5 w-3.5 mr-1.5" /> Add your first honor
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {honors.map((a) => (
                <AchievementCard
                  key={a.id}
                  achievement={a}
                  onEdit={() => handleEdit(a)}
                  onDelete={() => deleteMutation.mutate(a.id)}
                />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      <AchievementModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        defaultType={defaultType}
        editing={editing}
      />
    </div>
  );
}
