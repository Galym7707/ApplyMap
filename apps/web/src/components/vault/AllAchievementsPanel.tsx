"use client";

import type { ReactNode } from "react";
import { FileText, Loader2, Sparkles, Trophy, Upload } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { AchievementImportResult, AchievementImportSelectionItem } from "@/types";

const ACTIVITY_POSITION_LIMIT = 50;
const ACTIVITY_ORGANIZATION_LIMIT = 100;
const ACTIVITY_DESCRIPTION_LIMIT = 150;
const HONOR_DESCRIPTION_LIMIT = 100;

function CharacterBadge({ count = 0, limit }: { count?: number; limit: number }) {
  const isOver = count > limit;
  return (
    <Badge variant={isOver ? "destructive" : "secondary"} className="shrink-0">
      {count}/{limit} chars
    </Badge>
  );
}

function CommonAppField({
  label,
  value,
  count,
  limit,
}: {
  label: string;
  value?: string;
  count?: number;
  limit: number;
}) {
  return (
    <div className="rounded-lg bg-white px-3 py-2">
      <div className="mb-1 flex items-center justify-between gap-3">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{label}</p>
        <CharacterBadge count={count ?? value?.length ?? 0} limit={limit} />
      </div>
      <p className="text-sm leading-relaxed text-slate-800">{value || "Not enough information yet."}</p>
    </div>
  );
}

