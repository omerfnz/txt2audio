import { useState, useEffect, useCallback, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import { getProjectStatus } from '../api/client';
import axios from 'axios';
import type { ChunkData, LogEntry } from '../types';

// Helper to get API base URL
const getApiBase = () => {
  // Development mode
  if (import.meta.env.DEV) {
    return 'http://localhost:8000/api';
  }

  // Production mode - same domain, different port
  const protocol = window.location.protocol;
  const host = window.location.hostname.replace('4173', '8000').replace('5173', '8000');
  return `${protocol}//${host}/api`;
};

export const useProjectStatus = (projectId: number | null) => {
  const [status, setStatus] = useState<string>('idle');
  const [progress, setProgress] = useState<number>(0);
  const [chunks, setChunks] = useState<ChunkData[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [processingStartTime, setProcessingStartTime] = useState<Date | null>(null);
  const [estimatedEndTime, setEstimatedEndTime] = useState<Date | null>(null);

  const lastMessage = useWebSocket();

  const addLog = useCallback((message: string) => {
    setLogs(prev => [...prev, { message, timestamp: new Date() }]);
  }, []);

  // Load project data
  useEffect(() => {
    if (!projectId) {
      setStatus('idle');
      setProgress(0);
      setChunks([]);
      setLogs([]);
      setProcessingStartTime(null);
      setEstimatedEndTime(null);
      return;
    }

    const loadProject = async () => {
      try {
        const projectData = await getProjectStatus(projectId);
        setStatus(projectData.status);
        setProgress(projectData.progress || 0);

        // Load chunks
        const chunksResponse = await axios.get<{ chunks: Array<{ index: number; is_processed: boolean; text?: string }> }>(
          `${getApiBase()}/projects/${projectId}/chunks`
        );
        
        setChunks(chunksResponse.data.chunks.map(c => ({
          index: c.index,
          isProcessed: c.is_processed,
          text: c.text,
        })));

        // Restore start time from local storage if processing
        if (projectData.status === 'processing' || projectData.status === 'merging') {
          const savedTime = localStorage.getItem(`processingStartTime_${projectId}`);
          if (savedTime) {
            setProcessingStartTime(new Date(savedTime));
          } else {
             // If no saved time but processing, set it to now (or estimate)
             const now = new Date();
             if (projectData.progress && projectData.progress > 0) {
                 // Estimate start time based on progress
                 const estimatedElapsed = (projectData.progress / 100) * 3600000; // Rough estimate
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

    // Filter messages for current project if project_id is present
    if (lastMessage.project_id && lastMessage.project_id !== projectId) return;

      if (lastMessage.type === 'status_update') {
      const newStatus = lastMessage.status || 'unknown';
      
      // Special handling for chunk_skipped: don't change the overall status
      if (newStatus === 'chunk_skipped') {
        // Just log the skipped chunk, don't change the overall status to "chunk_skipped"
        const chunkIndex = lastMessage.chunk_index;
        const message = lastMessage.message || `Chunk ${chunkIndex} skipped`;
        addLog(`⚠️ ${message}`);
        // Don't update status or processingStartTime - keep processing
        return;
      }
      
      setStatus(newStatus);
      if (lastMessage.progress !== undefined) {
        setProgress(lastMessage.progress);
      }
      
      if ((newStatus === 'processing' || newStatus === 'merging') && !processingStartTime) {
        const now = new Date();
        setProcessingStartTime(now);
        localStorage.setItem(`processingStartTime_${projectId}`, now.toISOString());
      }
      
      addLog(`Status: ${newStatus} (${lastMessage.progress || 0}%)`);
      } else if (lastMessage.type === 'progress_update') {
      const newProgress = lastMessage.progress || 0;
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

        if (lastMessage.chunk_text_preview) {
          const preview = lastMessage.chunk_text_preview.replace(/\s+/g, ' ').trim();
          const shortPreview = preview.length > 80 ? `${preview.slice(0, 80)}…` : preview;
          addLog(`Processed chunk ${chunkIndex}: "${shortPreview}"`);
        } else {
          addLog(`Processed chunk ${chunkIndex}`);
        }
      } else if (status === 'merging') {
        addLog(`Merging progress: ${newProgress.toFixed(1)}%`);
      }
    }
  }, [lastMessage, projectId, addLog, processingStartTime, status]);

  // Calculate estimated end time
  const prevRemainingRef = useRef<number | null>(null);

  useEffect(() => {
    if ((status === 'processing' || status === 'merging') && processingStartTime && progress > 2 && progress < 100) {
      const now = Date.now();
      const elapsed = now - processingStartTime.getTime();
      
      // Wait for at least 5 seconds of data and 2% progress
      if (elapsed > 5000) {
        // Raw estimate based on cumulative average speed
        const estimatedTotalDuration = (elapsed / progress) * 100;
        const rawRemaining = estimatedTotalDuration - elapsed;
        
        let finalRemaining = rawRemaining;

        // Apply smoothing if we have a previous estimate
        // Weight: 70% previous estimate, 30% new calculation
        // This prevents jitter when instantaneous speed fluctuates
        if (prevRemainingRef.current !== null) {
          // Adjust previous remaining time by subtracting the time passed since last update
          // This is tricky in useEffect, so we just smooth the absolute value
          finalRemaining = (prevRemainingRef.current * 0.7) + (rawRemaining * 0.3);
        }
        
        if (finalRemaining < 0) finalRemaining = 0;

        prevRemainingRef.current = finalRemaining;
        setEstimatedEndTime(new Date(now + finalRemaining));
      }
    } else if (status === 'completed' || status === 'failed' || progress >= 100) {
      setEstimatedEndTime(null);
      prevRemainingRef.current = null;
      if (projectId && (status === 'completed' || status === 'failed')) {
        localStorage.removeItem(`processingStartTime_${projectId}`);
      }
    } else if (progress <= 2) {
      // Not enough data for estimation
      setEstimatedEndTime(null);
      prevRemainingRef.current = null;
    }
  }, [status, progress, processingStartTime, projectId]);

  return {
    status,
    progress,
    chunks,
    logs,
    processingStartTime,
    estimatedEndTime
  };
};
