import { useEffect, useRef, useState } from "react";

interface WebSocketMessage {
  type: "status_update" | "progress_update" | "ping" | "error";
  status?: string;
  progress?: number;
  chunk_index?: number;
  project_id?: number;
  error?: string;
}

// Lightning AI ve localhost uyumlu dinamik WebSocket URL
const getWsUrl = () => {
  const isLocalhost = window.location.hostname === 'localhost';
  if (isLocalhost) {
    return "ws://localhost:8000/api/ws";
  }
  // Lightning AI için wss:// kullan ve portu değiştir
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = window.location.hostname.replace('4173', '8000');
  return `${wsProtocol}//${wsHost}/api/ws`;
};

const WS_URL = getWsUrl();

export function useWebSocket(): WebSocketMessage | null {
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 3;

  useEffect(() => {
    const connect = () => {
      try {
        if (ws.current?.readyState === WebSocket.OPEN) {
          return; // Already connected
        }

        console.log(`🔌 WebSocket connecting to ${WS_URL}...`);
        ws.current = new WebSocket(WS_URL);

        ws.current.onopen = () => {
          console.log("✓ WebSocket Connected");
          reconnectAttempts.current = 0;
        };

        ws.current.onmessage = (event: MessageEvent<string>) => {
          try {
            const message = JSON.parse(event.data) as WebSocketMessage;
            if (message.type !== "ping") {
              console.log("📨 WebSocket message:", message);
            }
            setLastMessage(message);
          } catch (e) {
            console.error("Error parsing WS message:", e);
          }
        };

        ws.current.onerror = () => {
          console.error("❌ WebSocket error");
        };

        ws.current.onclose = () => {
          console.log("✗ WebSocket Disconnected");

          // Otomatik reconnect
          if (reconnectAttempts.current < maxReconnectAttempts) {
            reconnectAttempts.current++;
            console.log(
              `🔄 Reconnecting... (${reconnectAttempts.current}/${maxReconnectAttempts})`
            );
            setTimeout(connect, 2000);
          } else {
            console.warn("⚠ WebSocket connection failed - polling fallback");
            // Fallback: REST API ile poll et
            setupPolling();
          }
        };
      } catch (e) {
        console.error("Failed to create WebSocket:", e);
      }
    };

    const setupPolling = () => {
      // WebSocket başarısız olursa REST API ile poll et
      console.log("📡 Starting REST API polling...");
      // Bu kısım opsiyonel - sonra implemente edilebilir
    };

    connect();

    return () => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.close();
      }
    };
  }, []);

  return lastMessage;
}
