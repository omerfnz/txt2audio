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

    const isLocal = typeof window !== 'undefined' && window.location.hostname === 'localhost';
    if (isLocal) {
      return 'ws://localhost:8000/api/ws';
    }

    // CloudSpaces/Lightning AI için aynı domain farklı port
    if (window.location.hostname.includes('cloudspaces.litng.ai') || window.location.hostname.includes('litng.ai')) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const hostname = window.location.hostname;
      // Frontend portundan backend portuna geçiş
      const backendPort = hostname.includes('5173') ? hostname.replace('5173', '8000') :
                         hostname.includes('4173') ? hostname.replace('4173', '8000') : hostname;
      return `${protocol}//${backendPort}/api/ws`;
    }

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
