import { useEffect, useState, useRef } from 'react'
import { Navbar, type NavTab } from './components/layout/Navbar'
import { HomePage } from './pages/HomePage'
import { CalendarPage } from './pages/CalendarPage'
import { TimelinePage } from './pages/TimelinePage'
import { HighlightsPage } from './pages/HighlightsPage'
import { CollectionsPage } from './pages/CollectionsPage'
import { MomentsPage } from './pages/MomentsPage'
import { ManagementPage } from './pages/ManagementPage'
import { SetupWizardPage } from './pages/SetupWizardPage'
import { PhotoDetailModal } from './components/photo/PhotoDetailModal'
import { api } from './services/api'
import type { SystemStatus } from './types/system'

const GithubIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
    <path
      fillRule="evenodd"
      d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
      clipRule="evenodd"
    />
  </svg>
)

export default function App() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [currentTab, setCurrentTab] = useState<NavTab>('home')
  const [isManagementMode, setIsManagementMode] = useState(false)
  const [selectedPhotoId, setSelectedPhotoId] = useState<number | null>(null)
  const [timelineTag, setTimelineTag] = useState<string | undefined>(undefined)
  const [visitedTabs, setVisitedTabs] = useState<Set<NavTab>>(() => new Set([currentTab]))
  const [refreshKey, setRefreshKey] = useState(0)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  const handleSelectTab = (tab: NavTab) => {
    if (tab === 'timeline') {
      setTimelineTag(undefined)
    }
    setCurrentTab(tab)
    setVisitedTabs((prev) => {
      const next = new Set(prev)
      next.add(tab)
      return next
    })
    scrollContainerRef.current?.scrollTo({ top: 0, behavior: 'instant' })
  }

  const handleSelectTag = (tagName: string) => {
    setTimelineTag(tagName)
    setCurrentTab('timeline')
    setVisitedTabs((prev) => {
      const next = new Set(prev)
      next.add('timeline')
      return next
    })
    setSelectedPhotoId(null)
    scrollContainerRef.current?.scrollTo({ top: 0, behavior: 'instant' })
  }

  const fetchStatus = () => {
    setLoading(true)
    api.getSystemStatus()
      .then((data) => {
        setSystemStatus(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error('Failed to get status:', err)
        setLoading(false)
      })
  }

  const handleUpdated = () => {
    fetchStatus()
    setRefreshKey((k) => k + 1)
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  if (loading && !systemStatus) {
    return (
      <div className="min-h-screen bg-[#FBFBFA] flex items-center justify-center text-xs tracking-wider text-[#8C827A] font-mono">
        GROWING UP · 正在载入时光档案...
      </div>
    )
  }

  if (systemStatus && !systemStatus.first_setup_completed) {
    return <SetupWizardPage onSetupComplete={fetchStatus} />
  }

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[#FBFBFA] text-[#2C2A29] font-sans selection:bg-[#EAE4DC]">
      <Navbar
        currentTab={currentTab}
        onSelectTab={handleSelectTab}
        isManagementMode={isManagementMode}
        onToggleManagementMode={() => {
          const nextMode = !isManagementMode
          setIsManagementMode(nextMode)
          if (!nextMode && currentTab === 'management') {
            handleSelectTab('home')
          }
        }}
      />

      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto overflow-x-hidden flex flex-col justify-between"
      >
        <main className="flex-1">
          {visitedTabs.has('home') && (
            <div className={currentTab === 'home' ? 'block' : 'hidden'}>
              <HomePage
                key={refreshKey}
                onNavigate={handleSelectTab}
                onOpenPhoto={(id) => setSelectedPhotoId(id)}
              />
            </div>
          )}

          {visitedTabs.has('calendar') && (
            <div className={currentTab === 'calendar' ? 'block' : 'hidden'}>
              <CalendarPage
                key={refreshKey}
                onOpenPhoto={(id) => setSelectedPhotoId(id)}
              />
            </div>
          )}

          {visitedTabs.has('timeline') && (
            <div className={currentTab === 'timeline' ? 'block' : 'hidden'}>
              <TimelinePage
                key={`${refreshKey}-${timelineTag || 'all'}`}
                initialTag={timelineTag}
                onOpenPhoto={(id) => setSelectedPhotoId(id)}
              />
            </div>
          )}

          {visitedTabs.has('highlights') && (
            <div className={currentTab === 'highlights' ? 'block' : 'hidden'}>
              <HighlightsPage
                key={refreshKey}
                onOpenPhoto={(id) => setSelectedPhotoId(id)}
              />
            </div>
          )}

          {visitedTabs.has('collections') && (
            <div className={currentTab === 'collections' ? 'block' : 'hidden'}>
              <CollectionsPage
                key={refreshKey}
                onOpenPhoto={(id) => setSelectedPhotoId(id)}
                isManagementMode={isManagementMode}
              />
            </div>
          )}

          {visitedTabs.has('moments') && (
            <div className={currentTab === 'moments' ? 'block' : 'hidden'}>
              <MomentsPage
                key={refreshKey}
                onOpenPhoto={(id) => setSelectedPhotoId(id)}
              />
            </div>
          )}

          {currentTab === 'management' && (
            <div className="block">
              <ManagementPage />
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="border-t border-[#EAE7E1] bg-[#FBFBFA] py-8 text-center text-xs text-[#A8A199] shrink-0 mt-auto">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-3">
            <div className="flex items-center gap-2.5 flex-wrap justify-center sm:justify-start">
              <span className="font-medium text-[#6B5E54]">拾光记 · 私有化家庭时光画册与岁月档案系统</span>
              <span className="text-[#DDD7CD] hidden sm:inline">|</span>
              <a
                href="https://github.com/shywei/TimeGallery"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-[#7D756E] hover:text-[#1A1918] transition-colors group cursor-pointer"
                title="前往 GitHub 查看 TimeGallery 开源仓库"
              >
                <GithubIcon className="w-3.5 h-3.5 text-[#8C827A] group-hover:text-[#1A1918] transition-colors" />
                <span className="font-mono text-[11px] underline decoration-[#DDD7CD] underline-offset-4 group-hover:decoration-[#1A1918]">
                  GitHub / TimeGallery
                </span>
              </a>
            </div>

            <div className="flex items-center gap-3">
              <span className="font-mono text-[11px] text-[#8C827A]">
                {isManagementMode ? '● 管理模式运行中' : '○ 浏览模式'} · v1.0.0
              </span>
            </div>
          </div>
        </footer>
      </div>

      {/* Global Photo Detail Modal */}
      {selectedPhotoId !== null && (
        <PhotoDetailModal
          photoId={selectedPhotoId}
          isManagementMode={isManagementMode}
          onClose={() => setSelectedPhotoId(null)}
          onUpdated={handleUpdated}
          onSelectPhoto={(id) => setSelectedPhotoId(id)}
          onSelectTag={handleSelectTag}
        />
      )}
    </div>
  )
}
