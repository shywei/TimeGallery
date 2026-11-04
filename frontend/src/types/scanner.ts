export interface MissingRange {
  start: string
  end: string
  count: number
}

export interface MissingDatesSummary {
  range_start: string | null
  range_end: string | null
  total_days: number
  recorded_days: number
  missing_count: number
  missing_dates: string[]
  missing_ranges: MissingRange[]
}

export interface ScanJob {
  id: number
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
  scan_type: string
  started_at: string
  finished_at: string | null
  total_files: number
  processed_files: number
  success_count: number
  error_count: number
  conflict_count: number
  message: string | null
  missing_info?: MissingDatesSummary | null
}

export interface ScanIssue {
  id: number
  scan_job_id: number
  issue_type: string
  filename: string
  relative_path: string
  parsed_date: string | null
  existing_photo_id: number | null
  details: string | null
  status: 'OPEN' | 'RESOLVED' | 'IGNORED'
  created_at: string
  resolved_at: string | null
}
