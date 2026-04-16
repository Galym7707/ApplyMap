"use client";

import type { ReactNode } from "react";
import { CheckCircle2, Circle, FileText, Loader2, RefreshCw, Sparkles, Trophy, Upload } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { AchievementImportResult, AchievementImportSelectionItem, AchievementImportStep } from "@/types";

const ACTIVITY_POSITION_LIMIT = 50;
const ACTIVITY_ORGANIZATION_LIMIT = 100;
const ACTIVITY_DESCRIPTION_LIMIT = 150;
const HONOR_DESCRIPTION_LIMIT = 100;

const LIVE_IMPORT_STEPS: AchievementImportStep[] = [
  {
    key: "upload",
    label: "Upload file",
    status: "pending",
    detail: "Sending the selected file to the backend.",
  },
  {
    key: "extract_text",
    label: "Extract text",
    status: "pending",
    detail: "Reading PDF, DOCX, or text content while preserving bullets and line breaks.",
  },
  {
    key: "candidate_scan",
    label: "Scan candidates",
    status: "pending",
    detail: "Looking for awards, activities, research, leadership, service, work, and competitions.",
  },
  {
    key: "chancellor_analysis",
    label: "Chancellor analysis",
    status: "pending",
    detail: "Classifying, scoring, ranking, and checking unclear claims.",
  },
  {
    key: "common_app_format",
    label: "Common App formatting",
    status: "pending",
    detail: "Writing copy-paste-ready activity and honor fields under character limits.",
  },
  {
    key: "save_results",
    label: "Save results",
    status: "pending",
    detail: "Saving extracted items and the shortlist to your vault.",
  },
];

export interface ImportProgressState {
  fileName: string;
  fileSizeLabel: string;
  currentStepIndex: number;
  sourcePreview: string[];
}

export type ClarificationAnswers = Record<string, string>;

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

function getAnswerInputProps(question: string) {
  const normalized = question.toLowerCase();
  if (normalized.includes("hours per week") || normalized.includes("hrs/week")) {
    return { type: "number", placeholder: "e.g. 5" };
  }
  if (normalized.includes("weeks per year") || normalized.includes("wks/year")) {
    return { type: "number", placeholder: "e.g. 36" };
  }
  if (normalized.includes("start date")) {
    return { type: "text", placeholder: "e.g. 2024-09" };
  }
  if (normalized.includes("end date")) {
    return { type: "text", placeholder: "e.g. 2026-05 or Present" };
  }
  if (normalized.includes("year") || normalized.includes("date")) {
    return { type: "text", placeholder: "e.g. 2025, Grade 11" };
  }
  if (normalized.includes("participant") || normalized.includes("team")) {
    return { type: "text", placeholder: "e.g. 200 participants / 30 teams" };
  }
  if (normalized.includes("status")) {
    return { type: "text", placeholder: "e.g. active, maintained, completed" };
  }
  return { type: "text", placeholder: "Type the missing detail here" };
}

function ClarificationFields({
  questions,
  scope,
  answers,
  onAnswerChange,
}: {
  questions: string[];
  scope: string;
  answers: ClarificationAnswers;
  onAnswerChange: (key: string, value: string) => void;
}) {
  if (questions.length === 0) return null;

  return (
    <div className="mt-3 space-y-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-3">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-amber-700">
        Answer before reanalysis
      </p>
      {questions.map((question, index) => {
        const key = `${scope}:${index}:${question}`;
        const inputProps = getAnswerInputProps(question);
        return (
          <div key={key} className="grid gap-2 md:grid-cols-[minmax(0,0.95fr)_minmax(180px,0.75fr)]">
            <Label htmlFor={key} className="text-xs leading-relaxed text-amber-950">
              {question}
            </Label>
            <Input
              id={key}
              type={inputProps.type}
              value={answers[key] ?? ""}
              placeholder={inputProps.placeholder}
              onChange={(event) => onAnswerChange(key, event.target.value)}
              className="h-9 border-amber-200 bg-white text-sm"
            />
          </div>
        );
      })}
    </div>
  );
}

