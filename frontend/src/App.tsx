import { useState, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { UploadView } from './views/UploadView';
import { ProjectView } from './views/ProjectView';

function App() {
  const [view, setView] = useState<'upload' | 'project'>('upload');
  const [currentProjectId, setCurrentProjectId] = useState<number | null>(null);

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

  return (
    <div className="flex h-screen overflow-hidden bg-[#0a0a0a] text-slate-200">
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
