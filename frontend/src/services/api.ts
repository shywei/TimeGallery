import type { SystemStatus, SystemConfig } from '../types/system'
import type { PhotoItem, PhotoDetail } from '../types/photo'
import type { DayViewData, WeekViewData, MonthCalendarData, MonthPhotoWallData } from '../types/calendar'
import type { CollectionItem, CollectionDetail } from '../types/collection'
import type { ScanJob, ScanIssue, MissingDatesSummary } from '../types/scanner'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options)
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(errorData.detail || errorData.message || `Request failed with status ${res.status}`)
  }
  return res.json()
}

export const api = {
  // System
  getSystemStatus: () => request<SystemStatus>('/api/system/status'),
  getSystemConfig: () => request<SystemConfig>('/api/system/config'),
  updateSystemConfig: (data: any) => request<any>('/api/system/config', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }),

  // Home
  getHomeOverview: () => request<any>('/api/home/overview'),

  // Photos
  getPhotos: (params?: { page?: number; page_size?: number; year?: number; month?: number; is_highlight?: boolean; tag_id?: number }) => {
    const search = new URLSearchParams()
    if (params?.page) search.set('page', params.page.toString())
    if (params?.page_size) search.set('page_size', params.page_size.toString())
    if (params?.year) search.set('year', params.year.toString())
    if (params?.month) search.set('month', params.month.toString())
    if (params?.is_highlight !== undefined) search.set('is_highlight', params.is_highlight.toString())
    if (params?.tag_id) search.set('tag_id', params.tag_id.toString())
    return request<{ total: number; page: number; page_size: number; items: PhotoItem[] }>(`/api/photos?${search.toString()}`)
  },
  getPhotoDetail: (id: number) => request<PhotoDetail>(`/api/photos/${id}`),
  updatePhotoMetadata: (id: number, data: { description?: string; is_highlight?: boolean; tags?: string[] }) =>
    request<PhotoDetail>(`/api/photos/${id}/metadata`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),

  // Calendar
  getDayView: (dateStr: string) => request<DayViewData>(`/api/calendar/day/${dateStr}`),
  getWeekView: (dateStr: string) => request<WeekViewData>(`/api/calendar/week/${dateStr}`),
  getMonthCalendar: (year: number, month: number) => request<MonthCalendarData>(`/api/calendar/month/${year}/${month}`),
  getMonthPhotoWall: (year: number, month: number) => request<MonthPhotoWallData>(`/api/calendar/month/${year}/${month}/photo-wall`),
  resolveQuickDate: (dateStr: string) => request<{ input: string; date: string; has_photo: boolean; photo_id: number | null }>(`/api/calendar/date/${dateStr}`),

  // Timeline
  getTimeline: (page = 1, pageSize = 30, tag?: string) =>
    request<any>(`/api/timeline?page=${page}&page_size=${pageSize}${tag ? `&tag=${encodeURIComponent(tag)}` : ''}`),

  // Highlights
  getHighlights: (tag?: string) => request<PhotoItem[]>(`/api/highlights${tag ? `?tag=${encodeURIComponent(tag)}` : ''}`),
  setHighlight: (id: number) => request<PhotoDetail>(`/api/highlights/${id}`, { method: 'POST' }),
  removeHighlight: (id: number) => request<PhotoDetail>(`/api/highlights/${id}`, { method: 'DELETE' }),

  // Tags
  getTags: () => request<{ id: number; name: string; count: number }[]>('/api/tags'),

  // Collections
  getCollections: () => request<CollectionItem[]>('/api/collections'),
  getCollection: (id: number) => request<CollectionDetail>(`/api/collections/${id}`),
  createCollection: (data: { name: string; description?: string }) => request<CollectionItem>('/api/collections', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }),
  updateCollection: (id: number, data: any) => request<CollectionDetail>(`/api/collections/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }),
  deleteCollection: (id: number) => request<any>(`/api/collections/${id}`, { method: 'DELETE' }),
  addPhotosToCollection: (id: number, photo_ids: number[]) => request<CollectionDetail>(`/api/collections/${id}/photos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ photo_ids })
  }),
  removePhotoFromCollection: (colId: number, photoId: number) => request<any>(`/api/collections/${colId}/photos/${photoId}`, { method: 'DELETE' }),

  // Scanner
  triggerFullScan: () => request<any>('/api/scanner/full-scan', { method: 'POST' }),
  triggerIncrementalScan: () => request<any>('/api/scanner/incremental-scan', { method: 'POST' }),
  getScanJobs: () => request<ScanJob[]>('/api/scanner/jobs'),
  getScanJob: (id: number) => request<ScanJob>(`/api/scanner/jobs/${id}`),
  getMissingDates: () => request<MissingDatesSummary>('/api/scanner/missing-dates'),
  getScanIssues: (status?: string) => request<ScanIssue[]>(`/api/scanner/issues${status ? `?status=${status}` : ''}`),
  resolveIssue: (id: number) => request<ScanIssue>(`/api/scanner/issues/${id}/resolve`, { method: 'POST' }),
  ignoreIssue: (id: number) => request<ScanIssue>(`/api/scanner/issues/${id}/ignore`, { method: 'POST' }),

  // Backup
  createBackup: () => request<any>('/api/backup/create', { method: 'POST' }),
  listBackups: () => request<any[]>('/api/backup/list'),
  restoreBackup: (filename: string) => request<any>('/api/backup/restore', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename })
  }),
  exportJsonUrl: '/api/backup/export-json'
}
