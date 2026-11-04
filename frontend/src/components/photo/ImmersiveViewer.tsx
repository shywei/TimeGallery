import React, { useEffect } from 'react'
import { X, ChevronLeft, ChevronRight, Sparkles } from 'lucide-react'

interface ImmersiveViewerProps {
  photoUrl: string
  photoDate: string
  ageDisplay?: string
  isHighlight?: boolean
  onToggleHighlight?: () => void
  onClose: () => void
  onPrev?: () => void
  onNext?: () => void
}

export const ImmersiveViewer: React.FC<ImmersiveViewerProps> = ({
  photoUrl,
  photoDate,
  ageDisplay,
  isHighlight,
  onToggleHighlight,
  onClose,
  onPrev,
  onNext
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      else if (e.key === 'ArrowLeft' && onPrev) onPrev()
      else if (e.key === 'ArrowRight' && onNext) onNext()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose, onPrev, onNext])

  return (
    <div className="fixed inset-0 z-50 bg-[#121110]/95 backdrop-blur-md flex flex-col items-center justify-between p-4 sm:p-8 animate-in fade-in duration-200">
      {/* Top Bar */}
      <div className="w-full flex justify-between items-center text-[#E0DDD8] max-w-7xl">
        <div className="flex items-center gap-3 sm:gap-4">
          <span className="font-serif text-lg tracking-wide">{photoDate}</span>
          {ageDisplay && (
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#2A2825] text-[#C4BEB5]">
              {ageDisplay}
            </span>
          )}
          {onToggleHighlight && (
            <button
              onClick={onToggleHighlight}
              className={`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer ${
                isHighlight
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30'
                  : 'bg-white/10 hover:bg-white/20 text-white/80 hover:text-white border border-white/20'
              }`}
              title={isHighlight ? '点击取消精选' : '点击设为精选'}
            >
              <Sparkles className={`w-3.5 h-3.5 ${isHighlight ? 'text-amber-400 fill-amber-400' : ''}`} />
              <span>{isHighlight ? '已设精选' : '设为精选'}</span>
            </button>
          )}
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-full hover:bg-white/10 text-white/80 hover:text-white transition-colors"
          title="退出沉浸模式 (ESC)"
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      {/* Main Image View */}
      <div className="relative flex-1 w-full flex items-center justify-center my-4 overflow-hidden">
        {onPrev && (
          <button
            onClick={onPrev}
            className="absolute left-2 sm:left-6 z-10 p-3 rounded-full bg-black/40 hover:bg-black/70 text-white/80 hover:text-white transition-all backdrop-blur-sm"
            title="前一张 (左方向键)"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
        )}

        <img
          src={photoUrl}
          alt={photoDate}
          className="max-h-[82vh] max-w-[92vw] object-contain rounded-lg shadow-2xl select-none"
        />

        {onNext && (
          <button
            onClick={onNext}
            className="absolute right-2 sm:right-6 z-10 p-3 rounded-full bg-black/40 hover:bg-black/70 text-white/80 hover:text-white transition-all backdrop-blur-sm"
            title="后一张 (右方向键)"
          >
            <ChevronRight className="w-6 h-6" />
          </button>
        )}
      </div>

      {/* Bottom Hint */}
      <div className="text-[11px] text-[#8C857D] font-mono tracking-wider">
        键盘方向键 ◀ ▶ 切换 · ESC 退出沉浸浏览
      </div>
    </div>
  )
}
