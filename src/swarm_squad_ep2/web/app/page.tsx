"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { Chat } from "@/components/chat";
import { MessageInput } from "@/components/message-input";
import { Users, User, Hash } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getUsers, getRoomStructure } from "@/lib/mock-data";
import { ThemeToggle } from "@/components/theme-toggle";
import { useWebSocket } from "@/hooks/use-websocket";
import { fetchRooms } from "@/lib/api";

export default function Page() {
  const [currentRoomId, setCurrentRoomId] = useState<string>("");
  const [roomCategories, setRoomCategories] = useState<any[]>([]);
  const [allRooms, setAllRooms] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [isLoadingRooms, setIsLoadingRooms] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const {
    isConnected: wsConnected,
    messages: wsMessages,
    sendMessage,
  } = useWebSocket();

  const currentRoom = allRooms.find((room) => room.id === currentRoomId);

  // Fetch rooms from API
  useEffect(() => {
    const loadRooms = async () => {
      try {
        setIsLoadingRooms(true);
        console.log("Fetching rooms from API...");
        const rooms = await fetchRooms();
        console.log("Received rooms from API:", rooms);
        setAllRooms(rooms);

        // If no rooms received from API, use fallback
        if (!rooms || rooms.length === 0) {
          console.warn("No rooms received from API, using fallback");
          const fallbackCategories = getRoomStructure(3);
          setRoomCategories(fallbackCategories);
          setAllRooms(fallbackCategories.flatMap((cat) => cat.rooms));
          setUsers(getUsers(3));
          if (!currentRoomId) {
            setCurrentRoomId("master-vehicles");
          }
          return;
        }

        // Organize rooms into categories
        const categories = [
          {
            id: "1",
            name: "VEHICLE CHANNELS",
            rooms: rooms.filter(
              (room) =>
                room.type === "master-vehicle" || room.type === "vehicle",
            ),
          },
          {
            id: "2",
            name: "LLM CHANNELS",
            rooms: rooms.filter(
              (room) => room.type === "master-llm" || room.type === "llm",
            ),
          },
          {
            id: "3",
            name: "VEH2LLM CHANNELS",
            rooms: rooms.filter((room) => room.type === "vl"),
          },
        ];
        console.log("Organized categories:", categories);
        setRoomCategories(categories);

        // Generate users based on detected rooms
        const vehicleCount = rooms.filter((r) => r.type === "vehicle").length;
        console.log("Detected vehicle count:", vehicleCount);
        const dynamicUsers = getUsers(vehicleCount);
        setUsers(dynamicUsers);

        // Set default room to master-vehicles if available, otherwise first room
        if (!currentRoomId && rooms.length > 0) {
          const defaultRoom =
            rooms.find((r) => r.id === "master-vehicles") || rooms[0];
          setCurrentRoomId(defaultRoom.id);
        }
      } catch (error) {
        console.error("Failed to load rooms:", error);
        // Fallback to default structure if API fails
        const fallbackCategories = getRoomStructure(3);
        setRoomCategories(fallbackCategories);
        setAllRooms(fallbackCategories.flatMap((cat) => cat.rooms));
        setUsers(getUsers(3)); // Default fallback users
        if (!currentRoomId) {
          setCurrentRoomId("master-vehicles");
        }
      } finally {
        setIsLoadingRooms(false);
      }
    };

    loadRooms();
  }, [currentRoomId]);

  // Refresh rooms when connection status changes and periodically
  useEffect(() => {
    if (wsConnected && !isRefreshing) {
      // Reload rooms when websocket connects and periodically
      const loadRooms = async () => {
        // Prevent concurrent refresh calls
        if (isRefreshing) return;

        try {
          setIsRefreshing(true);
          console.log("Refreshing rooms due to WebSocket connection change");
          const rooms = await fetchRooms();
          if (rooms.length > allRooms.length) {
            console.log(
              `Room count increased from ${allRooms.length} to ${rooms.length}, updating`,
            );
            setAllRooms(rooms);

            // Re-organize categories with new rooms
            const categories = [
              {
                id: "1",
                name: "VEHICLE CHANNELS",
                rooms: rooms.filter(
                  (room) =>
                    room.type === "master-vehicle" || room.type === "vehicle",
                ),
              },
              {
                id: "2",
                name: "LLM CHANNELS",
                rooms: rooms.filter(
                  (room) => room.type === "master-llm" || room.type === "llm",
                ),
              },
              {
                id: "3",
                name: "VEH2LLM CHANNELS",
                rooms: rooms.filter((room) => room.type === "vl"),
              },
            ];
            setRoomCategories(categories);

            // Update users
            const vehicleCount = rooms.filter(
              (r) => r.type === "vehicle",
            ).length;
            setUsers(getUsers(vehicleCount));
          }
        } catch (error) {
          console.error("Failed to reload rooms:", error);
        } finally {
          setIsRefreshing(false);
        }
      };

      loadRooms();

      // Set up periodic refresh every 10 seconds
      const interval = setInterval(loadRooms, 10000);
      return () => clearInterval(interval);
    }
  }, [wsConnected, allRooms.length, isRefreshing]);

  // Debug logging
  useEffect(() => {
    console.log("WebSocket status:", wsConnected);
    console.log("Total WebSocket messages:", wsMessages.length);
    console.log("Current room:", currentRoomId);
    if (wsMessages.length > 0) {
      console.log("Latest message:", wsMessages[wsMessages.length - 1]);
    }
  }, [wsConnected, wsMessages, currentRoomId]);

  return (
    <div className="flex h-[calc(100vh-5.5rem)] overflow-hidden">
      <Sidebar
        categories={roomCategories}
        currentRoomId={currentRoomId}
        onRoomChange={setCurrentRoomId}
      />
      <div className="flex flex-1 min-w-0">
        <div className="flex-1 flex flex-col min-w-0">
          <div className="h-14 flex-shrink-0 flex items-center justify-center px-4 border-b border-border bg-background relative">
            <h2 className="text-base font-semibold flex items-center gap-2">
              <Hash className="h-5 w-5" />
              {currentRoom?.name || currentRoomId}
            </h2>
          </div>
          <div className="flex-1 overflow-hidden">
            {currentRoomId && <Chat roomId={currentRoomId} />}
          </div>
        </div>
        <div className="w-72 border-l border-border flex flex-col">
          <div className="h-14 flex items-center justify-center px-4 border-b border-border">
            <h2 className="text-base font-semibold flex items-center gap-2">
              <Users className="h-5 w-5" />
              Users
            </h2>
          </div>
          <ScrollArea className="flex-1">
            <div className="p-4">
              {users
                .filter((user) => user.roomId === currentRoomId)
                .map((user) => (
                  <div
                    key={user.id}
                    className="flex items-center space-x-3 p-2 pl-8"
                  >
                    <div className="relative">
                      <User className="h-4 w-4 text-foreground" />
                      <div
                        className={`absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full ${user.status === "online" ? "bg-green-500" : "bg-gray-400"}`}
                      />
                    </div>
                    <span className="text-sm">{user.name}</span>
                  </div>
                ))}
            </div>
          </ScrollArea>
        </div>
      </div>
      <div className="fixed bottom-0 left-0 right-0 border-t border-border bg-background">
        <div className="flex h-[5.5rem] items-center">
          <div className="w-72 border-r border-border h-full flex flex-col items-center justify-center px-4">
            <h3 className="text-lg font-bold text-center">Swarm Squad</h3>
            <p className="text-sm text-muted-foreground text-center">
              The Digital Dialogue
            </p>
          </div>
          <div className="flex-1 relative px-8">
            <MessageInput
              currentRoomId={currentRoomId}
              onSendMessage={sendMessage}
              isConnected={wsConnected}
            />
          </div>
          <div className="w-72 border-l border-border h-full flex flex-col items-center justify-center px-4 gap-3">
            <div
              className={`flex items-center justify-center gap-2 ${wsConnected ? "text-green-500" : "text-red-500"}`}
            >
              <div className="h-1 w-1 rounded-full bg-current" />
              <span className="text-sm">
                {wsConnected ? "WS Connected" : "WS Disconnected"}
              </span>
            </div>
            <div className="w-full">
              <ThemeToggle />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
