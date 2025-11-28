import { Play, Pause, SkipBack, SkipForward, Download, Volume2 } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

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

        if (audioUrl) {
            audioRef.current.src = audioUrl;
            audioRef.current.load();
            // Auto play new audio
            const playPromise = audioRef.current.play();
            if (playPromise !== undefined) {
                playPromise
                    .then(() => setIsPlaying(true))
                    .catch(() => setIsPlaying(false));
            }
        } else {
            // Reset state when no audio URL
            const audio = audioRef.current;
            audio.pause();
            audio.src = '';
            setIsPlaying(false);
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

    const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!audioRef.current) return;
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const percentage = x / rect.width;
        const newTime = percentage * audioRef.current.duration;
        audioRef.current.currentTime = newTime;
    };

    const handleDownload = async () => {
        if (!projectId) return;
        try {
            // Dynamic URL for localhost and Lightning AI
            const apiBase = window.location.hostname === 'localhost'
                ? 'http://localhost:8000/api'
                : `${window.location.protocol}//${window.location.hostname.replace('4173', '8000')}/api`;

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
        <div className="h-24 bg-slate-900 border-t border-slate-700 px-6 flex items-center justify-between shrink-0">
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
                        <p className="text-sm font-medium text-slate-100 truncate">
                            {projectId ? `Project #${projectId}` : 'Audio Track'}
                        </p>
                        <p className="text-xs text-slate-400">
                            {isPlaying ? 'Playing...' : 'Paused'}
                        </p>
                    </div>
                ) : (
                    <p className="text-sm text-slate-400">No track selected</p>
                )}
            </div>

            {/* Controls */}
            <div className="flex-1 flex flex-col items-center gap-2">
                <div className="flex items-center gap-6">
                    <button
                        onClick={onPrevious}
                        className="text-slate-400 hover:text-slate-100 transition-colors disabled:opacity-30"
                        disabled={!onPrevious}
                    >
                        <SkipBack className="w-5 h-5" />
                    </button>
                    <button
                        onClick={handlePlayPause}
                        disabled={!audioUrl}
                        className="w-12 h-12 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white flex items-center justify-center hover:scale-105 transition-transform shadow-lg hover:shadow-indigo-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-1" />}
                    </button>
                    <button
                        onClick={onNext}
                        className="text-slate-400 hover:text-slate-100 transition-colors disabled:opacity-30"
                        disabled={!onNext}
                    >
                        <SkipForward className="w-5 h-5" />
                    </button>
                </div>

                {/* Progress Bar */}
                <div className="w-full max-w-md flex items-center gap-3 text-xs text-slate-400">
                    <span>{formatTime(currentTime)}</span>
                    <div
                        className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden cursor-pointer"
                        onClick={handleProgressClick}
                    >
                        <div
                            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                    <span>{formatTime(duration)}</span>
                </div>
            </div>

            {/* Volume & Actions */}
            <div className="w-1/4 flex items-center justify-end gap-4">
                <div className="flex items-center gap-2 group">
                    <Volume2 className="w-5 h-5 text-slate-400 group-hover:text-slate-100" />
                    <div
                        className="w-20 h-1.5 bg-slate-700 rounded-full overflow-hidden cursor-pointer"
                        onClick={(e) => {
                            const rect = e.currentTarget.getBoundingClientRect();
                            const x = e.clientX - rect.left;
                            const percentage = (x / rect.width) * 100;
                            setVolume(Math.min(100, Math.max(0, percentage)));
                        }}
                    >
                        <div
                            className="h-full bg-slate-400 group-hover:bg-indigo-500 transition-colors"
                            style={{ width: `${volume}%` }}
                        />
                    </div>
                </div>
                <button
                    onClick={handleDownload}
                    disabled={!projectId}
                    className="p-2 hover:bg-slate-800 rounded-full text-slate-400 hover:text-emerald-400 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                >
                    <Download className="w-5 h-5" />
                </button>
            </div>
        </div>
    );
}
