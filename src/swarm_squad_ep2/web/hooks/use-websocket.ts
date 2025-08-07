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
const MAX_RECONNECT_DELAY = 30000; // 30 seconds max
const API_BASE_URL = "http://localhost:8000"; // Updated to match server port

export function useWebSocket() {
  const [messages, setMessages] = useState<VehicleMessage[]>([]);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableRooms, setAvailableRooms] = useState<string[]>([]);
  const messageCounterRef = useRef(0); // Use ref for message counter
  const reconnectAttempts = useRef(0);
  const historicalMessagesLoaded = useRef(false);
  const roomsCached = useRef(false);

  // Fetch available rooms from API (with periodic refresh)
  const fetchAvailableRooms = useCallback(async () => {
    console.log("Fetching rooms for WebSocket connection...");

    try {
      const response = await fetch(`${API_BASE_URL}/rooms`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const text = await response.text();
      if (!text.trim()) {
        console.warn("Received empty response from /rooms");
        const fallbackRooms = ["v1", "v2", "v3"];
        setAvailableRooms(fallbackRooms);
        roomsCached.current = true;
        return fallbackRooms;
      }
      const rooms = JSON.parse(text);
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
  }, [availableRooms]);

  // Fetch historical messages (only once)
  const fetchHistoricalMessages = useCallback(async () => {
    // Only fetch historical messages once
    if (historicalMessagesLoaded.current) {
      console.log("Historical messages already loaded, skipping");
      return;
    }

    try {
      setError(null);
      const response = await fetch(`${API_BASE_URL}/messages?limit=50`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const text = await response.text();
      if (!text.trim()) {
        console.warn("Received empty response from /messages");
        historicalMessagesLoaded.current = true;
        return;
      }
      const historicalMessages = JSON.parse(text);

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
      historicalMessagesLoaded.current = true;
    } catch (error) {
      console.error("Error fetching historical messages:", error);
      setError(
        error instanceof Error ? error.message : "Failed to fetch messages",
      );
      historicalMessagesLoaded.current = true; // Mark as attempted even if failed
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initialize WebSocket connection
  const connectWebSocket = useCallback((rooms: string[]) => {
    if (rooms.length === 0) {
      console.warn("No rooms available for WebSocket connection");
      console.log("WebSocket connection cancelled - no rooms");
      return null;
    }

    const websocketUrl = `ws://localhost:8000/ws?rooms=${rooms.join(",")}`;
    console.log("Connecting to WebSocket:", websocketUrl);
    console.log("Subscribing to rooms:", rooms);
    console.log("Total rooms count:", rooms.length);

    const ws = new WebSocket(websocketUrl);

    ws.onopen = () => {
      console.log("WebSocket connected to rooms:", rooms);
      setIsConnected(true);
      setError(null);
      // Reset reconnection attempts on successful connection
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        // Check if event.data is empty or null
        if (!event.data || event.data.trim() === "") {
          console.warn("Received empty WebSocket message, skipping");
          return;
        }

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
        // Exponential backoff with jitter
        reconnectAttempts.current++;
        const backoffDelay = Math.min(
          RECONNECT_DELAY * Math.pow(2, reconnectAttempts.current - 1),
          MAX_RECONNECT_DELAY,
        );
        const jitteredDelay = backoffDelay + Math.random() * 1000; // Add up to 1s jitter

        console.log(
          `Attempting to reconnect in ${Math.round(jitteredDelay / 1000)}s (attempt ${reconnectAttempts.current})`,
        );

        setTimeout(() => {
          console.log("Attempting to reconnect...");
          connectWebSocket(rooms);
        }, jitteredDelay);
      }
    };

    setSocket(ws);
    return ws;
  }, []);

  // Set up WebSocket connection and cleanup
  useEffect(() => {
    let ws: WebSocket | null = null;
    let isMounted = true;

    // First fetch available rooms, then connect to WebSocket
    const initializeConnection = async () => {
      try {
        const rooms = await fetchAvailableRooms();
        if (isMounted && rooms.length > 0) {
          ws = connectWebSocket(rooms);
          // Only fetch historical messages on initial load
          if (!historicalMessagesLoaded.current) {
            fetchHistoricalMessages();
          }
        }
      } catch (error) {
        console.error("Error initializing connection:", error);
        if (isMounted) {
          setError("Failed to initialize connection");
        }
      }
    };

    initializeConnection();

    return () => {
      isMounted = false;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close(1000, "Component unmounting");
      }
    };
  }, []); // Remove dependencies to prevent re-initialization

  // Send message function
  const sendMessage = useCallback(async (roomId: string, content: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/messages/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          room_id: roomId,
          entity_id: "user", // User messages
          content: content,
          message_type: "user_message",
          timestamp: new Date().toISOString(),
          state: {},
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.status}`);
      }

      const text = await response.text();
      let result;
      try {
        result = text.trim() ? JSON.parse(text) : {};
      } catch (parseError) {
        console.warn("Response is not valid JSON, treating as success:", text);
        result = { success: true };
      }
      console.log("Message sent successfully:", result);
      return true;
    } catch (error) {
      console.error("Error sending message:", error);
      setError("Failed to send message");
      return false;
    }
  }, []);

  return {
    messages,
    socket,
    isLoading,
    isConnected,
    error,
    availableRooms,
    sendMessage,
  };
}
