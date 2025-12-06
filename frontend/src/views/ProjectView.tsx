import { useState } from 'react';
import { Player } from '../components/Player';
import { useProjectStatus } from '../hooks/useProjectStatus';
import { Terminal, CheckCircle, Circle } from 'lucide-react';
import { getAudioQuality, normalizeAudio, cancelProcessing, type AudioQualityResponse } from '../api/client';
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
                                <Button onClick={handlePlayFinal} size="sm">
                                    Play Final Audio (MP3)
                                </Button>
                                <Button
                                    onClick={handleAnalyzeQuality}
                                    disabled={qualityLoading || normalizeLoading}
                                    variant="outline"
                                    size="sm"
                                >
                                    {qualityLoading ? 'Analyzing…' : 'Analyze Quality (ACX)'}
                                </Button>
                                <Button
                                    onClick={handleNormalize}
                                    disabled={normalizeLoading}
                                    variant="outline"
                                    size="sm"
                                >
                                    {normalizeLoading ? 'Normalizing…' : 'Normalize for ACX'}
                                </Button>
                            </div>
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

                    {/* Logs + Quality Panel */}
                    <Card className="flex flex-col h-[500px]">
                        <CardHeader className="pb-2">
                            <div className="flex items-center gap-2">
                                <Terminal className="w-4 h-4 text-muted-foreground" />
                                <CardTitle className="text-sm">System Logs</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="flex-1 overflow-hidden p-4 pt-0 space-y-3">
                            {/* ACX Quality Panel */}
                            {quality && (
                                <Card className="p-3">
                                    <CardContent className="p-0 space-y-1">
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="font-semibold text-foreground text-xs">
                                                ACX Quality
                                            </span>
                                            <Badge
                                                variant={quality.overall_acx_compliant ? "default" : "secondary"}
                                                className="text-[10px]"
                                            >
                                                {quality.overall_acx_compliant ? 'COMPLIANT' : 'NEEDS WORK'}
                                            </Badge>
                                        </div>
                                        <div className="grid grid-cols-3 gap-2">
                                            <div>
                                                <p className="text-[10px] text-muted-foreground">RMS</p>
                                                <p className="text-[11px] text-foreground">
                                                    {quality.analysis.rms_db.toFixed(2)} dB
                                                </p>
                                                <p className="text-[10px] text-muted-foreground">
                                                    {quality.compliance_details.rms.target}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-[10px] text-muted-foreground">Peak</p>
                                                <p className="text-[11px] text-foreground">
                                                    {quality.analysis.peak_db.toFixed(2)} dB
                                                </p>
                                                <p className="text-[10px] text-muted-foreground">
                                                    {quality.compliance_details.peak.target}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-[10px] text-muted-foreground">Noise Floor</p>
                                                <p className="text-[11px] text-foreground">
                                                    {quality.analysis.noise_floor_db.toFixed(2)} dB
                                                </p>
                                                <p className="text-[10px] text-muted-foreground">
                                                    {quality.compliance_details.noise_floor.target}
                                                </p>
                                            </div>
                                        </div>
                                        <p className="text-[10px] text-muted-foreground pt-1 border-t border-border mt-1">
                                            Duration: {quality.analysis.duration_seconds.toFixed(1)}s • Sample
                                            Rate: {quality.analysis.sample_rate} Hz • Channels:{' '}
                                            {quality.analysis.channels}
                                        </p>
                                    </CardContent>
                                </Card>
                            )}

                            {qualityError && (
                                <Card className="bg-destructive/10 border-destructive">
                                    <CardContent className="p-2 text-destructive text-[11px]">
                                        {qualityError}
                                    </CardContent>
                                </Card>
                            )}

                            <ScrollArea className="flex-1">
                                <div className="space-y-1 text-muted-foreground font-mono text-xs pr-4">
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
