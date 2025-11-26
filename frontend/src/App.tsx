import { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { FileUpload } from './components/FileUpload';
import { Player } from './components/Player';
import { createProject, startProcessing } from './api/client';
import { useWebSocket } from './hooks/useWebSocket';
import { Terminal, CheckCircle, Circle } from 'lucide-react';
import { clsx } from 'clsx';

interface ChunkData {
    index: number;
    isProcessed: boolean;
}

interface Message {
    type: 'status_update' | 'progress_update';
    status?: string;
    progress?: number;
    chunk_index?: number;
    project_id?: number;
    error?: string;
}

function App() {
  const [view, setView] = useState<'upload' | 'project'>('upload');
  const [projectId, setProjectId] = useState<number | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [chunks, setChunks] = useState<ChunkData[]>([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle');

  const lastMessage = useWebSocket() as Message | null;

  // Handle WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.type === 'status_update') {
      setStatus(lastMessage.status || 'unknown');
      if (lastMessage.progress !== undefined) {
        setProgress(lastMessage.progress);
      }
      setLogs(prev => [
        ...prev,
        `Status: ${lastMessage.status} (${lastMessage.progress}%)`
      ]);
    } else if (lastMessage.type === 'progress_update') {
      setProgress(lastMessage.progress || 0);

      if (lastMessage.chunk_index !== undefined) {
        setChunks(prev => {
          const newChunks = [...prev];
          if (!newChunks[lastMessage.chunk_index!]) {
            newChunks[lastMessage.chunk_index!] = {
              index: lastMessage.chunk_index!,
              isProcessed: true
            };
          } else {
            newChunks[lastMessage.chunk_index!].isProcessed = true;
          }
          return newChunks;
        });
        setLogs(prev => [...prev, `Processed chunk ${lastMessage.chunk_index}`]);
      }
    }
  }, [lastMessage]);

  const handleNewProject = useCallback(() => {
    setView('upload');
    setProjectId(null);
    setLogs([]);
    setChunks([]);
    setProgress(0);
    setStatus('idle');
  }, []);

  const handleUpload = useCallback(async (data: {
    text: File;
    audio: File | null;
    referenceVoicePath: string | null;
    useGpu: boolean;
    name: string;
  }) => {
    try {
      setLogs(prev => [...prev, "Uploading files..."]);

      const formData = new FormData();
      formData.append('name', data.name);
      formData.append('text_file', data.text);
      formData.append('use_gpu', String(data.useGpu));

      // Either upload audio file or use reference voice
      if (data.audio) {
        formData.append('voice_file', data.audio);
      } else if (data.referenceVoicePath) {
        formData.append('reference_voice_path', data.referenceVoicePath);
      }

      const res = await createProject(formData);
      setProjectId(res.project_id);
      setLogs(prev => [
        ...prev,
        `Project created: ${res.project_id}`,
        `Total chunks: ${res.total_chunks}`
      ]);

      // Initialize chunks
      setChunks(new Array(res.total_chunks).fill(null).map((_, i) => ({
        index: i,
        isProcessed: false
      })));

      setView('project');
      setStatus('processing');
      setProgress(0);

      setLogs(prev => [...prev, "Starting processing..."]);
      await startProcessing(res.project_id, data.useGpu);

    } catch (error) {
      console.error(error);
      setLogs(prev => [...prev, `Error: ${error instanceof Error ? error.message : 'Unknown error'}`]);
      setStatus('failed');
    }
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar - Fixed width, full height */}
      <Sidebar onNewProject={handleNewProject} />

      {/* Main Content Area - Flex-1, scrollable */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        <main className="flex-1 overflow-y-auto">
          <div className="min-h-full pb-32">
            {view === 'upload' ? (
              <div className="h-full flex items-center justify-center p-6">
                <FileUpload onUpload={handleUpload} />
              </div>
            ) : (
              <div className="p-8 h-full flex flex-col">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h1 className="text-3xl font-bold">Project View</h1>
                    <p className="text-slate-400">
                      ID: {projectId} • Status:{' '}
                      <span className="uppercase text-indigo-400">{status}</span>
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-indigo-400">
                      {progress.toFixed(1)}%
                    </p>
                    <p className="text-xs text-slate-400">Completed</p>
                  </div>
                </div>

                {/* Grid Layout for Chunks & Logs */}
                <div className="flex-1 grid grid-cols-3 gap-6 min-h-0">
                  {/* Chunks List */}
                  <div className="col-span-2 glass rounded-xl border border-white/10 p-4 overflow-hidden flex flex-col">
                    <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase tracking-wider">
                      Text Chunks
                    </h3>
                    <div className="flex-1 overflow-y-auto space-y-2 pr-2">
                      {chunks.map((chunk, idx) => (
                        <div
                          key={idx}
                          className={clsx(
                            'p-3 rounded-lg border flex items-center justify-between transition-colors',
                            chunk.isProcessed
                              ? 'bg-emerald-500/10 border-emerald-500/30'
                              : 'bg-slate-800/50 border-slate-700'
                          )}
                        >
                          <div className="flex items-center gap-3">
                            {chunk.isProcessed ? (
                              <CheckCircle className="w-5 h-5 text-emerald-500" />
                            ) : (
                              <Circle className="w-5 h-5 text-slate-500" />
                            )}
                            <span
                              className={clsx(
                                'text-sm',
                                chunk.isProcessed
                                  ? 'text-slate-100'
                                  : 'text-slate-400'
                              )}
                            >
                              Chunk #{idx + 1}
                            </span>
                          </div>
                          {chunk.isProcessed && (
                            <button className="text-xs bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 px-2 py-1 rounded transition-colors">
                              Play
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Logs Terminal */}
                  <div className="bg-[#0c0c0c] rounded-xl border border-slate-700 p-4 font-mono text-xs overflow-hidden flex flex-col">
                    <div className="flex items-center gap-2 text-slate-400 mb-2 border-b border-white/10 pb-2">
                      <Terminal className="w-4 h-4" />
                      <span>System Logs</span>
                    </div>
                    <div className="flex-1 overflow-y-auto space-y-1 text-slate-300">
                      {logs.map((log, i) => (
                        <div key={i}>
                          <span className="text-slate-500">
                            [{new Date().toLocaleTimeString()}]
                          </span>{' '}
                          {log}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>

        {/* Player - Fixed at bottom */}
        <Player />
      </div>
    </div>
  );
}

export default App;
