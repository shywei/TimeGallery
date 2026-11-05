import React, { useEffect, useState } from 'react'
import { X, Maximize2, Sparkles, Tag as TagIcon, Check, Loader2, Calendar, ChevronLeft, ChevronRight, FolderHeart, Plus } from 'lucide-react'
import { api } from '../../services/api'
import type { PhotoDetail } from '../../types/photo'
import type { CollectionItem } from '../../types/collection'
import { ImmersiveViewer } from './ImmersiveViewer'
import { MomentDetailModal } from '../moment/MomentDetailModal'

interface PhotoDetailModalProps {
  photoId: number
  isManagementMode: boolean
  onClose: () => void
  onUpdated?: () => void
  onSelectPhoto?: (photoId: number) => void
  onSelectTag?: (tagName: string) => void
}

export const PhotoDetailModal: React.FC<PhotoDetailModalProps> = ({
  photoId,
  isManagementMode: _isManagementMode,
  onClose,
  onUpdated,
  onSelectPhoto,
  onSelectTag
}) => {
  const [activePhotoId, setActivePhotoId] = useState<number>(photoId)
  const [detail, setDetail] = useState<PhotoDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isImmersive, setIsImmersive] = useState(false)

  // Description state
  const [description, setDescription] = useState('')
  const [savingDesc, setSavingDesc] = useState(false)
  const [togglingHighlight, setTogglingHighlight] = useState(false)

  // Tags state
  const [allTags, setAllTags] = useState<{ id: number; name: string; count: number }[]>([])
  const [showTagPicker, setShowTagPicker] = useState(false)
  const [newTagInput, setNewTagInput] = useState('')

  // Collections state
  const [allCollections, setAllCollections] = useState<CollectionItem[]>([])
  const [showColPicker, setShowColPicker] = useState(false)
  const [togglingColId, setTogglingColId] = useState<number | null>(null)
  const [showMomentModal, setShowMomentModal] = useState(false)

  const fetchCollections = () => {
    api.getCollections()
      .then((data) => setAllCollections(data))
      .catch(() => {})
  }

  const fetchTags = () => {
    api.getTags()
      .then((data) => setAllTags(data))
      .catch(() => {})
  }

  useEffect(() => {
    fetchCollections()
    fetchTags()
  }, [])

  const handleToggleCollection = async (colId: number, isCurrentlyIn: boolean) => {
    if (togglingColId) return
    setTogglingColId(colId)
    try {
      if (isCurrentlyIn) {
        await api.removePhotoFromCollection(colId, activePhotoId)
      } else {
        await api.addPhotosToCollection(colId, [activePhotoId])
      }
      fetchDetail(activePhotoId)
      fetchCollections()
      if (onUpdated) onUpdated()
    } catch (err: any) {
      alert(`合集操作失败: ${err.message}`)
    } finally {
      setTogglingColId(null)
    }
  }

  useEffect(() => {
    setActivePhotoId(photoId)
  }, [photoId])

  const fetchDetail = (targetId: number) => {
    setLoading(true)
    api.getPhotoDetail(targetId)
      .then((data) => {
        setDetail(data)
        setDescription(data.description || '')
        setShowTagPicker(false)
        setNewTagInput('')
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }

  useEffect(() => {
    fetchDetail(activePhotoId)
  }, [activePhotoId])

  const handleSwitchPhoto = (newId: number) => {
    setActivePhotoId(newId)
    if (onSelectPhoto) onSelectPhoto(newId)
  }

  const handleToggleHighlight = async () => {
    if (!detail || togglingHighlight) return
    setTogglingHighlight(true)
    const nextHighlight = detail.is_highlight === 1 ? 0 : 1
    try {
      if (nextHighlight === 1) {
        await api.setHighlight(activePhotoId)
      } else {
        await api.removeHighlight(activePhotoId)
      }
      setDetail((prev) => (prev ? { ...prev, is_highlight: nextHighlight } : null))
      if (onUpdated) onUpdated()
    } catch (err: any) {
      alert(`设置精选失败: ${err.message}`)
    } finally {
      setTogglingHighlight(false)
    }
  }

  const handleSaveDescription = async () => {
    if (!detail || savingDesc) return
    setSavingDesc(true)
    try {
      const updated = await api.updatePhotoMetadata(activePhotoId, {
        description: description.trim() || undefined
      })
      setDetail(updated)
      setDescription(updated.description || '')
      if (onUpdated) onUpdated()
    } catch (err: any) {
      alert(`保存故事失败: ${err.message}`)
    } finally {
      setSavingDesc(false)
    }
  }

  const handleRemoveTag = async (tagNameToRemove: string) => {
    if (!detail) return
    const nextTags = detail.tags
      .filter((t) => t.name !== tagNameToRemove)
      .map((t) => t.name)
    try {
      const updated = await api.updatePhotoMetadata(activePhotoId, { tags: nextTags })
      setDetail(updated)
      fetchTags()
      if (onUpdated) onUpdated()
    } catch (err: any) {
      alert(`移除标签失败: ${err.message}`)
    }
  }

  const handleAddTag = async (tagNameToAdd: string) => {
    if (!detail) return
    const cleanName = tagNameToAdd.trim()
    if (!cleanName) return
    if (detail.tags.some((t) => t.name === cleanName)) {
      setNewTagInput('')
      setShowTagPicker(false)
      return
    }
    const nextTags = [...detail.tags.map((t) => t.name), cleanName]
    try {
      const updated = await api.updatePhotoMetadata(activePhotoId, { tags: nextTags })
      setDetail(updated)
      setNewTagInput('')
      setShowTagPicker(false)
      fetchTags()
      if (onUpdated) onUpdated()
    } catch (err: any) {
      alert(`添加标签失败: ${err.message}`)
    }
  }

  useEffect(() => {
    if (isImmersive) return
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) {
        return
      }
      if (e.key === 'Escape') {
        onClose()
      } else if (e.key === 'ArrowLeft' && detail?.prev_photo_id) {
        handleSwitchPhoto(detail.prev_photo_id)
      } else if (e.key === 'ArrowRight' && detail?.next_photo_id) {
        handleSwitchPhoto(detail.next_photo_id)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isImmersive, detail, onClose])

  const isDescDirty = detail ? description.trim() !== (detail.description || '').trim() : false
  const availableTagsToAdd = detail ? allTags.filter((t) => !detail.tags.some((dt) => dt.name === t.name)) : []

  if (isImmersive && detail) {
    return (
      <ImmersiveViewer
        photoUrl={detail.original_url || detail.preview_url}
        photoDate={detail.photo_date}
        ageDisplay={detail.age_at_photo?.display}
        isHighlight={detail.is_highlight === 1}
        onToggleHighlight={handleToggleHighlight}
        onClose={() => setIsImmersive(false)}
        onPrev={detail.prev_photo_id ? () => handleSwitchPhoto(detail.prev_photo_id!) : undefined}
        onNext={detail.next_photo_id ? () => handleSwitchPhoto(detail.next_photo_id!) : undefined}
      />
    )
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-150">
      <div className="bg-[#FAF9F5] border border-[#E5E0D8] rounded-3xl shadow-2xl max-w-5xl w-full max-h-[90vh] flex flex-col md:flex-row overflow-hidden relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-20 p-2 rounded-full bg-white/80 hover:bg-white text-[#5C554E] hover:text-[#1A1918] shadow-sm transition-all"
        >
          <X className="w-5 h-5" />
        </button>

        {loading ? (
          <div className="w-full h-80 flex items-center justify-center text-sm text-[#7D756E] gap-2">
            <Loader2 className="w-5 h-5 animate-spin" />
            正在加载档案详情...
          </div>
        ) : error || !detail ? (
          <div className="w-full p-8 text-center text-sm text-red-600">
            {error || '未找到照片信息'}
          </div>
        ) : (
          <>
            {/* Left: Image Preview Container */}
            <div className="md:w-3/5 bg-[#171615] flex items-center justify-center relative p-2 min-h-[360px] md:min-h-[500px]">
              {detail.prev_photo_id && (
                <button
                  onClick={() => handleSwitchPhoto(detail.prev_photo_id!)}
                  className="absolute left-3 z-10 p-2.5 rounded-full bg-black/40 hover:bg-black/70 text-white/80 hover:text-white transition-all backdrop-blur-sm shadow-md"
                  title={`前一日照片 (${detail.prev_date || ''})`}
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
              )}
              <img
                src={detail.preview_url}
                alt={detail.photo_date}
                className="max-h-[75vh] max-w-full object-contain rounded-lg select-none"
              />
              {detail.next_photo_id && (
                <button
                  onClick={() => handleSwitchPhoto(detail.next_photo_id!)}
                  className="absolute right-3 z-10 p-2.5 rounded-full bg-black/40 hover:bg-black/70 text-white/80 hover:text-white transition-all backdrop-blur-sm shadow-md"
                  title={`后一日照片 (${detail.next_date || ''})`}
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              )}
              <button
                onClick={() => setIsImmersive(true)}
                className="absolute bottom-4 right-4 p-2.5 rounded-full bg-black/60 hover:bg-black/80 text-white/90 hover:text-white transition-all backdrop-blur-md shadow-lg flex items-center gap-1.5 text-xs font-medium"
                title="进入全屏沉浸浏览"
              >
                <Maximize2 className="w-4 h-4" />
                <span>全屏沉浸</span>
              </button>
            </div>

            {/* Right: Metadata Panel */}
            <div className="md:w-2/5 p-6 sm:p-8 flex flex-col justify-between overflow-y-auto max-h-[85vh]">
              <div>
                <div className="flex items-center justify-between border-b border-[#EAE5DC] pb-4 mb-4">
                  <div>
                    <span className="text-xs uppercase tracking-widest text-[#8C827A] font-medium flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      记录日期
                    </span>
                    <h3 className="font-serif text-2xl font-medium text-[#1A1918] mt-0.5">
                      {detail.photo_date}
                    </h3>
                  </div>
                  {detail.age_at_photo && (
                    <span className="text-xs px-3 py-1 rounded-full bg-[#EFECE6] text-[#5C534B] font-medium">
                      {detail.age_at_photo.display}
                    </span>
                  )}
                </div>

                <div className="space-y-4">
                    <div>
                      <button
                        type="button"
                        disabled={togglingHighlight}
                        onClick={handleToggleHighlight}
                        className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium transition-all cursor-pointer ${
                          detail.is_highlight === 1
                            ? 'bg-amber-50 text-amber-900 border border-amber-300 hover:bg-amber-100 shadow-2xs'
                            : 'bg-white text-[#6E665D] border border-[#DDD7CD] hover:border-[#8C7A6B] hover:text-[#1A1918] hover:bg-[#FAF8F5]'
                        }`}
                        title={detail.is_highlight === 1 ? '点击取消精选' : '点击将此照片设为精选瞬间'}
                      >
                        {togglingHighlight ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin text-[#8C7A6B]" />
                        ) : (
                          <Sparkles className={`w-3.5 h-3.5 ${detail.is_highlight === 1 ? 'text-amber-500 fill-amber-500' : 'text-[#8C7A6B]'}`} />
                        )}
                        <span>{detail.is_highlight === 1 ? '已设为精选 · 点击取消' : '标为精选照片'}</span>
                      </button>
                    </div>

                    {/* Photo Story / 心语 */}
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <h4 className="text-xs font-medium uppercase tracking-wider text-[#8C827A]">
                          照片心语与故事
                        </h4>
                        {isDescDirty && (
                          <div className="flex items-center gap-1.5 animate-in fade-in duration-150">
                            <button
                              type="button"
                              onClick={() => setDescription(detail.description || '')}
                              disabled={savingDesc}
                              className="text-[11px] text-[#8C827A] hover:text-[#1A1918] cursor-pointer px-2 py-0.5 rounded transition-colors"
                            >
                              还原
                            </button>
                            <button
                              type="button"
                              onClick={handleSaveDescription}
                              disabled={savingDesc}
                              className="text-[11px] bg-[#2C2622] hover:bg-[#3D352F] text-white px-2.5 py-1 rounded-md font-medium cursor-pointer shadow-xs flex items-center gap-1 transition-colors"
                              title="保存修改 (或按 Ctrl+Enter)"
                            >
                              {savingDesc ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                              <span>更新故事</span>
                            </button>
                          </div>
                        )}
                      </div>
                      <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        onKeyDown={(e) => {
                          if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                            e.preventDefault()
                            handleSaveDescription()
                          }
                        }}
                        rows={3}
                        className="w-full p-3 bg-white border border-[#ECE7DE] focus:border-[#8C7A6B] rounded-xl text-xs text-[#2C2A29] leading-relaxed resize-none focus:outline-none focus:ring-1 focus:ring-[#8C7A6B]/30 placeholder:text-[#BBB4A9] transition-all shadow-2xs"
                        placeholder="记录这一天的时光故事... (修改后点击“更新故事”或按 Ctrl+Enter 保存)"
                      />
                    </div>

                    {/* Tags / 标签 (类似合集那样，可以移除添加) */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-xs font-medium uppercase tracking-wider text-[#8C827A] flex items-center gap-1">
                          <TagIcon className="w-3.5 h-3.5" /> 标签分类
                        </h4>
                        <button
                          type="button"
                          onClick={() => setShowTagPicker(!showTagPicker)}
                          className="text-xs text-[#8C7A6B] hover:text-[#1A1918] font-medium flex items-center gap-0.5 cursor-pointer px-2 py-0.5 rounded-md hover:bg-[#EFECE6] transition-colors"
                        >
                          <Plus className="w-3 h-3" />
                          <span>{showTagPicker ? '收起' : '添加标签'}</span>
                        </button>
                      </div>

                      <div className="flex flex-wrap gap-1.5 items-center">
                        {detail.tags.length === 0 && !showTagPicker && (
                          <p className="text-xs text-[#A8A199] italic">暂无标签</p>
                        )}
                        {detail.tags.map((t) => (
                          <span
                            key={t.id}
                            className="text-xs px-2.5 py-1 rounded-lg bg-[#EFECE6] text-[#5C534B] flex items-center gap-1.5 shadow-2xs"
                          >
                            <button
                              type="button"
                              onClick={() => {
                                if (onSelectTag) {
                                  onSelectTag(t.name)
                                  onClose()
                                }
                              }}
                              className="hover:text-[#1A1918] hover:underline cursor-pointer"
                              title={`筛选 #${t.name} 的照片`}
                            >
                              #{t.name}
                            </button>
                            <button
                              type="button"
                              onClick={() => handleRemoveTag(t.name)}
                              className="text-[#A8A199] hover:text-red-500 transition-colors ml-0.5 cursor-pointer"
                              title={`移除标签 #${t.name}`}
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </span>
                        ))}
                      </div>

                      {showTagPicker && (
                        <div className="p-3 bg-white rounded-xl border border-[#ECE7DE] shadow-xs space-y-2 mt-2 animate-in fade-in duration-150">
                          <div className="text-[11px] font-medium text-[#7D756E]">输入新标签或选择已有标签：</div>
                          <div className="flex gap-2">
                            <input
                              type="text"
                              value={newTagInput}
                              onChange={(e) => setNewTagInput(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  e.preventDefault()
                                  handleAddTag(newTagInput)
                                }
                              }}
                              placeholder="标签名，按回车添加"
                              className="flex-1 px-2.5 py-1 text-xs border border-[#DDD7CD] rounded-lg focus:outline-none focus:ring-1 focus:ring-[#8C7A6B]"
                            />
                            <button
                              type="button"
                              onClick={() => handleAddTag(newTagInput)}
                              className="px-3 py-1 bg-[#2C2622] text-white text-xs rounded-lg font-medium hover:bg-[#3D352F] cursor-pointer"
                            >
                              添加
                            </button>
                          </div>
                          {availableTagsToAdd.length > 0 && (
                            <div className="pt-1.5 border-t border-[#F0ECE6]">
                              <div className="text-[10px] text-[#A8A199] mb-1">推荐/已有标签：</div>
                              <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
                                {availableTagsToAdd.map((tag) => (
                                  <button
                                    key={tag.id}
                                    type="button"
                                    onClick={() => handleAddTag(tag.name)}
                                    className="text-[11px] px-2 py-0.5 rounded-md bg-[#FAF8F5] hover:bg-[#EFECE6] text-[#6E665D] hover:text-[#1A1918] border border-[#EAE5DC] cursor-pointer transition-colors"
                                  >
                                    +{tag.name}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Special Moment / 特别时刻入口 */}
                    {detail.has_moment && detail.moment && (
                      <div className="p-3.5 bg-gradient-to-r from-amber-50/80 to-[#FAF8F5] border border-amber-200/80 rounded-2xl shadow-2xs space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-semibold text-amber-900 flex items-center gap-1.5">
                            <Sparkles className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                            今日特别时刻
                          </span>
                          <span className="text-[10px] text-amber-800/80 font-mono">
                            {detail.moment.photo_count} 图 · {detail.moment.video_count} 视频
                          </span>
                        </div>
                        <p className="text-xs text-[#5C534B]">
                          这一天留下了珍贵的专属画册（{detail.moment.title}）。
                        </p>
                        <button
                          type="button"
                          onClick={() => setShowMomentModal(true)}
                          className="w-full py-2 px-3 rounded-xl bg-[#2C2622] hover:bg-[#3D352F] text-white text-xs font-medium transition-colors shadow-xs flex items-center justify-center gap-1.5 cursor-pointer"
                        >
                          <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                          <span>查看特别时刻画册 ({detail.moment.photo_count + detail.moment.video_count})</span>
                        </button>
                      </div>
                    )}

                    {/* Theme Collections / 主题合集 */}
                    <div className="pt-1">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-xs font-medium uppercase tracking-wider text-[#8C827A] flex items-center gap-1">
                          <FolderHeart className="w-3.5 h-3.5" /> 所属主题合集
                        </h4>
                        <button
                          type="button"
                          onClick={() => setShowColPicker(!showColPicker)}
                          className="text-xs text-[#8C7A6B] hover:text-[#1A1918] font-medium flex items-center gap-0.5 cursor-pointer px-2 py-0.5 rounded-md hover:bg-[#EFECE6] transition-colors"
                        >
                          <Plus className="w-3 h-3" />
                          <span>{showColPicker ? '收起' : '管理合集'}</span>
                        </button>
                      </div>

                      {detail.collections.length === 0 && !showColPicker && (
                        <p className="text-xs text-[#A8A199] italic">暂未归入任何主题合集</p>
                      )}

                      {detail.collections.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mb-2">
                          {detail.collections.map((c) => (
                            <span
                              key={c.id}
                              className="text-xs px-2.5 py-1 rounded-lg bg-[#F5F2EB] text-[#5C534B] border border-[#E5DFD5] flex items-center gap-1.5 shadow-2xs"
                            >
                              <FolderHeart className="w-3 h-3 text-[#8C7A6B]" />
                              <span>{c.name}</span>
                              <button
                                type="button"
                                onClick={() => handleToggleCollection(c.id, true)}
                                className="text-[#A8A199] hover:text-red-500 transition-colors ml-0.5 cursor-pointer"
                                title="从该合集中移出"
                              >
                                <X className="w-3 h-3" />
                              </button>
                            </span>
                          ))}
                        </div>
                      )}

                      {showColPicker && (
                        <div className="p-3 bg-white rounded-xl border border-[#ECE7DE] shadow-xs space-y-2 mt-1 animate-in fade-in duration-150">
                          <div className="text-[11px] font-medium text-[#7D756E]">勾选以归入或移出合集：</div>
                          {allCollections.length === 0 ? (
                            <div className="text-xs text-[#A8A199] py-1">暂无合集，请在“主题合集”页面新建。</div>
                          ) : (
                            <div className="space-y-1.5 max-h-36 overflow-y-auto">
                              {allCollections.map((col) => {
                                const inCol = detail.collections.some((c) => c.id === col.id)
                                return (
                                  <label
                                    key={col.id}
                                    className="flex items-center gap-2 text-xs text-[#3D3833] cursor-pointer hover:bg-[#FAF8F5] p-1.5 rounded-lg transition-colors"
                                  >
                                    <input
                                      type="checkbox"
                                      checked={inCol}
                                      onChange={() => handleToggleCollection(col.id, inCol)}
                                      disabled={togglingColId === col.id}
                                      className="rounded border-[#C4BEB5] text-[#8C7A6B] focus:ring-[#8C7A6B] cursor-pointer"
                                    />
                                    <span className="font-medium flex-1">{col.name}</span>
                                    {inCol && <span className="text-[10px] text-[#8C7A6B] font-medium">已加入</span>}
                                  </label>
                                )
                              })}
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* On This Day / 历史上的今天小图入口 */}
                    {detail.on_this_day_photos && detail.on_this_day_photos.length > 0 && (
                      <div className="pt-4 border-t border-[#EAE5DC] space-y-2.5">
                        <div className="flex items-center justify-between">
                          <h4 className="text-xs font-medium uppercase tracking-wider text-[#8C7A6B] flex items-center gap-1.5">
                            <Sparkles className="w-3.5 h-3.5 text-[#8C7A6B]" />
                            历史上的今天
                          </h4>
                          <span className="text-[10px] text-[#A8A199] font-mono">
                            共 {detail.on_this_day_photos.length} 张同日照片
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-2.5">
                          {detail.on_this_day_photos.map((item) => (
                            <button
                              key={item.id}
                              type="button"
                              onClick={() => handleSwitchPhoto(item.id)}
                              className="group text-left p-2 rounded-2xl bg-white border border-[#EAE5DC] hover:border-[#8C7A6B] hover:shadow-xs transition-all flex items-center gap-2.5 cursor-pointer"
                              title={`点击跳转查看 ${item.photo_date}（${item.title}）`}
                            >
                              <div className="w-12 h-12 rounded-xl bg-[#EAE7E1] overflow-hidden shrink-0">
                                <img
                                  src={item.thumbnail_url}
                                  alt={item.photo_date}
                                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                                />
                              </div>
                              <div className="min-w-0 flex-1">
                                <div className="text-xs font-medium text-[#1A1918] truncate group-hover:text-[#8C7A6B]">
                                  {item.title}
                                </div>
                                <div className="text-[10px] text-[#8C827A] font-mono">
                                  {item.photo_date}
                                </div>
                                {item.age_display && (
                                  <div className="text-[10px] text-[#A8A199] truncate">
                                    {item.age_display}
                                  </div>
                                )}
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Technical details */}
                    <div className="pt-4 border-t border-[#EAE5DC] text-[11px] text-[#8C827A] space-y-1">
                      <div>原始文件: {detail.filename}</div>
                      <div>分辨率: {detail.width} × {detail.height} 像素</div>
                    </div>
                  </div>
                </div>
              </div>
          </>
        )}
      </div>

      {/* Special Moment Modal */}
      {showMomentModal && detail && (
        <MomentDetailModal
          momentDateOrId={detail.photo_date}
          onClose={() => setShowMomentModal(false)}
          onOpenPhoto={onSelectPhoto}
        />
      )}
    </div>
  )
}
