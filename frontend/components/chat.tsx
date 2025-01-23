import { ScrollArea } from "@/components/ui/scroll-area";
import { messages, users } from "@/lib/mock-data";
import { useWebSocket } from "@/hooks/use-websocket";
import { generateColor } from "@/lib/utils";
import { Car, User } from "lucide-react";
import { useEffect, useState } from "react";

interface Message {
  id: string;
  content: string;
  timestamp: string;
  userId?: string;
  roomId: string;
  isVehicle?: boolean;
  vehicleId?: string;
}

// Function to colorize specific parts of the vehicle message
function colorizeVehicleMessage(message: string, vehicleId: string, color: string) {
  // Remove any malformed percentage strings that might appear
  message = message.replace(/\d+%,\s*\d+%">/, '');

  // Color the vehicle ID and all numerical data
  return message
    // First color the vehicle ID
    .replace(
      new RegExp(`Vehicle ${vehicleId}`),
      `<span style="color: ${color}">Vehicle ${vehicleId}</span>`
    )
    // Then color coordinates
    .replace(
      /\(([-\d.]+,\s*[-\d.]+)\)/g,
      match => `<span style="color: ${color}">${match}</span>`
    )
    // Then color speed values
    .replace(
      /([\d.]+)(\s*km\/h)/g,
      (_, num, unit) => `<span style="color: ${color}">${num}</span>${unit}`
    )
    // Finally color battery percentage
    .replace(
      /([\d.]+)(%)/g,
      (_, num, unit) => `<span style="color: ${color}">${num}</span>${unit}`
    );
}

export function Chat({ roomId }: { roomId: string }) {
  const [allMessages, setAllMessages] = useState<Message[]>([]);
  const { messages: vehicleMessages } = useWebSocket();
  
  useEffect(() => {
    const mockRoomMessages = messages.filter((message) => message.roomId === roomId);
    const vehicleMsgs = vehicleMessages.map((vm) => ({
      id: `${vm.vehicle_id}-${vm.timestamp}`,
      content: vm.message,
      timestamp: vm.timestamp,
      roomId,
      isVehicle: true,
      vehicleId: vm.vehicle_id
    }));
    
    setAllMessages([...mockRoomMessages, ...vehicleMsgs].sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    ));
  }, [roomId, vehicleMessages]);

  return (
    <ScrollArea className="flex-1">
      <div className="flex justify-center w-full mt-4">
        <div className="w-full max-w-[1500px] px-2">
          <div className="space-y-4 py-4">
            {allMessages.map((message) => {
              const user = message.userId ? users.find((u) => u.id === message.userId) : null;
              const colors = message.vehicleId ? generateColor(message.vehicleId) : null;
              
              return (
                <div key={message.id} className="flex space-x-2">
                  <div 
                    className="flex-shrink-0 w-8 h-8 sm:w-12 sm:h-12 rounded-full flex items-center justify-center mr-2"
                    style={{
                      backgroundColor: colors ? colors.bg : 'rgb(209, 213, 219)',
                    }}
                  >
                    {message.isVehicle ? (
                      <Car className="h-4 w-4 sm:h-6 sm:w-6" style={{ color: colors?.text }} />
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
                        {message.isVehicle ? message.vehicleId : user?.name}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p 
                      className="mt-1 text-sm sm:text-base break-words"
                      dangerouslySetInnerHTML={{
                        __html: message.isVehicle && message.vehicleId
                          ? colorizeVehicleMessage(message.content, message.vehicleId, colors?.bg || 'inherit')
                          : message.content
                      }}
                    />
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