function SelectionColumn({
  title,
  subtitle,
  items,
  icon,
}: {
  title: string;
  subtitle: string;
  items: AchievementImportSelectionItem[];
  icon: ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-navy-50 text-navy-900">
          {icon}
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
          <p className="text-xs text-slate-500">{subtitle}</p>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">
          No shortlist generated yet.
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.achievement_id} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <div className="mb-2 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Rank #{item.rank}
                  </p>
                  <h4 className="truncate text-sm font-semibold text-slate-900">{item.title}</h4>
                </div>
                <Badge variant="info" className="shrink-0">
                  {item.type === "activity" ? "Activity" : "Honor"}
                </Badge>
              </div>

              {item.type === "activity" ? (
                <div className="space-y-2">
                  <CommonAppField
                    label="Position / leadership"
                    value={item.common_app_position}
                    count={item.position_character_count}
                    limit={ACTIVITY_POSITION_LIMIT}
                  />
                  <CommonAppField
                    label="Organization"
                    value={item.common_app_organization}
                    count={item.organization_character_count}
                    limit={ACTIVITY_ORGANIZATION_LIMIT}
                  />
                  <CommonAppField
                    label="Activity description"
                    value={item.common_app_activity_description || item.common_app_text}
                    count={item.activity_description_character_count ?? item.character_count}
                    limit={ACTIVITY_DESCRIPTION_LIMIT}
                  />
                </div>
              ) : (
                <CommonAppField
                  label="Honor title / description"
                  value={item.common_app_honor_description || item.common_app_text}
                  count={item.honor_character_count ?? item.character_count}
                  limit={HONOR_DESCRIPTION_LIMIT}
                />
              )}

              {item.selection_reason && (
                <p className="mt-2 text-xs leading-relaxed text-slate-500">{item.selection_reason}</p>
              )}

              {(item.missing_or_unclear_facts ?? []).length > 0 && (
                <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-amber-700">
                    Ask before finalizing
                  </p>
                  <ul className="mt-1 list-disc space-y-1 pl-4 text-xs leading-relaxed text-amber-900">
                    {(item.missing_or_unclear_facts ?? []).map((fact) => (
                      <li key={fact}>{fact}</li>
                    ))}
                  </ul>
                </div>
              )}

              {(item.verification_notes ?? []).length > 0 && (
                <div className="mt-3 rounded-lg border border-slate-200 bg-white px-3 py-2">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                    Google source notes
                  </p>
                  <ul className="mt-1 list-disc space-y-1 pl-4 text-xs leading-relaxed text-slate-600">
                    {(item.verification_notes ?? []).map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function AllAchievementsPanel({
  result,
  wordLimit,
  onWordLimitChange,
  onUploadClick,
  onClear,
  isImporting,
  achievementCount,
  activityCount,
  honorCount,
}: {
  result: AchievementImportResult | null;
  wordLimit: string;
  onWordLimitChange: (value: string) => void;
  onUploadClick: () => void;
  onClear: () => void;
  isImporting: boolean;
  achievementCount: number;
  activityCount: number;
  honorCount: number;
}) {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl border border-slate-200 bg-gradient-to-br from-white via-white to-navy-50 p-6">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-navy-500">
                AI Curation
              </p>
              <h2 className="mt-2 text-xl font-semibold text-slate-900">
                Upload one mixed file and build the strongest Common App shortlist
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
                The app extracts achievements from one messy note, classifies them into activities and
                honors, picks the strongest top 10 and top 5, and writes Common App-ready fields under
                strict character limits.
              </p>
            </div>
            <div className="hidden rounded-2xl bg-white p-3 shadow-sm lg:block">
              <Sparkles className="h-8 w-8 text-navy-700" />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-[1fr_auto]">
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white/70 p-5">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 flex h-10 w-10 items-center justify-center rounded-xl bg-navy-100 text-navy-900">
                  <Upload className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Supported MVP formats</h3>
                  <p className="mt-1 text-sm text-slate-600">
                    Text-based `.txt`, `.md`, `.csv`, or `.json` files work best right now.
                  </p>
                  <p className="mt-2 text-xs leading-relaxed text-slate-500">
                    Best input shape: one note or bullet list with awards, leadership, volunteering,
                    competitions, research, and activities all mixed together.
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5">
              <Label htmlFor="vault-word-limit">Target word limit</Label>
              <Input
                id="vault-word-limit"
                type="number"
                min={5}
                max={40}
                value={wordLimit}
                onChange={(event) => onWordLimitChange(event.target.value)}
                className="mt-2"
              />
              <p className="mt-2 text-xs text-slate-500">
                Backup cap only. Common App character limits are enforced separately.
              </p>
              <Button
                className="mt-4 w-full gap-2 bg-navy-950 text-white hover:bg-navy-900"
                onClick={onUploadClick}
                disabled={isImporting}
              >
                {isImporting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4" />
                    Upload mixed achievement file
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">All Items</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{achievementCount}</p>
            <p className="mt-1 text-sm text-slate-500">
              Current vault total across both manual and AI-imported entries
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Activities / Honors</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">
              {activityCount} / {honorCount}
            </p>
            <p className="mt-1 text-sm text-slate-500">Live counts already stored in your vault</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Latest Import</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{result?.imported_count ?? 0}</p>
            <p className="mt-1 text-sm text-slate-500">New items extracted from the latest uploaded file</p>
          </div>
        </div>
      </div>

      {result ? (
        <>
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
                  Strongest Angle
                </p>
                <p className="mt-2 text-base font-medium leading-relaxed text-emerald-950">
                  {result.strongest_angle}
                </p>
                <p className="mt-2 text-sm text-emerald-800">
                  Latest file: {result.file_name} - {result.word_limit} word limit
                </p>
              </div>
              <Button variant="outline" onClick={onClear}>
                Clear latest analysis
              </Button>
            </div>
          </div>

          {result.needs_student_clarification && (result.clarifying_questions ?? []).length > 0 && (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-700">
                Questions before final wording
              </p>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-amber-950">
                {(result.clarifying_questions ?? []).map((question) => (
                  <li key={question}>{question}</li>
                ))}
              </ul>
            </div>
          )}

          {result.additional_information_recommended && result.additional_information_draft && (
            <div className="rounded-2xl border border-sky-200 bg-sky-50 p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-700">
                Additional Information draft
              </p>
              {result.additional_information_reason && (
                <p className="mt-2 text-sm leading-relaxed text-sky-900">
                  {result.additional_information_reason}
                </p>
              )}
              <p className="mt-3 rounded-lg bg-white px-4 py-3 text-sm leading-relaxed text-slate-800">
                {result.additional_information_draft}
              </p>
            </div>
          )}

          {(result.formatting_notes ?? []).length > 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                Formatting and verification notes
              </p>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-600">
                {(result.formatting_notes ?? []).map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="grid gap-6 xl:grid-cols-2">
            <SelectionColumn
              title="Top 10 Activities"
              subtitle="These should sit at the top of your Common App order."
              items={result.top_activities}
              icon={<FileText className="h-5 w-5" />}
            />
            <SelectionColumn
              title="Top 5 Honors"
              subtitle="Best award shortlist based on selectivity and distinctiveness."
              items={result.top_honors}
              icon={<Trophy className="h-5 w-5" />}
            />
          </div>
        </>
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-200 bg-white px-8 py-12 text-center">
          <Sparkles className="mx-auto h-8 w-8 text-slate-300" />
          <h3 className="mt-4 text-sm font-semibold text-slate-700">No AI shortlist yet</h3>
          <p className="mt-2 text-sm leading-relaxed text-slate-500">
            Upload a mixed achievement file to generate the strongest activity and honor shortlist on this screen.
          </p>
        </div>
      )}
    </div>
  );
}
