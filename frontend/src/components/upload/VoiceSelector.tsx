import { useRef } from 'react';
import { FileAudio, ChevronDown } from 'lucide-react';
import { clsx } from 'clsx';

interface ReferenceVoice {
    name: string;
    path: string;
    filename: string;
}

interface VoiceCategory {
    [key: string]: ReferenceVoice[];
}

interface VoiceSelectorProps {
    voiceMode: 'upload' | 'reference';
    setVoiceMode: (mode: 'upload' | 'reference') => void;
    referenceVoices: VoiceCategory;
    selectedCategory: string;
    setSelectedCategory: (category: string) => void;
    selectedVoice: string;
    setSelectedVoice: (voice: string) => void;
    audioFile: File | null;
    setAudioFile: (file: File) => void;
}

export function VoiceSelector({
    voiceMode,
    setVoiceMode,
    referenceVoices,
    selectedCategory,
    setSelectedCategory,
    selectedVoice,
    setSelectedVoice,
    audioFile,
    setAudioFile
}: VoiceSelectorProps) {
    const audioInputRef = useRef<HTMLInputElement>(null);

    return (
        <div className="space-y-4">
            <label className="block text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                Voice Selection
            </label>

            <div className="grid grid-cols-2 gap-4">
                <button
                    type="button"
                    onClick={() => setVoiceMode('reference')}
                    className={clsx(
                        "p-4 rounded-xl border-2 text-left transition-all duration-200",
                        voiceMode === 'reference'
                            ? "bg-emerald-500/10 border-emerald-500 shadow-lg shadow-emerald-500/20"
                            : "bg-slate-900/50 border-slate-700 hover:border-emerald-500/50"
                    )}
                >
                    <div className="flex items-center gap-3">
                        <div className={clsx("w-3 h-3 rounded-full border-2", voiceMode === 'reference' ? "border-emerald-500 bg-emerald-500" : "border-slate-500")} />
                        <div>
                            <p className="font-semibold text-slate-100">Use Reference Voice</p>
                            <p className="text-xs text-slate-400">Choose from preloaded voices</p>
                        </div>
                    </div>
                </button>

                <button
                    type="button"
                    onClick={() => setVoiceMode('upload')}
                    className={clsx(
                        "p-4 rounded-xl border-2 text-left transition-all duration-200",
                        voiceMode === 'upload'
                            ? "bg-indigo-500/10 border-indigo-500 shadow-lg shadow-indigo-500/20"
                            : "bg-slate-900/50 border-slate-700 hover:border-indigo-500/50"
                    )}
                >
                    <div className="flex items-center gap-3">
                        <div className={clsx("w-3 h-3 rounded-full border-2", voiceMode === 'upload' ? "border-indigo-500 bg-indigo-500" : "border-slate-500")} />
                        <div>
                            <p className="font-semibold text-slate-100">Upload Your Voice</p>
                            <p className="text-xs text-slate-400">Use your own audio file</p>
                        </div>
                    </div>
                </button>
            </div>

            {voiceMode === 'reference' && (
                <div className="grid md:grid-cols-2 gap-4 animate-fade-in">
                    <div className="relative">
                        <select
                            value={selectedCategory}
                            onChange={(e) => setSelectedCategory(e.target.value)}
                            className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none cursor-pointer"
                        >
                            {Object.keys(referenceVoices).map(category => (
                                <option key={category} value={category}>
                                    {category.charAt(0).toUpperCase() + category.slice(1)} Voices
                                </option>
                            ))}
                        </select>
                        <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
                    </div>

                    <div className="relative">
                        <select
                            value={selectedVoice}
                            onChange={(e) => setSelectedVoice(e.target.value)}
                            className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none cursor-pointer"
                        >
                            {(referenceVoices[selectedCategory] || []).map((voice: ReferenceVoice) => (
                                <option key={voice.path} value={voice.path}>
                                    {voice.name}
                                </option>
                            ))}
                        </select>
                        <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
                    </div>
                </div>
            )}

            {voiceMode === 'upload' && (
                <div
                    onClick={(e) => {
                        e.stopPropagation();
                        audioInputRef.current?.click();
                    }}
                    className={clsx(
                        "p-6 rounded-2xl border-2 flex items-center gap-4 cursor-pointer transition-all duration-300 group/card animate-fade-in",
                        audioFile ? "bg-emerald-500/10 border-emerald-500 glow" : "bg-slate-900/50 border-slate-700 hover:border-emerald-500/50 hover:bg-slate-800/50"
                    )}
                >
                    <div className={clsx("p-3 rounded-xl transition-all", audioFile ? "bg-emerald-500" : "bg-slate-800 group-hover/card:bg-emerald-500/20")}>
                        <FileAudio className={clsx("w-7 h-7", audioFile ? "text-white" : "text-emerald-400")} />
                    </div>
                    <div className="text-left overflow-hidden flex-1">
                        <p className="text-sm font-semibold text-slate-100 truncate mb-1">
                            {audioFile ? audioFile.name : "Select Audio File"}
                        </p>
                        <p className="text-xs text-slate-400">.wav, .mp3 (6-10s recommended)</p>
                    </div>
                    <input
                        type="file"
                        ref={audioInputRef}
                        className="hidden"
                        accept="audio/*"
                        onChange={(e) => e.target.files?.[0] && setAudioFile(e.target.files[0])}
                    />
                </div>
            )}
        </div>
    );
}
