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
    <div className="h-24 sm:h-32 border-t border-border bg-background">
      <form
        onSubmit={handleSubmit}
        className="flex items-center justify-center gap-2 sm:gap-6 w-full h-full px-2 max-w-[1500px] mx-auto"
      >
        <div className="flex items-center gap-2 sm:gap-2">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-10 w-10 sm:h-14 sm:w-14"
          >
            <Paperclip
              className="h-5 w-5"
              style={{ height: "20px", width: "20px" }}
              aria-hidden="true"
            />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-10 w-10 sm:h-14 sm:w-14"
          >
            <Image
              className="h-5 w-5"
              style={{ height: "20px", width: "20px" }}
              aria-hidden="true"
            />
          </Button>
          <EmojiPicker
            onEmojiSelect={handleEmojiSelect}
            className="h-10 w-10 sm:h-14 sm:w-14"
            iconClassName="!h-5 !w-5 sm:!h-[22px] sm:!w-[22px]"
          />
        </div>
        <div className="flex-grow max-w-[1200px]">
          <Input
            placeholder="Send a message..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="h-12 sm:h-14 text-base sm:text-lg border-gray-300 dark:border-gray-600"
          />
        </div>
        <Button
          type="submit"
          size="lg"
          className="gap-1 sm:gap-2 h-12 sm:h-14 px-4 sm:px-6 text-base sm:text-lg"
        >
          <span className="hidden sm:inline">Send</span>
          <SendHorizontal
            className="h-5 w-5"
            style={{ height: "20px", width: "20px" }}
          />
        </Button>
      </form>
    </div>
  );
}
