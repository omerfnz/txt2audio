import { Play, Pause, SkipBack, SkipForward, Download, Volume2 } from 'lucide-react';
import { useState } from 'react';

interface PlayerProps {
    currentTrack?: string | null;
    isPlaying?: boolean;
    progress?: number;
    onPlayPause?: () => void;
}

export function Player({ currentTrack, isPlaying = false, progress = 0, onPlayPause }: PlayerProps) {
    const [volume] = useState(80);

    return (
        <div className="h-24 bg-slate-900 border-t border-slate-700 px-6 flex items-center justify-between shrink-0">
            {/* Track Info */}
            <div className="w-1/4">
                {currentTrack ? (
                    <div>
                        <p className="text-sm font-medium text-slate-100 truncate">{currentTrack}</p>
                        <p className="text-xs text-slate-400">Processing...</p>
                    </div>
                ) : (
                    <p className="text-sm text-slate-400">No track selected</p>
                )}
            </div>

            {/* Controls */}
            <div className="flex-1 flex flex-col items-center gap-2">
                <div className="flex items-center gap-6">
                    <button className="text-slate-400 hover:text-slate-100 transition-colors">
                        <SkipBack className="w-5 h-5" />
                    </button>
                    <button
                        onClick={onPlayPause}
                        className="w-12 h-12 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white flex items-center justify-center hover:scale-105 transition-transform shadow-lg hover:shadow-indigo-500/50"
                    >
                        {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current ml-1" />}
                    </button>
                    <button className="text-slate-400 hover:text-slate-100 transition-colors">
                        <SkipForward className="w-5 h-5" />
                    </button>
                </div>

                {/* Progress Bar */}
                <div className="w-full max-w-md flex items-center gap-3 text-xs text-slate-400">
                    <span>0:00</span>
                    <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                    <span>3:45</span>
                </div>
            </div>

            {/* Volume & Actions */}
            <div className="w-1/4 flex items-center justify-end gap-4">
                <div className="flex items-center gap-2 group">
                    <Volume2 className="w-5 h-5 text-slate-400 group-hover:text-slate-100" />
                    <div className="w-20 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-slate-400 group-hover:bg-indigo-500 transition-colors"
                            style={{ width: `${volume}%` }}
                        />
                    </div>
                </div>
                <button className="p-2 hover:bg-slate-800 rounded-full text-slate-400 hover:text-emerald-400 transition-colors">
                    <Download className="w-5 h-5" />
                </button>
            </div>
        </div>
    );
}
