import { Chapter } from '@/types';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { BookOpen } from 'lucide-react';

interface ChapterListProps {
  chapters: Chapter[];
  onChapterClick?: (chunkIndex: number) => void;
  selectedChunkIndex?: number | null;
}

export const ChapterList = ({ chapters, onChapterClick, selectedChunkIndex }: ChapterListProps) => {
  if (chapters.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8 text-sm">
        No chapters detected
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {chapters.map((chapter) => (
        <Card
          key={chapter.order}
          className={cn(
            'p-3 cursor-pointer transition-all duration-200 border-none',
            'hover:bg-primary/10 hover:ring-1 hover:ring-primary/20',
            selectedChunkIndex === chapter.chunk_index && 'bg-primary/10 ring-2 ring-primary'
          )}
          onClick={() => onChapterClick?.(chapter.chunk_index)}
        >
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-primary shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-foreground truncate">
                {chapter.title}
              </div>
              {chapter.timestamp_formatted && (
                <div className="text-xs text-muted-foreground mt-0.5">
                  {chapter.timestamp_formatted}
                </div>
              )}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};
