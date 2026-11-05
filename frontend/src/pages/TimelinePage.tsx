import React, { useEffect, useState } from 'react'
import { Clock, Tag as TagIcon, Sparkles } from 'lucide-react'
import { api } from '../services/api'

interface TimelinePageProps {
  initialTag?: string
  onOpenPhoto: (photoId: number) => void
}

export const TimelinePage: React.FC<TimelinePageProps> = ({ initialTag, onOpenPhoto }) => {
  const [groups, setGroups] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(true)
  const [selectedTag, setSelectedTag] = useState<string | undefined>(initialTag)
  const [tags, setTags] = useState<{ id: number; name: string; count: number }[]>([])

  useEffect(() => {
    setSelectedTag(initialTag)
  }, [initialTag])

  useEffect(() => {
    api.getTags().then(setTags).catch(() => {})
  }, [])

  useEffect(() => {
    setPage(1)
  }, [selectedTag])

  useEffect(() => {
    setLoading(true)
    api.getTimeline(page, 30, selectedTag)
      .then((data) => {
        if (page === 1) {
          setGroups(data.groups)
        } else {
          setGroups((prev) => [...prev, ...data.groups])
        }
        setTotal(data.total)
        setHasMore(data.has_more)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [page, selectedTag])

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 pb-24">
      {/* Header */}
      <div className="text-center max-w-xl mx-auto">
        <span className="text-[11px] uppercase tracking-widest text-[#8C827A] font-medium flex items-center justify-center gap-1.5 mb-2">
          <Clock className="w-3.5 h-3.5 text-[#8C7A6B]" />
          Chronological Stream
        </span>
        <h1 className="font-serif text-3xl sm:text-4xl font-medium text-[#1A1918]">
          时光河流
        </h1>
        <p className="text-xs text-[#7D756E] mt-2">
          按时间倒序顺流而下，{selectedTag ? `当前筛选 #${selectedTag} 标签，共包含 ${total} 个瞬间。` : `共记载了 ${total} 个生活瞬间。`}
        </p>
      </div>

      {/* Tag Filter Pills */}
      {tags.length > 0 && (
        <div className="flex items-center justify-center gap-2 overflow-x-auto pb-2 scrollbar-none flex-wrap">
          <button
            onClick={() => setSelectedTag(undefined)}
            className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all shrink-0 cursor-pointer ${
              selectedTag === undefined
                ? 'bg-[#2C2622] text-white shadow-xs'
                : 'bg-white text-[#6B635B] border border-[#DDD7CD] hover:border-[#8C7A6B] hover:text-[#1A1918]'
            }`}
          >
            全部时间线
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

      {/* Timeline Stream */}
      {groups.length === 0 && !loading ? (
        <div className="text-center py-16 bg-white rounded-3xl border border-[#EAE7E1] text-[#7D756E] text-sm">
          暂无照片记录。
        </div>
      ) : (
        <div className="space-y-12 relative before:absolute before:inset-0 before:left-4 sm:before:left-1/2 before:-translate-x-1/2 before:w-0.5 before:bg-[#EAE5DC] before:z-0">
          {groups.map((group) => (
            <div key={group.period} className="relative z-10 space-y-6">
              {/* Period Header Badge */}
              <div className="flex justify-center">
                <span className="px-4 py-1.5 rounded-full bg-[#2C2622] text-[#F7F5F0] font-mono text-xs font-medium tracking-wider shadow-sm">
                  {group.period}
                </span>
              </div>

              {/* Photos grid in period */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {group.photos.map((photo: any) => (
                  <div
                    key={photo.id}
                    onClick={() => onOpenPhoto(photo.id)}
                    className="group bg-white rounded-2xl border border-[#EAE7E1] p-3 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
                  >
                    <div className="aspect-[4/3] rounded-xl bg-[#EFECE6] overflow-hidden mb-3 relative">
                      <img
                        src={photo.thumbnail_url}
                        alt=""
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        loading="lazy"
                      />
                      {photo.is_highlight === 1 && (
                        <div className="absolute top-2 right-2 p-1 rounded-full bg-black/40 text-amber-300">
                          <Sparkles className="w-3 h-3" />
                        </div>
                      )}
                    </div>
                    <div>
                      <div className="flex justify-between items-center text-xs font-mono font-medium text-[#1A1918] mb-1">
                        <span>{photo.photo_date}</span>
                        {photo.age && (
                          <span className="text-[10px] font-sans text-[#8C827A]">
                            {photo.age.display}
                          </span>
                        )}
                      </div>
                      {photo.description && (
                        <p className="text-[11px] text-[#6B635B] line-clamp-2 italic">
                          {photo.description}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Load More Button */}
      {hasMore && (
        <div className="text-center pt-6">
          <button
            onClick={() => setPage((prev) => prev + 1)}
            disabled={loading}
            className="px-6 py-2.5 rounded-xl border border-[#DDD7CD] bg-white text-xs font-medium text-[#4A3E36] hover:bg-[#FAF8F5] transition-colors"
          >
            {loading ? '正在加载...' : '加载更多时光'}
          </button>
        </div>
      )}
    </div>
  )
}
