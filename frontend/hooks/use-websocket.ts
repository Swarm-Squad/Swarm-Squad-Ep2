import { useEffect, useState } from 'react';

interface VehicleMessage {
  timestamp: string;
  vehicle_id: string;
  message: string;
  type: 'vehicle_update';
}

export function useWebSocket() {
  const [messages, setMessages] = useState<VehicleMessage[]>([]);
  const [socket, setSocket] = useState<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prev) => [...prev, data].slice(-50)); // Keep last 50 messages
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    setSocket(ws);

    return () => {
      ws.close();
    };
  }, []);

  return { messages, socket };
} 