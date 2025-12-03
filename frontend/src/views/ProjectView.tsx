import { useState } from 'react';
import { Player } from '../components/Player';
import { useProjectStatus } from '../hooks/useProjectStatus';
import { Terminal, CheckCircle, Circle } from 'lucide-react';
import { clsx } from 'clsx';

interface ProjectViewProps {
    projectId: number;
}

// Helper to get API base URL
const getApiBase = () => {
    if (window.location.hostname === 'localhost') {
        return 'http://localhost:8000/api';
    }
    const protocol = window.location.protocol;
    const host = window.location.hostname.replace('4173', '8000');
    return `${protocol}//${host}/api`;
};

export const ProjectView = ({ projectId }: ProjectViewProps) => {
    const { status, progress, chunks, logs, processingStartTime, estimatedEndTime } = useProjectStatus(projectId);
    const [currentAudioUrl, setCurrentAudioUrl] = useState<string | null>(null);
    const [currentChunkIndex, setCurrentChunkIndex] = useState<number | null>(null);

    const handlePlayChunk = (chunkIndex: number) => {
        if (status === 'completed') {
            handlePlayFinal();
            return;
        }
        const audioUrl = `${getApiBase()}/audio/chunk/${projectId}/${chunkIndex}`;
        setCurrentAudioUrl(audioUrl);
        setCurrentChunkIndex(chunkIndex);
    };

    const handlePlayFinal = () => {
        const audioUrl = `${getApiBase()}/audio/download/${projectId}`;
        setCurrentAudioUrl(audioUrl);
        setCurrentChunkIndex(null);
    };

    const handleNextChunk = () => {
        if (currentChunkIndex === null) return;
        const nextIndex = currentChunkIndex + 1;
        if (nextIndex < chunks.length && chunks[nextIndex]?.isProcessed) {
            handlePlayChunk(nextIndex);
        }
    };

    const handlePreviousChunk = () => {
        if (currentChunkIndex === null) return;
        const prevIndex = currentChunkIndex - 1;
        if (prevIndex >= 0 && chunks[prevIndex]?.isProcessed) {
            handlePlayChunk(prevIndex);
        }
    };

    return (
        <div className="flex flex-col h-full overflow-hidden">
            <div className="flex-1 overflow-y-auto p-8 pb-32">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-100">Project View</h1>
                        <p className="text-slate-400">
                            ID: {projectId} • Status:{' '}
                            <span className={clsx(
                                "uppercase font-semibold",
                                status === 'merging' ? 'text-purple-400' :
                                    status === 'processing' ? 'text-indigo-400' :
                                        status === 'completed' ? 'text-emerald-400' :
                                            status === 'failed' ? 'text-red-400' : 'text-slate-400'
                            )}>
                                {status === 'merging' ? 'Merging' : status}
                            </span>
                        </p>
                    </div>
                    <div className="flex items-center gap-4">
                        {status === 'completed' && (
                            <button
                                onClick={handlePlayFinal}
                                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors text-sm font-semibold shadow-lg shadow-indigo-500/20"
                            >
                                Play Final Audio (MP3)
                            </button>
                        )}
                        {(status === 'processing' || status === 'merging') && (
                            <div className="text-right">
                                {processingStartTime ? (
                                    <>
                                        <p className="text-xs text-slate-400">
                                            Started: {processingStartTime.toLocaleTimeString()}
                                        </p>
                                        {estimatedEndTime && (
                                            <p className="text-xs text-emerald-400">
                                                Est. finish: {estimatedEndTime.toLocaleTimeString()}
                                            </p>
                                        )}
                                        {progress > 0 && (
                                            <p className="text-xs text-slate-500 mt-1">
                                                Elapsed: {Math.floor((Date.now() - processingStartTime.getTime()) / 1000 / 60)} min
                                            </p>
                                        )}
                                    </>
                                ) : (
                                    <p className="text-xs text-slate-500">
                                        {status === 'merging' ? 'Merging...' : 'Processing...'}
                                    </p>
                                )}
                            </div>
                        )}
                        <div className="text-right">
                            <p className="text-2xl font-bold text-indigo-400">
                                {progress.toFixed(1)}%
                            </p>
                            <p className="text-xs text-slate-400">Completed</p>
                        </div>
                    </div>
                </div>

                {/* Grid Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Chunks List */}
                    <div className="lg:col-span-2 bg-slate-900/50 rounded-xl border border-white/10 p-4 flex flex-col h-[500px]">
                        <h3 className="text-sm font-semibold text-slate-400 mb-4 uppercase tracking-wider">
                            Text Chunks
                        </h3>
                        <div className="flex-1 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                            {chunks.map((chunk, idx) => (
                                <div
                                    key={idx}
                                    className={clsx(
                                        'p-3 rounded-lg border flex items-center justify-between transition-all duration-200',
                                        chunk.isProcessed
                                            ? 'bg-emerald-500/5 border-emerald-500/20 hover:bg-emerald-500/10'
                                            : 'bg-slate-800/30 border-slate-700',
                                        currentChunkIndex === idx && 'ring-1 ring-indigo-500 bg-indigo-500/10'
                                    )}
                                >
                                    <div className="flex items-center gap-3">
                                        {chunk.isProcessed ? (
                                            <CheckCircle className="w-5 h-5 text-emerald-500" />
                                        ) : (
                                            <Circle className="w-5 h-5 text-slate-600" />
                                        )}
                                        <span
                                            className={clsx(
                                                'text-sm font-medium',
                                                chunk.isProcessed
                                                    ? 'text-slate-200'
                                                    : 'text-slate-500'
                                            )}
                                        >
                                            Chunk #{idx + 1}
                                        </span>
                                    </div>
                                    {chunk.isProcessed && status !== 'completed' && (
                                        <button
                                            onClick={() => handlePlayChunk(idx)}
                                            className={clsx(
                                                'text-xs px-3 py-1.5 rounded transition-colors font-medium',
                                                currentChunkIndex === idx
                                                    ? 'bg-indigo-500 text-white'
                                                    : 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400'
                                            )}
                                        >
                                            {currentChunkIndex === idx ? 'Playing' : 'Play'}
                                        </button>
                                    )}
                                </div>
                            ))}
                            {chunks.length === 0 && (
                                <div className="text-center text-slate-500 py-10">
                                    No chunks available yet.
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Logs Terminal */}
                    <div className="bg-[#0c0c0c] rounded-xl border border-slate-800 p-4 font-mono text-xs flex flex-col h-[500px]">
                        <div className="flex items-center gap-2 text-slate-400 mb-2 border-b border-white/5 pb-2">
                            <Terminal className="w-4 h-4" />
                            <span>System Logs</span>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-1 text-slate-300 custom-scrollbar">
                            {logs.map((log, i) => (
                                <div key={i} className="break-words">
                                    <span className="text-slate-600 mr-2">
                                        [{log.timestamp.toLocaleTimeString()}]
                                    </span>
                                    {log.message}
                                </div>
                            ))}
                            {logs.length === 0 && (
                                <div className="text-slate-700 italic">Waiting for logs...</div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Player - Fixed at bottom */}
            <Player
                audioUrl={currentAudioUrl}
                projectId={projectId}
                onNext={handleNextChunk}
                onPrevious={handlePreviousChunk}
            />
        </div>
    );
};
