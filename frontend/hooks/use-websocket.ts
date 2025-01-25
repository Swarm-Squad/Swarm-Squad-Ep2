import { useEffect, useState, useCallback } from "react";

interface VehicleMessage {
  id?: number; // Make ID optional since WebSocket messages don't have it initially
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

  // Fetch historical messages
  const fetchHistoricalMessages = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch(`${API_BASE_URL}/messages?limit=50`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const historicalMessages = await response.json();

      // Validate message format for historical messages (which should have IDs)
      const validMessages = historicalMessages.filter((msg: any) => {
        return (
          msg &&
          typeof msg.id === "number" &&
          typeof msg.message === "string" &&
          typeof msg.vehicle_id === "string" &&
          typeof msg.timestamp === "string"
        );
      });

      setMessages(validMessages);
    } catch (error) {
      console.error("Error fetching historical messages:", error);
      setError(
        error instanceof Error ? error.message : "Failed to fetch messages",
      );
      setMessages([]); // Reset messages on error
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
          // Generate a temporary ID for WebSocket messages
          const messageWithId = {
            ...data,
            id: `ws-${Date.now()}-${Math.random()}`,
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
    fetchHistoricalMessages();
    const ws = connectWebSocket();

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
