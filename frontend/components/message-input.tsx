"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { EmojiPicker } from "./emoji-picker";
import { Image, Paperclip, SendHorizontal } from "lucide-react";

export function MessageInput() {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    console.log("Sending message:", message);
    setMessage("");
  };

  const handleEmojiSelect = (emoji: string) => {
    setMessage((prev) => prev + emoji);
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2">
      <div className="flex items-center gap-1 sm:gap-2">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-9 w-9 sm:h-10 sm:w-10"
        >
          <Paperclip className="h-[18px] w-[18px] sm:h-5 sm:w-5" />
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-9 w-9 sm:h-10 sm:w-10"
        >
          <Image className="h-[18px] w-[18px] sm:h-5 sm:w-5" />
        </Button>
        <EmojiPicker
          onEmojiSelect={handleEmojiSelect}
          className="h-9 w-9 sm:h-10 sm:w-10"
          iconClassName="!h-[18px] !w-[18px] sm:!h-5 sm:!w-5"
        />
      </div>
      <div className="flex-grow">
        <Input
          placeholder="Send a message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="h-9 sm:h-10 text-sm sm:text-base"
        />
      </div>
      <Button
        type="submit"
        size="sm"
        className="gap-1 sm:gap-2 h-9 sm:h-10 px-3 sm:px-4 text-sm sm:text-base"
      >
        <span className="hidden sm:inline">Send</span>
        <SendHorizontal className="h-[18px] w-[18px] sm:h-5 sm:w-5" />
      </Button>
    </form>
  );
}
