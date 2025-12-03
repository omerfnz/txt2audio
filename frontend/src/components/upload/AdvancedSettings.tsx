import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { clsx } from 'clsx';

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
        <div className="border border-slate-700 rounded-2xl overflow-hidden">
            <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="w-full flex items-center justify-between p-5 bg-slate-900/50 hover:bg-slate-800/50 transition-colors"
            >
                <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-purple-500"></div>
                    <span className="font-semibold text-slate-100">Advanced Settings</span>
                </div>
                <ChevronDown className={clsx("w-5 h-5 text-slate-400 transition-transform", showAdvanced ? "rotate-180" : "")} />
            </button>

            {showAdvanced && (
                <div className="p-5 border-t border-slate-700 space-y-6 bg-slate-900/30">
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-2">Language</label>
                        <select
                            value={language}
                            onChange={(e) => setLanguage(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-slate-100 text-sm focus:outline-none focus:border-purple-500"
                        >
                            <option value="en">English</option>
                            <option value="es">Spanish</option>
                            <option value="fr">French</option>
                            <option value="de">German</option>
                            <option value="it">Italian</option>
                            <option value="pt">Portuguese</option>
                            <option value="pl">Polish</option>
                            <option value="tr">Turkish</option>
                            <option value="ru">Russian</option>
                            <option value="nl">Dutch</option>
                            <option value="cs">Czech</option>
                            <option value="ar">Arabic</option>
                            <option value="zh-cn">Chinese</option>
                            <option value="ja">Japanese</option>
                            <option value="hu">Hungarian</option>
                            <option value="ko">Korean</option>
                        </select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-2 flex justify-between">
                                <span>Speed</span>
                                <span className="text-purple-400">{speed}x</span>
                            </label>
                            <input
                                type="range"
                                min="0.5"
                                max="2.0"
                                step="0.1"
                                value={speed}
                                onChange={(e) => setSpeed(parseFloat(e.target.value))}
                                className="w-full accent-purple-500"
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-2 flex justify-between">
                                <span>Temperature</span>
                                <span className="text-purple-400">{temperature}</span>
                            </label>
                            <input
                                type="range"
                                min="0.01"
                                max="1.0"
                                step="0.01"
                                value={temperature}
                                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                                className="w-full accent-purple-500"
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-2 flex justify-between">
                                <span>Top K</span>
                                <span className="text-purple-400">{topK}</span>
                            </label>
                            <input
                                type="range"
                                min="1"
                                max="100"
                                step="1"
                                value={topK}
                                onChange={(e) => setTopK(parseInt(e.target.value))}
                                className="w-full accent-purple-500"
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-2 flex justify-between">
                                <span>Top P</span>
                                <span className="text-purple-400">{topP}</span>
                            </label>
                            <input
                                type="range"
                                min="0.01"
                                max="1.0"
                                step="0.01"
                                value={topP}
                                onChange={(e) => setTopP(parseFloat(e.target.value))}
                                className="w-full accent-purple-500"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-2 flex justify-between">
                            <span>Repetition Penalty</span>
                            <span className="text-purple-400">{repetitionPenalty}</span>
                        </label>
                        <input
                            type="range"
                            min="1.0"
                            max="10.0"
                            step="0.1"
                            value={repetitionPenalty}
                            onChange={(e) => setRepetitionPenalty(parseFloat(e.target.value))}
                            className="w-full accent-purple-500"
                        />
                    </div>
                </div>
            )}
        </div>
    );
}
