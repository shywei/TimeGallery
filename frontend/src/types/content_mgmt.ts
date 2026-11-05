export interface DailyPhotoMgmt {
  id: number | null
  photo_date: string
  filename: string
  relative_path: string
  file_size: number
  file_size_display: string
  width: number | null
  height: number | null
  mime_type: string
  thumbnail_url: string | null
  preview_url: string | null
  description: string | null
  is_highlight: number
  tags: string[]
  unindexed?: boolean
}

export interface MomentMediaMgmt {
  id: number
  media_type: 'PHOTO' | 'VIDEO'
  filename: string
  relative_path: string
  file_size: number
  file_size_display: string
  thumbnail_url: string
  preview_url: string
  raw_url: string
  is_cover: boolean
}

export interface MomentMgmt {
  id: number | null
  moment_date: string
  folder_name: string
  title: string | null
  description: string | null
  cover_media_id: number | null
  cover_thumbnail_url: string | null
  photo_count: number
  video_count: number
  media_items: MomentMediaMgmt[]
  unindexed?: boolean
}

export interface DayContentStatus {
  date: string
  yymmdd: string
  has_daily_photo: boolean
  daily_photo: DailyPhotoMgmt | null
  has_moment: boolean
  moment: MomentMgmt | null
}

export interface TrashStats {
  file_count: number
  total_size_bytes: number
  total_size_display: string
}
