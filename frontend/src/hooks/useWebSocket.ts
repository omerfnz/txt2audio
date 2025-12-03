import { useState, useEffect, useCallback, useRef } from 'react';
import type { WebSocketMessage } from '../types';

const RECONNECT_INTERVAL = 3000;

export const useWebSocket = () => {
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const getWsUrl = () => {
    if (window.location.hostname === 'localhost') {
      return 'ws://localhost:8000/api/ws';
    }
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname.replace('4173', '8000');
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
