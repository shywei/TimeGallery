import React, { useEffect, useState } from 'react'
import {
  Grid,
  LayoutGrid,
  ChevronLeft,
  ChevronRight,
  Search,
  Sparkles,
  Loader2
} from 'lucide-react'
import { api } from '../services/api'
import type { DayViewData, WeekViewData, MonthCalendarData, MonthPhotoWallData } from '../types/calendar'

type CalendarViewMode = 'day' | 'week' | 'month'
type MonthLayoutMode = 'calendar' | 'wall'

interface CalendarPageProps {
  onOpenPhoto: (photoId: number) => void
  initialDate?: string
  initialView?: CalendarViewMode
}

const getBeijingTodayStr = () => {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(new Date())
}

export const CalendarPage: React.FC<CalendarPageProps> = ({
  onOpenPhoto,
  initialDate,
  initialView = 'month'
}) => {
  const todayStr = getBeijingTodayStr()
  const [currentDate, setCurrentDate] = useState(initialDate || todayStr)
  const [viewMode, setViewMode] = useState<CalendarViewMode>(initialView)
  const [monthLayout, setMonthLayout] = useState<MonthLayoutMode>('calendar')

  // Quick jump input state
  const [jumpInput, setJumpInput] = useState('')
  const [jumpError, setJumpError] = useState<string | null>(null)

  // Data states
  const [dayData, setDayData] = useState<DayViewData | null>(null)
  const [weekData, setWeekData] = useState<WeekViewData | null>(null)
  const [monthCalendarData, setMonthCalendarData] = useState<MonthCalendarData | null>(null)
  const [monthWallData, setMonthWallData] = useState<MonthPhotoWallData | null>(null)
  const [loading, setLoading] = useState(false)

  // Parse Year and Month from currentDate
  const [currYear, currMonth] = currentDate.split('-').map(Number)

  // Load View Data
  useEffect(() => {
    setLoading(true)
    if (viewMode === 'day') {
      api.getDayView(currentDate)
        .then((data) => {
          setDayData(data)
          setLoading(false)
        })
        .catch(() => setLoading(false))
    } else if (viewMode === 'week') {
      api.getWeekView(currentDate)
        .then((data) => {
          setWeekData(data)
          setLoading(false)
        })
        .catch(() => setLoading(false))
    } else if (viewMode === 'month') {
      if (monthLayout === 'calendar') {
        api.getMonthCalendar(currYear, currMonth)
          .then((data) => {
            setMonthCalendarData(data)
            setLoading(false)
          })
          .catch(() => setLoading(false))
      } else {
        api.getMonthPhotoWall(currYear, currMonth)
          .then((data) => {
            setMonthWallData(data)
            setLoading(false)
          })
          .catch(() => setLoading(false))
      }
    }
  }, [currentDate, viewMode, monthLayout, currYear, currMonth])

  // Handle Quick Date Jump
  const handleQuickJump = async (e: React.FormEvent) => {
    e.preventDefault()
    setJumpError(null)
    const trimmed = jumpInput.trim()
    if (!trimmed) return

    try {
      const res = await api.resolveQuickDate(trimmed)
      setCurrentDate(res.date)
      setJumpInput('')
      if (res.has_photo && res.photo_id) {
        onOpenPhoto(res.photo_id)
      } else {
        setViewMode('day')
      }
    } catch (err: any) {
      setJumpError(err.message || '无效的日期格式，请输入 YYYY-MM-DD 或 6位数字 YYMMDD')
    }
  }

  // Navigation handlers
  const handlePrev = () => {
    if (viewMode === 'day' && dayData) {
      setCurrentDate(dayData.prev_date)
    } else if (viewMode === 'week' && weekData) {
      setCurrentDate(weekData.prev_week_date)
    } else if (viewMode === 'month') {
      const prevM = currMonth > 1 ? currMonth - 1 : 12
      const prevY = currMonth > 1 ? currYear : currYear - 1
      setCurrentDate(`${prevY}-${String(prevM).padStart(2, '0')}-01`)
    }
  }

  const handleNext = () => {
    if (viewMode === 'day' && dayData) {
      setCurrentDate(dayData.next_date)
    } else if (viewMode === 'week' && weekData) {
      setCurrentDate(weekData.next_week_date)
    } else if (viewMode === 'month') {
      const nextM = currMonth < 12 ? currMonth + 1 : 1
      const nextY = currMonth < 12 ? currYear : currYear + 1
      setCurrentDate(`${nextY}-${String(nextM).padStart(2, '0')}-01`)
    }
  }

  const handleGoToday = () => {
    setCurrentDate(todayStr)
    if (viewMode === 'day') setViewMode('day')
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 pb-24">
      {/* 1. Header Toolbar */}
      <div className="bg-white border border-[#EAE7E1] rounded-3xl p-6 shadow-sm space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <span className="text-[11px] uppercase tracking-widest text-[#8C827A] font-medium">
              Calendar Archive
            </span>
            <div className="flex items-center gap-3 mt-1">
              <h1 className={`font-serif text-3xl font-medium text-[#1A1918] shrink-0 tabular-nums ${
                viewMode === 'week' ? 'w-72 sm:w-80' : 'w-52 sm:w-60'
              }`}>
                {viewMode === 'month'
                  ? `${currYear} 年 ${currMonth} 月`
                  : viewMode === 'week'
                  ? `${weekData?.start_date || ''} ~ ${weekData?.end_date || ''}`
                  : currentDate}
              </h1>
              <div className="flex items-center gap-1 shrink-0">
                <button
                  type="button"
                  onClick={handlePrev}
                  className="p-1.5 rounded-full hover:bg-[#F2EFE9] text-[#7D756E] transition-colors cursor-pointer"
                  title="上一周期"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <button
                  type="button"
                  onClick={handleNext}
                  className="p-1.5 rounded-full hover:bg-[#F2EFE9] text-[#7D756E] transition-colors cursor-pointer"
                  title="下一周期"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Quick Date Input */}
          <form onSubmit={handleQuickJump} className="flex items-center gap-2 max-w-md w-full">
            <div className="relative flex-1">
              <input
                type="text"
                value={jumpInput}
                onChange={(e) => setJumpInput(e.target.value)}
                placeholder="快速定位日期: 2024-11-03 或 241103"
                className="w-full px-4 py-2.5 bg-[#FAF8F5] border border-[#E5E0D8] rounded-xl text-xs text-[#2C2A29] focus:outline-none focus:ring-2 focus:ring-[#8C7A6B]/30 font-mono"
              />
              <Search className="w-3.5 h-3.5 text-[#9E958C] absolute right-3 top-3 pointer-events-none" />
            </div>
            <button
              type="submit"
              className="py-2.5 px-4 rounded-xl bg-[#2C2622] text-white text-xs font-medium hover:bg-[#3D352F] transition-colors shrink-0"
            >
              定位
            </button>
          </form>
        </div>

        {jumpError && (
          <div className="text-xs text-red-600 bg-red-50 p-2.5 rounded-xl border border-red-200/60">
            {jumpError}
          </div>
        )}

        {/* View Switchers & Shortcuts */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-[#ECE7DE]">
          {/* Shortcuts */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleGoToday}
              className="px-3 py-1.5 rounded-lg border border-[#DDD7CD] text-xs font-medium text-[#5C534B] hover:bg-[#F5F2EB] transition-colors"
            >
              Today (今天)
            </button>
            <button
              onClick={() => {
                setCurrentDate(todayStr)
                setViewMode('week')
              }}
              className="px-3 py-1.5 rounded-lg border border-[#DDD7CD] text-xs font-medium text-[#5C534B] hover:bg-[#F5F2EB] transition-colors"
            >
              This Week
            </button>
            <button
              onClick={() => {
                setCurrentDate(todayStr)
                setViewMode('month')
              }}
              className="px-3 py-1.5 rounded-lg border border-[#DDD7CD] text-xs font-medium text-[#5C534B] hover:bg-[#F5F2EB] transition-colors"
            >
              This Month
            </button>
          </div>

          {/* View Modes */}
          <div className="flex items-center gap-3">
            {viewMode === 'month' && (
              <div className="flex items-center bg-[#F2EFE9] p-1 rounded-xl">
                <button
                  onClick={() => setMonthLayout('calendar')}
                  className={`px-3 py-1 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all ${
                    monthLayout === 'calendar'
                      ? 'bg-white text-[#1A1918] shadow-xs'
                      : 'text-[#7D756E] hover:text-[#1A1918]'
                  }`}
                >
                  <Grid className="w-3.5 h-3.5" />
                  标准月历
                </button>
                <button
                  onClick={() => setMonthLayout('wall')}
                  className={`px-3 py-1 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all ${
                    monthLayout === 'wall'
                      ? 'bg-white text-[#1A1918] shadow-xs'
                      : 'text-[#7D756E] hover:text-[#1A1918]'
                  }`}
                >
                  <LayoutGrid className="w-3.5 h-3.5" />
                  照片墙
                </button>
              </div>
            )}

            <div className="flex items-center bg-[#F2EFE9] p-1 rounded-xl">
              <button
                onClick={() => setViewMode('day')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  viewMode === 'day'
                    ? 'bg-white text-[#1A1918] shadow-xs'
                    : 'text-[#7D756E] hover:text-[#1A1918]'
                }`}
              >
                日视图
              </button>
              <button
                onClick={() => setViewMode('week')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  viewMode === 'week'
                    ? 'bg-white text-[#1A1918] shadow-xs'
                    : 'text-[#7D756E] hover:text-[#1A1918]'
                }`}
              >
                周视图
              </button>
              <button
                onClick={() => setViewMode('month')}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  viewMode === 'month'
                    ? 'bg-white text-[#1A1918] shadow-xs'
                    : 'text-[#7D756E] hover:text-[#1A1918]'
                }`}
              >
                月视图
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Main View Presentation */}
      {loading ? (
        <div className="min-h-[50vh] flex items-center justify-center text-sm text-[#7D756E] gap-2">
          <Loader2 className="w-5 h-5 animate-spin text-[#8C7A6B]" />
          正在加载时光记录...
        </div>
      ) : (
        <>
          {/* Day View */}
          {viewMode === 'day' && dayData && (
            <div className="bg-white border border-[#EAE7E1] rounded-3xl p-8 shadow-sm max-w-3xl mx-auto">
              <div className="flex justify-between items-center border-b border-[#ECE7DE] pb-4 mb-6">
                <div>
                  <span className="text-[11px] uppercase tracking-wider text-[#8C827A] font-medium">
                    自然日记录
                  </span>
                  <h2 className="font-serif text-3xl font-medium text-[#1A1918]">
                    {dayData.date}
                  </h2>
                </div>
                {dayData.age && (
                  <span className="px-3 py-1 rounded-full bg-[#EFECE6] text-[#5C534B] text-xs font-medium">
                    {dayData.age.display}
                  </span>
                )}
              </div>

              {dayData.has_photo && dayData.photo ? (
                <div className="space-y-4">
                  <div
                    onClick={() => onOpenPhoto(dayData.photo!.id)}
                    className="bg-[#171615] rounded-2xl overflow-hidden cursor-pointer group flex items-center justify-center p-2 min-h-[380px]"
                  >
                    <img
                      src={dayData.photo.preview_url}
                      alt={dayData.date}
                      className="max-h-[550px] w-full object-contain rounded-lg group-hover:scale-[1.01] transition-transform duration-500"
                    />
                  </div>
                  <div className="p-4 bg-[#FCFBF9] rounded-2xl border border-[#EDE8E0] flex justify-between items-center">
                    <p className="text-sm text-[#5C534B] italic">
                      {dayData.photo.description || '这一天留下了珍贵的成长印记。'}
                    </p>
                    <button
                      onClick={() => onOpenPhoto(dayData.photo!.id)}
                      className="px-4 py-2 rounded-xl bg-[#2C2622] text-white text-xs font-medium hover:bg-[#3D352F] transition-colors shrink-0"
                    >
                      查看档案详情
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-16 border-2 border-dashed border-[#EAE5DC] rounded-2xl">
                  <p className="font-serif text-xl text-[#2C2A29] mb-1">这一天没有照片记录</p>
                  <p className="text-xs text-[#8C827A] max-w-sm mx-auto">
                    成长中的空白同样也是生命自然舒展的一部分。您可以点击下方前后箭头浏览相邻日期。
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Week View */}
          {viewMode === 'week' && weekData && (
            <div className="space-y-4">
              <div className="flex justify-between items-center px-1">
                <span className="text-xs font-medium text-[#7D756E]">
                  本周记录情况: <strong className="text-[#1A1918]">{weekData.recorded_days}</strong> / 7 天
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-7 gap-3">
                {weekData.days.map((d) => {
                  const dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
                  return (
                    <div
                      key={d.date}
                      className={`bg-white border rounded-2xl p-3 flex flex-col justify-between transition-all ${
                        d.is_today
                          ? 'border-[#8C7A6B] ring-2 ring-[#8C7A6B]/20'
                          : 'border-[#EAE7E1] hover:border-[#D1C7BA]'
                      }`}
                    >
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-[11px] font-medium text-[#7D756E]">
                          {dayNames[d.day_of_week - 1]}
                        </span>
                        <span className="text-xs font-mono font-medium text-[#1A1918]">
                          {d.day_number}
                        </span>
                      </div>

                      {d.has_photo && d.photo ? (
                        <div
                          onClick={() => onOpenPhoto(d.photo!.id)}
                          className="aspect-square rounded-xl bg-[#EFECE6] overflow-hidden cursor-pointer group mb-2"
                        >
                          <img
                            src={d.photo.thumbnail_url}
                            alt=""
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                            loading="lazy"
                          />
                        </div>
                      ) : (
                        <div
                          onClick={() => {
                            setCurrentDate(d.date)
                            setViewMode('day')
                          }}
                          className="aspect-square rounded-xl border border-dashed border-[#E5E0D8] flex items-center justify-center text-[10px] text-[#A8A199] hover:bg-[#FAF8F5] cursor-pointer mb-2"
                        >
                          无照片
                        </div>
                      )}

                      <button
                        onClick={() => {
                          setCurrentDate(d.date)
                          setViewMode('day')
                        }}
                        className="text-[10px] text-[#8C827A] hover:text-[#1A1918] text-center w-full py-0.5"
                      >
                        {d.date}
                      </button>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Month View - Standard Calendar Layout */}
          {viewMode === 'month' && monthLayout === 'calendar' && monthCalendarData && (
            <div className="space-y-4">
              <div className="flex justify-between items-center px-1">
                <span className="text-xs font-medium text-[#7D756E]">
                  当月已归档: <strong className="text-[#1A1918]">{monthCalendarData.recorded_days}</strong> / {monthCalendarData.days_in_month} 天
                </span>
              </div>

              {/* Day-of-week header */}
              <div className="grid grid-cols-7 gap-2 text-center text-xs font-medium text-[#8C827A] uppercase tracking-wider py-2">
                <span>周一</span>
                <span>周二</span>
                <span>周三</span>
                <span>周四</span>
                <span>周五</span>
                <span>周六</span>
                <span>周日</span>
              </div>

              {/* 7-column Calendar Matrix */}
              <div className="grid grid-cols-7 gap-2">
                {monthCalendarData.days.map((cell, idx) => (
                  <div
                    key={idx}
                    className={`min-h-[90px] sm:min-h-[110px] rounded-2xl p-2 flex flex-col justify-between border transition-all ${
                      !cell.is_current_month
                        ? 'bg-[#F7F6F2]/50 border-transparent text-[#BCB6AE]'
                        : cell.is_today
                        ? 'bg-white border-[#8C7A6B] ring-2 ring-[#8C7A6B]/20 text-[#1A1918]'
                        : 'bg-white border-[#EAE7E1] hover:border-[#D1C7BA] text-[#1A1918]'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-mono font-medium">
                        {cell.day_number}
                      </span>
                      {cell.has_photo && cell.photo?.is_highlight === 1 && (
                        <Sparkles className="w-3 h-3 text-amber-500" />
                      )}
                    </div>

                    {cell.has_photo && cell.photo ? (
                      <div
                        onClick={() => onOpenPhoto(cell.photo!.id)}
                        className="aspect-square rounded-xl bg-[#EFECE6] overflow-hidden cursor-pointer group my-1"
                      >
                        <img
                          src={cell.photo.thumbnail_url}
                          alt=""
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          loading="lazy"
                        />
                      </div>
                    ) : (
                      <div
                        onClick={() => {
                          if (cell.is_current_month) {
                            setCurrentDate(cell.date)
                            setViewMode('day')
                          }
                        }}
                        className="flex-1 cursor-pointer"
                      />
                    )}

                    <div className="text-right">
                      <button
                        onClick={() => {
                          setCurrentDate(cell.date)
                          setViewMode('day')
                        }}
                        className="text-[9px] text-[#A8A199] hover:text-[#52443B]"
                      >
                        详情
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Month View - Photo Wall Layout */}
          {viewMode === 'month' && monthLayout === 'wall' && monthWallData && (
            <div className="space-y-4">
              <div className="flex justify-between items-center px-1">
                <span className="text-xs font-medium text-[#7D756E]">
                  本月有效照片: <strong className="text-[#1A1918]">{monthWallData.total_photos}</strong> 张 (按拍摄日期升序排列)
                </span>
              </div>

              {monthWallData.items.length === 0 ? (
                <div className="bg-white rounded-3xl border border-[#EAE7E1] p-12 text-center text-[#7D756E]">
                  该月份暂无有效归档照片。
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                  {monthWallData.items.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => onOpenPhoto(item.id)}
                      className="group cursor-pointer bg-white rounded-2xl border border-[#EAE7E1] p-2 hover:shadow-md transition-all flex flex-col justify-between"
                    >
                      <div className="rounded-xl bg-[#EFECE6] overflow-hidden mb-2 relative">
                        <img
                          src={item.thumbnail_url}
                          alt={item.photo_date}
                          className="w-full object-cover group-hover:scale-105 transition-transform duration-500"
                          style={{ aspectRatio: `${item.aspect_ratio || 1}` }}
                          loading="lazy"
                        />
                        {item.is_highlight === 1 && (
                          <div className="absolute top-2 right-2 p-1 rounded-full bg-black/40 text-amber-300 backdrop-blur-xs">
                            <Sparkles className="w-3 h-3" />
                          </div>
                        )}
                      </div>
                      <div className="px-1 text-xs font-mono font-medium text-[#1A1918]">
                        {item.photo_date}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
