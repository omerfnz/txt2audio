import { useRef } from 'react';
import { Upload, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';

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
        <Card
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={(e) => {
                const target = e.target as HTMLElement;
                if (target === e.currentTarget || target.closest('.drop-zone-content')) {
                    textInputRef.current?.click();
                }
            }}
            className={cn(
                "border-2 border-dashed p-12 text-center transition-all duration-300 cursor-pointer relative overflow-hidden group",
                isDragging ? "border-primary bg-primary/10 scale-105" : "border-border hover:border-primary/50 hover:bg-accent/50"
            )}
        >
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-primary/5 to-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            <CardContent className="p-0">
                <div className="flex flex-col items-center gap-6 relative z-10 drop-zone-content">
                    <div className={cn(
                        "p-6 rounded-2xl transition-all duration-300",
                        isDragging ? "bg-primary scale-110 shadow-lg shadow-primary/50" : "bg-muted group-hover:scale-105"
                    )}>
                        <Upload className={cn("w-10 h-10 transition-colors", isDragging ? "text-primary-foreground" : "text-primary")} />
                    </div>
                    <div>
                        <p className="text-xl font-semibold text-foreground mb-2">Drag & Drop files here</p>
                        <p className="text-sm text-muted-foreground">or click to browse your files</p>
                    </div>
                </div>

                <div className="grid md:grid-cols-2 gap-6 mt-10">
                    <Card
                        onClick={(e) => {
                            e.stopPropagation();
                            textInputRef.current?.click();
                        }}
                        className={cn(
                            "p-6 border-2 flex items-center gap-4 cursor-pointer transition-all duration-300 group/card",
                            selectedFile ? "bg-primary/10 border-primary" : "bg-card border-border hover:border-primary/50 hover:bg-accent/50"
                        )}
                    >
                        <div className={cn("p-3 rounded-xl transition-all", selectedFile ? "bg-primary" : "bg-muted group-hover/card:bg-primary/20")}>
                            <FileText className={cn("w-7 h-7", selectedFile ? "text-primary-foreground" : "text-primary")} />
                        </div>
                        <div className="text-left overflow-hidden flex-1">
                            <p className="text-sm font-semibold text-foreground truncate mb-1">
                                {selectedFile ? selectedFile.name : "Select Text File"}
                            </p>
                            <p className="text-xs text-muted-foreground">.txt</p>
                        </div>
                        <input
                            type="file"
                            ref={textInputRef}
                            className="hidden"
                            accept=".txt"
                            onChange={(e) => e.target.files?.[0] && onFileSelect(e.target.files[0])}
                        />
                    </Card>

                    <Card className="p-6 border-2 border-border bg-card flex items-center justify-center">
                        <p className="text-sm text-muted-foreground">Choose voice option below →</p>
                    </Card>
                </div>
            </CardContent>
        </Card>
    );
}
