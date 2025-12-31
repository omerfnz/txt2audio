import { Play, Pause, SkipBack, SkipForward, Download, Volume2 } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { getApiBase } from '../api/client';

interface PlayerProps {
    audioUrl?: string | null;
    projectId?: number | null;
    onNext?: () => void;
    onPrevious?: () => void;
}

export function Player({ audioUrl, projectId, onNext, onPrevious }: PlayerProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [progress, setProgress] = useState(0);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(80);
    const audioRef = useRef<HTMLAudioElement>(null);

    // Update audio source when audioUrl changes
    useEffect(() => {
        if (!audioRef.current) return;

        if (audioUrl && audioUrl.trim() !== '') {
            try {
                audioRef.current.src = audioUrl;
                audioRef.current.load();
                // Auto play new audio
                const playPromise = audioRef.current.play();
                if (playPromise !== undefined) {
                    playPromise
                        .then(() => {
                            // Use setTimeout to avoid setState in effect
                            setTimeout(() => setIsPlaying(true), 0);
                        })
                        .catch((err) => {
                            console.warn('Auto-play prevented or failed:', err);
                            setTimeout(() => setIsPlaying(false), 0);
                        });
                }
            } catch (error) {
                console.error('Failed to set audio source:', error);
                setTimeout(() => setIsPlaying(false), 0);
            }
        } else {
            // Reset state when no audio URL
            const audio = audioRef.current;
            audio.pause();
            audio.src = '';
            setTimeout(() => setIsPlaying(false), 0);
        }

        const audio = audioRef.current;
        return () => {
            // Cleanup on unmount
            audio.pause();
        };
    }, [audioUrl]);

    // Update volume
    useEffect(() => {
        if (audioRef.current) {
            audioRef.current.volume = volume / 100;
        }
    }, [volume]);

    const handlePlayPause = () => {
        if (!audioRef.current || !audioUrl) return;

        if (isPlaying) {
            audioRef.current.pause();
            setIsPlaying(false);
        } else {
            audioRef.current.play().then(() => {
                setIsPlaying(true);
            }).catch((err) => {
                console.error('Playback error:', err);
                setIsPlaying(false);
            });
        }
    };

    const handleTimeUpdate = () => {
        if (audioRef.current) {
            const current = audioRef.current.currentTime;
            const total = audioRef.current.duration;
            setCurrentTime(current);
            setProgress((current / total) * 100);
        }
    };

    const handleLoadedMetadata = () => {
        if (audioRef.current) {
            setDuration(audioRef.current.duration);
        }
    };

    const handleEnded = () => {
        setIsPlaying(false);
        setProgress(0);
        setCurrentTime(0);
        if (onNext) onNext();
    };

    const handleDownload = async () => {
        if (!projectId) return;
        try {
            // Use getApiBase from client.ts for consistent URL handling
            const apiBase = getApiBase();
            const url = `${apiBase}/audio/download/${projectId}`;
            const link = document.createElement('a');
            link.href = url;
            link.download = `audiobook_${projectId}.mp3`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Download error:', error);
        }
    };

    const formatTime = (time: number) => {
        if (isNaN(time)) return '0:00';
        const minutes = Math.floor(time / 60);
        const seconds = Math.floor(time % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    };

    return (
        <div className="h-24 bg-card border-t border-border px-6 flex items-center justify-between shrink-0">
            <audio
                ref={audioRef}
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={handleLoadedMetadata}
                onEnded={handleEnded}
            />

            {/* Track Info */}
            <div className="w-1/4">
                {audioUrl ? (
                    <div>
                        <p className="text-sm font-medium text-foreground truncate">
                            {projectId ? `Project #${projectId}` : 'Audio Track'}
                        </p>
                        <p className="text-xs text-muted-foreground">
                            {isPlaying ? 'Playing...' : 'Paused'}
                        </p>
                    </div>
                ) : (
                    <p className="text-sm text-muted-foreground">No track selected</p>
                )}
            </div>

            {/* Controls */}
            <div className="flex-1 flex flex-col items-center gap-2">
                <div className="flex items-center gap-6">
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={onPrevious}
                        disabled={!onPrevious}
                    >
                        <SkipBack className="w-5 h-5" />
                    </Button>
                    <Button
                        onClick={handlePlayPause}
                        disabled={!audioUrl}
                        size="icon"
                        className="w-12 h-12 rounded-full"
                    >
                        {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-1" />}
                    </Button>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={onNext}
                        disabled={!onNext}
                    >
                        <SkipForward className="w-5 h-5" />
                    </Button>
                </div>

                {/* Progress Bar */}
                <div className="w-full max-w-md flex items-center gap-3 text-xs text-muted-foreground">
                    <span>{formatTime(currentTime)}</span>
                    <Slider
                        value={[progress]}
                        onValueChange={(value: number[]) => {
                            if (audioRef.current) {
                                const newTime = (value[0] / 100) * audioRef.current.duration;
                                audioRef.current.currentTime = newTime;
                            }
                        }}
                        max={100}
                        step={0.1}
                        className="flex-1"
                    />
                    <span>{formatTime(duration)}</span>
                </div>
            </div>

            {/* Volume & Actions */}
            <div className="w-1/4 flex items-center justify-end gap-4">
                <div className="flex items-center gap-2 group">
                    <Volume2 className="w-5 h-5 text-muted-foreground group-hover:text-foreground" />
                    <Slider
                        value={[volume]}
                        onValueChange={(value: number[]) => setVolume(value[0])}
                        max={100}
                        step={1}
                        className="w-20"
                    />
                </div>
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleDownload}
                    disabled={!projectId}
                >
                    <Download className="w-5 h-5" />
                </Button>
            </div>
        </div>
    );
}
