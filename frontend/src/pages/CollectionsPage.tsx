import React, { useEffect, useState, useMemo, useRef } from 'react'
import { FolderHeart, Plus, Trash2, ArrowLeft, Loader2, X, Check, Search, Calendar, CheckSquare, Square } from 'lucide-react'
import { api } from '../services/api'
import type { CollectionItem, CollectionDetail } from '../types/collection'
import type { PhotoItem } from '../types/photo'

interface CollectionsPageProps {
  onOpenPhoto: (photoId: number) => void
  isManagementMode?: boolean
}

interface AddPhotosModalProps {
  collectionId: number
  collectionName: string
  existingPhotoIds: Set<number>
  onClose: () => void
  onSuccess: () => void
}

const PAGE_SIZE = 40

const AddPhotosModal: React.FC<AddPhotosModalProps> = ({
  collectionId,
  collectionName,
  existingPhotoIds,
  onClose,
  onSuccess
}) => {
  const [photos, setPhotos] = useState<PhotoItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [initialLoading, setInitialLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)

  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [selectedYear, setSelectedYear] = useState<string>('all')
  const [availableYears, setAvailableYears] = useState<string[]>([])

  // Selected photo IDs are retained across paging and search
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [submitting, setSubmitting] = useState(false)

  const gridContainerRef = useRef<HTMLDivElement>(null)

  // Fetch available photo archive years once from backend
  useEffect(() => {
    api.getPhotoYears()
      .then((yrs) => setAvailableYears(yrs))
      .catch(() => {})
  }, [])

  // Debounce user search input by 300ms
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm.trim())
    }, 300)
    return () => clearTimeout(timer)
  }, [searchTerm])

  // When year or debounced search changes, reset page to 1 and query backend
  useEffect(() => {
    let isCancelled = false
    setInitialLoading(true)
    setPage(1)

    const params = {
      page: 1,
      page_size: PAGE_SIZE,
      year: selectedYear === 'all' ? undefined : Number(selectedYear),
      search: debouncedSearch || undefined
    }

    api.getPhotos(params)
      .then((res) => {
        if (isCancelled) return
        setPhotos(res.items)
        setTotal(res.total)
        setInitialLoading(false)
        if (gridContainerRef.current) {
          gridContainerRef.current.scrollTop = 0
        }
      })
      .catch(() => {
        if (!isCancelled) setInitialLoading(false)
      })

    return () => {
      isCancelled = true
    }
  }, [selectedYear, debouncedSearch])

  const hasMore = photos.length < total

  // Load next page on scroll
  const loadNextPage = async () => {
    if (loadingMore || !hasMore) return
    setLoadingMore(true)
    const nextPage = page + 1

    try {
      const res = await api.getPhotos({
        page: nextPage,
        page_size: PAGE_SIZE,
        year: selectedYear === 'all' ? undefined : Number(selectedYear),
        search: debouncedSearch || undefined
      })

      setPhotos((prev) => {
        const seen = new Set(prev.map((p) => p.id))
        const newItems = res.items.filter((p) => !seen.has(p.id))
        return [...prev, ...newItems]
      })
      setTotal(res.total)
      setPage(nextPage)
    } catch (err) {
      console.error('Failed to load next page of photos:', err)
    } finally {
      setLoadingMore(false)
    }
  }

  const handleScroll = () => {
    const el = gridContainerRef.current
    if (!el || loadingMore || !hasMore) return
    // If scrolled close to bottom (within 180px), load next page
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 180) {
      loadNextPage()
    }
  }

  // Selectable photos in the currently loaded list (not yet in collection)
  const selectableLoaded = useMemo(() => {
    return photos.filter((p) => !existingPhotoIds.has(p.id))
  }, [photos, existingPhotoIds])

  const isAllLoadedSelected =
    selectableLoaded.length > 0 &&
    selectableLoaded.every((p) => selectedIds.has(p.id))

  const toggleSelect = (id: number) => {
    if (existingPhotoIds.has(id)) return
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleSelectAllLoaded = () => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (isAllLoadedSelected) {
        selectableLoaded.forEach((p) => next.delete(p.id))
      } else {
        selectableLoaded.forEach((p) => next.add(p.id))
      }
      return next
    })
  }

  const handleConfirm = async () => {
    if (selectedIds.size === 0) return
    setSubmitting(true)
    try {
      await api.addPhotosToCollection(collectionId, Array.from(selectedIds))
      onSuccess()
      onClose()
    } catch (err: any) {
      alert(`添加照片失败: ${err.message}`)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-150">
      <div className="bg-[#FAF9F5] border border-[#E5E0D8] rounded-3xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-[#EAE5DC] flex items-center justify-between">
          <div>
            <h3 className="font-serif text-xl font-medium text-[#1A1918]">
              添加每日主图至「{collectionName}」
            </h3>
            <p className="text-xs text-[#7D756E] mt-1">
              后端实时检索与滚动翻页加载，仅展示每日主图档案（特别时刻图集不在此处）。
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-[#EFECE6] text-[#7D756E] transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Toolbar: Backend Year filter & Search Bar */}
        <div className="px-6 py-3 bg-white border-b border-[#EAE5DC] space-y-2.5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            {/* Year tabs (Backend filtered) */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-xs text-[#8C827A] flex items-center gap-1 mr-1">
                <Calendar className="w-3.5 h-3.5" /> 年份:
              </span>
              <button
                type="button"
                onClick={() => setSelectedYear('all')}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                  selectedYear === 'all'
                    ? 'bg-[#2C2622] text-white shadow-xs'
                    : 'bg-[#F2EFE9] text-[#5C534B] hover:bg-[#EAE5DC]'
                }`}
              >
                全部年份
              </button>
              {availableYears.map((yr) => (
                <button
                  key={yr}
                  type="button"
                  onClick={() => setSelectedYear(yr)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                    selectedYear === yr
                      ? 'bg-[#2C2622] text-white shadow-xs'
                      : 'bg-[#F2EFE9] text-[#5C534B] hover:bg-[#EAE5DC]'
                  }`}
                >
                  {yr}年
                </button>
              ))}
            </div>

            {/* Quick batch select button for currently loaded */}
            {selectableLoaded.length > 0 && (
              <button
                type="button"
                onClick={toggleSelectAllLoaded}
                className="inline-flex items-center gap-1 text-xs text-[#6B5F54] hover:text-[#1A1918] bg-[#F7F5F0] hover:bg-[#EFECE6] border border-[#DDD7CD] px-2.5 py-1 rounded-lg transition-colors cursor-pointer"
              >
                {isAllLoadedSelected ? (
                  <>
                    <CheckSquare className="w-3.5 h-3.5 text-[#8C7A6B]" />
                    取消选中已加载项
                  </>
                ) : (
                  <>
                    <Square className="w-3.5 h-3.5 text-[#8C7A6B]" />
                    全选当前已加载 ({selectableLoaded.length})
                  </>
                )}
              </button>
            )}
          </div>

          {/* Search Input (Backend Debounced Query) */}
          <div className="flex items-center gap-2 bg-[#FAF8F5] px-3 py-1.5 rounded-xl border border-[#EAE5DC]">
            <Search className="w-4 h-4 text-[#8C827A]" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="后端检索：拍摄日期（如 2025、11-04、241104）或描述..."
              className="w-full text-xs bg-transparent outline-none text-[#1A1918] placeholder-[#A8A199]"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="text-xs text-[#A8A199] hover:text-[#5C534B] cursor-pointer"
              >
                清空
              </button>
            )}
          </div>
        </div>

        {/* Photos Grid with Infinite Scroll */}
        <div
          ref={gridContainerRef}
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto p-6 min-h-[300px]"
        >
          {initialLoading ? (
            <div className="h-64 flex items-center justify-center text-xs text-[#7D756E] gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-[#8C7A6B]" />
              正在检索每日主图档案...
            </div>
          ) : photos.length === 0 ? (
            <div className="h-64 flex flex-col items-center justify-center text-xs text-[#7D756E] gap-1">
              <span>未检索到匹配的每日主图照片。</span>
              {(searchTerm || selectedYear !== 'all') && (
                <button
                  onClick={() => {
                    setSearchTerm('')
                    setSelectedYear('all')
                  }}
                  className="text-xs text-[#8C7A6B] underline mt-1 cursor-pointer"
                >
                  清除所有筛选条件
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                {photos.map((p) => {
                  const inCol = existingPhotoIds.has(p.id)
                  const isSelected = selectedIds.has(p.id)
                  return (
                    <div
                      key={p.id}
                      onClick={() => toggleSelect(p.id)}
                      className={`relative rounded-xl overflow-hidden border transition-all ${
                        inCol
                          ? 'opacity-40 cursor-not-allowed border-[#DDD7CD] bg-gray-100'
                          : isSelected
                          ? 'border-[#8C7A6B] ring-3 ring-[#8C7A6B]/30 cursor-pointer shadow-sm'
                          : 'border-[#EAE5DC] hover:border-[#8C7A6B] cursor-pointer hover:shadow-xs'
                      }`}
                    >
                      <div className="aspect-square bg-[#EFECE6] overflow-hidden">
                        <img
                          src={p.thumbnail_url}
                          alt=""
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                      </div>
                      <div className="p-1.5 bg-white text-[10px] font-mono text-center truncate text-[#5C534B]">
                        {p.photo_date}
                      </div>

                      {inCol && (
                        <div className="absolute inset-0 bg-black/40 flex items-center justify-center text-white text-[11px] font-medium">
                          已在合集中
                        </div>
                      )}

                      {isSelected && (
                        <div className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-[#8C7A6B] text-white flex items-center justify-center shadow-sm">
                          <Check className="w-3.5 h-3.5" />
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Infinite Scroll Footer Indicator */}
              <div className="py-4 text-center">
                {loadingMore ? (
                  <div className="flex items-center justify-center gap-2 text-xs text-[#7D756E]">
                    <Loader2 className="w-4 h-4 animate-spin text-[#8C7A6B]" />
                    正在加载更多主图...
                  </div>
                ) : hasMore ? (
                  <button
                    onClick={loadNextPage}
                    className="text-xs text-[#8C7A6B] hover:text-[#5C534B] hover:underline cursor-pointer"
                  >
                    向下滚动自动翻页，或点击此处加载更多（已加载 {photos.length} / 共 {total} 张）
                  </button>
                ) : (
                  <p className="text-xs text-[#A8A199]">
                    已加载全部匹配的每日主图（共 {total} 张）
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 sm:p-6 border-t border-[#EAE5DC] bg-[#FAF8F5] flex justify-between items-center">
          <div className="text-xs text-[#5C534B]">
            已选择 <strong className="text-[#1A1918] font-semibold">{selectedIds.size}</strong> 张照片
            <span className="text-[#8C827A] ml-2 hidden sm:inline">
              (检索共找到 {total} 张，已加载 {photos.length} 张)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-medium text-[#7D756E] hover:bg-[#EFECE6] transition-colors cursor-pointer"
            >
              取消
            </button>
            <button
              onClick={handleConfirm}
              disabled={selectedIds.size === 0 || submitting}
              className="px-5 py-2 rounded-xl text-xs font-medium bg-[#2C2622] text-white hover:bg-[#3D352F] disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
            >
              {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>确认添加 ({selectedIds.size})</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export const CollectionsPage: React.FC<CollectionsPageProps> = ({
  onOpenPhoto,
  isManagementMode: _isManagementMode
}) => {
  const [collections, setCollections] = useState<CollectionItem[]>([])
  const [selectedColId, setSelectedColId] = useState<number | null>(null)
  const [selectedDetail, setSelectedDetail] = useState<CollectionDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)

  // Creation form state
  const [isCreating, setIsCreating] = useState(false)
  const [newColName, setNewColName] = useState('')
  const [newColDesc, setNewColDesc] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const fetchCollections = () => {
    setLoading(true)
    api.getCollections()
      .then((data) => {
        setCollections(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  const fetchSelectedCollection = (id: number) => {
    setLoading(true)
    api.getCollection(id)
      .then((data) => {
        setSelectedDetail(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  useEffect(() => {
    fetchCollections()
  }, [])

  useEffect(() => {
    if (selectedColId) {
      fetchSelectedCollection(selectedColId)
    } else {
      setSelectedDetail(null)
    }
  }, [selectedColId])

  const handleCreateCollection = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newColName.trim()) return
    setSubmitting(true)
    try {
      await api.createCollection({
        name: newColName.trim(),
        description: newColDesc.trim() || undefined
      })
      setIsCreating(false)
      setNewColName('')
      setNewColDesc('')
      fetchCollections()
    } catch (err: any) {
      alert(`创建失败: ${err.message}`)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteCollection = async (id: number) => {
    if (!window.confirm('确定要解散此主题合集吗？合集内的照片档案将完整保留，不受任何影响。')) return
    try {
      await api.deleteCollection(id)
      if (selectedColId === id) setSelectedColId(null)
      fetchCollections()
    } catch (err: any) {
      alert(`删除失败: ${err.message}`)
    }
  }

  const handleRemovePhoto = async (colId: number, photoId: number) => {
    try {
      await api.removePhotoFromCollection(colId, photoId)
      fetchSelectedCollection(colId)
      fetchCollections()
    } catch (err: any) {
      alert(`移除照片失败: ${err.message}`)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 pb-24">
      {/* If Viewing Collection Detail */}
      {selectedColId && selectedDetail ? (
        <div className="space-y-6">
          <button
            onClick={() => setSelectedColId(null)}
            className="text-xs font-medium text-[#7D756E] hover:text-[#1A1918] flex items-center gap-1.5 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> 返回全部合集
          </button>

          <div className="bg-white rounded-3xl border border-[#EAE7E1] p-8 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <span className="text-[11px] uppercase tracking-widest text-[#8C827A] font-medium">
                Collection Gallery
              </span>
              <h1 className="font-serif text-3xl font-medium text-[#1A1918] mt-1">
                {selectedDetail.name}
              </h1>
              {selectedDetail.description && (
                <p className="text-xs text-[#6B635B] mt-1 italic">
                  {selectedDetail.description}
                </p>
              )}
            </div>
            <div className="flex items-center gap-2.5">
              <button
                onClick={() => setShowAddModal(true)}
                className="px-4 py-2 rounded-xl text-xs font-medium bg-[#2C2622] text-white hover:bg-[#3D352F] transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                添加照片
              </button>
              <button
                onClick={() => handleDeleteCollection(selectedDetail.id)}
                className="px-3.5 py-2 rounded-xl text-xs text-red-600 hover:bg-red-50 border border-red-200 transition-colors flex items-center gap-1.5 shrink-0 cursor-pointer"
                title="删除合集（合集内照片仍会保留在每日相册中）"
              >
                <Trash2 className="w-3.5 h-3.5" />
                删除合集
              </button>
            </div>
          </div>

          {selectedDetail.photos.length === 0 ? (
            <div className="bg-white rounded-3xl border border-[#EAE7E1] p-16 text-center text-[#7D756E] text-xs space-y-4">
              <p>该合集暂未添加照片。您可以点击下方按钮挑选照片归入该合集，或在浏览任意照片时直接将其加入合集。</p>
              <button
                onClick={() => setShowAddModal(true)}
                className="px-5 py-2.5 rounded-xl text-xs font-medium bg-[#2C2622] text-white hover:bg-[#3D352F] transition-colors inline-flex items-center gap-1.5 shadow-sm cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                挑选照片加入此合集
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {selectedDetail.photos.map((p) => (
                <div
                  key={p.id}
                  className="group bg-white rounded-2xl border border-[#EAE7E1] p-3 hover:shadow-md transition-all flex flex-col justify-between"
                >
                  <div
                    onClick={() => onOpenPhoto(p.id)}
                    className="aspect-[4/3] rounded-xl bg-[#EFECE6] overflow-hidden mb-3 cursor-pointer"
                  >
                    <img
                      src={p.thumbnail_url}
                      alt=""
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-mono font-medium text-[#1A1918]">{p.photo_date}</span>
                    <button
                      onClick={() => handleRemovePhoto(selectedDetail.id, p.id)}
                      className="text-[11px] text-red-500 hover:text-red-700 cursor-pointer"
                      title="从当前合集移出此照片"
                    >
                      移出合集
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Collections List View */
        <div className="space-y-8">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-[#EAE7E1] pb-6">
            <div>
              <span className="text-[11px] uppercase tracking-widest text-[#8C827A] font-medium flex items-center gap-1.5 mb-1">
                <FolderHeart className="w-3.5 h-3.5 text-[#8C7A6B]" />
                Thematic Collections
              </span>
              <h1 className="font-serif text-3xl font-medium text-[#1A1918]">
                主题合集
              </h1>
              <p className="text-xs text-[#7D756E] mt-1">
                围绕重要时刻、旅行或纪念日等故事组织专属画册。
              </p>
            </div>

            {!isCreating && (
              <button
                onClick={() => setIsCreating(true)}
                className="px-4 py-2.5 rounded-xl bg-[#2C2622] text-white text-xs font-medium hover:bg-[#3D352F] transition-colors flex items-center gap-1.5 self-start sm:self-auto shadow-sm cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                新建合集
              </button>
            )}
          </div>

          {/* Creation Form */}
          {isCreating && (
            <div className="bg-white rounded-3xl border border-[#D6CBBF] p-6 shadow-sm max-w-xl animate-in fade-in">
              <h3 className="font-serif text-lg font-medium text-[#1A1918] mb-4">创建新主题合集</h3>
              <form onSubmit={handleCreateCollection} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-[#7D756E] mb-1">合集名称</label>
                  <input
                    type="text"
                    value={newColName}
                    onChange={(e) => setNewColName(e.target.value)}
                    placeholder="例如: 第一次海边旅行 / 毕业纪念"
                    className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#DDD7CD] rounded-xl text-xs text-[#2C2A29] focus:outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-[#7D756E] mb-1">合集描述 (选填)</label>
                  <textarea
                    value={newColDesc}
                    onChange={(e) => setNewColDesc(e.target.value)}
                    placeholder="简短介绍这组故事背后的回忆..."
                    rows={2}
                    className="w-full p-3 bg-[#FAF8F5] border border-[#DDD7CD] rounded-xl text-xs text-[#2C2A29] focus:outline-none"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsCreating(false)}
                    className="px-4 py-2 rounded-xl border border-[#DDD7CD] text-xs text-[#6B635B] hover:bg-white cursor-pointer"
                  >
                    取消
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-5 py-2 rounded-xl bg-[#2C2622] text-white text-xs font-medium hover:bg-[#3D352F] cursor-pointer"
                  >
                    {submitting ? '创建中...' : '确认创建'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {loading ? (
            <div className="min-h-[40vh] flex items-center justify-center text-sm text-[#7D756E] gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-[#8C7A6B]" />
              正在载入合集...
            </div>
          ) : collections.length === 0 ? (
            <div className="bg-white rounded-3xl border border-[#EAE7E1] p-16 text-center text-[#7D756E] max-w-lg mx-auto space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-[#F7F5F0] border border-[#EAE5DC] flex items-center justify-center mx-auto text-[#8C7A6B]">
                <FolderHeart className="w-6 h-6" />
              </div>
              <div>
                <p className="font-serif text-xl text-[#2C2A29]">暂无主题合集</p>
                <p className="text-xs text-[#8C827A] mt-1.5">
                  随时点击下方或右上角“新建合集”，将相关的照片故事聚合为专属画册。
                </p>
              </div>
              <button
                onClick={() => setIsCreating(true)}
                className="px-5 py-2.5 rounded-xl text-xs font-medium bg-[#2C2622] text-white hover:bg-[#3D352F] transition-colors inline-flex items-center gap-1.5 shadow-sm cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                新建第一个合集
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
              {collections.map((c) => (
                <div
                  key={c.id}
                  onClick={() => setSelectedColId(c.id)}
                  className="group cursor-pointer bg-white rounded-3xl border border-[#EAE7E1] p-4 hover:shadow-lg hover:border-[#D1C7BA] transition-all flex flex-col justify-between"
                >
                  <div className="aspect-[16/10] rounded-2xl bg-[#EFECE6] overflow-hidden mb-4 relative">
                    {c.cover_thumbnail_url ? (
                      <img
                        src={c.cover_thumbnail_url}
                        alt=""
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        loading="lazy"
                      />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center text-[#B0A79E] text-xs gap-1.5">
                        <FolderHeart className="w-6 h-6 text-[#C7BEB5]" />
                        <span>等待添加封面</span>
                      </div>
                    )}
                    <div className="absolute bottom-2 right-2 px-2.5 py-1 rounded-full bg-black/60 text-white text-[10px] font-mono backdrop-blur-xs">
                      {c.photo_count} 张照片
                    </div>
                  </div>

                  <div>
                    <h3 className="font-serif text-lg font-medium text-[#1A1918] group-hover:text-[#52443B] transition-colors">
                      {c.name}
                    </h3>
                    <p className="text-xs text-[#7D756E] mt-1 line-clamp-2">
                      {c.description || '暂无详细描述'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Add Photos Modal */}
      {showAddModal && selectedDetail && (
        <AddPhotosModal
          collectionId={selectedDetail.id}
          collectionName={selectedDetail.name}
          existingPhotoIds={new Set(selectedDetail.photos.map((p) => p.id))}
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            fetchSelectedCollection(selectedDetail.id)
            fetchCollections()
          }}
        />
      )}
    </div>
  )
}
