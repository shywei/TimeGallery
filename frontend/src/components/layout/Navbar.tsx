import React from 'react'
import { Calendar as CalendarIcon, Clock, Sparkles, FolderHeart, ShieldCheck, Eye } from 'lucide-react'

export type NavTab = 'home' | 'calendar' | 'timeline' | 'highlights' | 'collections' | 'moments' | 'management'

interface NavbarProps {
  currentTab: NavTab
  onSelectTab: (tab: NavTab) => void
  isManagementMode: boolean
  onToggleManagementMode: () => void
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onSelectTab,
  isManagementMode,
  onToggleManagementMode
}) => {
  return (
    <header className="shrink-0 z-40 bg-[#FBFBFA] border-b border-[#EAE7E1] transition-colors select-none">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand */}
        <div
          onClick={() => onSelectTab('home')}
          className="cursor-pointer group flex flex-col justify-center"
        >
          <span className="font-serif text-2xl font-medium tracking-tight text-[#1A1918] group-hover:text-[#52443B] transition-colors">
            拾光记
          </span>
          <span className="text-[10px] uppercase tracking-widest text-[#8C827A] font-medium">
            时光画册 · 岁月记录
          </span>
        </div>

        {/* Primary Navigation */}
        <nav className="hidden md:flex items-center space-x-1 sm:space-x-2">
          <button
            type="button"
            onClick={() => onSelectTab('home')}
            className={`px-4 py-2 rounded-full text-xs font-medium tracking-wide transition-all select-none cursor-pointer ${
              currentTab === 'home'
                ? 'bg-[#2C2622] text-[#F7F5F0] shadow-sm'
                : 'text-[#615A53] hover:text-[#1A1918] hover:bg-[#F0EDE6]'
            }`}
          >
            首页
          </button>

          <button
            type="button"
            onClick={() => onSelectTab('calendar')}
            className={`px-4 py-2 rounded-full text-xs font-medium tracking-wide transition-all select-none cursor-pointer flex items-center gap-1.5 ${
              currentTab === 'calendar'
                ? 'bg-[#2C2622] text-[#F7F5F0] shadow-sm'
                : 'text-[#615A53] hover:text-[#1A1918] hover:bg-[#F0EDE6]'
            }`}
          >
            <CalendarIcon className="w-3.5 h-3.5" />
            日历档案
          </button>

          <button
            type="button"
            onClick={() => onSelectTab('timeline')}
            className={`px-4 py-2 rounded-full text-xs font-medium tracking-wide transition-all select-none cursor-pointer flex items-center gap-1.5 ${
              currentTab === 'timeline'
                ? 'bg-[#2C2622] text-[#F7F5F0] shadow-sm'
                : 'text-[#615A53] hover:text-[#1A1918] hover:bg-[#F0EDE6]'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            时间轴
          </button>

          <button
            type="button"
            onClick={() => onSelectTab('highlights')}
            className={`px-4 py-2 rounded-full text-xs font-medium tracking-wide transition-all select-none cursor-pointer flex items-center gap-1.5 ${
              currentTab === 'highlights'
                ? 'bg-[#2C2622] text-[#F7F5F0] shadow-sm'
                : 'text-[#615A53] hover:text-[#1A1918] hover:bg-[#F0EDE6]'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            精选
          </button>

          <button
            type="button"
            onClick={() => onSelectTab('collections')}
            className={`px-4 py-2 rounded-full text-xs font-medium tracking-wide transition-all select-none cursor-pointer flex items-center gap-1.5 ${
              currentTab === 'collections'
                ? 'bg-[#2C2622] text-[#F7F5F0] shadow-sm'
                : 'text-[#615A53] hover:text-[#1A1918] hover:bg-[#F0EDE6]'
            }`}
          >
            <FolderHeart className="w-3.5 h-3.5" />
            主题合集
          </button>

          <button
            type="button"
            onClick={() => onSelectTab('moments')}
            className={`px-4 py-2 rounded-full text-xs font-medium tracking-wide transition-all select-none cursor-pointer flex items-center gap-1.5 ${
              currentTab === 'moments'
                ? 'bg-[#2C2622] text-[#F7F5F0] shadow-sm'
                : 'text-[#615A53] hover:text-[#1A1918] hover:bg-[#F0EDE6]'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
            特别时刻
          </button>

          {isManagementMode && (
            <button
              type="button"
              onClick={() => onSelectTab('management')}
              className={`px-4 py-2 rounded-full text-xs font-medium tracking-wide transition-all select-none cursor-pointer flex items-center gap-1.5 ${
                currentTab === 'management'
                  ? 'bg-[#8C7A6B] text-white shadow-sm'
                  : 'text-[#8C7A6B] hover:bg-[#F0EDE6]'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              后台维护
            </button>
          )}
        </nav>

        {/* Mode Switcher */}
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleManagementMode}
            className={`px-3.5 py-1.5 rounded-full text-xs font-medium tracking-wider flex items-center gap-2 border transition-all ${
              isManagementMode
                ? 'bg-[#F2ECE4] border-[#D6CBBF] text-[#4A3D34]'
                : 'bg-white border-[#E5E0D8] text-[#7A7168] hover:border-[#C4B9AD]'
            }`}
            title={isManagementMode ? '点击退出管理模式' : '点击进入管理模式'}
          >
            {isManagementMode ? (
              <>
                <ShieldCheck className="w-3.5 h-3.5 text-[#8C7A6B]" />
                <span>管理模式</span>
              </>
            ) : (
              <>
                <Eye className="w-3.5 h-3.5 text-[#9E958C]" />
                <span>浏览模式</span>
              </>
            )}
          </button>
        </div>
      </div>
    </header>
  )
}
