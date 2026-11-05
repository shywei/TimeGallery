import React, { useEffect, useState } from 'react'
import {
  X,
  Play,
  Image as ImageIcon,
  Video,
  Calendar,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Edit3,
  Check,
  Star
} from 'lucide-react'
import { api } from '../../services/api'
import type { MomentDetail, MomentMediaItem } from '../../types/moment'

interface MomentDetailModalProps {
  momentDateOrId: string | number
  onClose: () => void
  onOpenPhoto?: (photoId: number) => void
  onUpdated?: () => void
}

export const MomentDetailModal: React.FC<MomentDetailModalProps> = ({
  momentDateOrId,
  onClose,
  onOpenPhoto,
  onUpdated
}) => {
  const [detail, setDetail] = useState<MomentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Edit metadata state
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState('')
  const [editDesc, setEditDesc] = useState('')
  const [savingMeta, setSavingMeta] = useState(false)

  // Active preview state for clicking an item in the gallery
  const [activeMedia, setActiveMedia] = useState<MomentMediaItem | null>(null)
  const [activeMediaIndex, setActiveMediaIndex] = useState<number>(0)

  useEffect(() => {
    setLoading(true)
    api.getMomentDetail(momentDateOrId)
      .then((data) => {
        setDetail(data)
        setEditTitle(data.title || '')
        setEditDesc(data.description || '')
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [momentDateOrId])

  const handleSaveMeta = async () => {
    if (!detail) return
    setSavingMeta(true)
    try {
      const res = await api.updateMoment(detail.moment_date, {
        title: editTitle.trim() || undefined,
        description: editDesc.trim() || undefined
      })
      setDetail({
        ...detail,
        title: res.title,
        description: res.description
      })
      setIsEditing(false)
      if (onUpdated) onUpdated()
    } catch (err: any) {
      alert(`保存时刻信息失败: ${err.message}`)
    } finally {
      setSavingMeta(false)
    }
  }

  const handleSetCover = async (mediaId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!detail) return
    try {
      await api.updateMoment(detail.moment_date, { cover_media_id: mediaId })
      setDetail({
        ...detail,
        cover_media_id: mediaId
      })
      if (onUpdated) onUpdated()
    } catch (err: any) {
      alert(`设置封面失败: ${err.message}`)
    }
  }

  const handleOpenItem = (item: MomentMediaItem, index: number) => {
    setActiveMedia(item)
    setActiveMediaIndex(index)
  }

  const handlePrevItem = () => {
    if (!detail || activeMediaIndex <= 0) return
    const nextIdx = activeMediaIndex - 1
    setActiveMediaIndex(nextIdx)
    setActiveMedia(detail.media_items[nextIdx])
  }

  const handleNextItem = () => {
    if (!detail || activeMediaIndex >= detail.media_items.length - 1) return
    const nextIdx = activeMediaIndex + 1
    setActiveMediaIndex(nextIdx)
    setActiveMedia(detail.media_items[nextIdx])
  }

  // Keyboard navigation for active media
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (activeMedia) {
          setActiveMedia(null)
        } else {
          onClose()
        }
      } else if (activeMedia) {
        if (e.key === 'ArrowLeft') {
          handlePrevItem()
        } else if (e.key === 'ArrowRight') {
          handleNextItem()
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [activeMedia, activeMediaIndex, detail])

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6 animate-in fade-in duration-150">
      <div className="bg-[#FAF9F5] border border-[#E5E0D8] rounded-3xl shadow-2xl max-w-5xl w-full max-h-[90vh] flex flex-col overflow-hidden relative">
        {/* Modal Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-20 p-2 rounded-full bg-white/80 hover:bg-white text-[#5C554E] hover:text-[#1A1918] shadow-sm transition-all cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {loading ? (
          <div className="w-full h-80 flex items-center justify-center text-sm text-[#7D756E] gap-2">
            <Loader2 className="w-5 h-5 animate-spin" />
            正在载入特别时刻画册...
          </div>
        ) : error || !detail ? (
          <div className="w-full p-8 text-center text-sm text-red-600">
            {error || '未找到特别时刻信息'}
          </div>
        ) : (
          <div className="flex flex-col h-full max-h-[90vh] overflow-hidden">
            {/* Header info bar */}
            <div className="p-6 sm:p-8 border-b border-[#EAE5DC] bg-white shrink-0">
              {isEditing ? (
                <div className="space-y-3 animate-in fade-in duration-150">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-amber-900 flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                      编辑特别时刻信息
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          setEditTitle(detail.title || '')
                          setEditDesc(detail.description || '')
                          setIsEditing(false)
                        }}
                        disabled={savingMeta}
                        className="text-xs px-3 py-1.5 rounded-lg border border-[#DDD7CD] hover:bg-[#FAF8F5] text-[#6E665D] cursor-pointer transition-colors"
                      >
                        取消
                      </button>
                      <button
                        type="button"
                        onClick={handleSaveMeta}
                        disabled={savingMeta}
                        className="text-xs px-3.5 py-1.5 rounded-lg bg-[#2C2622] hover:bg-[#3D352F] text-white font-medium flex items-center gap-1.5 cursor-pointer shadow-xs transition-colors"
                      >
                        {savingMeta ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                        <span>保存修改</span>
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-[11px] font-medium text-[#7D756E] mb-1">时刻标题</label>
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      placeholder="例如：抓周日 / 迪士尼乐园游玩 / 2周岁生日聚会"
                      className="w-full px-3 py-2 text-sm border border-[#DDD7CD] rounded-xl focus:outline-none focus:ring-1 focus:ring-[#8C7A6B] bg-[#FAF8F5]"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-medium text-[#7D756E] mb-1">回忆说明 / 故事</label>
                    <textarea
                      value={editDesc}
                      onChange={(e) => setEditDesc(e.target.value)}
                      rows={2}
                      placeholder="记录该时刻的精彩回忆与说明故事..."
                      className="w-full px-3 py-2 text-xs border border-[#DDD7CD] rounded-xl focus:outline-none focus:ring-1 focus:ring-[#8C7A6B] bg-[#FAF8F5] leading-relaxed resize-none"
                    />
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] uppercase tracking-widest text-amber-700 font-semibold px-2.5 py-0.5 rounded-full bg-amber-50 border border-amber-200/80 flex items-center gap-1">
                          <Sparkles className="w-3 h-3 text-amber-500 fill-amber-500" />
                          特别时刻
                        </span>
                        <span className="text-xs text-[#8C827A] flex items-center gap-1 font-mono">
                          <Calendar className="w-3 h-3" />
                          {detail.moment_date}
                        </span>
                        {detail.age_at_moment?.display && (
                          <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#EFECE6] text-[#5C534B]">
                            {detail.age_at_moment.display}
                          </span>
                        )}
                        <button
                          type="button"
                          onClick={() => setIsEditing(true)}
                          className="text-xs text-[#8C7A6B] hover:text-[#1A1918] flex items-center gap-1 px-2 py-0.5 rounded-md hover:bg-[#FAF8F5] transition-colors cursor-pointer ml-1"
                          title="编辑时刻标题与说明"
                        >
                          <Edit3 className="w-3 h-3" />
                          <span>编辑标题与说明</span>
                        </button>
                      </div>
                      <h2 className="font-serif text-2xl sm:text-3xl font-medium text-[#1A1918] mt-1.5">
                        {detail.title}
                      </h2>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-[#6B635B] bg-[#FAF8F5] px-3.5 py-2 rounded-xl border border-[#ECE7DE]">
                      <span className="flex items-center gap-1 font-medium">
                        <ImageIcon className="w-3.5 h-3.5 text-[#8C7A6B]" />
                        {detail.photo_count} 张照片
                      </span>
                      <span className="text-[#DDD7CD]">·</span>
                      <span className="flex items-center gap-1 font-medium">
                        <Video className="w-3.5 h-3.5 text-amber-600" />
                        {detail.video_count} 个视频
                      </span>
                    </div>
                  </div>

                  {detail.description ? (
                    <p className="text-xs text-[#5C554E] mt-3 italic bg-[#FAF9F5] p-3 rounded-xl border border-[#ECE7DE] leading-relaxed">
                      {detail.description}
                    </p>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setIsEditing(true)}
                      className="text-xs text-[#A8A199] hover:text-[#5C554E] mt-3 italic block cursor-pointer"
                    >
                      + 点击添加回忆说明与故事...
                    </button>
                  )}
                </>
              )}
            </div>

            {/* Media Grid Stream */}
            <div className="flex-1 overflow-y-auto p-6 sm:p-8 space-y-6">
              {/* Daily Archive Photo Link (if exists) */}
              {detail.day_photo && onOpenPhoto && (
                <div className="p-3.5 bg-white border border-[#EAE5DC] rounded-2xl flex items-center justify-between gap-4 shadow-2xs">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-[#EAE7E1] overflow-hidden shrink-0">
                      <img
                        src={detail.day_photo.thumbnail_url}
                        alt="今日主图"
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div>
                      <div className="text-xs font-medium text-[#1A1918]">当天主归档照片</div>
                      <div className="text-[11px] text-[#8C827A] truncate max-w-md">
                        {detail.day_photo.description || '这一天已被收录入日常完整档案'}
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      onOpenPhoto(detail.day_photo!.id)
                      onClose()
                    }}
                    className="px-3 py-1.5 rounded-xl text-xs font-medium bg-[#FAF8F5] hover:bg-[#EFECE6] border border-[#DDD7CD] text-[#5C534B] hover:text-[#1A1918] transition-colors cursor-pointer shrink-0"
                  >
                    查看今日主图
                  </button>
                </div>
              )}

              {/* Grid of Moment Photos and Videos */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                {detail.media_items.map((item, idx) => {
                  const isCover = item.id === detail.cover_media_id
                  return (
                    <div
                      key={item.id}
                      onClick={() => handleOpenItem(item, idx)}
                      className={`group relative aspect-square bg-[#EAE7E1] rounded-2xl overflow-hidden cursor-pointer border hover:border-[#8C7A6B] hover:shadow-md transition-all select-none ${
                        isCover ? 'ring-2 ring-amber-400 border-amber-300' : 'border-[#EAE5DC]'
                      }`}
                    >
                      <img
                        src={item.thumbnail_url}
                        alt={item.filename}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        loading="lazy"
                      />

                      {/* Cover Badge or Set Cover Button */}
                      {isCover ? (
                        <div className="absolute top-2 left-2 z-10 px-2 py-0.5 rounded-full bg-amber-500/90 text-white text-[9px] font-semibold flex items-center gap-1 shadow-sm backdrop-blur-xs">
                          <Star className="w-2.5 h-2.5 fill-current" />
                          <span>封面</span>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={(e) => handleSetCover(item.id, e)}
                          className="absolute top-2 left-2 z-10 px-2 py-0.5 rounded-full bg-black/60 hover:bg-black/80 text-white/90 text-[9px] font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 shadow-sm backdrop-blur-xs cursor-pointer"
                          title="设为此画册的封面"
                        >
                          <Star className="w-2.5 h-2.5" />
                          <span>设为封面</span>
                        </button>
                      )}

                      {/* Media Type Badge */}
                      {item.media_type === 'VIDEO' ? (
                        <div className="absolute inset-0 bg-black/25 flex items-center justify-center group-hover:bg-black/40 transition-colors">
                          <div className="w-10 h-10 rounded-full bg-white/90 text-[#1A1918] flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                            <Play className="w-5 h-5 ml-0.5 fill-current" />
                          </div>
                          <span className="absolute bottom-2 right-2 text-[10px] px-1.5 py-0.5 rounded bg-black/70 text-white font-mono flex items-center gap-1">
                            <Video className="w-2.5 h-2.5" /> 视频
                          </span>
                        </div>
                      ) : (
                        <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-2">
                          <span className="text-[10px] text-white/90 truncate font-mono">
                            {item.filename}
                          </span>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Media Fullscreen Preview / Video Player Modal */}
      {activeMedia && (
        <div className="fixed inset-0 z-60 bg-black/90 backdrop-blur-md flex flex-col justify-between p-4 sm:p-6 animate-in fade-in duration-150">
          {/* Top Bar */}
          <div className="flex items-center justify-between text-white/90 max-w-6xl w-full mx-auto shrink-0 pb-2">
            <div className="flex items-center gap-2 text-xs">
              <span className="font-mono">{activeMedia.filename}</span>
              <span className="text-white/40">·</span>
              <span className="text-white/70">
                {activeMediaIndex + 1} / {detail?.media_items.length}
              </span>
            </div>
            <button
              onClick={() => setActiveMedia(null)}
              className="p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Center Stage: Photo or Video Player */}
          <div className="flex-1 flex items-center justify-center relative min-h-0">
            {activeMediaIndex > 0 && (
              <button
                onClick={handlePrevItem}
                className="absolute left-2 sm:left-6 z-10 p-3 rounded-full bg-black/50 hover:bg-black/80 text-white transition-colors cursor-pointer"
              >
                <ChevronLeft className="w-6 h-6" />
              </button>
            )}

            {activeMedia.media_type === 'PHOTO' ? (
              <img
                src={activeMedia.preview_url || activeMedia.original_url}
                alt={activeMedia.filename}
                className="max-h-full max-w-full object-contain rounded-lg select-none"
              />
            ) : (
              <div className="w-full max-w-4xl max-h-full flex items-center justify-center">
                <video
                  src={activeMedia.stream_url || activeMedia.original_url}
                  controls
                  autoPlay
                  className="max-h-[75vh] max-w-full rounded-2xl shadow-2xl bg-black"
                >
                  您的浏览器不支持视频播放。
                </video>
              </div>
            )}

            {detail && activeMediaIndex < detail.media_items.length - 1 && (
              <button
                onClick={handleNextItem}
                className="absolute right-2 sm:right-6 z-10 p-3 rounded-full bg-black/50 hover:bg-black/80 text-white transition-colors cursor-pointer"
              >
                <ChevronRight className="w-6 h-6" />
              </button>
            )}
          </div>

          {/* Bottom Bar: Action link */}
          <div className="max-w-6xl w-full mx-auto pt-2 flex justify-between items-center text-xs text-white/60 shrink-0">
            <span>按 ← / → 切换媒体，Esc 退出</span>
            <a
              href={activeMedia.original_url}
              target="_blank"
              rel="noreferrer"
              className="hover:text-white transition-colors underline cursor-pointer"
            >
              查看原始文件
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
