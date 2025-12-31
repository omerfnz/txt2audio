import type { Chapter } from '@/types';
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
            'hover:bg-primary/10 hover:ring-1 hover:ring-primary/20 active:scale-[0.98]',
            'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
            selectedChunkIndex === chapter.chunk_index && 'bg-primary/10 ring-2 ring-primary'
          )}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Chapter clicked:', chapter.title, 'chunk_index:', chapter.chunk_index);
            if (onChapterClick) {
              onChapterClick(chapter.chunk_index);
            } else {
              console.warn('onChapterClick is not defined');
            }
          }}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              if (onChapterClick) {
                onChapterClick(chapter.chunk_index);
              }
            }
          }}
        >
          <div className="flex items-center gap-2 w-full">
            <BookOpen className="w-4 h-4 text-primary shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-foreground truncate">
                {chapter.title}
              </div>
              {chapter.timestamp_formatted ? (
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="text-[10px] font-mono text-primary bg-primary/10 px-1.5 py-0.5 rounded">
                    {chapter.timestamp_formatted}
                  </span>
                  <span className="text-[9px] text-muted-foreground/70">YouTube timestamp</span>
                </div>
              ) : (
                <div className="text-[9px] text-muted-foreground/50 mt-0.5 italic">
                  Timestamp available after completion
                </div>
              )}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
};
