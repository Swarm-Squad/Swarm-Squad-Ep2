import { ScrollArea } from "@/components/ui/scroll-area";
import { useWebSocket } from "@/hooks/use-websocket";
import { generateColor } from "@/lib/utils";
import { Car, User } from "lucide-react";
import { useEffect, useState } from "react";
import { Message, fetchMessages } from "@/lib/api";

interface Message {
  id: string | number; // Allow both string and number IDs
  content: string;
  timestamp: string;
  userId?: string;
  roomId: string;
  isVehicle?: boolean;
  vehicleId?: string;
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
  const [messages, setMessages] = useState<Message[]>([]);
  const { messages: wsMessages } = useWebSocket();

  useEffect(() => {
    if (!roomId) return;

    // Load initial messages from database
    async function loadMessages() {
      const fetchedMessages = await fetchMessages(roomId);
      setMessages(fetchedMessages);
    }
    loadMessages();
  }, [roomId]);

  // Handle incoming websocket messages
  useEffect(() => {
    if (!roomId) return;

    const newMessages = wsMessages
      .filter((msg) => msg.room_id === roomId)
      .map((msg) => ({
        id: msg.id || Date.now(),
        room_id: msg.room_id,
        entity_id: msg.entity_id,
        content: msg.message,
        timestamp: msg.timestamp,
        message_type: msg.type,
        state: msg.state || {},
      }));

    if (newMessages.length > 0) {
      setMessages((prev) => [...prev, ...newMessages]);
    }
  }, [wsMessages, roomId]);

  return (
    <ScrollArea className="flex-1">
      <div className="flex justify-center w-full mt-4">
        <div className="w-full max-w-[1500px] px-4">
          <div className="space-y-4 py-4">
            {messages.map((message) => {
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
                        {message.state.latitude && message.state.longitude && (
                          <span className="mr-2">
                            Location: ({message.state.latitude.toFixed(4)},{" "}
                            {message.state.longitude.toFixed(4)})
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
            })}
          </div>
        </div>
      </div>
    </ScrollArea>
  );
}
