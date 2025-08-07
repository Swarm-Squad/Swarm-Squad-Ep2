import { ScrollArea } from "@/components/ui/scroll-area";
import { useWebSocket } from "@/hooks/use-websocket";
import { generateColor } from "@/lib/utils";
import { Car, User } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchMessages } from "@/lib/api";

// Color palettes for different entity types
const VEHICLE_COLORS = [
  "#3B82F6", // Blue
  "#10B981", // Green
  "#F59E0B", // Yellow
  "#EF4444", // Red
  "#8B5CF6", // Purple
  "#06B6D4", // Cyan
  "#F97316", // Orange
  "#84CC16", // Lime
  "#EC4899", // Pink
  "#6366F1", // Indigo
];

const LLM_COLORS = [
  "#DC2626", // Red
  "#7C3AED", // Violet
  "#059669", // Emerald
  "#D97706", // Amber
  "#DB2777", // Rose
  "#9333EA", // Purple
  "#0891B2", // Sky
  "#65A30D", // Green
  "#BE185D", // Pink
  "#7C2D12", // Orange
];

function getEntityColor(entityId: string): string {
  if (entityId.startsWith("v")) {
    const num = parseInt(entityId.slice(1)) || 1;
    return VEHICLE_COLORS[(num - 1) % VEHICLE_COLORS.length];
  } else if (entityId.startsWith("l")) {
    // LLMs use the same color as their corresponding vehicle
    const num = parseInt(entityId.slice(1)) || 1;
    return VEHICLE_COLORS[(num - 1) % VEHICLE_COLORS.length];
  }
  return "#6B7280"; // Default gray
}

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
    console.log(
      `Chat component for roomId: ${roomId}, wsMessages count: ${wsMessages.length}`,
    );
    if (!roomId || !wsMessages.length) return;

    // Filter messages for the current room and convert to ChatMessage format
    const newMessages = wsMessages
      .filter((msg) => {
        console.log(`Filtering message for roomId: ${roomId}`, msg);

        // Handle master rooms - show all messages of the respective type
        if (roomId === "master-vehicles") {
          return msg.entity_id && msg.entity_id.startsWith("v");
        }
        if (roomId === "master-llms") {
          return msg.entity_id && msg.entity_id.startsWith("l");
        }

        // Show messages from the specific room or related rooms
        // For vehicle rooms (v1), show messages from v1
        if (roomId === msg.entity_id || roomId === msg.room_id) {
          return true;
        }

        // Also show vehicle messages in vehicle-to-LLM rooms
        if (roomId.startsWith("vl")) {
          const vehicleNum = roomId.slice(2); // Extract number from vl1 -> 1
          return (
            msg.entity_id === `v${vehicleNum}` ||
            msg.entity_id === `l${vehicleNum}`
          );
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
      console.log(
        `Found ${newMessages.length} new messages for roomId: ${roomId}`,
        newMessages,
      );
      setMessages((prev) => {
        // Avoid duplicates by checking if message ID already exists
        const existingIds = new Set(prev.map((m) => m.id));
        const uniqueNewMessages = newMessages.filter(
          (m) => !existingIds.has(m.id),
        );

        if (uniqueNewMessages.length > 0) {
          console.log(
            `Adding ${uniqueNewMessages.length} unique messages to roomId: ${roomId}`,
          );
          const combined = [...prev, ...uniqueNewMessages];
          // Sort by timestamp - no message limit, allow continuous growth
          return combined.sort(
            (a, b) =>
              new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
          );
        }
        return prev;
      });
    } else {
      console.log(`No messages found for roomId: ${roomId} after filtering`);
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
                  const entityColor = getEntityColor(message.entity_id);
                  const colors = isVehicle
                    ? generateColor(message.entity_id)
                    : null;

                  return (
                    <div key={message.id} className="flex space-x-4">
                      <div
                        className="flex-shrink-0 w-8 h-8 sm:w-12 sm:h-12 rounded-full flex items-center justify-center"
                        style={{
                          backgroundColor: entityColor,
                        }}
                      >
                        {isVehicle ? (
                          <Car className="h-4 w-4 sm:h-6 sm:w-6 text-white" />
                        ) : (
                          <User className="h-4 w-4 sm:h-6 sm:w-6 text-white" />
                        )}
                      </div>
                      <div className="flex-grow">
                        <div className="flex items-baseline gap-2 flex-wrap">
                          <span
                            className="font-semibold text-sm sm:text-base"
                            style={{ color: entityColor }}
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
                                  entityColor,
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
