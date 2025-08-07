"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { Image, Paperclip, SendHorizontal } from "lucide-react";

interface MessageInputProps {
  currentRoomId?: string;
  onSendMessage?: (roomId: string, content: string) => Promise<boolean>;
  isConnected?: boolean;
}

export function MessageInput({
  currentRoomId,
  onSendMessage,
  isConnected = false,
}: MessageInputProps) {
  const [message, setMessage] = useState("");
  const [isSending, setIsSending] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || !currentRoomId || !onSendMessage || isSending)
      return;

    setIsSending(true);
    try {
      const success = await onSendMessage(currentRoomId, message.trim());
      if (success) {
        setMessage("");
      }
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2">
      <div className="flex items-center gap-1 sm:gap-2">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-9 w-9 sm:h-10 sm:w-10"
          disabled
        >
          <Paperclip className="h-[18px] w-[18px] sm:h-5 sm:w-5" />
        </Button>
      </div>
      <div className="flex-grow">
        <Input
          placeholder={
            isConnected && currentRoomId
              ? `Send a message to ${currentRoomId}...`
              : "Connecting..."
          }
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="h-9 sm:h-10 text-sm sm:text-base"
          disabled={!isConnected || !currentRoomId || isSending}
        />
      </div>
      <Button
        type="submit"
        size="sm"
        disabled={
          !isConnected || !currentRoomId || !message.trim() || isSending
        }
        className="gap-1 sm:gap-2 h-9 sm:h-10 px-3 sm:px-4 text-sm sm:text-base"
      >
        <span className="hidden sm:inline">
          {isSending ? "Sending..." : "Send"}
        </span>
        <SendHorizontal className="h-[18px] w-[18px] sm:h-5 sm:w-5" />
      </Button>
    </form>
  );
}
