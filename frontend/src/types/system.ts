export interface SystemStatus {
  app_name: string
  app_version: string
  status: string
  first_setup_completed: boolean
  photo_count: number
  days_recorded: number
  photo_root_configured: boolean
}

export interface SystemConfig {
  app_name: string
  birth_date: string | null
  photo_root: string | null
  data_root: string
  thumbnail_size: number
  preview_size: number
  first_setup_completed: boolean
}

export interface SetupPayload {
  birth_date: string
  photo_root: string
}
