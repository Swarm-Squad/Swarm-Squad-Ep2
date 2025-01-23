"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Chat } from "@/components/chat"
import { MessageInput } from "@/components/message-input"
import { getAllRooms } from "@/lib/mock-data"

export default function Page() {
  const [currentRoomId, setCurrentRoomId] = useState("1")
  const currentRoom = getAllRooms().find((room) => room.id === currentRoomId)

  return (
    <div className="flex h-screen">
      <Sidebar currentRoomId={currentRoomId} onRoomChange={setCurrentRoomId} />
      <div className="flex-1 flex flex-col">
        <div className="h-14 flex items-center justify-center px-4 border-b border-border">
          <h1 className="text-base font-semibold flex items-center gap-2"># {currentRoom?.name}</h1>
        </div>
        <Chat roomId={currentRoomId} />
        <MessageInput />
      </div>
    </div>
  )
}

