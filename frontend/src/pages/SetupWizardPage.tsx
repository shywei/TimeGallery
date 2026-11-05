import React, { useState } from 'react'
import { Calendar, Folder, Sparkles, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'

interface SetupWizardPageProps {
  onSetupComplete: () => void
}

export const SetupWizardPage: React.FC<SetupWizardPageProps> = ({ onSetupComplete }) => {
  const [baselineType, setBaselineType] = useState('BIRTHDAY')
  const [baselineDate, setBaselineDate] = useState('')
  const [baselineLabel, setBaselineLabel] = useState('')
  const [photoRoot, setPhotoRoot] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [step, setStep] = useState<'form' | 'scanning' | 'done'>('form')
  const [scanMessage, setScanMessage] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (baselineType !== 'NONE' && !baselineDate) {
      setError('请选择或输入基准日期')
      return
    }

    if (!photoRoot.trim()) {
      setError('请输入本地原始照片存放目录路径')
      return
    }

    setLoading(true)

    try {
      // 1. Submit Setup
      const setupRes = await fetch('/api/system/setup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          baseline_type: baselineType,
          baseline_date: baselineDate || undefined,
          baseline_label: baselineLabel || undefined,
          birth_date: baselineDate || undefined,
          photo_root: photoRoot.trim()
        })
      })

      if (!setupRes.ok) {
        const data = await setupRes.json().catch(() => ({}))
        throw new Error(data.detail || data.message || `设置失败 (${setupRes.status})`)
      }

      // 2. Trigger Initial Scan
      setStep('scanning')
      setScanMessage('正在启动照片目录初始全量索引...')

      const scanRes = await fetch('/api/scanner/full-scan', { method: 'POST' })
      if (!scanRes.ok) {
        setScanMessage('向导配置成功，照片后台扫描已就绪。')
      } else {
        setScanMessage('初始全量索引已启动，后台正在读取每日照片...')
      }

      setStep('done')
    } catch (err: any) {
      setError(err.message || '初始化过程中发生错误，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#FBFBFA] flex flex-col justify-center items-center px-4 py-12">
      <div className="w-full max-w-xl bg-white border border-[#EAE7E1] rounded-3xl shadow-sm p-8 sm:p-12 relative overflow-hidden">
        {/* Top Accent bar */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-[#D4C7B8] via-[#8C7A6B] to-[#4A3E36]" />

        <div className="text-center mb-8">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#F5F2EB] text-[#7A6B5D] text-xs font-medium tracking-wide uppercase mb-3">
            <Sparkles className="w-3.5 h-3.5" /> 首次初始化向导
          </span>
          <h1 className="text-3xl font-serif text-[#1C1A19] font-medium tracking-tight">
            欢迎来到 拾光记
          </h1>
          <p className="text-sm text-[#7D756E] mt-2 max-w-md mx-auto leading-relaxed">
            为您与珍爱的人建立专属时光画册。请配置基础信息以开始归档。
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50/80 border border-red-200/60 flex items-start gap-3 text-red-700 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-red-500" />
            <div>
              <p className="font-medium">初始化失败</p>
              <p className="text-xs text-red-600 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {step === 'form' && (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-xs uppercase font-medium text-[#7D756E] tracking-wider mb-2">
                1. 纪年基准类型 (Milestone Baseline)
              </label>
              <select
                value={baselineType}
                onChange={(e) => setBaselineType(e.target.value)}
                className="w-full px-4 py-3 bg-[#FAF8F5] border border-[#E5E0D8] rounded-xl text-sm text-[#2C2A29] focus:outline-none focus:ring-2 focus:ring-[#8C7A6B]/30 focus:border-[#8C7A6B] transition-colors"
              >
                <option value="BIRTHDAY">生日（展示岁数、月份与天数，如 2 岁 3 个月 12 天）</option>
                <option value="ANNIVERSARY">纪念日（如相恋/结婚纪念日，展示相伴天数与周年）</option>
                <option value="START_DATE">记录起始日（展示记录开启第 N 天）</option>
                <option value="CUSTOM">自定义里程碑（可自由指定前缀与天数）</option>
                <option value="NONE">不启用基准日（仅展示自然日期）</option>
              </select>
            </div>

            {baselineType !== 'NONE' && (
              <>
                <div>
                  <label className="block text-xs uppercase font-medium text-[#7D756E] tracking-wider mb-2">
                    2. 基准日期 (Baseline Date)
                  </label>
                  <div className="relative">
                    <input
                      type="date"
                      value={baselineDate}
                      onChange={(e) => setBaselineDate(e.target.value)}
                      className="w-full px-4 py-3 bg-[#FAF8F5] border border-[#E5E0D8] rounded-xl text-sm text-[#2C2A29] focus:outline-none focus:ring-2 focus:ring-[#8C7A6B]/30 focus:border-[#8C7A6B] transition-colors"
                      placeholder="YYYY-MM-DD"
                      required
                    />
                    <Calendar className="w-4 h-4 text-[#A8A199] absolute right-3.5 top-3.5 pointer-events-none" />
                  </div>
                  <p className="text-xs text-[#A8A199] mt-1.5">
                    用于精准计算照片拍摄时的相对时间跨度与岁月里程碑。
                  </p>
                </div>

                {(baselineType === 'ANNIVERSARY' || baselineType === 'START_DATE' || baselineType === 'CUSTOM') && (
                  <div>
                    <label className="block text-xs uppercase font-medium text-[#7D756E] tracking-wider mb-2">
                      自定义显示前缀 (可选)
                    </label>
                    <input
                      type="text"
                      value={baselineLabel}
                      onChange={(e) => setBaselineLabel(e.target.value)}
                      placeholder={baselineType === 'ANNIVERSARY' ? '相伴 / 领证' : baselineType === 'START_DATE' ? '记录' : '来到新家'}
                      className="w-full px-4 py-3 bg-[#FAF8F5] border border-[#E5E0D8] rounded-xl text-sm text-[#2C2A29] focus:outline-none focus:ring-2 focus:ring-[#8C7A6B]/30 focus:border-[#8C7A6B] transition-colors"
                    />
                  </div>
                )}
              </>
            )}

            <div>
              <label className="block text-xs uppercase font-medium text-[#7D756E] tracking-wider mb-2">
                {baselineType !== 'NONE' ? '3.' : '2.'} 原始照片本地根目录 (Photo Root Directory)
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={photoRoot}
                  onChange={(e) => setPhotoRoot(e.target.value)}
                  className="w-full px-4 py-3 bg-[#FAF8F5] border border-[#E5E0D8] rounded-xl text-sm text-[#2C2A29] focus:outline-none focus:ring-2 focus:ring-[#8C7A6B]/30 focus:border-[#8C7A6B] transition-colors font-mono"
                  placeholder="例如: D:\photos 或 C:\Users\YourName\Pictures\GrowingUp"
                  required
                />
                <Folder className="w-4 h-4 text-[#A8A199] absolute right-3.5 top-3.5 pointer-events-none" />
              </div>
              <div className="text-xs text-[#8C827A] mt-2 space-y-1 bg-[#F5F2EC] p-3 rounded-lg border border-[#EAE5DC]">
                <p className="font-medium text-[#5C534B]">★ 文件规范与安全保证：</p>
                <p>• 照片文件采用六位数字 <code className="bg-white px-1.5 py-0.5 rounded border border-[#DDD7CD] text-[#2C2A29]">yymmdd.jpg</code> 命名（如 <code className="text-[#2C2A29]">241103.jpg</code> 代表 2024年11月03日）。</p>
                <p>• <strong>支持多硬盘/多盘符相册</strong>：在此配置首个目录，进入系统后可在管理设置中随时追加更多本地或移动硬盘目录。</p>
                <p>• 日常浏览与扫描期间，原始照片目录始终保持<strong>只读</strong>，安全可靠。</p>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 px-6 rounded-xl bg-[#2C2622] text-[#F7F5F0] font-medium text-sm hover:bg-[#3D352F] active:scale-[0.99] transition-all flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  正在保存并验证目录...
                </>
              ) : (
                '完成初始化并开始探索'
              )}
            </button>
          </form>
        )}

        {step === 'done' && (
          <div className="text-center py-6 space-y-4">
            <CheckCircle className="w-14 h-14 text-emerald-600 mx-auto" />
            <h3 className="text-xl font-serif font-medium text-[#1C1A19]">初始化已成功完成</h3>
            <p className="text-sm text-[#6B635B] max-w-sm mx-auto">
              {scanMessage}
            </p>
            <div className="pt-4">
              <button
                onClick={onSetupComplete}
                className="py-3 px-8 rounded-xl bg-[#2C2622] text-white text-sm font-medium hover:bg-[#3D352F] transition-colors"
              >
                进入拾光记
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
