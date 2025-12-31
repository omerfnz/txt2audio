import { useState, useEffect } from 'react';
import { Player } from '../components/Player';
import { useProjectStatus } from '../hooks/useProjectStatus';
import { Terminal, CheckCircle, Circle, Clock, Zap, Download } from 'lucide-react';
import { cancelProcessing, resumeProject, getApiBase, getTimelapse } from '../api/client';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ChapterSidebar } from '@/components/ChapterSidebar';

interface ProjectViewProps {
    projectId: number;
}

const formatDuration = (ms: number) => {
    if (ms < 0) ms = 0;
    const seconds = Math.floor((ms / 1000) % 60);
    const minutes = Math.floor((ms / (1000 * 60)) % 60);
    const hours = Math.floor(ms / (1000 * 60 * 60));

    if (hours > 0) return `${hours}h ${minutes}m ${seconds}s`;
    if (minutes > 0) return `${minutes}m ${seconds}s`;
    return `${seconds}s`;
};

export const ProjectView = ({ projectId }: ProjectViewProps) => {
    const { status, progress, chunks, logs, processingStartTime, estimatedEndTime, speed } = useProjectStatus(projectId);
    const [currentAudioUrl, setCurrentAudioUrl] = useState<string | null>(null);
    const [currentChunkIndex, setCurrentChunkIndex] = useState<number | null>(null);
    const [cancelLoading, setCancelLoading] = useState(false);
    const [resumeLoading, setResumeLoading] = useState(false);
    const [now, setNow] = useState(Date.now());
    const [timelapseLoading, setTimelapseLoading] = useState(false);

    // Update 'now' every second for real-time elapsed/remaining updates
    useEffect(() => {
        const interval = setInterval(() => setNow(Date.now()), 1000);
        return () => clearInterval(interval);
    }, []);

    // Check if project can be resumed
    const canResume = status === 'cancelled' || status === 'failed' || status === 'created';

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
        const audioUrl = `${getApiBase()}/audio/stream/${projectId}`;
        setCurrentAudioUrl(audioUrl);
        setCurrentChunkIndex(null);
    };

    const handleCancel = async () => {
        try {
            setCancelLoading(true);
            await cancelProcessing(projectId);
        } catch (error) {
            console.error('Cancel processing failed:', error);
        } finally {
            setCancelLoading(false);
        }
    };

    const handleResume = async () => {
        try {
            setResumeLoading(true);
            const result = await resumeProject(projectId, true);
            console.log('Resume started:', result);
        } catch (error) {
            console.error('Resume processing failed:', error);
            alert(error instanceof Error ? error.message : 'Resume failed. Please try again.');
        } finally {
            setResumeLoading(false);
        }
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

    const handleChapterClick = (chunkIndex: number) => {
        // Scroll to chunk in the list (wait a bit for DOM to be ready)
        setTimeout(() => {
            const chunkElement = document.getElementById(`chunk-${chunkIndex}`);
            if (chunkElement) {
                chunkElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                // Highlight the chunk briefly
                chunkElement.classList.add('ring-2', 'ring-primary');
                setTimeout(() => {
                    chunkElement.classList.remove('ring-2', 'ring-primary');
                }, 2000);
            }
        }, 100);
        
        // Also play the chunk if it's processed
        if (chunks[chunkIndex]?.isProcessed) {
            handlePlayChunk(chunkIndex);
        } else {
            // Show a message if chunk is not processed yet
            console.log(`Chunk ${chunkIndex} is not processed yet`);
        }
    };

    const handleExportTimelapse = async () => {
        try {
            setTimelapseLoading(true);
            const response = await getTimelapse(projectId);
            
            if (response.timelapse) {
                // Copy to clipboard
                await navigator.clipboard.writeText(response.timelapse);
                // Show toast notification instead of alert
                if (window.toast) {
                    window.toast.success('YouTube Timelapse kopyalandı!', {
                        description: 'Video açıklamasına yapıştırabilirsiniz.',
                    });
                } else {
                    alert('YouTube Timelapse kopyalandı!\n\nVideo açıklamasına yapıştırabilirsiniz.\n\nFormat:\n0:00 Chapter 1\n15:32 Chapter 2\n...');
                }
            } else {
                alert(response.message || 'No timelapse available');
            }
        } catch (error) {
            console.error('Failed to export timelapse:', error);
            alert('Failed to export timelapse. Please try again.');
        } finally {
            setTimelapseLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full overflow-hidden">
            <div className="flex-1 overflow-y-auto p-8 pb-32">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-foreground">Project View</h1>
                        <div className="text-muted-foreground flex items-center gap-2 mt-1">
                            <span>ID: {projectId} • Status:</span>
                            <Badge
                                variant={
                                    status === 'completed' ? 'default' :
                                        status === 'failed' ? 'destructive' :
                                            status === 'processing' || status === 'merging' ? 'secondary' : 'outline'
                                }
                                className="uppercase font-bold tracking-wider text-[10px]"
                            >
                                {status === 'merging' ? 'Merging' : status}
                            </Badge>
                        </div>
                    </div>

                    <div className="flex items-center gap-6">
                        {/* Improved Timing Container */}
                        {(status === 'processing' || status === 'merging' || status === 'mastering') && (
                            <div className="flex items-center gap-4 bg-muted/30 p-3 rounded-lg border border-border/50">
                                <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-[10px] uppercase font-bold">
                                    {processingStartTime && (
                                        <>
                                            <div className="flex items-center gap-1 text-muted-foreground">
                                                <Clock className="w-3 h-3" /> Elapsed:
                                            </div>
                                            <span className="text-foreground tabular-nums">
                                                {formatDuration(now - processingStartTime.getTime())}
                                            </span>
                                        </>
                                    )}
                                    {estimatedEndTime && (
                                        <>
                                            <div className="flex items-center gap-1 text-primary/70">
                                                <Clock className="w-3 h-3" /> Remaining:
                                            </div>
                                            <span className="text-primary tabular-nums">
                                                {formatDuration(estimatedEndTime.getTime() - now)}
                                            </span>
                                            
                                            <div className="flex items-center gap-1 text-primary/70">
                                                <Zap className="w-3 h-3" /> Est. Finish:
                                            </div>
                                            <span className="text-primary tabular-nums">
                                                {estimatedEndTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                            </span>
                                        </>
                                    )}
                                    {speed && (
                                         <>
                                            <div className="flex items-center gap-1 text-muted-foreground">
                                                <Zap className="w-3 h-3" /> Speed:
                                            </div>
                                            <span className="text-foreground">
                                                {speed.toFixed(1)} <span className="text-[8px]">CH/MIN</span>
                                            </span>
                                         </>
                                    )}
                                </div>
                                <div className="h-8 w-px bg-border/50 mx-1" />
                                <Button
                                    onClick={handleCancel}
                                    disabled={cancelLoading}
                                    variant="destructive"
                                    size="sm"
                                    className="h-8 px-3 text-[10px] font-bold uppercase"
                                >
                                    {cancelLoading ? '...' : 'Cancel'}
                                </Button>
                            </div>
                        )}

                        {status === 'completed' && (
                            <>
                                <Button onClick={handlePlayFinal} size="sm" className="bg-primary hover:bg-primary/90 font-bold uppercase tracking-wider text-[11px]">
                                    Play Final Audio (MP3)
                                </Button>
                                <Button 
                                    onClick={handleExportTimelapse} 
                                    size="sm" 
                                    variant="outline"
                                    className="font-bold uppercase tracking-wider text-[11px]"
                                    disabled={timelapseLoading}
                                >
                                    {timelapseLoading ? (
                                        <>Loading...</>
                                    ) : (
                                        <>
                                            <Download className="w-3 h-3 mr-1" />
                                            Export Timelapse
                                        </>
                                    )}
                                </Button>
                            </>
                        )}

                        {canResume && (
                            <Button
                                onClick={handleResume}
                                disabled={resumeLoading}
                                variant="default"
                                size="sm"
                                className="bg-green-600 hover:bg-green-700 font-bold uppercase tracking-wider text-[11px]"
                            >
                                {resumeLoading ? 'Resuming…' : '▶ Resume Processing'}
                            </Button>
                        )}

                        <div className="flex flex-col items-end min-w-32">
                             <div className="flex items-baseline gap-1">
                                <span className="text-3xl font-black text-primary tabular-nums">
                                    {progress.toFixed(1)}
                                </span>
                                <span className="text-xs font-bold text-primary/70">%</span>
                             </div>
                            <Progress value={progress} className="w-32 h-1.5 mt-1" />
                        </div>
                    </div>
                </div>

                {/* Grid Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Chunks List */}
                    <Card className="lg:col-span-2 flex flex-col h-[500px] border-none bg-background/50 shadow-xl ring-1 ring-border/50">
                        <CardHeader className="bg-muted/30 border-b border-border/50 py-3">
                            <CardTitle className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground flex items-center justify-between">
                                <span>Text Chunks</span>
                                <Badge variant="outline" className="text-[9px]">{chunks.length} Total</Badge>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 overflow-hidden p-4 pt-0">
                            <ScrollArea className="h-full">
                                <div className="space-y-2 pr-4 py-4">
                                    {chunks.map((chunk, idx) => {
                                        return (
                                            <Card
                                                id={`chunk-${idx}`}
                                                key={idx}
                                                className={cn(
                                                    'p-3 flex items-center justify-between transition-all duration-250 border-none',
                                                    chunk.isProcessed
                                                        ? 'bg-primary/5 hover:bg-primary/10 ring-1 ring-primary/20'
                                                        : 'bg-muted/20 ring-1 ring-border/30',
                                                    currentChunkIndex === idx && 'ring-2 ring-primary bg-primary/10'
                                                )}
                                            >
                                                <div className="flex flex-col gap-1 flex-1 mr-4">
                                                    <div className="flex items-center gap-3">
                                                        {chunk.isProcessed ? (
                                                            <CheckCircle className="w-4 h-4 text-primary shrink-0" />
                                                        ) : (
                                                            <Circle className="w-4 h-4 text-muted-foreground/30 shrink-0" />
                                                        )}
                                                        <span className="text-[11px] font-bold text-foreground/80 uppercase tracking-wider">
                                                            Chunk {String(idx + 1).padStart(3, '0')}
                                                        </span>
                                                    </div>
                                                    {chunk.text && (
                                                        <p className="text-[11px] text-muted-foreground leading-relaxed pl-7 line-clamp-2">
                                                            {chunk.text}
                                                        </p>
                                                    )}
                                                </div>
                                                {chunk.isProcessed && status !== 'completed' && (
                                                    <Button
                                                        onClick={() => handlePlayChunk(idx)}
                                                        variant={currentChunkIndex === idx ? "default" : "outline"}
                                                        size="sm"
                                                        className="h-7 px-3 text-[10px] font-bold uppercase shrink-0"
                                                    >
                                                        {currentChunkIndex === idx ? 'Playing' : 'Listen'}
                                                    </Button>
                                                )}
                                            </Card>
                                        );
                                    })}
                                    {chunks.length === 0 && (
                                        <div className="text-center text-muted-foreground py-20 flex flex-col items-center gap-4">
                                            <div className="w-12 h-12 rounded-full bg-muted/30 flex items-center justify-center">
                                                <Terminal className="w-6 h-6 opacity-20" />
                                            </div>
                                            <span className="text-xs uppercase tracking-widest font-semibold opacity-50">No Chunks Available</span>
                                        </div>
                                    )}
                                </div>
                            </ScrollArea>
                        </CardContent>
                    </Card>

                    {/* Right Column Stack */}
                    <div className="flex flex-col gap-6 h-[500px]">
                        
                        {/* Chapters Sidebar */}
                        <ChapterSidebar
                            projectId={projectId}
                            onChapterClick={handleChapterClick}
                            selectedChunkIndex={currentChunkIndex}
                        />
                        
                        {/* Audio Tools Panel */}
                        <Card className="flex-none border-none bg-background/50 shadow-xl ring-1 ring-border/50">
                            <CardHeader className="bg-muted/30 border-b border-border/50 py-3">
                                <CardTitle className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">Audio Tools</CardTitle>
                            </CardHeader>
                            <CardContent className="p-4 space-y-4">
                                <div className="space-y-2">
                                    <div className="flex flex-col">
                                        <span className="text-[10px] font-bold uppercase tracking-wider">Auto ACX Mastering</span>
                                        <span className="text-[9px] text-muted-foreground mt-0.5">Automated normalization & quality control</span>
                                        <div className="mt-2 text-right">
                                            <Badge variant="default" className="h-5 text-[9px] font-black tracking-widest bg-green-600/20 text-green-500 border-none px-2 ring-1 ring-green-500/30">
                                                ✅ ACTIVE
                                            </Badge>
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Logs Panel */}
                        <Card className="flex-1 flex flex-col min-h-0 border-none bg-background/50 shadow-xl ring-1 ring-border/50">
                            <CardHeader className="bg-muted/30 border-b border-border/50 py-3">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Terminal className="w-3 h-3 text-muted-foreground" />
                                        <CardTitle className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">System Logs</CardTitle>
                                    </div>
                                    <Badge variant="outline" className="text-[8px] border-border/50 font-mono">{logs.length}</Badge>
                                </div>
                            </CardHeader>
                            <CardContent className="flex-1 overflow-hidden p-4">
                                <ScrollArea className="h-full w-full">
                                    <div className="space-y-2 pr-4">
                                        {logs.map((log, i) => (
                                            <div key={i} className="flex gap-3 text-[10px] group">
                                                <span className="text-muted-foreground/30 font-mono shrink-0 select-none">
                                                    {log.timestamp.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                                </span>
                                                <span className="text-foreground/70 font-medium group-hover:text-foreground transition-colors leading-relaxed">
                                                    {log.message}
                                                </span>
                                            </div>
                                        ))}
                                        {logs.length === 0 && (
                                            <div className="text-center py-10 opacity-20 italic text-[10px] uppercase tracking-widest">Awaiting system logs...</div>
                                        )}
                                    </div>
                                </ScrollArea>
                            </CardContent>
                        </Card>
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
