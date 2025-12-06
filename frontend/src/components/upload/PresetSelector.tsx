import { useEffect, useState } from 'react';
import { Sliders, Info } from 'lucide-react';
import { getTTSPresets } from '../../api/client';
import { Label } from '@/components/ui/label';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from '@/components/ui/accordion';
import { Card, CardContent } from '@/components/ui/card';

interface TTSPreset {
    name: string;
    description: string;
    language: string;
    content_type: string;
    parameters: {
        temperature: number;
        top_p: number;
        repetition_penalty: number;
        speed: number;
        enable_text_splitting: boolean;
    };
}

interface PresetSelectorProps {
    selectedPresetId: string;
    setSelectedPresetId: (presetId: string) => void;
    language?: string;
    onPresetChange?: (params: TTSPreset['parameters']) => void;
}

export function PresetSelector({
    selectedPresetId,
    setSelectedPresetId,
    language = 'en',
    onPresetChange
}: PresetSelectorProps) {
    const [presets, setPresets] = useState<Record<string, TTSPreset>>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showDetails, setShowDetails] = useState(false);

    useEffect(() => {
        fetchPresets();
    }, []);

    // Notify parent when preset changes
    useEffect(() => {
        if (presets && presets[selectedPresetId] && onPresetChange) {
            onPresetChange(presets[selectedPresetId].parameters);
        }
    }, [selectedPresetId, presets, onPresetChange]);

    const fetchPresets = async () => {
        try {
            setLoading(true);
            const data = await getTTSPresets();
            if (data && data.presets) {
                setPresets(data.presets);
            } else {
                setPresets({});
            }
            setError(null);
        } catch (err) {
            console.error('Failed to fetch presets:', err);
            setError('Failed to load TTS presets');
            setPresets({});
        } finally {
            setLoading(false);
        }
    };

    const safePresets = presets || {};
    const selectedPreset = safePresets[selectedPresetId];

    // Filter presets by language
    const filteredPresets = Object.entries(safePresets).filter(
        ([, preset]) => preset.language === language || preset.content_type === 'custom'
    );

    if (loading) {
        return (
            <div className="space-y-3">
                <Label className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                    TTS Preset
                </Label>
                <div className="bg-card border border-border rounded-xl px-4 py-3 animate-pulse">
                    <div className="h-5 bg-muted rounded w-32"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="space-y-3">
                <Label className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-destructive"></span>
                    TTS Preset
                </Label>
                <Card className="bg-destructive/10 border-destructive">
                    <CardContent className="px-4 py-3 text-destructive text-sm">
                        {error}
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            <Label className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                TTS Preset
            </Label>

            {/* Preset Dropdown */}
            <Select value={selectedPresetId} onValueChange={setSelectedPresetId}>
                <SelectTrigger>
                    <SelectValue placeholder="Select preset" />
                </SelectTrigger>
                <SelectContent>
                    {filteredPresets.map(([presetId, preset]) => (
                        <SelectItem key={presetId} value={presetId}>
                            {preset.name}
                        </SelectItem>
                    ))}
                </SelectContent>
            </Select>

            {/* Preset Description */}
            {selectedPreset && (
                <Card className="animate-fade-in">
                    <CardContent className="p-4 space-y-3">
                        <p className="text-sm text-foreground leading-relaxed">
                            {selectedPreset.description}
                        </p>

                        {/* Accordion for Parameter Details */}
                        <Accordion type="single" collapsible value={showDetails ? "parameters" : ""} onValueChange={(value: string) => setShowDetails(value === "parameters")}>
                            <AccordionItem value="parameters" className="border-none">
                                <AccordionTrigger className="py-0 text-xs font-medium hover:no-underline">
                                    <div className="flex items-center gap-2">
                                        {showDetails ? <Sliders className="w-4 h-4" /> : <Info className="w-4 h-4" />}
                                        {showDetails ? 'Hide Parameters' : 'Show Parameters'}
                                    </div>
                                </AccordionTrigger>
                                <AccordionContent>
                                    <div className="grid grid-cols-2 gap-3 pt-2 border-t border-border">
                                        <div className="space-y-1">
                                            <p className="text-xs text-muted-foreground font-medium">Temperature</p>
                                            <div className="flex items-center gap-2">
                                                <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-gradient-to-r from-blue-500 to-violet-500 rounded-full"
                                                        style={{ width: `${selectedPreset.parameters.temperature * 100}%` }}
                                                    ></div>
                                                </div>
                                                <span className="text-xs text-foreground font-mono w-8 text-right">
                                                    {selectedPreset.parameters.temperature.toFixed(2)}
                                                </span>
                                            </div>
                                        </div>

                                        <div className="space-y-1">
                                            <p className="text-xs text-muted-foreground font-medium">Top-P</p>
                                            <div className="flex items-center gap-2">
                                                <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-full"
                                                        style={{ width: `${selectedPreset.parameters.top_p * 100}%` }}
                                                    ></div>
                                                </div>
                                                <span className="text-xs text-foreground font-mono w-8 text-right">
                                                    {selectedPreset.parameters.top_p.toFixed(2)}
                                                </span>
                                            </div>
                                        </div>

                                        <div className="space-y-1">
                                            <p className="text-xs text-muted-foreground font-medium">Repetition Penalty</p>
                                            <div className="flex items-center gap-2">
                                                <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-full"
                                                        style={{ width: `${(selectedPreset.parameters.repetition_penalty / 3) * 100}%` }}
                                                    ></div>
                                                </div>
                                                <span className="text-xs text-foreground font-mono w-8 text-right">
                                                    {selectedPreset.parameters.repetition_penalty.toFixed(1)}
                                                </span>
                                            </div>
                                        </div>

                                        <div className="space-y-1">
                                            <p className="text-xs text-muted-foreground font-medium">Speed</p>
                                            <div className="flex items-center gap-2">
                                                <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-gradient-to-r from-pink-500 to-rose-500 rounded-full"
                                                        style={{ width: `${(selectedPreset.parameters.speed / 2) * 100}%` }}
                                                    ></div>
                                                </div>
                                                <span className="text-xs text-foreground font-mono w-8 text-right">
                                                    {selectedPreset.parameters.speed.toFixed(1)}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </AccordionContent>
                            </AccordionItem>
                        </Accordion>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
