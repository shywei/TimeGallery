import React, { useEffect, useState, useRef } from 'react'
import {
  Calendar,
  Upload,
  Trash2,
  Image as ImageIcon,
  Video,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Plus,
  Loader2,
  FolderHeart,
  ChevronLeft,
  ChevronRight,
  Archive,
  Info
} from 'lucide-react'
import { api } from '../../services/api'
import type { DayContentStatus, TrashStats } from '../../types/content_mgmt'

interface ContentManagementTabProps {
  initialDate?: string
}

export const ContentManagementTab: React.FC<ContentManagementTabProps> = ({ initialDate }) => {
  // Current selected date (defaults to initialDate or today in local format)
  const todayStr = new Date().toISOString().split('T')[0]
  const [selectedDate, setSelectedDate] = useState<string>(initialDate || todayStr)
  const [dayStatus, setDayStatus] = useState<DayContentStatus | null>(null)
  const [loadingDay, setLoadingDay] = useState(false)

  useEffect(() => {
    if (initialDate) {
      setSelectedDate(initialDate)
    }
  }, [initialDate])

  // Trash state
  const [trashStats, setTrashStats] = useState<TrashStats | null>(null)
  const [clearingTrash, setClearingTrash] = useState(false)

  // Upload daily photo state
  const [uploadingDaily, setUploadingDaily] = useState(false)
  const dailyFileInputRef = useRef<HTMLInputElement>(null)

  // Special moment state
  const [momentTitle, setMomentTitle] = useState('')
  const [momentDesc, setMomentDesc] = useState('')
  const [uploadingMoment, setUploadingMoment] = useState(false)
  const momentFilesInputRef = useRef<HTMLInputElement>(null)

  // Status message / toast
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const showFeedback = (type: 'success' | 'error', text: string) => {
    setFeedback({ type, text })
    setTimeout(() => setFeedback(null), 4000)
  }

  const fetchDayStatus = (dateStr: string) => {
    setLoadingDay(true)
    api.getDayContentStatus(dateStr)
      .then((data) => {
        setDayStatus(data)
        if (data.moment) {
          setMomentTitle(data.moment.title || '')
          setMomentDesc(data.moment.description || '')
        } else {
          setMomentTitle('')
          setMomentDesc('')
        }
        setLoadingDay(false)
      })
      .catch((err) => {
        showFeedback('error', `加载日期档案失败: ${err.message}`)
        setLoadingDay(false)
      })
  }

  const fetchTrashStats = () => {
    api.getTrashStats()
      .then(setTrashStats)
      .catch(() => {})
  }

  useEffect(() => {
    fetchDayStatus(selectedDate)
    fetchTrashStats()
  }, [selectedDate])

  // Navigate date by +/- 1 day
  const handleDateShift = (deltaDays: number) => {
    const cur = new Date(selectedDate)
    cur.setDate(cur.getDate() + deltaDays)
    setSelectedDate(cur.toISOString().split('T')[0])
  }

  // Daily photo upload/replace
  const handleDailyFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return
    const file = files[0]

    setUploadingDaily(true)
    try {
      const res = await api.uploadDailyPhoto(selectedDate, file)
      showFeedback('success', res.message || '每日主图保存成功！')
      fetchDayStatus(selectedDate)
      fetchTrashStats()
    } catch (err: any) {
      showFeedback('error', `上传主图失败: ${err.message}`)
    } finally {
      setUploadingDaily(false)
      if (dailyFileInputRef.current) dailyFileInputRef.current.value = ''
    }
  }

  // Daily photo delete
  const handleDeleteDailyPhoto = async () => {
    if (!window.confirm(`确定要删除 ${selectedDate} 的每日主图吗？\n原图将安全移至回收站，并携带时间戳备份。`)) {
      return
    }
    try {
      const res = await api.deleteDailyPhoto(selectedDate)
      showFeedback('success', res.message || '主图已安全移至回收站')
      fetchDayStatus(selectedDate)
      fetchTrashStats()
    } catch (err: any) {
      showFeedback('error', `删除主图失败: ${err.message}`)
    }
  }

  // Moment media upload
  const handleMomentFilesSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setUploadingMoment(true)
    try {
      const fileList = Array.from(files)
      const res = await api.uploadMomentMedia(selectedDate, fileList, momentTitle, momentDesc)
      showFeedback('success', res.message || '特别时刻媒体添加成功！')
      fetchDayStatus(selectedDate)
      fetchTrashStats()
    } catch (err: any) {
      showFeedback('error', `上传特别时刻媒体失败: ${err.message}`)
    } finally {
      setUploadingMoment(false)
      if (momentFilesInputRef.current) momentFilesInputRef.current.value = ''
    }
  }

  // Delete single media item from moment
  const handleDeleteMomentMedia = async (mediaId: number, filename: string) => {
    if (!window.confirm(`确定将「${filename}」移入回收站吗？`)) return
    try {
      const res = await api.deleteMomentMedia(mediaId)
      showFeedback('success', res.message || '文件已移入回收站')
      fetchDayStatus(selectedDate)
      fetchTrashStats()
    } catch (err: any) {
      showFeedback('error', `删除媒体失败: ${err.message}`)
    }
  }

  // Delete entire moment
  const handleDeleteEntireMoment = async () => {
    if (!window.confirm(`确定要解散并删除 ${selectedDate} 的整个特别时刻吗？\n文件夹及全部照片/视频将完整移入回收站保护。`)) {
      return
    }
    try {
      const res = await api.deleteMoment(selectedDate)
      showFeedback('success', res.message || '特别时刻已移至回收站')
      fetchDayStatus(selectedDate)
      fetchTrashStats()
    } catch (err: any) {
      showFeedback('error', `删除特别时刻失败: ${err.message}`)
    }
  }

  // Empty trash
  const handleEmptyTrash = async () => {
    if (!trashStats || trashStats.file_count === 0) return
    if (!window.confirm(`警告：确定要彻底清空回收站吗？\n此操作将永久抹除当前回收站内的 ${trashStats.file_count} 个历史备份文件（${trashStats.total_size_display}），不可撤销！`)) {
      return
    }
    setClearingTrash(true)
    try {
      const res = await api.emptyTrash()
      showFeedback('success', `回收站已清空，释放了 ${res.freed_display} 磁盘空间`)
      fetchTrashStats()
    } catch (err: any) {
      showFeedback('error', `清空回收站失败: ${err.message}`)
    } finally {
      setClearingTrash(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Toast Feedback */}
      {feedback && (
        <div
          className={`p-4 rounded-2xl border text-xs flex items-center justify-between shadow-sm animate-in fade-in duration-200 ${
            feedback.type === 'success'
              ? 'bg-[#EBF7EE] border-[#B2D8B9] text-[#2E5936]'
              : 'bg-red-50 border-red-200 text-red-700'
          }`}
        >
          <div className="flex items-center gap-2">
            {feedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
            )}
            <span className="font-medium">{feedback.text}</span>
          </div>
          <button
            onClick={() => setFeedback(null)}
            className="text-[11px] underline opacity-75 hover:opacity-100 cursor-pointer"
          >
            关闭
          </button>
        </div>
      )}

      {/* Date Control Bar & Trash Widget */}
      <div className="bg-white rounded-3xl border border-[#EAE7E1] p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        {/* Date Selector */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5 bg-[#FAF8F5] px-3 py-1.5 rounded-2xl border border-[#DDD7CD]">
            <Calendar className="w-4 h-4 text-[#8C7A6B]" />
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="text-xs bg-transparent outline-none font-mono text-[#1A1918] cursor-pointer"
            />
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => handleDateShift(-1)}
              className="p-1.5 rounded-xl border border-[#DDD7CD] hover:bg-[#FAF8F5] text-[#5C534B] transition-colors cursor-pointer"
              title="前一天"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setSelectedDate(todayStr)}
              className="px-2.5 py-1.5 rounded-xl border border-[#DDD7CD] hover:bg-[#FAF8F5] text-xs font-medium text-[#5C534B] transition-colors cursor-pointer"
            >
              今天
            </button>
            <button
              onClick={() => handleDateShift(1)}
              className="p-1.5 rounded-xl border border-[#DDD7CD] hover:bg-[#FAF8F5] text-[#5C534B] transition-colors cursor-pointer"
              title="后一天"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <span className="text-xs font-mono text-[#8C827A] ml-2">
            目录对应: <strong className="text-[#1A1918]">{dayStatus?.yymmdd || '...'}</strong>
          </span>
        </div>

        {/* Trash Status & Action */}
        <div className="flex items-center gap-3 bg-[#FAF8F5] px-4 py-2 rounded-2xl border border-[#EAE5DC]">
          <div className="flex items-center gap-2 text-xs text-[#5C534B]">
            <Archive className="w-4 h-4 text-[#8C7A6B]" />
            <span>
              回收站:{' '}
              <strong className="text-[#1A1918]">{trashStats?.file_count || 0}</strong> 个文件 (
              {trashStats?.total_size_display || '0 B'})
            </span>
          </div>
          {trashStats && trashStats.file_count > 0 && (
            <button
              onClick={handleEmptyTrash}
              disabled={clearingTrash}
              className="px-2.5 py-1 text-[11px] font-medium text-red-600 hover:bg-red-50 rounded-lg border border-red-200 transition-colors flex items-center gap-1 cursor-pointer"
              title="彻底清空回收站中所有被替换或删除的历史快照"
            >
              {clearingTrash && <Loader2 className="w-3 h-3 animate-spin" />}
              <span>彻底清空</span>
            </button>
          )}
        </div>
      </div>

      {loadingDay ? (
        <div className="h-64 flex items-center justify-center text-xs text-[#7D756E] gap-2">
          <Loader2 className="w-5 h-5 animate-spin text-[#8C7A6B]" />
          正在读取该日档案与媒体状态...
        </div>
      ) : dayStatus ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Card A: 每日主图维护 */}
          <div className="bg-white rounded-3xl border border-[#EAE7E1] p-6 shadow-sm flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex justify-between items-center border-b border-[#F0ECE6] pb-3">
                <div className="flex items-center gap-2">
                  <ImageIcon className="w-4 h-4 text-[#8C7A6B]" />
                  <h3 className="font-serif text-lg font-medium text-[#1A1918]">每日主图</h3>
                </div>
                <span
                  className={`text-[11px] px-2.5 py-0.5 rounded-full font-medium ${
                    dayStatus.has_daily_photo
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-amber-50 text-amber-700 border border-amber-200'
                  }`}
                >
                  {dayStatus.has_daily_photo ? '已归档' : '未归档 (缺失)'}
                </span>
              </div>

              {dayStatus.has_daily_photo && dayStatus.daily_photo ? (
                <div className="space-y-3">
                  <div className="aspect-[4/3] rounded-2xl bg-[#EFECE6] overflow-hidden border border-[#E8E4DC] relative group">
                    <img
                      src={dayStatus.daily_photo.preview_url || dayStatus.daily_photo.thumbnail_url || ''}
                      alt=""
                      className="w-full h-full object-contain"
                    />
                    <div className="absolute top-2 left-2 px-2.5 py-1 rounded-lg bg-black/60 text-white font-mono text-[10px] backdrop-blur-xs">
                      {dayStatus.daily_photo.filename}
                    </div>
                  </div>

                  <div className="bg-[#FAF8F5] p-3 rounded-xl border border-[#EDE8E0] text-xs space-y-1 text-[#6B635B]">
                    <div className="flex justify-between">
                      <span>文件大小:</span>
                      <strong className="font-mono text-[#1A1918]">{dayStatus.daily_photo.file_size_display}</strong>
                    </div>
                    {dayStatus.daily_photo.width && dayStatus.daily_photo.height && (
                      <div className="flex justify-between">
                        <span>分辨率:</span>
                        <strong className="font-mono text-[#1A1918]">
                          {dayStatus.daily_photo.width} × {dayStatus.daily_photo.height}
                        </strong>
                      </div>
                    )}
                    {dayStatus.daily_photo.description && (
                      <div className="pt-1 border-t border-[#EAE5DC] text-[11px] italic">
                        "{dayStatus.daily_photo.description}"
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="aspect-[4/3] rounded-2xl bg-[#FAF8F5] border-2 border-dashed border-[#DDD7CD] flex flex-col items-center justify-center p-6 text-center text-[#8C827A] space-y-2">
                  <ImageIcon className="w-8 h-8 text-[#BBB4A9]" />
                  <p className="font-medium text-xs text-[#5C534B]">该日期尚未上传每日主图</p>
                  <p className="text-[11px]">
                    规范格式: <span className="font-mono font-semibold text-[#1A1918]">{dayStatus.yymmdd}.jpg</span>
                  </p>
                </div>
              )}
            </div>

            {/* Daily Photo Actions */}
            <div className="pt-4 border-t border-[#F0ECE6] flex items-center justify-between gap-3">
              <input
                type="file"
                ref={dailyFileInputRef}
                onChange={handleDailyFileSelect}
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
              />

              <button
                type="button"
                onClick={() => dailyFileInputRef.current?.click()}
                disabled={uploadingDaily}
                className="px-4 py-2 rounded-xl bg-[#2C2622] text-white text-xs font-medium hover:bg-[#3D352F] transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer disabled:opacity-50"
              >
                {uploadingDaily ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
                <span>{dayStatus.has_daily_photo ? '替换为主图 (旧图移至回收站)' : '上传并归档此日主图'}</span>
              </button>

              {dayStatus.has_daily_photo && (
                <button
                  type="button"
                  onClick={handleDeleteDailyPhoto}
                  className="px-3.5 py-2 rounded-xl text-xs text-red-600 hover:bg-red-50 border border-red-200 transition-colors flex items-center gap-1.5 cursor-pointer"
                  title="将主图移至回收站"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>删除主图</span>
                </button>
              )}
            </div>
          </div>

          {/* Card B: 特殊时刻维护 */}
          <div className="bg-white rounded-3xl border border-[#EAE7E1] p-6 shadow-sm flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex justify-between items-center border-b border-[#F0ECE6] pb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-amber-500" />
                  <h3 className="font-serif text-lg font-medium text-[#1A1918]">特别时刻 (回忆图集)</h3>
                </div>
                <span
                  className={`text-[11px] px-2.5 py-0.5 rounded-full font-medium ${
                    dayStatus.has_moment
                      ? 'bg-amber-50 text-amber-700 border border-amber-200'
                      : 'bg-gray-100 text-[#7D756E]'
                  }`}
                >
                  {dayStatus.has_moment
                    ? `包含 ${dayStatus.moment?.photo_count || 0} 图 / ${dayStatus.moment?.video_count || 0} 视频`
                    : '暂无特别时刻'}
                </span>
              </div>

              {/* Title & Story Inputs */}
              <div className="space-y-2 bg-[#FAF8F5] p-3.5 rounded-2xl border border-[#EAE5DC]">
                <div>
                  <label className="block text-[11px] font-medium text-[#7D756E] mb-1">特别时刻标题 (选填)</label>
                  <input
                    type="text"
                    value={momentTitle}
                    onChange={(e) => setMomentTitle(e.target.value)}
                    placeholder="如: 两周岁生日抓周 / 海边踏浪"
                    className="w-full px-3 py-1.5 bg-white border border-[#DDD7CD] rounded-xl text-xs text-[#1A1918] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-[#7D756E] mb-1">背后的故事或手记 (选填)</label>
                  <textarea
                    value={momentDesc}
                    onChange={(e) => setMomentDesc(e.target.value)}
                    placeholder="记录这一天特别的欢声笑语..."
                    rows={2}
                    className="w-full px-3 py-1.5 bg-white border border-[#DDD7CD] rounded-xl text-xs text-[#1A1918] focus:outline-none"
                  />
                </div>
              </div>

              {/* Media Grid or Empty State */}
              {dayStatus.has_moment && dayStatus.moment?.media_items?.length ? (
                <div className="space-y-2">
                  <span className="text-[11px] font-medium text-[#8C827A] block">
                    当前图集文件 ({dayStatus.moment.media_items.length} 个)
                  </span>
                  <div className="grid grid-cols-3 sm:grid-cols-4 gap-2.5 max-h-[260px] overflow-y-auto p-1">
                    {dayStatus.moment.media_items.map((m) => (
                      <div
                        key={m.id}
                        className="relative rounded-xl overflow-hidden border border-[#E8E4DC] bg-[#FAF8F5] group aspect-square"
                      >
                        <img
                          src={m.thumbnail_url}
                          alt=""
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                        {m.media_type === 'VIDEO' && (
                          <div className="absolute top-1 left-1 p-1 rounded-md bg-black/60 text-white">
                            <Video className="w-3 h-3" />
                          </div>
                        )}
                        <button
                          type="button"
                          onClick={() => handleDeleteMomentMedia(m.id, m.filename)}
                          className="absolute top-1 right-1 p-1 rounded-md bg-red-600/80 hover:bg-red-700 text-white opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer shadow-xs"
                          title="移入回收站"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                        <div className="absolute bottom-0 inset-x-0 bg-black/60 text-white text-[9px] p-1 truncate font-mono text-center">
                          {m.filename}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="p-6 rounded-2xl bg-[#FAF8F5] border-2 border-dashed border-[#DDD7CD] text-center text-[#8C827A] space-y-1">
                  <FolderHeart className="w-7 h-7 text-[#BBB4A9] mx-auto mb-1" />
                  <p className="text-xs text-[#5C534B]">该日无特殊时刻文件夹</p>
                  <p className="text-[11px]">
                    点击下方选择照片或视频上传，系统将自动创建 <span className="font-mono font-semibold text-[#1A1918]">{dayStatus.yymmdd}/</span> 专属图集。
                  </p>
                </div>
              )}
            </div>

            {/* Moment Actions */}
            <div className="pt-4 border-t border-[#F0ECE6] flex items-center justify-between gap-3">
              <input
                type="file"
                ref={momentFilesInputRef}
                onChange={handleMomentFilesSelect}
                multiple
                accept="image/*,video/*"
                className="hidden"
              />

              <button
                type="button"
                onClick={() => momentFilesInputRef.current?.click()}
                disabled={uploadingMoment}
                className="px-4 py-2 rounded-xl bg-[#2C2622] text-white text-xs font-medium hover:bg-[#3D352F] transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer disabled:opacity-50"
              >
                {uploadingMoment ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
                <span>{dayStatus.has_moment ? '追加照片/视频' : '创建并上传照片/视频'}</span>
              </button>

              {dayStatus.has_moment && (
                <button
                  type="button"
                  onClick={handleDeleteEntireMoment}
                  className="px-3.5 py-2 rounded-xl text-xs text-red-600 hover:bg-red-50 border border-red-200 transition-colors flex items-center gap-1.5 cursor-pointer"
                  title="解散并删除此特殊时刻文件夹"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>解散时刻</span>
                </button>
              )}
            </div>
          </div>
        </div>
      ) : null}

      {/* Safety Notice Banner */}
      <div className="bg-[#FAF8F5] rounded-2xl p-4 border border-[#EAE5DC] flex items-start gap-3 text-xs text-[#7D756E]">
        <Info className="w-4 h-4 text-[#8C7A6B] shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <p className="font-medium text-[#1A1918]">数据安全与回收站机制说明：</p>
          <p>
            在此处执行“替换”或“删除”时，系统绝不会直接抹除原始文件，而是会自动附加精确至秒级的时间戳版本（如{' '}
            <code className="text-[#8C7A6B] bg-[#EFECE6] px-1 py-0.5 rounded font-mono">
              241111_20261105_143015.jpg
            </code>
            ）移至隐藏的 <code className="text-[#8C7A6B] bg-[#EFECE6] px-1 py-0.5 rounded font-mono">.trash/</code> 目录，彻底杜绝误删风险与命名冲突。
          </p>
        </div>
      </div>
    </div>
  )
}
