import { useEffect, useState, useCallback, useRef } from "react";

interface VehicleMessage {
  id?: number | string; // Allow both number (DB) and string (WebSocket) IDs
  timestamp: string;
  entity_id: string; // Changed from vehicle_id to match backend
  content: string; // Changed from message to match backend
  message_type: string; // Changed from type to match backend
  room_id?: string; // Add room_id to track which room the message came from
  state: {
    latitude?: number;
    longitude?: number;
    speed?: number;
    battery?: number;
    status?: string;
  };
}

const RECONNECT_DELAY = 2000; // 2 seconds
const API_BASE_URL = "http://localhost:8000"; // Updated to match server port

export function useWebSocket() {
  const [messages, setMessages] = useState<VehicleMessage[]>([]);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableRooms, setAvailableRooms] = useState<string[]>([]);
  const messageCounterRef = useRef(0); // Use ref for message counter

  // Fetch available rooms from API
  const fetchAvailableRooms = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/rooms`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const rooms = await response.json();
      const roomIds = rooms.map((room: any) => room.id);
      console.log("Fetched available rooms:", roomIds);
      setAvailableRooms(roomIds);
      return roomIds;
    } catch (error) {
      console.error("Error fetching rooms:", error);
      // Fallback to basic vehicle rooms if API fails
      const fallbackRooms = ["v1", "v2", "v3"];
      console.log("Using fallback rooms:", fallbackRooms);
      setAvailableRooms(fallbackRooms);
      return fallbackRooms;
    }
  }, []);

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
          (typeof msg.id === "number" || typeof msg.id === "string") &&
          typeof msg.content === "string" &&
          typeof msg.entity_id === "string" &&
          typeof msg.timestamp === "string"
        );
      });

      // Only set historical messages if we don't have any messages yet
      setMessages((currentMessages) =>
        currentMessages.length === 0 ? validMessages : currentMessages,
      );

      console.log(`Loaded ${validMessages.length} historical messages`);
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
  const connectWebSocket = useCallback((rooms: string[]) => {
    if (rooms.length === 0) {
      console.warn("No rooms available for WebSocket connection");
      return null;
    }

    const websocketUrl = `ws://localhost:8000/ws?rooms=${rooms.join(",")}`;
    console.log("Connecting to WebSocket:", websocketUrl);
    console.log("Subscribing to rooms:", rooms);

    const ws = new WebSocket(websocketUrl);

    ws.onopen = () => {
      console.log("WebSocket connected to rooms:", rooms);
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("Received WebSocket message:", data);

        // Handle both message formats (from API and real-time)
        if (
          data &&
          (typeof data.content === "string" ||
            typeof data.message === "string") &&
          typeof data.entity_id === "string" &&
          typeof data.timestamp === "string"
        ) {
          messageCounterRef.current += 1;
          const messageWithId = {
            ...data,
            // Normalize message field names
            content: data.content || data.message,
            message_type: data.message_type || "vehicle_update",
            room_id: data.room_id || data.entity_id,
            state: data.state || {},
            id:
              data.id ||
              `${data.entity_id}-${Date.now()}-${messageCounterRef.current}`,
          };

          setMessages((prev) => {
            const newMessages = [...prev, messageWithId];
            console.log(
              `Total messages: ${newMessages.length} (latest from ${messageWithId.entity_id})`,
            );
            return newMessages.slice(-50); // Keep last 50 messages
          });
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

    ws.onclose = (event) => {
      console.log("WebSocket disconnected:", event.code, event.reason);
      setIsConnected(false);

      // Only attempt reconnect if it wasn't a manual close
      if (event.code !== 1000) {
        setTimeout(() => {
          console.log("Attempting to reconnect...");
          connectWebSocket(rooms);
        }, RECONNECT_DELAY);
      }
    };

    setSocket(ws);
    return ws;
  }, []);

  // Set up WebSocket connection and cleanup
  useEffect(() => {
    let ws: WebSocket | null = null;

    // First fetch available rooms, then connect to WebSocket
    const initializeConnection = async () => {
      const rooms = await fetchAvailableRooms();
      if (rooms.length > 0) {
        ws = connectWebSocket(rooms);
        fetchHistoricalMessages();
      }
    };

    initializeConnection();

    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close(1000, "Component unmounting");
      }
    };
  }, [fetchAvailableRooms, connectWebSocket, fetchHistoricalMessages]);

  return {
    messages,
    socket,
    isLoading,
    isConnected,
    error,
    availableRooms,
  };
}
