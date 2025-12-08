import { useRef, useState, useCallback, useEffect } from 'react';

// WebSocket URL helper
const getWebSocketUrl = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname === 'localhost' 
        ? 'localhost:8000' 
        : window.location.hostname.replace('4173', '8000');
    return `${protocol}//${host}/ws/generate-f5`;
};

export const useF5TTS = () => {
    const socketRef = useRef<WebSocket | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const nextStartTimeRef = useRef<number>(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isConnected, setIsConnected] = useState(false);

    // Initialize AudioContext (must be user interaction triggered usually)
    const initAudioContext = () => {
        if (!audioContextRef.current) {
            const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
            audioContextRef.current = new AudioContextClass();
        }
        if (audioContextRef.current.state === 'suspended') {
            audioContextRef.current.resume();
        }
    };

    const stop = useCallback(() => {
        if (socketRef.current) {
            socketRef.current.close();
            socketRef.current = null;
        }
        if (audioContextRef.current) {
            audioContextRef.current.close();
            audioContextRef.current = null;
        }
        setIsPlaying(false);
        setIsConnected(false);
        nextStartTimeRef.current = 0;
    }, []);

    const speak = useCallback((text: string, refAudioPath: string, refText?: string, speed: number = 1.0) => {
        // Reset state
        stop();
        initAudioContext();
        
        const url = getWebSocketUrl();
        console.log("Connecting to F5 WebSocket:", url);
        
        socketRef.current = new WebSocket(url);

        socketRef.current.onopen = () => {
            console.log("F5 WebSocket Connected");
            setIsConnected(true);
            setIsPlaying(true);
            
            if (audioContextRef.current) {
                nextStartTimeRef.current = audioContextRef.current.currentTime + 0.1; // Small buffer
            }

            // Send config
            socketRef.current?.send(JSON.stringify({
                text,
                ref_audio_path: refAudioPath,
                ref_text: refText,
                speed
            }));
        };

        socketRef.current.onmessage = async (event) => {
            if (typeof event.data === 'string') {
                if (event.data === "END_OF_STREAM") {
                    console.log("F5 Stream Finished");
                    setIsPlaying(false);
                    // Don't close immediately if audio is still playing in queue?
                    // For now, let's keep it open until user stops or new request
                    socketRef.current?.close();
                } else if (event.data.startsWith("ERROR:")) {
                    console.error("F5 Error:", event.data);
                    alert(event.data);
                    setIsPlaying(false);
                    socketRef.current?.close();
                }
                return;
            }

            // Binary Audio Data
            if (event.data instanceof Blob) {
                const arrayBuffer = await event.data.arrayBuffer();
                const ctx = audioContextRef.current;
                
                if (!ctx) return;

                try {
                    const decodedBuffer = await ctx.decodeAudioData(arrayBuffer);
                    const source = ctx.createBufferSource();
                    source.buffer = decodedBuffer;
                    source.connect(ctx.destination);

                    // Scheduler Logic
                    const scheduleTime = Math.max(ctx.currentTime, nextStartTimeRef.current);
                    source.start(scheduleTime);
                    
                    nextStartTimeRef.current = scheduleTime + decodedBuffer.duration;
                } catch (error) {
                    console.error("Audio decode error:", error);
                }
            }
        };

        socketRef.current.onerror = (error) => {
            console.error("WebSocket Error:", error);
            setIsPlaying(false);
            setIsConnected(false);
        };

        socketRef.current.onclose = () => {
            console.log("WebSocket Closed");
            setIsConnected(false);
        };

    }, [stop]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            stop();
        };
    }, [stop]);

    return { speak, stop, isPlaying, isConnected };
};

