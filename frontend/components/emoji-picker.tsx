"use client"

import dynamic from "next/dynamic"
import { Smile } from "lucide-react"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Button } from "@/components/ui/button"
import { useTheme } from "next-themes"
import { cn } from "@/lib/utils"

const Picker = dynamic(() => import("@emoji-mart/react"), { ssr: false })

interface EmojiPickerProps {
  onEmojiSelect: (emoji: string) => void
  className?: string
  iconClassName?: string
}

export function EmojiPicker({ onEmojiSelect, className, iconClassName }: EmojiPickerProps) {
  const { theme } = useTheme()

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button type="button" variant="ghost" size="icon" className={cn("h-16 w-16", className)}>
          <Smile className={cn("h-12 w-12", iconClassName)} />
        </Button>
      </PopoverTrigger>
      <PopoverContent side="top" className="p-0 border-none" style={{ width: "320px" }}>
        <div className="rounded-md border border-border overflow-hidden">
          <Picker
            data={async () => {
              const response = await fetch(
                'https://cdn.jsdelivr.net/npm/@emoji-mart/data'
              )
              return response.json()
            }}
            onEmojiSelect={(emoji: any) => onEmojiSelect(emoji.native)}
            theme={theme === "dark" ? "dark" : "light"}
            previewPosition="none"
            searchPosition="top"
            skinTonePosition="none"
            navPosition="top"
            perLine={8}
          />
        </div>
      </PopoverContent>
    </Popover>
  )
}

