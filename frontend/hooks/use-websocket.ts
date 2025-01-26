import { useEffect, useState, useCallback, useRef } from "react";

interface VehicleMessage {
  id?: number | string; // Allow both number (DB) and string (WebSocket) IDs
  timestamp: string;
  vehicle_id: string;
  message: string;
  type: "vehicle_update";
  state: {
    latitude: number;
    longitude: number;
    speed: number;
    battery: number;
    status: string;
  };
}

const WEBSOCKET_URL = "ws://localhost:8000/ws";
const RECONNECT_DELAY = 2000; // 2 seconds
const API_BASE_URL = "http://localhost:8000";

export function useWebSocket() {
  const [messages, setMessages] = useState<VehicleMessage[]>([]);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messageCounterRef = useRef(0); // Use ref for message counter

  // Fetch historical messages
  const fetchHistoricalMessages = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch(`${API_BASE_URL}/messages?limit=50`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const historicalMessages = await response.json();

      // Validate message format for historical messages
      const validMessages = historicalMessages.filter((msg: any) => {
        return (
          msg &&
          typeof msg.id === "number" &&
          typeof msg.message === "string" &&
          typeof msg.vehicle_id === "string" &&
          typeof msg.timestamp === "string"
        );
      });

      // Only set historical messages if we don't have any messages yet
      setMessages((currentMessages) =>
        currentMessages.length === 0 ? validMessages : currentMessages,
      );
    } catch (error) {
      console.error("Error fetching historical messages:", error);
      setError(
        error instanceof Error ? error.message : "Failed to fetch messages",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initialize WebSocket connection
  const connectWebSocket = useCallback(() => {
    const ws = new WebSocket(WEBSOCKET_URL);

    ws.onopen = () => {
      console.log("WebSocket connected");
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // Less strict validation for real-time messages
        if (
          data &&
          typeof data.message === "string" &&
          typeof data.vehicle_id === "string" &&
          typeof data.timestamp === "string" &&
          typeof data.state === "object"
        ) {
          messageCounterRef.current += 1;
          const messageWithId = {
            ...data,
            id: `${data.vehicle_id}-${Date.now()}-${messageCounterRef.current}`,
          };
          setMessages((prev) => [...prev, messageWithId].slice(-50)); // Keep last 50 messages
        } else {
          console.warn("Received invalid message format:", data);
        }
      } catch (error) {
        console.error("Error processing WebSocket message:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setIsConnected(false);
      setError("WebSocket connection error");
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setIsConnected(false);
      // Attempt to reconnect after delay
      setTimeout(() => {
        console.log("Attempting to reconnect...");
        connectWebSocket();
      }, RECONNECT_DELAY);
    };

    setSocket(ws);

    return ws;
  }, []);

  // Set up WebSocket connection and cleanup
  useEffect(() => {
    const ws = connectWebSocket();
    fetchHistoricalMessages(); // Fetch historical messages after WebSocket is connected

    return () => {
      ws.close();
    };
  }, [fetchHistoricalMessages, connectWebSocket]);

  return {
    messages,
    socket,
    isLoading,
    isConnected,
    error,
  };
}
