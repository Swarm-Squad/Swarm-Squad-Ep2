import { ScrollArea } from "@/components/ui/scroll-area";
import { useWebSocket } from "@/hooks/use-websocket";
import { generateColor } from "@/lib/utils";
import { Car, User } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchMessages } from "@/lib/api";

interface ChatMessage {
  id: string | number;
  content: string;
  timestamp: string;
  entity_id: string;
  room_id: string;
  message_type: string;
  state?: {
    latitude?: number;
    longitude?: number;
    speed?: number;
    battery?: number;
    status?: string;
  };
}

// Function to colorize specific parts of the vehicle message
function colorizeVehicleMessage(
  message: string,
  vehicleId: string,
  color: string,
) {
  // Remove any malformed percentage strings that might appear
  message = message.replace(/\d+%,\s*\d+%">/, "");

  // Color the vehicle ID and all numerical data
  return (
    message
      // First color the vehicle ID
      .replace(
        new RegExp(`Vehicle ${vehicleId}`),
        `<span style="color: ${color}">Vehicle ${vehicleId}</span>`,
      )
      // Then color coordinates
      .replace(
        /\(([-\d.]+,\s*[-\d.]+)\)/g,
        (match) => `<span style="color: ${color}">${match}</span>`,
      )
      // Then color speed values
      .replace(
        /([\d.]+)(\s*km\/h)/g,
        (_, num, unit) => `<span style="color: ${color}">${num}</span>${unit}`,
      )
      // Finally color battery percentage
      .replace(
        /([\d.]+)(%)/g,
        (_, num, unit) => `<span style="color: ${color}">${num}</span>${unit}`,
      )
  );
}

export function Chat({ roomId }: { roomId: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const { messages: wsMessages, isConnected } = useWebSocket();

  useEffect(() => {
    if (!roomId) return;

    // Load initial messages from database
    async function loadMessages() {
      try {
        const fetchedMessages = await fetchMessages(roomId);
        const formattedMessages = fetchedMessages.map((msg) => ({
          id: msg.id,
          content: msg.content,
          timestamp: msg.timestamp,
          entity_id: msg.entity_id,
          room_id: msg.room_id,
          message_type: msg.message_type,
          state: msg.state,
        }));
        setMessages(formattedMessages);
      } catch (error) {
        console.error("Error loading messages:", error);
      }
    }
    loadMessages();
  }, [roomId]);

  // Handle incoming websocket messages
  useEffect(() => {
    if (!roomId || !wsMessages.length) return;

    // Filter messages for the current room and convert to ChatMessage format
    const newMessages = wsMessages
      .filter((msg) => {
        // Show messages from the specific room or related rooms
        // For vehicle rooms (v1), show messages from v1 and vl1
        // For LLM rooms (l1), show messages from l1 and vl1
        if (roomId === msg.entity_id || roomId === msg.room_id) {
          return true;
        }
        // Also show vehicle messages in vehicle-to-LLM rooms
        if (
          roomId.startsWith("vl") &&
          msg.entity_id.startsWith("v") &&
          roomId.slice(2) === msg.entity_id.slice(1)
        ) {
          return true;
        }
        return false;
      })
      .map((msg) => ({
        id: msg.id || `${msg.entity_id}-${Date.now()}`,
        content: msg.content,
        timestamp: msg.timestamp,
        entity_id: msg.entity_id,
        room_id: msg.room_id || roomId,
        message_type: msg.message_type,
        state: msg.state,
      }));

    if (newMessages.length > 0) {
      setMessages((prev) => {
        // Avoid duplicates by checking if message ID already exists
        const existingIds = new Set(prev.map((m) => m.id));
        const uniqueNewMessages = newMessages.filter(
          (m) => !existingIds.has(m.id),
        );

        if (uniqueNewMessages.length > 0) {
          const combined = [...prev, ...uniqueNewMessages];
          // Sort by timestamp and keep last 100 messages
          return combined
            .sort(
              (a, b) =>
                new Date(a.timestamp).getTime() -
                new Date(b.timestamp).getTime(),
            )
            .slice(-100);
        }
        return prev;
      });
    }
  }, [wsMessages, roomId]);

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-2 text-xs flex items-center justify-center text-gray-500 border-b">
        WebSocket:{" "}
        {isConnected ? (
          <span className="text-green-600">Connected</span>
        ) : (
          <span className="text-red-600">Disconnected</span>
        )}
        <span className="mx-2">-</span>
        Messages: {messages.length}
        <span className="mx-2">-</span>
        Room: {roomId}
      </div>

      <ScrollArea className="flex-1">
        <div className="flex justify-center w-full mt-4">
          <div className="w-full max-w-[1500px] px-4">
            <div className="space-y-4 py-4">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  No messages yet.{" "}
                  {isConnected
                    ? "Waiting for vehicle updates..."
                    : "Connecting to WebSocket..."}
                </div>
              ) : (
                messages.map((message) => {
                  const isVehicle = message.message_type === "vehicle_update";
                  const colors = isVehicle
                    ? generateColor(message.entity_id)
                    : null;

                  return (
                    <div key={message.id} className="flex space-x-4">
                      <div
                        className="flex-shrink-0 w-8 h-8 sm:w-12 sm:h-12 rounded-full flex items-center justify-center"
                        style={{
                          backgroundColor: colors?.bg || "rgb(209, 213, 219)",
                        }}
                      >
                        {isVehicle ? (
                          <Car
                            className="h-4 w-4 sm:h-6 sm:w-6"
                            style={{ color: colors?.text }}
                          />
                        ) : (
                          <User className="h-4 w-4 sm:h-6 sm:w-6 text-gray-500" />
                        )}
                      </div>
                      <div className="flex-grow">
                        <div className="flex items-baseline gap-2 flex-wrap">
                          <span
                            className="font-semibold text-sm sm:text-base"
                            style={{ color: colors?.bg }}
                          >
                            {message.entity_id}
                          </span>
                          <span className="text-xs text-gray-500">
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <p
                          className="mt-1 text-sm sm:text-base break-words"
                          dangerouslySetInnerHTML={{
                            __html: isVehicle
                              ? colorizeVehicleMessage(
                                  message.content,
                                  message.entity_id,
                                  colors?.bg || "inherit",
                                )
                              : message.content,
                          }}
                        />
                        {isVehicle && message.state && (
                          <div className="mt-1 text-xs text-gray-500">
                            {message.state.latitude &&
                              message.state.longitude && (
                                <span className="mr-2">
                                  Location: ({message.state.latitude.toFixed(4)}
                                  , {message.state.longitude.toFixed(4)})
                                </span>
                              )}
                            {message.state.speed && (
                              <span className="mr-2">
                                Speed: {message.state.speed.toFixed(1)} km/h
                              </span>
                            )}
                            {message.state.battery && (
                              <span>
                                Battery: {message.state.battery.toFixed(1)}%
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
