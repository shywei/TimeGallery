import React, { useEffect, useState } from 'react'
import { Sparkles, Calendar, Image as ImageIcon, Video, Loader2 } from 'lucide-react'
import { api } from '../services/api'
import type { MomentItem } from '../types/moment'
import { MomentDetailModal } from '../components/moment/MomentDetailModal'

interface MomentsPageProps {
  onOpenPhoto?: (photoId: number) => void
}

export const MomentsPage: React.FC<MomentsPageProps> = ({ onOpenPhoto }) => {
  const [moments, setMoments] = useState<MomentItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedMomentDate, setSelectedMomentDate] = useState<string | null>(null)

  const fetchMoments = () => {
    setLoading(true)
    api.getMoments()
      .then((data) => {
        setMoments(data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  useEffect(() => {
    fetchMoments()
  }, [])

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 pb-24">
      {/* Header */}
      <div className="text-center max-w-xl mx-auto">
        <span className="text-[11px] uppercase tracking-widest text-[#8C827A] font-medium flex items-center justify-center gap-1.5 mb-2">
          <Sparkles className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
          Special Moments Collection
        </span>
        <h1 className="font-serif text-3xl sm:text-4xl font-medium text-[#1A1918]">
          特别时刻
        </h1>
        <p className="text-xs text-[#7D756E] mt-2">
          日常生活一日一照，而在生日、旅行、节日等特别的日子里，多图与视频成册，定格生命中最丰沛闪耀的瞬间。
        </p>
      </div>

      {/* Moments Grid */}
      {loading ? (
        <div className="min-h-[40vh] flex items-center justify-center text-sm text-[#7D756E] gap-2 font-mono">
          <Loader2 className="w-5 h-5 animate-spin text-[#8C7A6B]" />
          拾光记 · 正在载入特别时刻画册...
        </div>
      ) : moments.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-3xl border border-[#EAE7E1] text-[#7D756E] space-y-3">
          <div className="w-12 h-12 rounded-full bg-[#FAF8F5] text-[#8C7A6B] flex items-center justify-center mx-auto border border-[#EAE5DC]">
            <Sparkles className="w-6 h-6 text-amber-500" />
          </div>
          <p className="font-serif text-xl text-[#2C2A29]">暂无特别时刻画册</p>
          <p className="text-xs text-[#8C827A] max-w-md mx-auto leading-relaxed">
            在照片文件夹中创建形如 6 位日期的子文件夹（如 <code className="bg-[#EFECE6] px-1.5 py-0.5 rounded text-[#1A1918] font-mono">241103</code>），在其中放入该日期的多张照片或视频，系统扫描后即可自动聚合为特别时刻。
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {moments.map((m) => (
            <div
              key={m.id}
              onClick={() => setSelectedMomentDate(m.moment_date)}
              className="group cursor-pointer bg-white rounded-3xl border border-[#EAE7E1] overflow-hidden hover:shadow-lg hover:border-[#8C7A6B] transition-all flex flex-col justify-between"
            >
              {/* Cover Image / Video Preview */}
              <div className="aspect-video sm:aspect-4/3 bg-[#EAE7E1] relative overflow-hidden">
                {m.cover_url ? (
                  <img
                    src={m.cover_url}
                    alt={m.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    loading="lazy"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-[#2C2622] text-amber-200">
                    <Sparkles className="w-10 h-10" />
                  </div>
                )}

                {/* Badges on Cover */}
                <div className="absolute top-3 left-3 flex items-center gap-1.5">
                  <span className="text-[10px] uppercase font-semibold px-2.5 py-1 rounded-full bg-black/60 text-white backdrop-blur-md flex items-center gap-1 shadow-sm font-mono">
                    <Calendar className="w-3 h-3 text-amber-300" />
                    {m.moment_date}
                  </span>
                  {m.age_display && (
                    <span className="text-[10px] px-2.5 py-1 rounded-full bg-white/90 text-[#3D352F] backdrop-blur-md font-medium shadow-sm">
                      {m.age_display}
                    </span>
                  )}
                </div>

                {/* Media count pill */}
                <div className="absolute bottom-3 right-3 flex items-center gap-1.5 text-[10px] px-2.5 py-1 rounded-full bg-black/70 text-white backdrop-blur-md font-medium shadow-sm">
                  {m.photo_count > 0 && (
                    <span className="flex items-center gap-1">
                      <ImageIcon className="w-3 h-3 text-white/80" />
                      {m.photo_count}
                    </span>
                  )}
                  {m.video_count > 0 && (
                    <span className="flex items-center gap-1 text-amber-300">
                      <Video className="w-3 h-3" />
                      {m.video_count}
                    </span>
                  )}
                </div>
              </div>

              {/* Card Footer Body */}
              <div className="p-5 flex items-center justify-between">
                <div className="min-w-0 flex-1 mr-3">
                  <h3 className="font-serif text-lg font-medium text-[#1A1918] group-hover:text-[#8C7A6B] transition-colors truncate">
                    {m.title}
                  </h3>
                  {m.description ? (
                    <p className="text-xs text-[#6B635B] mt-0.5 truncate italic">
                      {m.description}
                    </p>
                  ) : (
                    <p className="text-xs text-[#8C827A] mt-0.5">
                      共收录 {m.total_media} 个回忆切片
                    </p>
                  )}
                </div>
                <button
                  type="button"
                  className="px-3.5 py-1.5 rounded-xl text-xs font-medium bg-[#FAF8F5] group-hover:bg-[#2C2622] text-[#5C534B] group-hover:text-white border border-[#DDD7CD] group-hover:border-[#2C2622] transition-all cursor-pointer shadow-2xs shrink-0"
                >
                  翻阅画册
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Moment Detail Modal */}
      {selectedMomentDate && (
        <MomentDetailModal
          momentDateOrId={selectedMomentDate}
          onClose={() => setSelectedMomentDate(null)}
          onOpenPhoto={onOpenPhoto}
          onUpdated={fetchMoments}
        />
      )}
    </div>
  )
}
