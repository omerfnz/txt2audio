import { useState, useEffect, useCallback, useRef } from 'react';
import type { WebSocketMessage } from '../types';

const RECONNECT_INTERVAL = 3000;

export const useWebSocket = () => {
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const getWsUrl = () => {
    const envUrl = import.meta.env.VITE_WS_URL as string | undefined;
    if (envUrl) return envUrl;

    const hostname = window.location.hostname;
    const isLocal = hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0';
    
    if (isLocal) {
      return 'ws://localhost:8000/api/ws';
    }

    // CloudSpaces/Lightning AI için aynı domain farklı port
    if (hostname.includes('cloudspaces.litng.ai') || hostname.includes('litng.ai')) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const port = window.location.port;
      let backendPort = '8000';
      
      // Eğer port varsa ve 5173 veya 4173 ise, 8000'e çevir
      if (port === '5173' || port === '4173') {
        backendPort = '8000';
      } else if (port) {
        backendPort = port;
      }
      
      return `${protocol}//${hostname}:${backendPort}/api/ws`;
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
        reconnectTimeoutRef.current = setTimeout(connect, RECONNECT_INTERVAL);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      reconnectTimeoutRef.current = setTimeout(connect, RECONNECT_INTERVAL);
    }
  }, []);

  useEffect(() => {
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
