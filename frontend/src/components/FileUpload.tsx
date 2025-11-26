import { useState, useRef, useEffect, useCallback } from 'react';
import { Upload, FileAudio, FileText, Cpu, Zap, ChevronDown } from 'lucide-react';
import { clsx } from 'clsx';
import { getReferenceVoices } from '../api/client';

interface ReferenceVoice {
    name: string;
    path: string;
    filename: string;
}

interface VoiceCategory {
    [key: string]: ReferenceVoice[];
}

interface FileUploadProps {
    onUpload: (data: {
        text: File;
        audio: File | null;
        referenceVoicePath: string | null;
        useGpu: boolean;
        name: string;
    }) => void;
}

export function FileUpload({ onUpload }: FileUploadProps) {
    const [textFile, setTextFile] = useState<File | null>(null);
    const [audioFile, setAudioFile] = useState<File | null>(null);
    const [projectName, setProjectName] = useState('');
    const [useGpu, setUseGpu] = useState(true);
    const [isDragging, setIsDragging] = useState(false);
    const [voiceMode, setVoiceMode] = useState<'upload' | 'reference'>('reference');
    const [referenceVoices, setReferenceVoices] = useState<VoiceCategory>({});
    const [selectedCategory, setSelectedCategory] = useState<string>('');
    const [selectedVoice, setSelectedVoice] = useState<string>('');

    const textInputRef = useRef<HTMLInputElement>(null);
    const audioInputRef = useRef<HTMLInputElement>(null);

    // Load reference voices on mount
    useEffect(() => {
        async function loadVoices() {
            try {
                const data = await getReferenceVoices();
                setReferenceVoices(data.voices);

                // Auto-select first category and voice
                const categories = Object.keys(data.voices);
                if (categories.length > 0) {
                    setSelectedCategory(categories[0]);
                    if (data.voices[categories[0]].length > 0) {
                        setSelectedVoice(data.voices[categories[0]][0].path);
                    }
                }
            } catch (error) {
                console.error('Failed to load reference voices:', error);
            }
        }
        loadVoices();
    }, []);

    const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback(() => {
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        setIsDragging(false);

        const files = Array.from(e.dataTransfer.files);
        const txt = files.find(f => f.name.endsWith('.txt') || f.name.endsWith('.epub'));
        const audio = files.find(f => f.type.startsWith('audio/'));

        if (txt) setTextFile(txt);
        if (audio) {
            setAudioFile(audio);
            setVoiceMode('upload');
        }
    }, []);

    const handleCategoryChange = useCallback((categoryName: string) => {
        setSelectedCategory(categoryName);
        if (referenceVoices[categoryName]?.length > 0) {
            setSelectedVoice(referenceVoices[categoryName][0].path);
        }
    }, [referenceVoices]);

    const handleSubmit = useCallback(() => {
        if (!textFile || !projectName) return;

        if (voiceMode === 'upload' && !audioFile) return;
        if (voiceMode === 'reference' && !selectedVoice) return;

        onUpload({
            text: textFile,
            audio: voiceMode === 'upload' ? audioFile : null,
            referenceVoicePath: voiceMode === 'reference' ? selectedVoice : null,
            useGpu,
            name: projectName
        });
    }, [textFile, projectName, voiceMode, audioFile, selectedVoice, useGpu, onUpload]);

    const canSubmit = textFile && projectName && (
        (voiceMode === 'upload' && audioFile) ||
        (voiceMode === 'reference' && selectedVoice)
    );

    return (
        <div className="w-full max-w-4xl mx-auto p-8 glass rounded-3xl shadow-2xl animate-slide-up">
            <h2 className="text-3xl font-bold mb-8 bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                Create New Audiobook
            </h2>

            <div className="space-y-8">
                {/* Project Name */}
                <div className="animate-fade-in">
                    <label className="block text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
                        Project Name
                    </label>
                    <input
                        type="text"
                        value={projectName}
                        onChange={(e) => setProjectName(e.target.value)}
                        className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-5 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200 placeholder:text-slate-500"
                        placeholder="My Awesome Book"
                    />
                </div>

                {/* Drop Zone */}
                <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={clsx(
                        "border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 cursor-pointer relative overflow-hidden group",
                        isDragging ? "border-indigo-500 bg-indigo-500/10 scale-105" : "border-slate-600 hover:border-indigo-500/50 hover:bg-slate-800/50"
                    )}
                >
                    <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-purple-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                    <div className="flex flex-col items-center gap-6 relative z-10">
                        <div className={clsx(
                            "p-6 rounded-2xl transition-all duration-300",
                            isDragging ? "bg-indigo-500 scale-110 shadow-lg shadow-indigo-500/50" : "bg-gradient-to-br from-slate-800 to-slate-900 group-hover:scale-105"
                        )}>
                            <Upload className={clsx("w-10 h-10 transition-colors", isDragging ? "text-white" : "text-indigo-400")} />
                        </div>
                        <div>
                            <p className="text-xl font-semibold text-slate-100 mb-2">Drag & Drop files here</p>
                            <p className="text-sm text-slate-400">or click to browse your files</p>
                        </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6 mt-10">
                        {/* Text File */}
                        <div
                            onClick={() => textInputRef.current?.click()}
                            className={clsx(
                                "p-6 rounded-2xl border-2 flex items-center gap-4 cursor-pointer transition-all duration-300 group/card",
                                textFile ? "bg-indigo-500/10 border-indigo-500 glow" : "bg-slate-900/50 border-slate-700 hover:border-indigo-500/50 hover:bg-slate-800/50"
                            )}
                        >
                            <div className={clsx("p-3 rounded-xl transition-all", textFile ? "bg-indigo-500" : "bg-slate-800 group-hover/card:bg-indigo-500/20")}>
                                <FileText className={clsx("w-7 h-7", textFile ? "text-white" : "text-indigo-400")} />
                            </div>
                            <div className="text-left overflow-hidden flex-1">
                                <p className="text-sm font-semibold text-slate-100 truncate mb-1">
                                    {textFile ? textFile.name : "Select Text File"}
                                </p>
                                <p className="text-xs text-slate-400">.txt, .epub</p>
                            </div>
                            <input
                                type="file"
                                ref={textInputRef}
                                className="hidden"
                                accept=".txt,.epub"
                                onChange={(e) => e.target.files?.[0] && setTextFile(e.target.files[0])}
                            />
                        </div>

                        {/* Voice Selection Placeholder */}
                        <div className="p-6 rounded-2xl border-2 border-slate-700 bg-slate-900/50 flex items-center justify-center">
                            <p className="text-sm text-slate-400">Choose voice option below →</p>
                        </div>
                    </div>
                </div>

                {/* Voice Mode Selection */}
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

                    {/* Reference Voice Dropdown */}
                    {voiceMode === 'reference' && (
                        <div className="grid md:grid-cols-2 gap-4 animate-fade-in">
                            {/* Category Selector */}
                            <div className="relative">
                                <select
                                    value={selectedCategory}
                                    onChange={(e) => handleCategoryChange(e.target.value)}
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

                            {/* Voice Selector */}
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

                    {/* Upload Voice File */}
                    {voiceMode === 'upload' && (
                        <div
                            onClick={() => audioInputRef.current?.click()}
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

                {/* GPU/CPU Toggle */}
                <div className="flex items-center justify-between p-5 glass rounded-2xl">
                    <div className="flex items-center gap-4">
                        {useGpu ? <Zap className="w-7 h-7 text-yellow-400" /> : <Cpu className="w-7 h-7 text-blue-400" />}
                        <div>
                            <p className="text-sm font-semibold text-slate-100">Processing Unit</p>
                            <p className="text-xs text-slate-400">
                                {useGpu ? "GPU (Faster)" : "CPU (Slower)"}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={() => setUseGpu(!useGpu)}
                        className={clsx(
                            "relative inline-flex h-7 w-14 items-center rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                            useGpu ? "bg-gradient-to-r from-indigo-600 to-purple-600" : "bg-slate-700"
                        )}
                    >
                        <span
                            className={clsx(
                                "inline-block h-5 w-5 transform rounded-full bg-white transition-transform duration-300 shadow-lg",
                                useGpu ? "translate-x-8" : "translate-x-1"
                            )}
                        />
                    </button>
                </div>

                {/* Submit Button */}
                <button
                    onClick={handleSubmit}
                    disabled={!canSubmit}
                    className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed text-white py-4 px-6 rounded-2xl font-bold text-lg transition-all duration-300 shadow-lg hover:shadow-indigo-500/50 disabled:shadow-none transform hover:scale-[1.02] disabled:scale-100"
                >
                    Start Processing
                </button>
            </div>
        </div>
    );
}
