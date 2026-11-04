export interface CollectionItem {
  id: number
  name: string
  description: string | null
  cover_photo_id: number | null
  cover_thumbnail_url: string | null
  photo_count: number
  sort_order: number
  created_at: string
}

export interface CollectionDetail extends CollectionItem {
  photos: {
    id: number
    photo_date: string
    filename: string
    width: number
    height: number
    is_highlight: number
    description: string | null
    thumbnail_url: string
    preview_url: string
    sort_order: number
  }[]
}
