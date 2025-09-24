// データ型の定義
export type DataType = 'numeric' | 'categorical' | 'ordinal' | 'text'

export interface ColumnInfo {
  name: string
  data_type: DataType
  unique_count: number
  missing_count: number
  missing_rate: number
  sample_values: any[]
}

export interface UploadResponse {
  job_id: string
  filename: string
  columns: ColumnInfo[]
  preview_data: Record<string, any>[]
  message: string
}

export interface VariableMapping {
  moderators: string[]
  outcomes: string[]
  intervention: string
}

export interface DataProcessingSettings {
  center_outcomes: boolean
  center_moderators: boolean
  ordinal_outcomes: string[]
  run_sensitivity: boolean
  seed: number
}

export interface AnalysisSettings {
  variable_mapping: VariableMapping
  data_processing: DataProcessingSettings
  fdr_alpha: number
  min_sample_size: number
  generate_plots: boolean
  max_plots: number
}

export interface AnalysisRequest {
  job_id: string
  settings: AnalysisSettings
}

export interface SimpleSlope {
  slope: number
  p_value: number
  ci_lower: number
  ci_upper: number
  cohens_d: number
}

export interface InteractionResult {
  moderator: string
  outcome: string
  n_used: number
  median: number
  mean: number
  std: number
  beta_interaction: number
  p_interaction: number
  q_interaction: number
  partial_eta2: number
  simple_slope_low: SimpleSlope
  simple_slope_high: SimpleSlope
  r_squared: number
  adj_r_squared: number
}

export type AnalysisStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface AnalysisResult {
  job_id: string
  status: AnalysisStatus
  created_at: string
  completed_at?: string
  results: InteractionResult[]
  summary: Record<string, any>
  notes: string[]
  logs: string
  figures: string[]
  error_message?: string
}

export interface JobStatus {
  job_id: string
  status: AnalysisStatus
  progress: number
  message: string
  created_at: string
  updated_at: string
}

export interface ErrorResponse {
  error: string
  detail?: string
  job_id?: string
}
