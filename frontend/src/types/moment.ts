export interface MomentItem {
  id: number
  moment_date: string
  folder_name: string
  title: string
  description?: string
  cover_media_id?: number | null
  photo_count: number
  video_count: number
  total_media: number
  cover_url?: string
  age_display?: string
}

export interface MomentMediaItem {
  id: number
  media_type: 'PHOTO' | 'VIDEO'
  filename: string
  file_size: number
  thumbnail_url: string
  preview_url?: string
  stream_url?: string
  original_url: string
  sort_order: number
}

export interface MomentDetail {
  id: number
  moment_date: string
  folder_name: string
  title: string
  description?: string
  cover_media_id?: number | null
  photo_count: number
  video_count: number
  total_media: number
  age_at_moment?: {
    years: number
    months: number
    days: number
    display: string
  }
  day_photo?: {
    id: number
    thumbnail_url: string
    preview_url: string
    description?: string
  }
  media_items: MomentMediaItem[]
}
