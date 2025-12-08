import { useState } from 'react';
import { Player } from '../components/Player';
import { useProjectStatus } from '../hooks/useProjectStatus';
import { Terminal, CheckCircle, Circle } from 'lucide-react';
import { getAudioQuality, normalizeAudio, cancelProcessing, resumeProject, type AudioQualityResponse } from '../api/client';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';

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
    const [quality, setQuality] = useState<AudioQualityResponse | null>(null);
    const [qualityLoading, setQualityLoading] = useState(false);
    const [normalizeLoading, setNormalizeLoading] = useState(false);
    const [qualityError, setQualityError] = useState<string | null>(null);
    const [cancelLoading, setCancelLoading] = useState(false);
    const [resumeLoading, setResumeLoading] = useState(false);

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
        const audioUrl = `${getApiBase()}/audio/download/${projectId}`;
        setCurrentAudioUrl(audioUrl);
        setCurrentChunkIndex(null);
    };

    const handleAnalyzeQuality = async () => {
        try {
            setQualityLoading(true);
            setQualityError(null);
            const result = await getAudioQuality(projectId);
            setQuality(result);
        } catch (error) {
            console.error('Audio quality analysis failed:', error);
            setQuality(null);
            setQualityError(
                error instanceof Error ? error.message : 'Audio quality analysis failed'
            );
        } finally {
            setQualityLoading(false);
        }
    };

    const handleNormalize = async () => {
        try {
            setNormalizeLoading(true);
            setQualityError(null);
            await normalizeAudio(projectId);

            // Normalizasyon bittikten sonra kaliteyi tekrar ölçmek için kullanıcıyı yönlendirmek üzere
            // sadece state'i resetliyoruz; kullanıcı yeniden "Analyze Quality" butonuna basabilir.
            setQuality(null);
        } catch (error) {
            console.error('Audio normalization failed:', error);
            setQualityError(
                error instanceof Error ? error.message : 'Audio normalization failed'
            );
        } finally {
            setNormalizeLoading(false);
        }
    };

    const handleCancel = async () => {
        try {
            setCancelLoading(true);
            await cancelProcessing(projectId);
            // Durum, WebSocket üzerinden güncellenecek (status: 'cancelled')
        } catch (error) {
            console.error('Cancel processing failed:', error);
        } finally {
            setCancelLoading(false);
        }
    };

    const handleResume = async () => {
        try {
            setResumeLoading(true);
            // GPU kullanımını varsayılan olarak aktif ediyoruz (sunucu tarafında kontrol edilecek)
            const result = await resumeProject(projectId, true);
            console.log('Resume started:', result);
            // Durum, WebSocket üzerinden güncellenecek (status: 'processing')
        } catch (error) {
            console.error('Resume processing failed:', error);
            // Kullanıcıya hata göster
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

    return (
        <div className="flex flex-col h-full overflow-hidden">
            <div className="flex-1 overflow-y-auto p-8 pb-32">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-3xl font-bold text-foreground">Project View</h1>
                        <p className="text-muted-foreground">
                            ID: {projectId} • Status:{' '}
                            <Badge
                                variant={
                                    status === 'completed' ? 'default' :
                                        status === 'failed' ? 'destructive' :
                                            status === 'processing' || status === 'merging' ? 'secondary' : 'outline'
                                }
                                className="uppercase"
                            >
                                {status === 'merging' ? 'Merging' : status}
                            </Badge>
                        </p>
                    </div>
                    <div className="flex items-center gap-4">
                        {status === 'completed' && (
                            <div className="flex items-center gap-3">
                                <Button onClick={handlePlayFinal} size="sm" className="w-full sm:w-auto">
                                    Play Final Audio (MP3)
                                </Button>
                            </div>
                        )}
                        {canResume && (
                            <Button
                                onClick={handleResume}
                                disabled={resumeLoading}
                                variant="default"
                                size="sm"
                                className="bg-green-600 hover:bg-green-700"
                            >
                                {resumeLoading ? 'Resuming…' : '▶ Resume Processing'}
                            </Button>
                        )}
                        {(status === 'processing' || status === 'merging') && (
                            <div className="flex items-center gap-4">
                                <div className="text-right">
                                    {processingStartTime ? (
                                        <>
                                            <p className="text-xs text-muted-foreground">
                                                Started: {processingStartTime.toLocaleTimeString()}
                                            </p>
                                            {estimatedEndTime && (
                                                <p className="text-xs text-primary">
                                                    Est. finish: {estimatedEndTime.toLocaleTimeString()}
                                                </p>
                                            )}
                                            {progress > 0 && (
                                                <p className="text-xs text-muted-foreground mt-1">
                                                    Elapsed: {Math.floor((Date.now() - processingStartTime.getTime()) / 1000 / 60)} min
                                                </p>
                                            )}
                                        </>
                                    ) : (
                                        <p className="text-xs text-muted-foreground">
                                            {status === 'merging' ? 'Merging...' : 'Processing...'}
                                        </p>
                                    )}
                                </div>
                                <Button
                                    onClick={handleCancel}
                                    disabled={cancelLoading}
                                    variant="destructive"
                                    size="sm"
                                >
                                    {cancelLoading ? 'Cancelling…' : 'Cancel Processing'}
                                </Button>
                            </div>
                        )}
                        <div className="text-right">
                            <p className="text-2xl font-bold text-primary">
                                {progress.toFixed(1)}%
                            </p>
                            <p className="text-xs text-muted-foreground">Completed</p>
                            <Progress value={progress} className="w-20 mt-1" />
                        </div>
                    </div>
                </div>

                {/* Grid Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Chunks List */}
                    <Card className="lg:col-span-2 flex flex-col h-[500px]">
                        <CardHeader>
                            <CardTitle className="text-sm uppercase tracking-wider">Text Chunks</CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 overflow-hidden p-4 pt-0">
                            <ScrollArea className="h-full">
                                <div className="space-y-2 pr-4">
                                    {chunks.map((chunk, idx) => {
                                        return (
                                            <Card
                                                key={idx}
                                                className={cn(
                                                    'p-3 flex items-center justify-between transition-all duration-200',
                                                    chunk.isProcessed
                                                        ? 'bg-primary/5 border-primary/20 hover:bg-primary/10'
                                                        : 'bg-muted/30',
                                                    currentChunkIndex === idx && 'ring-2 ring-primary'
                                                )}
                                            >
                                                <div className="flex flex-col gap-1 flex-1 mr-4">
                                                    <div className="flex items-center gap-3">
                                                        {chunk.isProcessed ? (
                                                            <CheckCircle className="w-5 h-5 text-primary shrink-0" />
                                                        ) : (
                                                            <Circle className="w-5 h-5 text-muted-foreground shrink-0" />
                                                        )}
                                                        <span className="text-sm font-medium text-foreground whitespace-nowrap">
                                                            Chunk #{idx + 1}
                                                        </span>
                                                    </div>
                                                    {chunk.text && (
                                                        <p className="text-xs text-muted-foreground whitespace-pre-wrap">
                                                            {chunk.text}
                                                        </p>
                                                    )}
                                                </div>
                                                {chunk.isProcessed && status !== 'completed' && (
                                                    <Button
                                                        onClick={() => handlePlayChunk(idx)}
                                                        variant={currentChunkIndex === idx ? "default" : "outline"}
                                                        size="sm"
                                                        className="shrink-0"
                                                    >
                                                        {currentChunkIndex === idx ? 'Playing' : 'Play'}
                                                    </Button>
                                                )}
                                            </Card>
                                        );
                                    })}
                                    {chunks.length === 0 && (
                                        <div className="text-center text-muted-foreground py-10">
                                            No chunks available yet.
                                        </div>
                                    )}
                                </div>
                            </ScrollArea>
                        </CardContent>
                    </Card>

                    {/* Right Column Stack */}
                    <div className="flex flex-col gap-6 h-[500px]">
                        
                        {/* Audio Tools Panel */}
                        <Card className="flex-none">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm">Audio Tools</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {/* ACX Quality Check */}
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs font-medium">ACX Quality Check</span>
                                        <Button 
                                            variant="outline" 
                                            size="sm" 
                                            onClick={handleAnalyzeQuality}
                                            disabled={qualityLoading || !status || status !== 'completed'}
                                            className="h-7 text-xs"
                                        >
                                            {qualityLoading ? 'Analyzing...' : 'Analyze'}
                                        </Button>
                                    </div>
                                    
                                    {qualityError && (
                                        <p className="text-xs text-destructive">{qualityError}</p>
                                    )}

                                    {quality && (
                                        <div className="rounded-md bg-muted p-2 space-y-1">
                                            <div className="flex justify-between text-xs">
                                                <span>Overall:</span>
                                                <Badge variant={quality.overall_acx_compliant ? "default" : "destructive"} className="h-5 text-[10px]">
                                                    {quality.overall_acx_compliant ? "PASS" : "FAIL"}
                                                </Badge>
                                            </div>
                                            <div className="grid grid-cols-2 gap-1 text-[10px] text-muted-foreground mt-1">
                                                <div>RMS: {quality.analysis.rms_db}dB</div>
                                                <div>Peak: {quality.analysis.peak_db}dB</div>
                                                <div>Noise: {quality.analysis.noise_floor_db}dB</div>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* ACX Mastering */}
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <div className="flex flex-col">
                                            <span className="text-xs font-medium">Auto-Mastering</span>
                                            <span className="text-[10px] text-muted-foreground">Normalize to ACX specs</span>
                                        </div>
                                        <Button 
                                            variant="secondary" 
                                            size="sm" 
                                            onClick={handleNormalize}
                                            disabled={normalizeLoading || !status || status !== 'completed'}
                                            className="h-7 text-xs"
                                        >
                                            {normalizeLoading ? 'Processing...' : 'Normalize'}
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Logs Panel */}
                        <Card className="flex-1 flex flex-col min-h-0">
                            <CardHeader className="pb-2">
                                <div className="flex items-center gap-2">
                                    <Terminal className="w-4 h-4 text-muted-foreground" />
                                    <CardTitle className="text-sm">System Logs</CardTitle>
                                </div>
                            </CardHeader>
                            <CardContent className="flex-1 overflow-hidden p-4 pt-0">
                                <ScrollArea className="h-full w-full pr-4">
                                    <div className="space-y-1 text-muted-foreground font-mono text-xs">
                                        {logs.map((log, i) => (
                                            <div key={i} className="break-words">
                                                <span className="text-muted-foreground/50 mr-2">
                                                    [{log.timestamp.toLocaleTimeString()}]
                                                </span>
                                                <span className="text-foreground">{log.message}</span>
                                            </div>
                                        ))}
                                        {logs.length === 0 && (
                                            <div className="text-muted-foreground italic">Waiting for logs...</div>
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
