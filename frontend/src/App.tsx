import { useState, useCallback, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { UploadView } from './views/UploadView';
import { ProjectView } from './views/ProjectView';
import { checkBackendHealth } from './api/client';
import { Loader2 } from 'lucide-react';

function App() {
  const [view, setView] = useState<'upload' | 'project'>('upload');
  const [currentProjectId, setCurrentProjectId] = useState<number | null>(null);
  const [checking, setChecking] = useState(true);

  // Backend health check on mount
  useEffect(() => {
    let retryCount = 0;
    const maxRetries = 10;

    const checkBackend = async () => {
      const isHealthy = await checkBackendHealth();

      if (isHealthy) {
        setChecking(false);
      } else if (retryCount < maxRetries) {
        retryCount++;
        console.log(`Backend not ready, retrying... (${retryCount}/${maxRetries})`);
        setTimeout(checkBackend, 1000); // Retry after 1 second
      } else {
        setChecking(false); // Give up and show UI anyway
        console.warn('Backend health check failed, proceeding anyway...');
      }
    };

    checkBackend();
  }, []);

  const handleNewProject = useCallback(() => {
    setView('upload');
    setCurrentProjectId(null);
  }, []);

  const handleProjectClick = useCallback((id: number) => {
    setCurrentProjectId(id);
    setView('project');
  }, []);

  const handleProjectCreated = useCallback((id: number) => {
    setCurrentProjectId(id);
    setView('project');
  }, []);

  // Show loading while checking backend
  if (checking) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto" />
          <div className="space-y-2">
            <p className="text-lg font-semibold text-foreground">
              Connecting to Backend...
            </p>
            <p className="text-sm text-muted-foreground">
              This usually takes a few seconds
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      {/* Sidebar - Fixed width, full height */}
      <Sidebar
        onNewProject={handleNewProject}
        onProjectClick={handleProjectClick}
        currentProjectId={currentProjectId}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden relative">
        <main className="flex-1 h-full overflow-hidden">
          {view === 'upload' ? (
            <UploadView onProjectCreated={handleProjectCreated} />
          ) : (
            currentProjectId && <ProjectView projectId={currentProjectId} />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
