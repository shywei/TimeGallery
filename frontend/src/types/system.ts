export type BaselineType = 'BIRTHDAY' | 'ANNIVERSARY' | 'START_DATE' | 'CUSTOM' | 'NONE'

export interface SystemStatus {
  app_name: string
  app_version: string
  status: string
  first_setup_completed: boolean
  photo_count: number
  days_recorded: number
  photo_root_configured: boolean
  photo_roots_count?: number
}

export interface SystemConfig {
  app_name: string
  birth_date: string | null
  baseline_type?: BaselineType
  baseline_date?: string | null
  baseline_label?: string | null
  photo_root: string | null
  photo_roots?: string[]
  primary_photo_root?: string | null
  data_root: string
  thumbnail_size: number
  preview_size: number
  first_setup_completed: boolean
}

export interface SetupPayload {
  birth_date?: string
  baseline_type?: BaselineType
  baseline_date?: string
  baseline_label?: string
  photo_root?: string
  photo_roots?: string[]
  primary_photo_root?: string
}

export interface SystemConfigUpdatePayload {
  photo_root?: string
  photo_roots?: string[]
  primary_photo_root?: string
  birth_date?: string
  baseline_type?: BaselineType
  baseline_date?: string
  baseline_label?: string
  thumbnail_size?: number
  preview_size?: number
}
