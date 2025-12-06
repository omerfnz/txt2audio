import { useRef } from 'react';
import { FileAudio } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Card } from '@/components/ui/card';

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
            <Label className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                Voice Selection
            </Label>

            <RadioGroup
                value={voiceMode}
                onValueChange={(value: string) => setVoiceMode(value as 'upload' | 'reference')}
                className="grid grid-cols-2 gap-4"
            >
                <Card
                    className={cn(
                        "p-4 border-2 cursor-pointer transition-all duration-200",
                        voiceMode === 'reference'
                            ? "bg-primary/10 border-primary shadow-lg shadow-primary/20"
                            : "bg-card border-border hover:border-primary/50"
                    )}
                    onClick={() => setVoiceMode('reference')}
                >
                    <div className="flex items-center gap-3">
                        <RadioGroupItem value="reference" id="reference" className="mt-0" />
                        <div className="flex-1">
                            <Label htmlFor="reference" className="font-semibold cursor-pointer">
                                Use Reference Voice
                            </Label>
                            <p className="text-xs text-muted-foreground">Choose from preloaded voices</p>
                        </div>
                    </div>
                </Card>

                <Card
                    className={cn(
                        "p-4 border-2 cursor-pointer transition-all duration-200",
                        voiceMode === 'upload'
                            ? "bg-primary/10 border-primary shadow-lg shadow-primary/20"
                            : "bg-card border-border hover:border-primary/50"
                    )}
                    onClick={() => setVoiceMode('upload')}
                >
                    <div className="flex items-center gap-3">
                        <RadioGroupItem value="upload" id="upload" className="mt-0" />
                        <div className="flex-1">
                            <Label htmlFor="upload" className="font-semibold cursor-pointer">
                                Upload Your Voice
                            </Label>
                            <p className="text-xs text-muted-foreground">Use your own audio file</p>
                        </div>
                    </div>
                </Card>
            </RadioGroup>

            {voiceMode === 'reference' && (
                <div className="grid md:grid-cols-2 gap-4 animate-fade-in">
                    <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                        <SelectTrigger>
                            <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                        <SelectContent>
                            {Object.keys(referenceVoices).map(category => (
                                <SelectItem key={category} value={category}>
                                    {category.charAt(0).toUpperCase() + category.slice(1)} Voices
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>

                    <Select value={selectedVoice} onValueChange={setSelectedVoice}>
                        <SelectTrigger>
                            <SelectValue placeholder="Select voice" />
                        </SelectTrigger>
                        <SelectContent>
                            {(referenceVoices[selectedCategory] || []).map((voice: ReferenceVoice) => (
                                <SelectItem key={voice.path} value={voice.path}>
                                    {voice.name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            )}

            {voiceMode === 'upload' && (
                <Card
                    onClick={(e) => {
                        e.stopPropagation();
                        audioInputRef.current?.click();
                    }}
                    className={cn(
                        "p-6 border-2 flex items-center gap-4 cursor-pointer transition-all duration-300 group/card animate-fade-in",
                        audioFile ? "bg-primary/10 border-primary" : "bg-card border-border hover:border-primary/50 hover:bg-accent/50"
                    )}
                >
                    <div className={cn("p-3 rounded-xl transition-all", audioFile ? "bg-primary" : "bg-muted group-hover/card:bg-primary/20")}>
                        <FileAudio className={cn("w-7 h-7", audioFile ? "text-primary-foreground" : "text-primary")} />
                    </div>
                    <div className="text-left overflow-hidden flex-1">
                        <p className="text-sm font-semibold text-foreground truncate mb-1">
                            {audioFile ? audioFile.name : "Select Audio File"}
                        </p>
                        <p className="text-xs text-muted-foreground">.wav, .mp3 (6-10s recommended)</p>
                    </div>
                    <input
                        type="file"
                        ref={audioInputRef}
                        className="hidden"
                        accept="audio/*"
                        onChange={(e) => e.target.files?.[0] && setAudioFile(e.target.files[0])}
                    />
                </Card>
            )}
        </div>
    );
}

