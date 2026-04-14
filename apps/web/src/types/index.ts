export interface User {
  id: string;
  email: string;
  role: "student" | "admin";
  full_name?: string;
  country?: string;
  created_at: string;
}

export interface StudentProfile {
  id: string;
  user_id: string;
  graduation_year?: number;
  curriculum?: string;
  intended_major?: string;
  sat_score?: number;
  act_score?: number;
  ielts_score?: string;
  toefl_score?: number;
  budget_range?: string;
  aid_needed?: boolean;
  application_preferences_json?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export type AchievementType = "activity" | "honor";
export type ImpactScope =
  | "school"
  | "local"
  | "regional"
  | "national"
  | "international"
  | "family"
  | "personal";
export type LeadershipLevel = "none" | "member" | "lead" | "founder" | "captain";

export interface Achievement {
  id: string;
  user_id: string;
  type: AchievementType;
  title: string;
  organization_name?: string;
  role_title?: string;
  description_raw?: string;
  category?: string;
  start_date?: string;
  end_date?: string;
  hours_per_week?: number;
  weeks_per_year?: number;
  impact_scope?: ImpactScope;
  leadership_level?: LeadershipLevel;
  major_relevance_score?: number;
  continuity_score?: number;
  selectivity_score?: number;
  distinctiveness_score?: number;
  truth_risk_flag?: boolean;
  created_at: string;
  updated_at: string;
  evidence_files: EvidenceFile[];
}

export interface EvidenceFile {
  id: string;
  file_url: string;
  file_name: string;
  mime_type?: string;
  uploaded_at: string;
}

export interface AchievementImportSelectionItem {
  achievement_id: string;
  type: AchievementType;
  rank: number;
  title: string;
  common_app_text: string;
  word_count: number;
  character_count: number;
  selection_reason?: string;
}

export interface AchievementImportResult {
  file_name: string;
  word_limit: number;
  imported_count: number;
  strongest_angle: string;
  imported_achievements: Achievement[];
  top_activities: AchievementImportSelectionItem[];
  top_honors: AchievementImportSelectionItem[];
}

export type WeightPreset =
  | "research_heavy"
  | "leadership_heavy"
  | "balanced_holistic"
  | "community_service_heavy";

export interface University {
  id: string;
  slug: string;
  name: string;
  country: string;
  application_system?: string;
  short_description?: string;
  weight_preset: WeightPreset;
  is_active: boolean;
  region?: string;
  city?: string;
  is_common_app?: boolean;
  application_source_url?: string;
  teaching_languages?: string[];
  major_strengths?: string[];
  education_years_required?: number;
  school_years_note?: string;
  aid_type?: string;
  aid_strength?: number;
  selectivity_score?: number;
  full_ride_possible?: boolean;
  full_tuition_possible?: boolean;
  aid_notes?: string;
  funding_source_url?: string;
  funding_source_title?: string;
  eligibility_notes?: string;
}

export interface CommonAppRecommendation {
  university_id: string;
  slug: string;
  name: string;
  country: string;
  category: "dream" | "target" | "safe";
  rationale: string;
  fit_notes?: string;
  aid_notes?: string;
  funding_source_url?: string;
}

export interface PolicyEntry {
  id: string;
  university_id: string;
  title: string;
  content: string;
  source_url?: string;
  source_title?: string;
  source_type: "official" | "public_example";
  reliability_tier: "A" | "B" | "C" | "D";
  excerpt?: string;
  created_at: string;
  updated_at: string;
}

export interface TargetUniversity {
  id: string;
  user_id: string;
  university_id: string;
  priority_order?: number;
  created_at: string;
  university: University;
}

export type ReportStatus = "pending" | "processing" | "completed" | "failed";
export type RecommendationType = "keep" | "remove" | "merge" | "rewrite" | "reorder";
export type ConfidenceLabel = "low" | "medium" | "high";

export interface Report {
  id: string;
  user_id: string;
  university_id: string;
  status: ReportStatus;
  summary_text?: string;
  version_number: number;
  created_at: string;
  completed_at?: string;
  university: University;
}

export interface Recommendation {
  id: string;
  report_id: string;
  achievement_id: string;
  recommendation_type: RecommendationType;
  suggested_rank?: number;
  rationale?: string;
  confidence_label: ConfidenceLabel;
  created_at: string;
  achievement: Achievement;
}

export interface RewriteVariant {
  id: string;
  achievement_id: string;
  report_id: string;
  style_mode: string;
  text: string;
  character_count: number;
  is_recommended: boolean;
  explanation?: string;
  created_at: string;
}

export interface SourceReference {
  id: string;
  report_id: string;
  university_policy_entry_id: string;
  section: "official_guidance" | "public_examples" | "recommendation_support";
  note?: string;
  created_at: string;
  policy_entry: PolicyEntry;
}

export interface ReportDetail extends Report {
  recommendations: Recommendation[];
  rewrite_variants: RewriteVariant[];
  source_references: SourceReference[];
}

export interface ApiResponse<T> {
  data: T;
  message: string;
  error?: string;
}
