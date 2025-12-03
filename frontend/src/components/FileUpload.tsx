import { useState, useEffect, useCallback } from 'react';
import { Cpu, Zap } from 'lucide-react';
import { clsx } from 'clsx';
import { getReferenceVoices } from '../api/client';
import { DropZone } from './upload/DropZone';
import { VoiceSelector } from './upload/VoiceSelector';
import { AdvancedSettings } from './upload/AdvancedSettings';

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
        language: string;
        speed: number;
        temperature: number;
        topK: number;
        topP: number;
        repetitionPenalty: number;
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

    // Advanced Settings State
    const [language, setLanguage] = useState('en');
    const [speed, setSpeed] = useState(1.0);
    const [temperature, setTemperature] = useState(0.75);
    const [topK, setTopK] = useState(50);
    const [topP, setTopP] = useState(0.85);
    const [repetitionPenalty, setRepetitionPenalty] = useState(2.0);
    const [isSubmitting, setIsSubmitting] = useState(false);

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
        if (isSubmitting) return;
        if (!textFile || !projectName) return;

        if (voiceMode === 'upload' && !audioFile) return;
        if (voiceMode === 'reference' && !selectedVoice) return;

        setIsSubmitting(true);
        onUpload({
            text: textFile,
            audio: voiceMode === 'upload' ? audioFile : null,
            referenceVoicePath: voiceMode === 'reference' ? selectedVoice : null,
            useGpu,
            name: projectName,
            language,
            speed,
            temperature,
            topK,
            topP,
            repetitionPenalty
        });
    }, [isSubmitting, textFile, projectName, voiceMode, audioFile, selectedVoice, useGpu, language, speed, temperature, topK, topP, repetitionPenalty, onUpload]);

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
                <DropZone
                    onFileSelect={setTextFile}
                    selectedFile={textFile}
                    isDragging={isDragging}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                />

                {/* Voice Selector */}
                <VoiceSelector
                    voiceMode={voiceMode}
                    setVoiceMode={setVoiceMode}
                    referenceVoices={referenceVoices}
                    selectedCategory={selectedCategory}
                    setSelectedCategory={handleCategoryChange}
                    selectedVoice={selectedVoice}
                    setSelectedVoice={setSelectedVoice}
                    audioFile={audioFile}
                    setAudioFile={setAudioFile}
                />

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

                {/* Advanced Settings */}
                <AdvancedSettings
                    language={language} setLanguage={setLanguage}
                    speed={speed} setSpeed={setSpeed}
                    temperature={temperature} setTemperature={setTemperature}
                    topK={topK} setTopK={setTopK}
                    topP={topP} setTopP={setTopP}
                    repetitionPenalty={repetitionPenalty} setRepetitionPenalty={setRepetitionPenalty}
                />

                {/* Submit Button */}
                <button
                    onClick={handleSubmit}
                    disabled={!canSubmit || isSubmitting}
                    className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed text-white py-4 px-6 rounded-2xl font-bold text-lg transition-all duration-300 shadow-lg hover:shadow-indigo-500/50 disabled:shadow-none transform hover:scale-[1.02] disabled:scale-100"
                >
                    {isSubmitting ? 'Creating Project...' : 'Start Processing'}
                </button>
            </div>
        </div>
    );
}

