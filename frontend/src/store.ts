import { create } from 'zustand';

interface Chunk {
    index: number;
    isProcessed: boolean;
}

interface ProjectState {
    currentProjectId: number | null;
    status: string;
    progress: number;
    chunks: Chunk[];
    setCurrentProject: (id: number) => void;
    updateStatus: (status: string, progress: number) => void;
    updateChunk: (index: number, isProcessed: boolean) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
    currentProjectId: null,
    status: 'idle',
    progress: 0,
    chunks: [],
    
    setCurrentProject: (id: number) => set({ currentProjectId: id }),
    
    updateStatus: (status: string, progress: number) => set({ status, progress }),
    
    updateChunk: (index: number, isProcessed: boolean) => set((state) => {
        const newChunks = [...state.chunks];
        newChunks[index] = { index, isProcessed };
        return { chunks: newChunks };
    }),
}));

