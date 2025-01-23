"use client"

import { ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

interface CategoryHeaderProps {
  name: string
  isExpanded: boolean
  onToggle: () => void
}

export function CategoryHeader({ name, isExpanded, onToggle }: CategoryHeaderProps) {
  return (
    <button
      onClick={onToggle}
      className="flex items-center gap-1 w-full px-2 py-1 text-xs font-semibold text-muted-foreground hover:text-foreground"
    >
      <ChevronDown className={cn("h-3 w-3 transition-transform", !isExpanded && "-rotate-90")} />
      {name}
    </button>
  )
}

