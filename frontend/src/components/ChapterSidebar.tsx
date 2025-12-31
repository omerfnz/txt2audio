import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ChapterList } from './ChapterList';
import { getChapters } from '@/api/client';
import { Chapter } from '@/types';
import { BookOpen } from 'lucide-react';

interface ChapterSidebarProps {
  projectId: number;
  onChapterClick?: (chunkIndex: number) => void;
  selectedChunkIndex?: number | null;
}

export const ChapterSidebar = ({
  projectId,
  onChapterClick,
  selectedChunkIndex,
}: ChapterSidebarProps) => {
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchChapters = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await getChapters(projectId);
        setChapters(
          response.chapters.map((ch) => ({
            title: ch.title,
            order: ch.order,
            chunk_index: ch.chunk_index,
          }))
        );
      } catch (err) {
        console.error('Failed to fetch chapters:', err);
        setError('Failed to load chapters');
      } finally {
        setLoading(false);
      }
    };

    if (projectId) {
      fetchChapters();
    }
  }, [projectId]);

  return (
    <Card className="flex flex-col h-full border-none bg-background/50 shadow-xl ring-1 ring-border/50">
      <CardHeader className="bg-muted/30 border-b border-border/50 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="w-3 h-3 text-muted-foreground" />
            <CardTitle className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">
              Chapters
            </CardTitle>
          </div>
          {chapters.length > 0 && (
            <Badge variant="outline" className="text-[9px] border-border/50 font-mono">
              {chapters.length}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-4">
        {loading ? (
          <div className="text-center text-muted-foreground py-8 text-sm">
            Loading chapters...
          </div>
        ) : error ? (
          <div className="text-center text-destructive py-8 text-sm">
            {error}
          </div>
        ) : (
          <ScrollArea className="h-full">
            <ChapterList
              chapters={chapters}
              onChapterClick={onChapterClick}
              selectedChunkIndex={selectedChunkIndex}
            />
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
};
