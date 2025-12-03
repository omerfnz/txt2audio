import { useRef } from 'react';
import { Upload, FileText } from 'lucide-react';
import { clsx } from 'clsx';

interface DropZoneProps {
    onFileSelect: (file: File) => void;
    selectedFile: File | null;
    isDragging: boolean;
    onDragOver: (e: React.DragEvent<HTMLDivElement>) => void;
    onDragLeave: () => void;
    onDrop: (e: React.DragEvent<HTMLDivElement>) => void;
}

export function DropZone({
    onFileSelect,
    selectedFile,
    isDragging,
    onDragOver,
    onDragLeave,
    onDrop
}: DropZoneProps) {
    const textInputRef = useRef<HTMLInputElement>(null);

    return (
        <div
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={(e) => {
                const target = e.target as HTMLElement;
                if (target === e.currentTarget || target.closest('.drop-zone-content')) {
                    textInputRef.current?.click();
                }
            }}
            className={clsx(
                "border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 cursor-pointer relative overflow-hidden group",
                isDragging ? "border-indigo-500 bg-indigo-500/10 scale-105" : "border-slate-600 hover:border-indigo-500/50 hover:bg-slate-800/50"
            )}
        >
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-purple-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            <div className="flex flex-col items-center gap-6 relative z-10 drop-zone-content">
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
                <div
                    onClick={(e) => {
                        e.stopPropagation();
                        textInputRef.current?.click();
                    }}
                    className={clsx(
                        "p-6 rounded-2xl border-2 flex items-center gap-4 cursor-pointer transition-all duration-300 group/card",
                        selectedFile ? "bg-indigo-500/10 border-indigo-500 glow" : "bg-slate-900/50 border-slate-700 hover:border-indigo-500/50 hover:bg-slate-800/50"
                    )}
                >
                    <div className={clsx("p-3 rounded-xl transition-all", selectedFile ? "bg-indigo-500" : "bg-slate-800 group-hover/card:bg-indigo-500/20")}>
                        <FileText className={clsx("w-7 h-7", selectedFile ? "text-white" : "text-indigo-400")} />
                    </div>
                    <div className="text-left overflow-hidden flex-1">
                        <p className="text-sm font-semibold text-slate-100 truncate mb-1">
                            {selectedFile ? selectedFile.name : "Select Text File"}
                        </p>
                        <p className="text-xs text-slate-400">.txt, .epub</p>
                    </div>
                    <input
                        type="file"
                        ref={textInputRef}
                        className="hidden"
                        accept=".txt,.epub"
                        onChange={(e) => e.target.files?.[0] && onFileSelect(e.target.files[0])}
                    />
                </div>

                <div className="p-6 rounded-2xl border-2 border-slate-700 bg-slate-900/50 flex items-center justify-center">
                    <p className="text-sm text-slate-400">Choose voice option below →</p>
                </div>
            </div>
        </div>
    );
}
