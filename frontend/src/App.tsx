import { useEffect, useState, useRef } from 'react'
import { Navbar, type NavTab } from './components/layout/Navbar'
import { HomePage } from './pages/HomePage'
import { CalendarPage } from './pages/CalendarPage'
import { TimelinePage } from './pages/TimelinePage'
import { HighlightsPage } from './pages/HighlightsPage'
import { CollectionsPage } from './pages/CollectionsPage'
import { ManagementPage } from './pages/ManagementPage'
import { SetupWizardPage } from './pages/SetupWizardPage'
import { PhotoDetailModal } from './components/photo/PhotoDetailModal'
import { api } from './services/api'
import type { SystemStatus } from './types/system'

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

          {currentTab === 'management' && (
            <div className="block">
              <ManagementPage />
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="border-t border-[#EAE7E1] bg-[#FBFBFA] py-8 text-center text-xs text-[#A8A199] shrink-0 mt-auto">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-2">
            <span>Growing Up · 家庭私有化数字成长档案系统</span>
            <span className="font-mono text-[11px]">
              {isManagementMode ? '● 管理模式运行中' : '○ 浏览模式'} · v2.0.0
            </span>
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