function ImportTracePanel({
  result,
  progress,
  isImporting,
}: {
  result: AchievementImportResult | null;
  progress: ImportProgressState | null;
  isImporting: boolean;
}) {
  if (!isImporting && !result) return null;

  const liveSteps = LIVE_IMPORT_STEPS.map((step, index) => ({
    ...step,
    status:
      !progress || index > progress.currentStepIndex
        ? "pending"
        : index === progress.currentStepIndex
        ? "active"
        : "complete",
  }));
  const steps = isImporting ? liveSteps : result?.processing_steps ?? [];
  const excerpts = isImporting ? progress?.sourcePreview ?? [] : result?.source_excerpts ?? [];
  const notes = result?.extraction_notes ?? [];

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
            AI work trace
          </p>
          <h3 className="mt-1 text-base font-semibold text-slate-900">
            {isImporting ? "Chancellor is analyzing your file" : "What the Chancellor completed"}
          </h3>
          {progress && (
            <p className="mt-1 text-sm text-slate-500">
              {progress.fileName} - {progress.fileSizeLabel}
            </p>
          )}
        </div>
        {isImporting && (
          <Badge variant="info" className="w-fit gap-1.5">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Running
          </Badge>
        )}
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-2">
          {steps.map((step) => {
            const isActive = step.status === "active";
            const isComplete = step.status === "complete";
            return (
              <div
                key={step.key}
                className={`rounded-xl border px-3 py-2 ${
                  isActive
                    ? "border-blue-200 bg-blue-50"
                    : isComplete
                    ? "border-emerald-200 bg-emerald-50"
                    : "border-slate-200 bg-slate-50"
                }`}
              >
                <div className="flex items-start gap-2">
                  {isComplete ? (
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                  ) : isActive ? (
                    <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-blue-600" />
                  ) : (
                    <Circle className="mt-0.5 h-4 w-4 shrink-0 text-slate-300" />
                  )}
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{step.label}</p>
                    <p className="mt-0.5 text-xs leading-relaxed text-slate-500">{step.detail}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Text being checked
          </p>
          {excerpts.length > 0 ? (
            <div className="mt-3 space-y-2">
              {excerpts.slice(0, 6).map((excerpt, index) => (
                <p key={`${excerpt}-${index}`} className="rounded-lg bg-white px-3 py-2 text-xs leading-relaxed text-slate-700">
                  {excerpt}
                </p>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-sm leading-relaxed text-slate-500">
              {isImporting
                ? "For PDF and DOCX files, text excerpts appear after backend extraction finishes."
                : "No source excerpts were returned for this import."}
            </p>
          )}

          {notes.length > 0 && (
            <div className="mt-4 border-t border-slate-200 pt-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Extraction notes
              </p>
              <ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-relaxed text-slate-600">
                {notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SelectionColumn({
  title,
  subtitle,
  items,
  icon,
  clarificationAnswers,
  onClarificationAnswerChange,
}: {
  title: string;
  subtitle: string;
  items: AchievementImportSelectionItem[];
  icon: ReactNode;
  clarificationAnswers: ClarificationAnswers;
  onClarificationAnswerChange: (key: string, value: string) => void;
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

              <ClarificationFields
                questions={item.missing_or_unclear_facts ?? []}
                scope={`item:${item.achievement_id}`}
                answers={clarificationAnswers}
                onAnswerChange={onClarificationAnswerChange}
              />

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
  onReanalyze,
  onClear,
  isImporting,
  importProgress,
  clarificationAnswers,
  onClarificationAnswerChange,
  canReanalyze,
  achievementCount,
  activityCount,
  honorCount,
}: {
  result: AchievementImportResult | null;
  wordLimit: string;
  onWordLimitChange: (value: string) => void;
  onUploadClick: () => void;
  onReanalyze: () => void;
  onClear: () => void;
  isImporting: boolean;
  importProgress: ImportProgressState | null;
  clarificationAnswers: ClarificationAnswers;
  onClarificationAnswerChange: (key: string, value: string) => void;
  canReanalyze: boolean;
  achievementCount: number;
  activityCount: number;
  honorCount: number;
}) {
  const hasClarificationAnswers = Object.values(clarificationAnswers).some((value) => value.trim().length > 0);

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
                  <h3 className="text-sm font-semibold text-slate-900">Supported formats</h3>
                  <p className="mt-1 text-sm text-slate-600">
                    `.pdf`, `.docx`, `.txt`, `.md`, `.csv`, or `.json` files are supported.
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
                    Analyzing file...
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
          <ImportTracePanel result={result} progress={importProgress} isImporting={isImporting} />

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

          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                  Clarification workspace
                </p>
                <p className="mt-1 text-sm leading-relaxed text-slate-600">
                  Fill one field per missing detail, then reanalyze the same file to rebuild the shortlist.
                </p>
              </div>
              <Button
                variant="outline"
                className="w-full gap-2 lg:w-auto"
                onClick={onReanalyze}
                disabled={isImporting || !hasClarificationAnswers || !canReanalyze}
              >
                {isImporting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                Reanalyze with answers
              </Button>
            </div>
            {!canReanalyze && (
              <p className="mt-3 text-xs leading-relaxed text-amber-700">
                Reanalysis needs the original file in this browser session. Upload the file again, then answer the fields.
              </p>
            )}
          </div>

          {result.needs_student_clarification && (result.clarifying_questions ?? []).length > 0 && (
            <div className="rounded-2xl border border-amber-200 bg-white p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-700">
                General questions before final wording
              </p>
              <ClarificationFields
                questions={result.clarifying_questions ?? []}
                scope="global"
                answers={clarificationAnswers}
                onAnswerChange={onClarificationAnswerChange}
              />
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
              clarificationAnswers={clarificationAnswers}
              onClarificationAnswerChange={onClarificationAnswerChange}
            />
            <SelectionColumn
              title="Top 5 Honors"
              subtitle="Best award shortlist based on selectivity and distinctiveness."
              items={result.top_honors}
              icon={<Trophy className="h-5 w-5" />}
              clarificationAnswers={clarificationAnswers}
              onClarificationAnswerChange={onClarificationAnswerChange}
            />
          </div>
        </>
      ) : (
        <>
          <ImportTracePanel result={result} progress={importProgress} isImporting={isImporting} />
          {!isImporting && (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-white px-8 py-12 text-center">
              <Sparkles className="mx-auto h-8 w-8 text-slate-300" />
              <h3 className="mt-4 text-sm font-semibold text-slate-700">No AI shortlist yet</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-500">
                Upload a mixed achievement file to generate the strongest activity and honor shortlist on this screen.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
