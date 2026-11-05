import React, { useEffect, useState } from 'react'
import {
  FolderSearch,
  AlertTriangle,
  Sliders,
  Database,
  Play,
  RotateCcw,
  Download,
  Loader2,
  FileCheck,
  CalendarX2,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  ImagePlus
} from 'lucide-react'
import { api } from '../services/api'
import type { ScanJob, ScanIssue, MissingDatesSummary } from '../types/scanner'
import type { SystemConfig } from '../types/system'
import { ContentManagementTab } from '../components/management/ContentManagementTab'

type MgmtTab = 'content' | 'scanner' | 'issues' | 'settings' | 'backup'

export const ManagementPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<MgmtTab>('content')
  const [contentTargetDate, setContentTargetDate] = useState<string | undefined>(undefined)

  // Scanner State
  const [scanJobs, setScanJobs] = useState<ScanJob[]>([])
  const [scanning, setScanning] = useState(false)
  const [activeJobId, setActiveJobId] = useState<number | null>(null)
  const [missingSummary, setMissingSummary] = useState<MissingDatesSummary | null>(null)
  const [showAllMissingDates, setShowAllMissingDates] = useState(false)
  const [copiedDates, setCopiedDates] = useState(false)

  // Issues State
  const [issues, setIssues] = useState<ScanIssue[]>([])
  const [issueFilter, setIssueFilter] = useState<'OPEN' | 'RESOLVED' | 'IGNORED' | ''>('OPEN')

  // Settings State
  const [config, setConfig] = useState<SystemConfig | null>(null)
  const [savingConfig, setSavingConfig] = useState(false)
  const [baselineTypeInput, setBaselineTypeInput] = useState<string>('BIRTHDAY')
  const [baselineDateInput, setBaselineDateInput] = useState('')
  const [baselineLabelInput, setBaselineLabelInput] = useState('')
  const [photoRootInput, setPhotoRootInput] = useState('')
  const [configSuccess, setConfigSuccess] = useState(false)

  // Backup State
  const [backups, setBackups] = useState<any[]>([])
  const [backupLoading, setBackupLoading] = useState(false)
  const [backupMsg, setBackupMsg] = useState<string | null>(null)

  // Fetch initial data based on activeTab
  const fetchScannerData = () => {
    api.getScanJobs().then((jobs) => {
      setScanJobs(jobs)
      const running = jobs.find((j) => j.status === 'RUNNING' || j.status === 'PENDING')
      if (running) {
        setScanning(true)
        setActiveJobId(running.id)
      } else {
        setScanning(false)
      }
    })
    api.getMissingDates().then(setMissingSummary).catch(() => {})
  }

  const handleCopyMissingDates = () => {
    if (!missingSummary || !missingSummary.missing_dates.length) return
    navigator.clipboard.writeText(missingSummary.missing_dates.join('\n'))
    setCopiedDates(true)
    setTimeout(() => setCopiedDates(false), 2000)
  }

  const fetchIssuesData = () => {
    api.getScanIssues(issueFilter || undefined).then(setIssues)
  }

  const fetchConfigData = () => {
    api.getSystemConfig().then((cfg) => {
      setConfig(cfg)
      setBaselineTypeInput(cfg.baseline_type || 'BIRTHDAY')
      setBaselineDateInput(cfg.baseline_date || cfg.birth_date || '')
      setBaselineLabelInput(cfg.baseline_label || '')
      setPhotoRootInput(cfg.photo_root || '')
    })
  }

  const fetchBackupsData = () => {
    api.listBackups().then(setBackups)
  }

  useEffect(() => {
    if (activeTab === 'scanner') fetchScannerData()
    else if (activeTab === 'issues') fetchIssuesData()
    else if (activeTab === 'settings') fetchConfigData()
    else if (activeTab === 'backup') fetchBackupsData()
  }, [activeTab, issueFilter])

  // Polling active scan job
  useEffect(() => {
    if (!scanning || !activeJobId) return

    const interval = setInterval(() => {
      api.getScanJob(activeJobId).then((job) => {
        if (job.status === 'COMPLETED' || job.status === 'FAILED' || job.status === 'CANCELLED') {
          setScanning(false)
          setActiveJobId(null)
          fetchScannerData()
        } else {
          setScanJobs((prev) => [job, ...prev.filter((j) => j.id !== job.id)])
        }
      })
    }, 1500)

    return () => clearInterval(interval)
  }, [scanning, activeJobId])

  // Trigger Scans
  const handleStartScan = async (type: 'full' | 'incremental') => {
    setScanning(true)
    try {
      const res = type === 'full' ? await api.triggerFullScan() : await api.triggerIncrementalScan()
      setActiveJobId(res.job_id)
      fetchScannerData()
    } catch (err: any) {
      alert(`启动扫描失败: ${err.message}`)
      setScanning(false)
    }
  }

  // Resolve / Ignore Issues
  const handleResolveIssue = async (id: number) => {
    try {
      await api.resolveIssue(id)
      fetchIssuesData()
    } catch (err: any) {
      alert(`操作失败: ${err.message}`)
    }
  }

  const handleIgnoreIssue = async (id: number) => {
    try {
      await api.ignoreIssue(id)
      fetchIssuesData()
    } catch (err: any) {
      alert(`操作失败: ${err.message}`)
    }
  }

  // Save Settings
  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault()
    setSavingConfig(true)
    setConfigSuccess(false)
    try {
      await api.updateSystemConfig({
        baseline_type: baselineTypeInput,
        baseline_date: baselineTypeInput !== 'NONE' ? (baselineDateInput.trim() || undefined) : undefined,
        baseline_label: baselineLabelInput.trim() || undefined,
        birth_date: baselineDateInput.trim() || undefined,
        photo_root: photoRootInput.trim() || undefined
      })
      setConfigSuccess(true)
      fetchConfigData()
    } catch (err: any) {
      alert(`更新设置失败: ${err.message}`)
    } finally {
      setSavingConfig(false)
    }
  }

  // Backup actions
  const handleCreateBackup = async () => {
    setBackupLoading(true)
    setBackupMsg(null)
    try {
      const res = await api.createBackup()
      setBackupMsg(`备份成功已生成快照: ${res.filename}`)
      fetchBackupsData()
    } catch (err: any) {
      alert(`备份失败: ${err.message}`)
    } finally {
      setBackupLoading(false)
    }
  }

  const handleRestoreBackup = async (filename: string) => {
    if (!window.confirm(`确定要从备份快照 ${filename} 恢复数据库吗？系统将自动在恢复前创建安全快照。`)) return
    setBackupLoading(true)
    try {
      await api.restoreBackup(filename)
      alert('数据库快照恢复成功！')
      fetchBackupsData()
    } catch (err: any) {
      alert(`恢复失败: ${err.message}`)
    } finally {
      setBackupLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 pb-24">
      {/* Management Header */}
      <div className="border-b border-[#EAE7E1] pb-6">
        <span className="text-[11px] uppercase tracking-widest text-[#8C7A6B] font-medium">
          Management Console
        </span>
        <h1 className="font-serif text-3xl font-medium text-[#1A1918] mt-1">
          档案后台维护
        </h1>
        <p className="text-xs text-[#7D756E] mt-1">
          维护原始照片索引、处理日期冲突与异常、调整系统配置与安全备份。
        </p>

        {/* Tab Switcher */}
        <div className="flex gap-2 pt-6 flex-wrap">
          <button
            onClick={() => setActiveTab('content')}
            className={`px-4 py-2 rounded-xl text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer ${
              activeTab === 'content'
                ? 'bg-[#2C2622] text-white shadow-xs'
                : 'bg-white border border-[#EAE7E1] text-[#6E665D] hover:bg-[#FAF8F5]'
            }`}
          >
            <ImagePlus className="w-3.5 h-3.5" />
            档案内容维护 (主图/时刻/回收站)
          </button>

          <button
            onClick={() => setActiveTab('scanner')}
            className={`px-4 py-2 rounded-xl text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer ${
              activeTab === 'scanner'
                ? 'bg-[#2C2622] text-white shadow-xs'
                : 'bg-white border border-[#EAE7E1] text-[#6E665D] hover:bg-[#FAF8F5]'
            }`}
          >
            <FolderSearch className="w-3.5 h-3.5" />
            照片扫描器
          </button>

          <button
            onClick={() => setActiveTab('issues')}
            className={`px-4 py-2 rounded-xl text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer ${
              activeTab === 'issues'
                ? 'bg-[#2C2622] text-white shadow-xs'
                : 'bg-white border border-[#EAE7E1] text-[#6E665D] hover:bg-[#FAF8F5]'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            异常排查
          </button>

          <button
            onClick={() => setActiveTab('settings')}
            className={`px-4 py-2 rounded-xl text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer ${
              activeTab === 'settings'
                ? 'bg-[#2C2622] text-white shadow-xs'
                : 'bg-white border border-[#EAE7E1] text-[#6E665D] hover:bg-[#FAF8F5]'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            系统配置
          </button>

          <button
            onClick={() => setActiveTab('backup')}
            className={`px-4 py-2 rounded-xl text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer ${
              activeTab === 'backup'
                ? 'bg-[#2C2622] text-white shadow-xs'
                : 'bg-white border border-[#EAE7E1] text-[#6E665D] hover:bg-[#FAF8F5]'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            数据备份与恢复
          </button>
        </div>
      </div>

      {/* Tab 0: Content Management (Upload / Replace / Delete / Trash) */}
      {activeTab === 'content' && (
        <ContentManagementTab initialDate={contentTargetDate} />
      )}

      {/* Tab 1: Scanner */}
      {activeTab === 'scanner' && (
        <div className="space-y-6">
          <div className="bg-white rounded-3xl border border-[#EAE7E1] p-6 sm:p-8 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h3 className="font-serif text-xl font-medium text-[#1A1918]">索引任务控制</h3>
              <p className="text-xs text-[#7D756E] mt-1 max-w-md">
                全量扫描将检查目录中的全部合法 yymmdd 照片；增量扫描重点排查变动项。
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => handleStartScan('incremental')}
                disabled={scanning}
                className="px-4 py-2.5 rounded-xl border border-[#D6CBBF] bg-white text-xs font-medium text-[#4A3E36] hover:bg-[#FAF8F5] transition-colors flex items-center gap-1.5 disabled:opacity-50"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                增量扫描
              </button>
              <button
                onClick={() => handleStartScan('full')}
                disabled={scanning}
                className="px-5 py-2.5 rounded-xl bg-[#2C2622] text-white text-xs font-medium hover:bg-[#3D352F] transition-colors flex items-center gap-1.5 disabled:opacity-50 shadow-sm"
              >
                {scanning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                全量扫描
              </button>
            </div>
          </div>

          {/* Missing Dates Continuity Alert / Result */}
          {missingSummary && (
            <div className={`rounded-3xl border p-6 sm:p-7 transition-all ${
              missingSummary.missing_count > 0
                ? 'bg-[#FDFBF7] border-[#E8DCCB]'
                : 'bg-[#F9FCF9] border-[#D4E8D4]'
            }`}>
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-2xl ${
                    missingSummary.missing_count > 0 ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                  }`}>
                    {missingSummary.missing_count > 0 ? (
                      <CalendarX2 className="w-5 h-5" />
                    ) : (
                      <CheckCircle2 className="w-5 h-5" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="font-serif text-lg font-medium text-[#1A1918]">
                        {missingSummary.missing_count > 0 ? '全量归档区间缺失照片提示' : '全量归档区间照片完整'}
                      </h4>
                      <span className={`text-[11px] px-2.5 py-0.5 rounded-full font-medium ${
                        missingSummary.missing_count > 0
                          ? 'bg-amber-50 text-amber-800 border border-amber-200'
                          : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      }`}>
                        {missingSummary.missing_count > 0
                          ? `缺少 ${missingSummary.missing_count} 天`
                          : '无缺失日期'}
                      </span>
                    </div>
                    <p className="text-xs text-[#7D756E] mt-0.5">
                      检测区间：最早照片 <strong className="font-mono text-[#3D352F]">{missingSummary.range_start || '-'}</strong> 至 最新照片 <strong className="font-mono text-[#3D352F]">{missingSummary.range_end || '-'}</strong>（共 {missingSummary.total_days} 天，已归档 {missingSummary.recorded_days} 天）
                      <span className="text-[#A89E94] ml-1.5 font-normal">
                        * 最新照片之后的日期为近期/未拍摄天数，不计入缺失
                      </span>
                    </p>
                  </div>
                </div>

                {missingSummary.missing_count > 0 && (
                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <button
                      onClick={handleCopyMissingDates}
                      className="px-3 py-1.5 rounded-xl border border-[#D6CBBF] bg-white text-xs font-medium text-[#4A3E36] hover:bg-[#FAF8F5] transition-colors flex items-center gap-1.5"
                      title="复制全部缺失日期清单"
                    >
                      {copiedDates ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                      {copiedDates ? '已复制日期' : '复制缺失日期'}
                    </button>
                    <button
                      onClick={() => setShowAllMissingDates(!showAllMissingDates)}
                      className="px-3 py-1.5 rounded-xl bg-[#2C2622] text-white text-xs font-medium hover:bg-[#3D352F] transition-colors flex items-center gap-1"
                    >
                      {showAllMissingDates ? '收起详情' : '展开具体日期'}
                      {showAllMissingDates ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                )}
              </div>

              {/* Missing Ranges Chips */}
              {missingSummary.missing_count > 0 && (
                <div className="mt-4 pt-4 border-t border-[#EAE1D3] space-y-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs text-[#8C7A6B] font-medium mr-1">
                      缺少日期区间:
                    </span>
                    {missingSummary.missing_ranges.map((rg, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-white border border-[#E0D4C3] text-xs font-mono text-[#4A3E36] shadow-2xs"
                      >
                        {rg.start === rg.end ? (
                          <>
                            <strong>{rg.start}</strong>
                            <span className="text-[10px] text-amber-700 bg-amber-50 px-1.5 py-0.2 rounded font-sans">
                              缺 1 天
                            </span>
                          </>
                        ) : (
                          <>
                            <strong>{rg.start}</strong> 至 <strong>{rg.end}</strong>
                            <span className="text-[10px] text-amber-700 bg-amber-50 px-1.5 py-0.2 rounded font-sans">
                              缺 {rg.count} 天
                            </span>
                          </>
                        )}
                      </span>
                    ))}
                  </div>

                  {/* Expanded All Missing Dates List */}
                  {showAllMissingDates && (
                    <div className="mt-3 p-4 bg-white/80 rounded-2xl border border-[#E5DACB] space-y-2">
                      <div className="flex justify-between items-center text-xs text-[#7D756E]">
                        <span>完整缺失日期清单（可将对应日期的照片以 yymmdd.jpg 放入目录重新全量扫描自动补录）：</span>
                        <span className="font-mono text-[11px]">共 {missingSummary.missing_dates.length} 个日期</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto pt-1">
                        {missingSummary.missing_dates.map((d) => (
                          <button
                            key={d}
                            onClick={() => {
                              setContentTargetDate(d)
                              setActiveTab('content')
                            }}
                            className="px-2 py-0.5 rounded-lg bg-[#FAF8F5] hover:bg-[#EFECE6] border border-[#EAE4DC] font-mono text-xs text-[#524C46] transition-colors cursor-pointer flex items-center gap-1 group"
                            title="点击前往内容维护面板为此日期补录主图/时刻"
                          >
                            <span>{d}</span>
                            <span className="text-[10px] text-[#8C7A6B] group-hover:underline">前往补录 &rarr;</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Scan Jobs History */}
          <div className="bg-white rounded-3xl border border-[#EAE7E1] overflow-hidden">
            <div className="px-6 py-4 border-b border-[#EAE7E1]">
              <h4 className="text-xs font-medium uppercase tracking-wider text-[#8C827A]">
                扫描历史记录
              </h4>
            </div>
            <div className="divide-y divide-[#F0EDE6]">
              {scanJobs.map((job) => (
                <div key={job.id} className="p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-[#1A1918]">
                        #{job.id} {job.scan_type}
                      </span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                        job.status === 'COMPLETED' ? 'bg-emerald-50 text-emerald-700' :
                        job.status === 'RUNNING' ? 'bg-blue-50 text-blue-700' :
                        job.status === 'FAILED' ? 'bg-red-50 text-red-700' : 'bg-gray-100 text-gray-700'
                      }`}>
                        {job.status}
                      </span>
                      {job.missing_info && job.missing_info.missing_count > 0 && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1">
                          <CalendarX2 className="w-2.5 h-2.5" />
                          区间缺 {job.missing_info.missing_count} 天
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-[#7D756E]">{job.message || '任务执行中...'}</p>
                    <p className="text-[10px] text-[#A8A199] font-mono">
                      开始: {job.started_at} {job.finished_at && `· 结束: ${job.finished_at}`}
                    </p>
                  </div>

                  <div className="flex items-center gap-6 text-xs text-[#524C46] bg-[#FCFBF8] px-4 py-2.5 rounded-xl border border-[#EFECE6]">
                    <div>
                      <span className="text-[#8C827A] block text-[10px]">扫描总数</span>
                      <strong className="font-mono">{job.total_files}</strong>
                    </div>
                    <div>
                      <span className="text-[#8C827A] block text-[10px]">成功归档</span>
                      <strong className="font-mono text-emerald-600">{job.success_count}</strong>
                    </div>
                    <div>
                      <span className="text-[#8C827A] block text-[10px]">冲突记录</span>
                      <strong className="font-mono text-amber-600">{job.conflict_count}</strong>
                    </div>
                    <div>
                      <span className="text-[#8C827A] block text-[10px]">格式/缺失异常</span>
                      <strong className="font-mono text-red-600">{job.error_count}</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Issues */}
      {activeTab === 'issues' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center bg-white p-4 rounded-2xl border border-[#EAE7E1]">
            <span className="text-xs font-medium text-[#7D756E]">
              当前筛选状态:
            </span>
            <div className="flex gap-2">
              {(['OPEN', 'RESOLVED', 'IGNORED', ''] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setIssueFilter(st)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                    issueFilter === st
                      ? 'bg-[#2C2622] text-white'
                      : 'bg-[#F2EFE9] text-[#6E665D] hover:text-[#1A1918]'
                  }`}
                >
                  {st === 'OPEN' ? '待处理' : st === 'RESOLVED' ? '已解决' : st === 'IGNORED' ? '已忽略' : '全部'}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-3xl border border-[#EAE7E1] overflow-hidden">
            {issues.length === 0 ? (
              <div className="p-16 text-center text-xs text-[#8C827A]">
                太棒了！当前没有任何异常记录。
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#FAF8F5] border-b border-[#EAE7E1] text-[#7D756E] uppercase font-medium">
                    <tr>
                      <th className="px-6 py-3">异常类型</th>
                      <th className="px-6 py-3">文件名</th>
                      <th className="px-6 py-3">相对路径</th>
                      <th className="px-6 py-3">解析日期</th>
                      <th className="px-6 py-3">详情说明</th>
                      <th className="px-6 py-3">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#F0EDE6] text-[#3D3833]">
                    {issues.map((iss) => (
                      <tr key={iss.id} className="hover:bg-[#FCFBF9]">
                        <td className="px-6 py-4 font-mono font-medium">
                          <span className={`px-2 py-0.5 rounded text-[10px] ${
                            iss.issue_type === 'DATE_CONFLICT' ? 'bg-amber-100 text-amber-800' :
                            iss.issue_type === 'FILE_MISSING' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {iss.issue_type}
                          </span>
                        </td>
                        <td className="px-6 py-4 font-mono">{iss.filename}</td>
                        <td className="px-6 py-4 text-[#7D756E] truncate max-w-xs">{iss.relative_path}</td>
                        <td className="px-6 py-4 font-mono">{iss.parsed_date || '-'}</td>
                        <td className="px-6 py-4 text-[#6B635B] max-w-sm">{iss.details || '-'}</td>
                        <td className="px-6 py-4 space-x-2">
                          {iss.status === 'OPEN' && (
                            <>
                              <button
                                onClick={() => handleResolveIssue(iss.id)}
                                className="text-emerald-600 hover:text-emerald-800 font-medium"
                              >
                                标为解决
                              </button>
                              <button
                                onClick={() => handleIgnoreIssue(iss.id)}
                                className="text-[#8C827A] hover:text-[#52443B]"
                              >
                                忽略
                              </button>
                            </>
                          )}
                          {iss.status !== 'OPEN' && (
                            <span className="text-[#A8A199]">{iss.status}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Settings */}
      {activeTab === 'settings' && config && (
        <div className="bg-white rounded-3xl border border-[#EAE7E1] p-8 max-w-2xl shadow-sm space-y-6">
          <div>
            <h3 className="font-serif text-xl font-medium text-[#1A1918]">系统参数与时光基准</h3>
            <p className="text-xs text-[#7D756E] mt-1">
              设置相册照片根目录，或配置生日、纪念日等纪年基准。
            </p>
          </div>

          {configSuccess && (
            <div className="p-3 bg-emerald-50 text-emerald-800 rounded-xl text-xs border border-emerald-200">
              设置已成功更新。
            </div>
          )}

          <form onSubmit={handleSaveConfig} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#7D756E] mb-1">
                时光纪年基准类型
              </label>
              <select
                value={baselineTypeInput}
                onChange={(e) => setBaselineTypeInput(e.target.value)}
                className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#DDD7CD] rounded-xl text-xs text-[#2C2A29] focus:outline-none focus:ring-1 focus:ring-[#8C7A6B]"
              >
                <option value="BIRTHDAY">生日（展示岁数、月份与天数，如 2 岁 3 个月 12 天）</option>
                <option value="ANNIVERSARY">纪念日（如相恋/结婚纪念日，展示相伴天数与周年）</option>
                <option value="START_DATE">记录起始日（展示记录开启第 N 天）</option>
                <option value="CUSTOM">自定义里程碑（可自由指定前缀与天数）</option>
                <option value="NONE">不启用基准日（仅展示自然日期）</option>
              </select>
            </div>

            {baselineTypeInput !== 'NONE' && (
              <>
                <div>
                  <label className="block text-xs font-medium text-[#7D756E] mb-1">
                    基准日期 (YYYY-MM-DD)
                  </label>
                  <input
                    type="date"
                    value={baselineDateInput}
                    onChange={(e) => setBaselineDateInput(e.target.value)}
                    className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#DDD7CD] rounded-xl text-xs text-[#2C2A29]"
                    required
                  />
                </div>

                {(baselineTypeInput === 'ANNIVERSARY' || baselineTypeInput === 'START_DATE' || baselineTypeInput === 'CUSTOM') && (
                  <div>
                    <label className="block text-xs font-medium text-[#7D756E] mb-1">
                      自定义显示前缀 (可选)
                    </label>
                    <input
                      type="text"
                      value={baselineLabelInput}
                      onChange={(e) => setBaselineLabelInput(e.target.value)}
                      placeholder={baselineTypeInput === 'ANNIVERSARY' ? '相伴 / 领证' : baselineTypeInput === 'START_DATE' ? '记录 / 摄影挑战' : '来到新家'}
                      className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#DDD7CD] rounded-xl text-xs text-[#2C2A29]"
                    />
                  </div>
                )}
              </>
            )}

            <div>
              <label className="block text-xs font-medium text-[#7D756E] mb-1">
                原始照片本地根目录
              </label>
              <input
                type="text"
                value={photoRootInput}
                onChange={(e) => setPhotoRootInput(e.target.value)}
                className="w-full px-3 py-2 bg-[#FAF8F5] border border-[#DDD7CD] rounded-xl text-xs text-[#2C2A29] font-mono"
                required
              />
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="submit"
                disabled={savingConfig}
                className="px-6 py-2.5 rounded-xl bg-[#2C2622] text-white text-xs font-medium hover:bg-[#3D352F] disabled:opacity-50 cursor-pointer"
              >
                {savingConfig ? '正在保存...' : '保存更改'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tab 4: Backup */}
      {activeTab === 'backup' && (
        <div className="space-y-6">
          <div className="bg-white rounded-3xl border border-[#EAE7E1] p-8 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h3 className="font-serif text-xl font-medium text-[#1A1918]">数据安全与元数据导出</h3>
              <p className="text-xs text-[#7D756E] mt-1 max-w-md">
                生成 SQLite 数据库原子快照，或导出全部归档元数据为标准 JSON 格式。
              </p>
            </div>
            <div className="flex gap-3">
              <a
                href={api.exportJsonUrl}
                download
                className="px-4 py-2.5 rounded-xl border border-[#D6CBBF] bg-white text-xs font-medium text-[#4A3E36] hover:bg-[#FAF8F5] transition-colors flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                导出元数据 JSON
              </a>
              <button
                onClick={handleCreateBackup}
                disabled={backupLoading}
                className="px-5 py-2.5 rounded-xl bg-[#2C2622] text-white text-xs font-medium hover:bg-[#3D352F] transition-colors flex items-center gap-1.5 disabled:opacity-50 shadow-sm"
              >
                {backupLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileCheck className="w-3.5 h-3.5" />}
                创建数据库快照
              </button>
            </div>
          </div>

          {backupMsg && (
            <div className="p-3 bg-emerald-50 text-emerald-800 rounded-xl text-xs border border-emerald-200">
              {backupMsg}
            </div>
          )}

          {/* Backup Snapshots List */}
          <div className="bg-white rounded-3xl border border-[#EAE7E1] overflow-hidden">
            <div className="px-6 py-4 border-b border-[#EAE7E1]">
              <h4 className="text-xs font-medium uppercase tracking-wider text-[#8C827A]">
                快照备份清单
              </h4>
            </div>
            <div className="divide-y divide-[#F0EDE6]">
              {backups.length === 0 ? (
                <div className="p-12 text-center text-xs text-[#8C827A]">
                  暂无快照备份。点击右上角“创建数据库快照”即可生成。
                </div>
              ) : (
                backups.map((b) => (
                  <div key={b.filename} className="p-4 sm:px-6 flex justify-between items-center">
                    <div>
                      <p className="text-xs font-mono font-medium text-[#1A1918]">{b.filename}</p>
                      <p className="text-[10px] text-[#8C827A]">
                        创建时间: {b.created_at} · 大小: {(b.size_bytes / 1024).toFixed(1)} KB
                      </p>
                    </div>
                    <button
                      onClick={() => handleRestoreBackup(b.filename)}
                      className="px-3 py-1.5 rounded-lg border border-[#DDD7CD] text-xs text-[#5C534B] hover:bg-[#FAF8F5]"
                    >
                      从此快照恢复
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
