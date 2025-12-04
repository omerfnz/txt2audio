export interface Project {
  id: number;
  name: string;
  status: 'created' | 'processing' | 'merging' | 'completed' | 'failed';
  created_at: string;
  audio_path?: string;
  total_chunks?: number;
  processed_chunks?: number;
  progress?: number;
}

export interface ChunkData {
  index: number;
  isProcessed: boolean;
  text?: string;
}

export interface LogEntry {
  message: string;
  timestamp: Date;
}

export interface WebSocketMessage {
  type: 'status_update' | 'progress_update' | 'ping';
  status?: string;
  progress?: number;
  chunk_index?: number;
  chunk_text_preview?: string;
  project_id?: number;
  error?: string;
}
