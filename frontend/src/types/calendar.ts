import type { PhotoItem, AgeInfo } from './photo'

export interface DayViewData {
  date: string
  has_photo: boolean
  photo: (PhotoItem & { original_url?: string; tags?: string[] }) | null
  has_moment?: boolean
  moment?: {
    id: number
    title: string
    photo_count: number
    video_count: number
    cover_url?: string | null
  } | null
  age: AgeInfo | null
  prev_date: string
  next_date: string
}

export interface WeekDayItem {
  date: string
  day_number: number
  day_of_week: number
  is_today: boolean
  has_photo: boolean
  photo: PhotoItem | null
  has_moment?: boolean
  moment?: {
    id: number
    title: string
    photo_count: number
    video_count: number
    cover_url?: string | null
  } | null
}

export interface WeekViewData {
  start_date: string
  end_date: string
  recorded_days: number
  total_days: number
  days: WeekDayItem[]
  prev_week_date: string
  next_week_date: string
  current_week_date: string
}

export interface MonthGridDayItem {
  date: string
  day_number: number
  is_current_month: boolean
  is_today: boolean
  has_photo: boolean
  photo: {
    id: number
    photo_date: string
    thumbnail_url: string
    preview_url: string
    is_highlight: number
  } | null
  has_moment?: boolean
  moment?: {
    id: number
    title: string
    photo_count: number
    video_count: number
    cover_url?: string | null
  } | null
}

export interface MonthCalendarData {
  year: number
  month: number
  days_in_month: number
  recorded_days: number
  total_days: number
  days: MonthGridDayItem[]
  prev_month: { year: number; month: number }
  next_month: { year: number; month: number }
}

export interface PhotoWallItem {
  id: number
  photo_date: string
  width: number
  height: number
  is_highlight: number
  description: string | null
  thumbnail_url: string
  preview_url: string
  aspect_ratio: number
  has_moment?: boolean
  moment?: {
    id: number
    title: string
    photo_count: number
    video_count: number
    cover_url?: string | null
  } | null
}

export interface MonthPhotoWallData {
  year: number
  month: number
  total_photos: number
  items: PhotoWallItem[]
  prev_month: { year: number; month: number }
  next_month: { year: number; month: number }
}
