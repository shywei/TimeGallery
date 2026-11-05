import React, { useEffect, useState } from 'react'
import { Sparkles, Loader2, Tag as TagIcon } from 'lucide-react'
import { api } from '../services/api'
import type { PhotoItem } from '../types/photo'

interface HighlightsPageProps {
  onOpenPhoto: (photoId: number) => void
  initialTag?: string
}

export const HighlightsPage: React.FC<HighlightsPageProps> = ({ onOpenPhoto, initialTag }) => {
  const [highlights, setHighlights] = useState<PhotoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTag, setSelectedTag] = useState<string | undefined>(initialTag)
  const [tags, setTags] = useState<{ id: number; name: string; count: number }[]>([])

  useEffect(() => {
    if (initialTag !== undefined) {
      setSelectedTag(initialTag)
    }
  }, [initialTag])

  useEffect(() => {
    api.getTags().then(setTags).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    api.getHighlights(selectedTag)
      .then((data) => {
        setHighlights(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [selectedTag])

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 pb-24">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-[#EAE7E1] pb-6">
        <div>
          <span className="text-[11px] uppercase tracking-widest text-[#8C827A] font-medium flex items-center gap-1.5 mb-1">
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            Curated Memories
          </span>
          <h1 className="font-serif text-3xl font-medium text-[#1A1918]">
            珍藏精选
          </h1>
          <p className="text-xs text-[#7D756E] mt-1">
            由您人工挑选的闪亮回忆，{selectedTag ? `当前正在筛选 #${selectedTag} 标签下的照片。` : `共收录了 ${highlights.length} 张精彩瞬间。`}
          </p>
        </div>

        {selectedTag && (
          <button
            onClick={() => setSelectedTag(undefined)}
            className="px-3 py-1.5 rounded-lg border border-[#DDD7CD] text-xs text-[#6B635B] hover:bg-white self-start sm:self-auto cursor-pointer"
          >
            显示全部精选
          </button>
        )}
      </div>

      {/* Tag Filter Pills */}
      {tags.length > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none pt-1">
          <button
            onClick={() => setSelectedTag(undefined)}
            className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all shrink-0 cursor-pointer ${
              selectedTag === undefined
                ? 'bg-[#2C2622] text-white shadow-xs'
                : 'bg-white text-[#6B635B] border border-[#DDD7CD] hover:border-[#8C7A6B] hover:text-[#1A1918]'
            }`}
          >
            全部精选
          </button>
          {tags.map((t) => (
            <button
              key={t.id}
              onClick={() => setSelectedTag(selectedTag === t.name ? undefined : t.name)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all shrink-0 cursor-pointer flex items-center gap-1.5 ${
                selectedTag === t.name
                  ? 'bg-[#8C7A6B] text-white shadow-xs ring-2 ring-[#8C7A6B]/20'
                  : 'bg-white text-[#6B635B] border border-[#DDD7CD] hover:border-[#8C7A6B] hover:text-[#1A1918]'
              }`}
            >
              <TagIcon className="w-3 h-3 opacity-70" />
              <span>#{t.name}</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${selectedTag === t.name ? 'bg-white/20 text-white' : 'bg-[#EFECE6] text-[#7D756E]'}`}>
                {t.count}
              </span>
            </button>
          ))}
        </div>
      )}

      {loading ? (
        <div className="min-h-[40vh] flex items-center justify-center text-sm text-[#7D756E] gap-2">
          <Loader2 className="w-5 h-5 animate-spin text-[#8C7A6B]" />
          正在整理精选集...
        </div>
      ) : highlights.length === 0 ? (
        <div className="bg-white rounded-3xl border border-[#EAE7E1] p-16 text-center text-[#7D756E] max-w-lg mx-auto space-y-2">
          <p className="font-serif text-xl text-[#2C2A29]">暂无精选照片</p>
          <p className="text-xs">
            在浏览照片详情时，点击右上角或进入“管理模式”将照片标记为精选，即可沉淀在此。
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {highlights.map((photo) => (
            <div
              key={photo.id}
              onClick={() => onOpenPhoto(photo.id)}
              className="group cursor-pointer bg-white rounded-2xl border border-[#EAE7E1] p-3 hover:shadow-lg transition-all flex flex-col justify-between"
            >
              <div className="aspect-[4/3] rounded-xl bg-[#EFECE6] overflow-hidden mb-3 relative">
                <img
                  src={photo.thumbnail_url}
                  alt={photo.photo_date}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  loading="lazy"
                />
                <div className="absolute top-2 right-2 p-1.5 rounded-full bg-black/40 text-amber-300 backdrop-blur-xs">
                  <Sparkles className="w-3.5 h-3.5" />
                </div>
              </div>
              <div>
                <div className="text-xs font-mono font-medium text-[#1A1918] mb-1">
                  {photo.photo_date}
                </div>
                {photo.description && (
                  <p className="text-xs text-[#59524B] line-clamp-2 italic mb-2">
                    {photo.description}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
