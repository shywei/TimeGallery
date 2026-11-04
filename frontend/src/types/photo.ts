export interface Tag {
  id: number
  name: string
}

export interface AgeInfo {
  years: number
  months: number
  days: number
  display: string
  is_valid: boolean
}

export interface PhotoItem {
  id: number
  photo_date: string
  filename: string
  relative_path: string
  width: number
  height: number
  status: string
  is_highlight: number
  description: string | null
  thumbnail_url: string
  preview_url: string
  age?: AgeInfo | null
}

export interface OnThisDayPhotoItem {
  id: number
  photo_date: string
  year: number
  diff_years: number
  title: string
  thumbnail_url: string
  preview_url: string
  age_display?: string | null
}

export interface PhotoDetail extends PhotoItem {
  file_size: number
  mime_type: string
  imported_at: string
  last_scanned_at: string
  original_url: string
  age_at_photo?: AgeInfo | null
  tags: Tag[]
  collections: { id: number; name: string }[]
  on_this_day_photos?: OnThisDayPhotoItem[]
  prev_photo_id?: number | null
  next_photo_id?: number | null
  prev_date?: string | null
  next_date?: string | null
}
