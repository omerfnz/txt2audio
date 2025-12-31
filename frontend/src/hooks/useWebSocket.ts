import { useState, useEffect, useCallback, useRef } from 'react';
import type { WebSocketMessage } from '../types';

const RECONNECT_INTERVAL = 3000;

export const useWebSocket = () => {
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const connectRef = useRef<(() => void) | undefined>(undefined);

  const getWsUrl = () => {
    const envUrl = import.meta.env.VITE_WS_URL as string | undefined;
    if (envUrl) return envUrl;

    const hostname = window.location.hostname;
    const isLocal = hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0';
    
    if (isLocal) {
      return 'ws://localhost:8000/api/ws';
    }

    // CloudSpaces/Lightning AI için
    if (hostname.includes('cloudspaces.litng.ai') || hostname.includes('litng.ai')) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      
      // CloudSpaces'te her portun kendi subdomain'i var.
      // 5173 (frontend) üzerinden geliyorsak, 8000 (backend) subdomain'ine gitmeliyiz.
      if (hostname.startsWith('5173-') || hostname.startsWith('4173-')) {
        const backendHostname = hostname.replace(/^(5173|4173)-/, '8000-');
        const wsUrl = `${protocol}//${backendHostname}/api/ws`;
        console.log('Lightning AI Direct WS URL:', wsUrl);
        return wsUrl;
      }
      
      // Eğer zaten 8000- ile başlıyorsa (backend subdomain)
      if (hostname.startsWith('8000-')) {
        return `${protocol}//${hostname}/api/ws`;
      }
      
      // Fallback: Aynı hostname, port 8000 ekle
      return `${protocol}//${hostname}:8000/api/ws`;
    }

    // Fallback: Aynı host ve port, sadece protocol değişikliği
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host; // port dahil
    return `${protocol}//${host}/api/ws`;
  };

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(getWsUrl());

      ws.onopen = () => {
        console.log('Connected to WebSocket');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'ping') {
            ws.send(JSON.stringify({ type: 'pong' }));
            return;
          }
          setLastMessage(data);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected. Reconnecting...');
        wsRef.current = null;
        if (connectRef.current) {
          reconnectTimeoutRef.current = setTimeout(connectRef.current, RECONNECT_INTERVAL);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      const connectFn = connectRef.current;
      if (connectFn) {
        reconnectTimeoutRef.current = setTimeout(connectFn, RECONNECT_INTERVAL);
      }
    }
  }, []);

  useEffect(() => {
    // Store connect in ref to avoid closure issues
    connectRef.current = connect;
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  return lastMessage;
};
