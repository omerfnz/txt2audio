import { useState } from 'react';
import { Label } from '@/components/ui/label';
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from '@/components/ui/accordion';
import { Slider } from '@/components/ui/slider';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';

interface AdvancedSettingsProps {
    language: string;
    setLanguage: (val: string) => void;
    speed: number;
    setSpeed: (val: number) => void;
    temperature: number;
    setTemperature: (val: number) => void;
    topK: number;
    setTopK: (val: number) => void;
    topP: number;
    setTopP: (val: number) => void;
    repetitionPenalty: number;
    setRepetitionPenalty: (val: number) => void;
}

export function AdvancedSettings({
    language, setLanguage,
    speed, setSpeed,
    temperature, setTemperature,
    topK, setTopK,
    topP, setTopP,
    repetitionPenalty, setRepetitionPenalty
}: AdvancedSettingsProps) {
    const [showAdvanced, setShowAdvanced] = useState(false);

    return (
        <Accordion type="single" collapsible value={showAdvanced ? "advanced" : ""} onValueChange={(value: string) => setShowAdvanced(value === "advanced")} className="border border-border rounded-2xl overflow-hidden">
            <AccordionItem value="advanced" className="border-none">
                <AccordionTrigger className="px-5 py-5 hover:no-underline">
                    <div className="flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-primary"></div>
                        <span className="font-semibold text-foreground">Advanced Settings</span>
                    </div>
                </AccordionTrigger>
                <AccordionContent>
                    <div className="px-5 pb-5 space-y-6">
                        <div>
                            <Label className="mb-2">Language</Label>
                            <Select value={language} onValueChange={setLanguage}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select language" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="en">English</SelectItem>
                                    <SelectItem value="es">Spanish</SelectItem>
                                    <SelectItem value="fr">French</SelectItem>
                                    <SelectItem value="de">German</SelectItem>
                                    <SelectItem value="it">Italian</SelectItem>
                                    <SelectItem value="pt">Portuguese</SelectItem>
                                    <SelectItem value="pl">Polish</SelectItem>
                                    <SelectItem value="tr">Turkish</SelectItem>
                                    <SelectItem value="ru">Russian</SelectItem>
                                    <SelectItem value="nl">Dutch</SelectItem>
                                    <SelectItem value="cs">Czech</SelectItem>
                                    <SelectItem value="ar">Arabic</SelectItem>
                                    <SelectItem value="zh-cn">Chinese</SelectItem>
                                    <SelectItem value="ja">Japanese</SelectItem>
                                    <SelectItem value="hu">Hungarian</SelectItem>
                                    <SelectItem value="ko">Korean</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label className="flex justify-between text-xs">
                                    <span>Speed</span>
                                    <span className="text-primary">{speed}x</span>
                                </Label>
                                <Slider
                                    value={[speed]}
                                    onValueChange={(value: number[]) => setSpeed(value[0])}
                                    min={0.5}
                                    max={2.0}
                                    step={0.1}
                                />
                            </div>

                            <div className="space-y-2">
                                <Label className="flex justify-between text-xs">
                                    <span>Temperature</span>
                                    <span className="text-primary">{temperature.toFixed(2)}</span>
                                </Label>
                                <Slider
                                    value={[temperature]}
                                    onValueChange={(value: number[]) => setTemperature(value[0])}
                                    min={0.01}
                                    max={1.0}
                                    step={0.01}
                                />
                            </div>

                            <div className="space-y-2">
                                <Label className="flex justify-between text-xs">
                                    <span>Top K</span>
                                    <span className="text-primary">{topK}</span>
                                </Label>
                                <Slider
                                    value={[topK]}
                                    onValueChange={(value: number[]) => setTopK(value[0])}
                                    min={1}
                                    max={100}
                                    step={1}
                                />
                            </div>

                            <div className="space-y-2">
                                <Label className="flex justify-between text-xs">
                                    <span>Top P</span>
                                    <span className="text-primary">{topP.toFixed(2)}</span>
                                </Label>
                                <Slider
                                    value={[topP]}
                                    onValueChange={(value: number[]) => setTopP(value[0])}
                                    min={0.01}
                                    max={1.0}
                                    step={0.01}
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label className="flex justify-between text-xs">
                                <span>Repetition Penalty</span>
                                <span className="text-primary">{repetitionPenalty.toFixed(1)}</span>
                            </Label>
                            <Slider
                                value={[repetitionPenalty]}
                                onValueChange={(value: number[]) => setRepetitionPenalty(value[0])}
                                min={1.0}
                                max={3.0}
                                step={0.1}
                            />
                        </div>
                    </div>
                </AccordionContent>
            </AccordionItem>
        </Accordion>
    );
}
