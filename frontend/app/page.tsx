"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { Chat } from "@/components/chat";
import { MessageInput } from "@/components/message-input";
import { Room } from "@/lib/api";
import { Users, User } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { users, getAllRooms } from "@/lib/mock-data";
import { ThemeToggle } from "@/components/theme-toggle";

export default function Page() {
  const [currentRoomId, setCurrentRoomId] = useState<string>("");
  const [wsConnected, setWsConnected] = useState(false);
  const rooms = getAllRooms();
  const currentRoom = rooms.find((room) => room.id === currentRoomId);

  useEffect(() => {
    if (!currentRoomId && rooms.length > 0) {
      setCurrentRoomId(rooms[0].id);
    }
  }, [currentRoomId, rooms]);

  return (
    <div className="flex h-screen">
      <Sidebar
        rooms={rooms}
        currentRoomId={currentRoomId}
        onRoomChange={setCurrentRoomId}
      />
      <div className="flex flex-1">
        <div className="flex-1 flex flex-col min-w-0">
          <div className="h-14 flex items-center justify-center px-4 border-b border-border">
            <h1 className="text-base font-semibold flex items-center gap-2">
              # {currentRoom?.name}
            </h1>
          </div>
          <Chat roomId={currentRoomId} />
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
            <MessageInput />
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
