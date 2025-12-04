import { useState, useEffect, useCallback } from 'react';
import { Cpu, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';
import { getReferenceVoices } from '../api/client';
import { DropZone } from './upload/DropZone';
import { VoiceSelector } from './upload/VoiceSelector';
import { PresetSelector } from './upload/PresetSelector';
import { AdvancedSettings } from './upload/AdvancedSettings';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';

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
        presetId: string;
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

    // TTS Preset State
    const [selectedPresetId, setSelectedPresetId] = useState<string>('en_fiction');

    // Advanced Settings State
    const [language, setLanguage] = useState('en');
    const [speed, setSpeed] = useState(0.9);
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
            presetId: selectedPresetId,
            language,
            speed,
            temperature,
            topK,
            topP,
            repetitionPenalty
        });
    }, [isSubmitting, textFile, projectName, voiceMode, audioFile, selectedVoice, useGpu, selectedPresetId, language, speed, temperature, topK, topP, repetitionPenalty, onUpload]);

    const canSubmit = textFile && projectName && (
        (voiceMode === 'upload' && audioFile) ||
        (voiceMode === 'reference' && selectedVoice)
    );

    return (
        <Card className="w-full max-w-4xl mx-auto p-8 animate-slide-up">
            <CardContent className="p-0">
                <h2 className="text-3xl font-bold mb-8 bg-gradient-to-r from-primary via-primary to-primary bg-clip-text text-transparent">
                    Create New Audiobook
                </h2>

                <div className="space-y-8">
                    {/* Project Name */}
                    <div className="animate-fade-in space-y-3">
                        <Label className="flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                            Project Name
                        </Label>
                        <Input
                            type="text"
                            value={projectName}
                            onChange={(e) => setProjectName(e.target.value)}
                            placeholder="My Awesome Book"
                            className="h-11"
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

                {/* TTS Preset Selector */}
                <PresetSelector
                    selectedPresetId={selectedPresetId}
                    setSelectedPresetId={setSelectedPresetId}
                    language={language}
                    onPresetChange={(params) => {
                        setTemperature(params.temperature);
                        setTopP(params.top_p);
                        setRepetitionPenalty(params.repetition_penalty);
                        setSpeed(params.speed);
                    }}
                />

                    {/* GPU/CPU Toggle */}
                    <Card className="p-5">
                        <CardContent className="p-0">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    {useGpu ? <Zap className="w-7 h-7 text-primary" /> : <Cpu className="w-7 h-7 text-muted-foreground" />}
                                    <div>
                                        <p className="text-sm font-semibold text-foreground">Processing Unit</p>
                                        <p className="text-xs text-muted-foreground">
                                            {useGpu ? "GPU (Faster)" : "CPU (Slower)"}
                                        </p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setUseGpu(!useGpu)}
                                    className={cn(
                                        "relative inline-flex h-7 w-14 items-center rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-ring",
                                        useGpu ? "bg-primary" : "bg-muted"
                                    )}
                                >
                                    <span
                                        className={cn(
                                            "inline-block h-5 w-5 transform rounded-full bg-background transition-transform duration-300 shadow-lg",
                                            useGpu ? "translate-x-8" : "translate-x-1"
                                        )}
                                    />
                                </button>
                            </div>
                        </CardContent>
                    </Card>

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
                    <Button
                        onClick={handleSubmit}
                        disabled={!canSubmit || isSubmitting}
                        size="lg"
                        className="w-full text-lg font-bold"
                    >
                        {isSubmitting ? 'Creating Project...' : 'Start Processing'}
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}

