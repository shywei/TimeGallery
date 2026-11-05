import React, { useEffect, useState, useRef } from 'react'
import { Calendar, Clock, Sparkles, FolderHeart, ArrowRight, Pause, Play, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'
import { api } from '../services/api'
import type { NavTab } from '../components/layout/Navbar'

interface HomePageProps {
  onNavigate: (tab: NavTab, params?: any) => void
  onOpenPhoto: (photoId: number) => void
}

export const HomePage: React.FC<HomePageProps> = ({ onNavigate, onOpenPhoto }) => {
  const [overview, setOverview] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [currentMemoryIdx, setCurrentMemoryIdx] = useState(0)
  const [isPaused, setIsPaused] = useState(false)
  const timerRef = useRef<any>(null)

  useEffect(() => {
    setLoading(true)
    api.getHomeOverview()
      .then((data) => {
        setOverview(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error('Failed to load home overview:', err)
        setLoading(false)
      })
  }, [])

  const memories = overview?.memories || []

  // Auto carousel effect
  useEffect(() => {
    if (isPaused || memories.length <= 1) return

    timerRef.current = setInterval(() => {
      setCurrentMemoryIdx((prev) => (prev + 1) % memories.length)
    }, 8000)

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [isPaused, memories.length])

  const handleManualSwitch = (idx: number) => {
    setCurrentMemoryIdx(idx)
    if (timerRef.current) clearInterval(timerRef.current)
  }

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center text-sm text-[#7D756E] gap-3">
        <Loader2 className="w-6 h-6 animate-spin text-[#8C7A6B]" />
        正在开启时光画册...
      </div>
    )
  }

  const currentMemory = memories[currentMemoryIdx]

  return (
    <div className="space-y-16 pb-24">
      {/* 1. Today in Her Life: Hero Memory Section */}
      <section
        className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4"
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
      >
        <div className="flex justify-between items-end mb-4">
          <div>
            <span className="text-[11px] uppercase tracking-widest text-[#8C827A] font-medium">
              Daily Memory
            </span>
            <h2 className="font-serif text-3xl font-medium text-[#1A1918] tracking-tight mt-0.5">
              岁月回响 · 历史上的今天
            </h2>
          </div>
          {memories.length > 1 && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsPaused(!isPaused)}
                className="p-1.5 rounded-full hover:bg-[#EFECE6] text-[#7D756E] transition-colors"
                title={isPaused ? '恢复自动轮播' : '暂停轮播'}
              >
                {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
              </button>
              <button
                onClick={() => handleManualSwitch((currentMemoryIdx - 1 + memories.length) % memories.length)}
                className="p-1.5 rounded-full hover:bg-[#EFECE6] text-[#7D756E] transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => handleManualSwitch((currentMemoryIdx + 1) % memories.length)}
                className="p-1.5 rounded-full hover:bg-[#EFECE6] text-[#7D756E] transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {currentMemory ? (
          <div className="bg-white rounded-3xl border border-[#EAE7E1] shadow-sm overflow-hidden flex flex-col lg:flex-row">
            {/* Main Visual Image */}
            <div
              onClick={() => onOpenPhoto(currentMemory.photo.id)}
              className="lg:w-7/12 bg-[#171615] relative group cursor-pointer overflow-hidden flex items-center justify-center min-h-[380px] sm:min-h-[460px] lg:min-h-[520px]"
            >
              <img
                src={currentMemory.photo.preview_url || currentMemory.photo.thumbnail_url}
                alt={currentMemory.photo.photo_date}
                className="max-h-[520px] w-full object-contain transition-transform duration-700 group-hover:scale-[1.02]"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-6">
                <span className="text-white text-xs tracking-wider flex items-center gap-1">
                  点击查看大图与故事 <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>

            {/* Sidebar Details & Memory Theme Switcher */}
            <div className="lg:w-5/12 p-8 sm:p-10 flex flex-col justify-between bg-[#FCFBF8]">
              <div>
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#EFEBE4] text-[#63574D] text-xs font-medium tracking-wide mb-4">
                  <Sparkles className="w-3.5 h-3.5 text-[#8C7A6B]" />
                  {currentMemory.title}
                </div>

                <div className="space-y-3">
                  <h3 className="font-serif text-3xl sm:text-4xl font-medium text-[#1A1918]">
                    {currentMemory.photo.photo_date}
                  </h3>
                  {currentMemory.photo.age?.display && (
                    <p className="text-sm font-medium text-[#7D756E]">
                      {currentMemory.photo.age.display}
                    </p>
                  )}
                  <p className="text-sm text-[#59524B] leading-relaxed pt-2">
                    {currentMemory.photo.description || '每一天的平凡瞬间，都是岁月长卷上不可复制的珍贵印记。'}
                  </p>
                </div>
              </div>

              {/* Memory Candidate Thumbnails */}
              {memories.length > 1 && (
                <div className="pt-8 border-t border-[#EAE5DC] mt-8">
                  <span className="text-xs uppercase tracking-wider text-[#8C827A] font-medium block mb-3">
                    历史上的今天与回忆
                  </span>
                  <div className="grid grid-cols-3 gap-3">
                    {memories.map((m: any, idx: number) => (
                      <button
                        key={idx}
                        onClick={() => handleManualSwitch(idx)}
                        className={`text-left rounded-xl p-1.5 border transition-all ${
                          idx === currentMemoryIdx
                            ? 'border-[#8C7A6B] bg-white ring-2 ring-[#8C7A6B]/20 shadow-xs'
                            : 'border-[#E8E4DC] hover:border-[#C4B9AD] opacity-75 hover:opacity-100'
                        }`}
                      >
                        <div className="aspect-square rounded-lg bg-[#EAE7E1] overflow-hidden mb-1.5">
                          <img
                            src={m.photo.thumbnail_url}
                            alt=""
                            className="w-full h-full object-cover"
                          />
                        </div>
                        <div className="text-[11px] font-medium text-[#1A1918] truncate">
                          {m.title}
                        </div>
                        <div className="text-[10px] text-[#8C827A] truncate font-mono">
                          {m.photo.photo_date}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-3xl border border-[#EAE7E1] p-12 text-center text-[#7D756E]">
            <p className="font-serif text-xl text-[#2C2A29] mb-2">时光画卷刚刚展开</p>
            <p className="text-xs max-w-sm mx-auto">
              随着您将更多每日生活照片放入目录并扫描，这里将自动浮现出历史上的今天、去年此时等生动回忆。
            </p>
          </div>
        )}
      </section>

      {/* 2. Growth Statistics */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white border border-[#EAE7E1] rounded-2xl p-6 sm:p-8 grid grid-cols-1 sm:grid-cols-3 gap-6 text-center divide-y sm:divide-y-0 sm:divide-x divide-[#ECE7DE]">
          <div className="pt-2 sm:pt-0">
            <span className="text-xs uppercase tracking-widest text-[#8C827A] font-medium">
              有效归档照片
            </span>
            <div className="font-serif text-3xl font-medium text-[#1A1918] mt-1">
              {overview?.total_photos || 0} <span className="text-sm font-sans font-normal text-[#7D756E]">张</span>
            </div>
          </div>
          <div className="pt-4 sm:pt-0">
            <span className="text-xs uppercase tracking-widest text-[#8C827A] font-medium">
              已记录自然日
            </span>
            <div className="font-serif text-3xl font-medium text-[#1A1918] mt-1">
              {overview?.days_recorded || 0} <span className="text-sm font-sans font-normal text-[#7D756E]">天</span>
            </div>
          </div>
          <div className="pt-4 sm:pt-0">
            <span className="text-xs uppercase tracking-widest text-[#8C827A] font-medium">
              时光里程碑
            </span>
            <div className="font-serif text-2xl font-medium text-[#1A1918] mt-1.5">
              {overview?.current_age?.display || '岁月漫漫 · 静好如初'}
            </div>
          </div>
        </div>
      </section>

      {/* 3. Recent Moments */}
      {overview?.recent_moments?.length > 0 && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-end mb-6">
            <div>
              <span className="text-[11px] uppercase tracking-widest text-[#8C827A] font-medium">
                Recent Moments
              </span>
              <h2 className="font-serif text-2xl font-medium text-[#1A1918]">
                近期瞬间
              </h2>
            </div>
            <button
              onClick={() => onNavigate('calendar')}
              className="text-xs font-medium text-[#6B5E54] hover:text-[#1A1918] flex items-center gap-1 group"
            >
              浏览完整日历 <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-3 sm:gap-4">
            {overview.recent_moments.map((m: any) => (
              <div
                key={m.id}
                onClick={() => onOpenPhoto(m.id)}
                className="group cursor-pointer bg-white rounded-2xl border border-[#EAE7E1] p-2 hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div className="aspect-square rounded-xl bg-[#EFECE6] overflow-hidden mb-2">
                  <img
                    src={m.thumbnail_url}
                    alt={m.photo_date}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    loading="lazy"
                  />
                </div>
                <div className="px-1 pb-1">
                  <div className="text-xs font-mono font-medium text-[#1A1918]">
                    {m.photo_date}
                  </div>
                  {m.age && (
                    <div className="text-[10px] text-[#8C827A] truncate">
                      {m.age.display}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 4. Selected Memories (Highlights Preview) */}
      {overview?.selected_memories?.length > 0 && (
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-end mb-6">
            <div>
              <span className="text-[11px] uppercase tracking-widest text-[#8C827A] font-medium">
                Curated Highlights
              </span>
              <h2 className="font-serif text-2xl font-medium text-[#1A1918]">
                珍藏精选
              </h2>
            </div>
            <button
              onClick={() => onNavigate('highlights')}
              className="text-xs font-medium text-[#6B5E54] hover:text-[#1A1918] flex items-center gap-1 group"
            >
              查看全部精选 <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
            {overview.selected_memories.slice(0, 4).map((h: any) => (
              <div
                key={h.id}
                onClick={() => onOpenPhoto(h.id)}
                className="group cursor-pointer bg-white rounded-2xl border border-[#EAE7E1] p-3 hover:shadow-md transition-all"
              >
                <div className="aspect-[4/3] rounded-xl bg-[#EFECE6] overflow-hidden mb-3">
                  <img
                    src={h.thumbnail_url}
                    alt={h.photo_date}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    loading="lazy"
                  />
                </div>
                <div className="text-xs font-medium text-[#1A1918] font-mono mb-1">
                  {h.photo_date}
                </div>
                <p className="text-xs text-[#6B635B] line-clamp-2 italic mb-2">
                  {h.description || '精心记录的珍贵瞬间'}
                </p>
                {h.tags?.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {h.tags.slice(0, 2).map((t: string, i: number) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-[#F5F2EB] text-[#7A6E63]">
                        #{t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 5. Explore Your Journey (Navigation Hub) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-t border-[#EAE7E1] pt-12">
          <span className="text-[11px] uppercase tracking-widest text-[#8C827A] font-medium block text-center mb-1">
            Explore Your Journey
          </span>
          <h2 className="font-serif text-2xl font-medium text-[#1A1918] text-center mb-8">
            档案导航中心
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div
              onClick={() => onNavigate('calendar')}
              className="p-6 rounded-2xl bg-white border border-[#EAE7E1] hover:border-[#8C7A6B] hover:shadow-sm transition-all cursor-pointer group"
            >
              <Calendar className="w-6 h-6 text-[#8C7A6B] mb-3" />
              <h3 className="font-serif text-lg font-medium text-[#1A1918] group-hover:text-[#52443B]">日历档案</h3>
              <p className="text-xs text-[#7D756E] mt-1">按日、周、月维度穿梭，支持标准月历与月度照片墙。</p>
            </div>

            <div
              onClick={() => onNavigate('timeline')}
              className="p-6 rounded-2xl bg-white border border-[#EAE7E1] hover:border-[#8C7A6B] hover:shadow-sm transition-all cursor-pointer group"
            >
              <Clock className="w-6 h-6 text-[#8C7A6B] mb-3" />
              <h3 className="font-serif text-lg font-medium text-[#1A1918] group-hover:text-[#52443B]">时光河流</h3>
              <p className="text-xs text-[#7D756E] mt-1">按时间倒序连续流淌，回溯每个月的时光变迁。</p>
            </div>

            <div
              onClick={() => onNavigate('highlights')}
              className="p-6 rounded-2xl bg-white border border-[#EAE7E1] hover:border-[#8C7A6B] hover:shadow-sm transition-all cursor-pointer group"
            >
              <Sparkles className="w-6 h-6 text-[#8C7A6B] mb-3" />
              <h3 className="font-serif text-lg font-medium text-[#1A1918] group-hover:text-[#52443B]">精选瞬间</h3>
              <p className="text-xs text-[#7D756E] mt-1">人工挑选的特别回忆，沉淀专属的标签与故事。</p>
            </div>

            <div
              onClick={() => onNavigate('collections')}
              className="p-6 rounded-2xl bg-white border border-[#EAE7E1] hover:border-[#8C7A6B] hover:shadow-sm transition-all cursor-pointer group"
            >
              <FolderHeart className="w-6 h-6 text-[#8C7A6B] mb-3" />
              <h3 className="font-serif text-lg font-medium text-[#1A1918] group-hover:text-[#52443B]">主题合集</h3>
              <p className="text-xs text-[#7D756E] mt-1">围绕特定时刻、旅行或重要纪念日汇聚成专属画册。</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
