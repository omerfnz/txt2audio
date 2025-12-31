import { useState, useEffect, useCallback, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import { getProjectStatus, getApiBase } from '../api/client';
import axios from 'axios';
import type { ChunkData, LogEntry } from '../types';

export const useProjectStatus = (projectId: number | null) => {
  const [status, setStatus] = useState<string>('idle');
  const [progress, setProgress] = useState<number>(0);
  const [chunks, setChunks] = useState<ChunkData[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [processingStartTime, setProcessingStartTime] = useState<Date | null>(null);
  const [estimatedEndTime, setEstimatedEndTime] = useState<Date | null>(null);
  const [speed, setSpeed] = useState<number | null>(null); // chunks per minute
  
  const lastMessage = useWebSocket();
  const prevRemainingRef = useRef<number | null>(null);

  const addLog = useCallback((message: string) => {
    setLogs(prev => [...prev, { message, timestamp: new Date() }]);
  }, []);

  // Load project data
  useEffect(() => {
    if (!projectId) {
      // Use setTimeout to avoid setState in effect
      setTimeout(() => {
        setStatus('idle');
        setProgress(0);
        setChunks([]);
        setLogs([]);
        setProcessingStartTime(null);
        setEstimatedEndTime(null);
        setSpeed(null);
      }, 0);
      return;
    }

    const loadProject = async () => {
      try {
        const projectData = await getProjectStatus(projectId);
        setStatus(projectData.status);
        setProgress(projectData.progress || 0);

        // Preference backend startedAt
        if (projectData.started_at) {
            setProcessingStartTime(new Date(projectData.started_at));
        }

        // Load chunks
        const chunksResponse = await axios.get<{ chunks: Array<{ index: number; is_processed: boolean; text?: string }> }>(
          `${getApiBase()}/projects/${projectId}/chunks`
        );
        
        const loadedChunks = chunksResponse.data.chunks.map(c => ({
          index: c.index,
          isProcessed: c.is_processed,
          text: c.text,
        }));
        setChunks(loadedChunks);

        // Fallback for processingStartTime if backend doesn't have it yet (legacy or new project)
        if (!projectData.started_at && (projectData.status === 'processing' || projectData.status === 'merging')) {
          const savedTime = localStorage.getItem(`processingStartTime_${projectId}`);
          if (savedTime) {
            setProcessingStartTime(new Date(savedTime));
          } else {
             const now = new Date();
             if (projectData.progress && projectData.progress > 0) {
                 const estimatedElapsed = (projectData.progress / 100) * 3600000;
                 const estimatedStart = new Date(now.getTime() - estimatedElapsed);
                 setProcessingStartTime(estimatedStart);
                 localStorage.setItem(`processingStartTime_${projectId}`, estimatedStart.toISOString());
             } else {
                 setProcessingStartTime(now);
                 localStorage.setItem(`processingStartTime_${projectId}`, now.toISOString());
             }
          }
        }
      } catch (error) {
        console.error('Failed to load project:', error);
        addLog(`Error loading project: ${error}`);
      }
    };

    loadProject();
  }, [projectId, addLog]);

  // Handle WebSocket messages
  useEffect(() => {
    if (!lastMessage || !projectId) return;
    if (lastMessage.project_id && lastMessage.project_id !== projectId) return;

    if (lastMessage.type === 'status_update') {
      const newStatus = lastMessage.status || 'unknown';
      
      if (newStatus === 'chunk_skipped') {
        const chunkIndex = lastMessage.chunk_index;
        const message = lastMessage.message || `Chunk ${chunkIndex} skipped`;
        // Use setTimeout to avoid setState in effect
        setTimeout(() => addLog(`⚠️ ${message}`), 0);
        return;
      }
      
      // Use setTimeout to avoid setState in effect
      setTimeout(() => {
        setStatus(newStatus);
        if (lastMessage.progress !== undefined) {
          setProgress(lastMessage.progress);
        }
        
        if ((newStatus === 'processing' || newStatus === 'merging') && !processingStartTime) {
          const now = new Date();
          setProcessingStartTime(now);
          localStorage.setItem(`processingStartTime_${projectId}`, now.toISOString());
        }
      }, 0);
      
      setTimeout(() => addLog(`Status: ${newStatus} (${lastMessage.progress || 0}%)`), 0);
    } else if (lastMessage.type === 'progress_update') {
      const newProgress = lastMessage.progress || 0;
      // Use setTimeout to avoid setState in effect
      setTimeout(() => {
        setProgress(newProgress);

        if (lastMessage.chunk_index !== undefined) {
          const chunkIndex = lastMessage.chunk_index;
          setChunks(prev => {
            const newChunks = [...prev];
            if (newChunks[chunkIndex]) {
              newChunks[chunkIndex].isProcessed = true;
              if (lastMessage.chunk_text_preview) {
                newChunks[chunkIndex].text = lastMessage.chunk_text_preview;
              }
            }
            return newChunks;
          });
        }

        if (lastMessage.chunk_index !== undefined) {
          if (lastMessage.chunk_text_preview) {
            const preview = lastMessage.chunk_text_preview.replace(/\s+/g, ' ').trim();
            const shortPreview = preview.length > 80 ? `${preview.slice(0, 80)}…` : preview;
            setTimeout(() => addLog(`Processed chunk ${lastMessage.chunk_index}: "${shortPreview}"`), 0);
          } else {
            setTimeout(() => addLog(`Processed chunk ${lastMessage.chunk_index}`), 0);
          }
        }
      }, 0);

      if (status === 'merging') {
        setTimeout(() => addLog(`Merging progress: ${newProgress.toFixed(1)}%`), 0);
      }
    }
  }, [lastMessage, projectId, addLog, processingStartTime, status]);

  // Calculate estimated end time and speed
  useEffect(() => {
    if ((status === 'processing' || status === 'merging') && processingStartTime && progress > 1 && progress < 100) {
      const now = Date.now();
      const elapsedMs = now - processingStartTime.getTime();
      
      // Raw estimate based on cumulative average speed
      const estimatedTotalDuration = (elapsedMs / progress) * 100;
      const rawRemaining = estimatedTotalDuration - elapsedMs;
      
      let finalRemaining = rawRemaining;

      // Smoothing
      if (prevRemainingRef.current !== null) {
        finalRemaining = (prevRemainingRef.current * 0.8) + (rawRemaining * 0.2);
      }
      
      if (finalRemaining < 0) finalRemaining = 0;
      prevRemainingRef.current = finalRemaining;
      // Use setTimeout to avoid setState in effect
      setTimeout(() => setEstimatedEndTime(new Date(now + finalRemaining)), 0);

      // Speed calculation: (processed_chunks / elapsed_minutes)
      const processedCount = chunks.filter(c => c.isProcessed).length;
      const elapsedMin = elapsedMs / 60000;
      if (elapsedMin > 0.05) { // At least 3 seconds
          setTimeout(() => setSpeed(processedCount / elapsedMin), 0);
      }
    } else if (status === 'completed' || status === 'failed' || progress >= 100) {
      // Use setTimeout to avoid setState in effect
      setTimeout(() => {
        setEstimatedEndTime(null);
        setSpeed(null);
      }, 0);
      prevRemainingRef.current = null;
      if (projectId && (status === 'completed' || status === 'failed')) {
        localStorage.removeItem(`processingStartTime_${projectId}`);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, progress, processingStartTime, projectId, chunks.length]);

  return {
    status,
    progress,
    chunks,
    logs,
    processingStartTime,
    estimatedEndTime,
    speed
  };
};
