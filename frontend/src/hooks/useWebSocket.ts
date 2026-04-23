import { useEffect, useRef, useState, useCallback } from "react";
import type { WsEvent } from "../types";

const WS_URL = `ws://${window.location.host}/ws`;

export function useWebSocket(onEvent: (e: WsEvent) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const connect = useCallback(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      // Reconnect after 3s
      setTimeout(connect, 3000);
    };
    ws.onerror = () => ws.close();
    ws.onmessage = (msg) => {
      try {
        const event: WsEvent = JSON.parse(msg.data);
        onEventRef.current(event);
      } catch {
        // ignore malformed frames
      }
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected };
}
