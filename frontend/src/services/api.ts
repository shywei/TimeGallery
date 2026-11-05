import type { SystemStatus, SystemConfig } from '../types/system'
import type { PhotoItem, PhotoDetail } from '../types/photo'
import type { DayViewData, WeekViewData, MonthCalendarData, MonthPhotoWallData } from '../types/calendar'
import type { CollectionItem, CollectionDetail } from '../types/collection'
import type { ScanJob, ScanIssue, MissingDatesSummary } from '../types/scanner'
import type { MomentItem, MomentDetail } from '../types/moment'
import type { DayContentStatus, TrashStats } from '../types/content_mgmt'

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
  getPhotos: (params?: { page?: number; page_size?: number; year?: number; month?: number; search?: string; is_highlight?: boolean; tag_id?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.page) searchParams.set('page', params.page.toString())
    if (params?.page_size) searchParams.set('page_size', params.page_size.toString())
    if (params?.year) searchParams.set('year', params.year.toString())
    if (params?.month) searchParams.set('month', params.month.toString())
    if (params?.search) searchParams.set('search', params.search)
    if (params?.is_highlight !== undefined) searchParams.set('is_highlight', params.is_highlight.toString())
    if (params?.tag_id) searchParams.set('tag_id', params.tag_id.toString())
    return request<{ total: number; page: number; page_size: number; items: PhotoItem[] }>(`/api/photos?${searchParams.toString()}`)
  },
  getPhotoYears: () => request<string[]>('/api/photos/years'),
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
  exportJsonUrl: '/api/backup/export-json',

  // Moments (特别时刻)
  getMoments: () => request<MomentItem[]>('/api/moments'),
  getMomentDetail: (momentDateOrId: string | number) => request<MomentDetail>(`/api/moments/${momentDateOrId}`),
  updateMoment: (momentDateOrId: string | number, payload: { title?: string; description?: string; cover_media_id?: number }) =>
    request<{ id: number; moment_date: string; title: string; description?: string; cover_media_id?: number }>(
      `/api/moments/${momentDateOrId}`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }
    ),

  // Content Management (手动维护主图与特殊时刻 & 回收站)
  getDayContentStatus: (dateStr: string) => request<DayContentStatus>(`/api/mgmt/content/day/${dateStr}`),
  uploadDailyPhoto: (dateStr: string, file: File, targetRoot?: string) => {
    const formData = new FormData()
    formData.append('date_str', dateStr)
    formData.append('file', file)
    if (targetRoot) formData.append('target_root', targetRoot)
    return request<{ success: boolean; message: string; photo: any }>('/api/mgmt/content/daily-photo', {
      method: 'POST',
      body: formData
    })
  },
  deleteDailyPhoto: (dateStr: string) => request<{ success: boolean; message: string }>(`/api/mgmt/content/daily-photo/${dateStr}`, {
    method: 'DELETE'
  }),
  uploadMomentMedia: (dateStr: string, files: File[], title?: string, description?: string, targetRoot?: string) => {
    const formData = new FormData()
    formData.append('date_str', dateStr)
    if (title) formData.append('title', title)
    if (description) formData.append('description', description)
    if (targetRoot) formData.append('target_root', targetRoot)
    files.forEach((f) => formData.append('files', f))
    return request<{ success: boolean; message: string; moment_id: number; photo_count: number; video_count: number }>('/api/mgmt/content/moment-media', {
      method: 'POST',
      body: formData
    })
  },
  deleteMomentMedia: (mediaId: number) => request<{ success: boolean; message: string }>(`/api/mgmt/content/moment-media/${mediaId}`, {
    method: 'DELETE'
  }),
  deleteMoment: (dateStr: string) => request<{ success: boolean; message: string }>(`/api/mgmt/content/moment/${dateStr}`, {
    method: 'DELETE'
  }),
  getTrashStats: () => request<TrashStats>('/api/mgmt/content/trash/stats'),
  emptyTrash: () => request<{ freed_bytes: number; deleted_count: number; freed_display: string }>('/api/mgmt/content/trash/empty', {
    method: 'POST'
  })
}
