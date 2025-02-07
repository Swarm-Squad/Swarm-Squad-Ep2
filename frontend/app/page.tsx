"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { Chat } from "@/components/chat";
import { MessageInput } from "@/components/message-input";
import { Room, fetchRooms } from "@/lib/api";

export default function Page() {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [currentRoomId, setCurrentRoomId] = useState<string>("");
  const currentRoom = rooms.find((room) => room.id === currentRoomId);

  useEffect(() => {
    let mounted = true;

    async function loadRooms() {
      const fetchedRooms = await fetchRooms();
      if (mounted) {
        setRooms(fetchedRooms);
        if (fetchedRooms.length > 0 && !currentRoomId) {
          setCurrentRoomId(fetchedRooms[0].id);
        }
      }
    }

    loadRooms();

    return () => {
      mounted = false;
    };
  }, [currentRoomId]);

  return (
    <div className="flex h-screen">
      <Sidebar
        rooms={rooms}
        currentRoomId={currentRoomId}
        onRoomChange={setCurrentRoomId}
      />
      <div className="flex-1 flex flex-col">
        <div className="h-14 flex items-center justify-center px-4 border-b border-border">
          <h1 className="text-base font-semibold flex items-center gap-2">
            # {currentRoom?.name}
          </h1>
        </div>
        <Chat roomId={currentRoomId} />
        <MessageInput />
      </div>
    </div>
  );
}
