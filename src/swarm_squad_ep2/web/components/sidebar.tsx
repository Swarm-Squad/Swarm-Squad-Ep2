"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Hash, LayoutList } from "lucide-react";
import { CategoryHeader } from "./category-header";

interface Room {
  id: string;
  name: string;
  type: string;
}

interface Category {
  id: string;
  name: string;
  rooms: Room[];
}

interface SidebarProps {
  currentRoomId: string;
  onRoomChange: (roomId: string) => void;
  categories: Category[];
}

export function Sidebar({
  currentRoomId,
  onRoomChange,
  categories,
}: SidebarProps) {
  const [expandedCategories, setExpandedCategories] = useState<
    Record<string, boolean>
  >({});

  // Update expanded categories when categories change
  useEffect(() => {
    if (categories.length > 0) {
      setExpandedCategories(
        Object.fromEntries(categories.map((category) => [category.id, true])),
      );
    }
  }, [categories]);

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories((prev) => ({
      ...prev,
      [categoryId]: !prev[categoryId],
    }));
  };

  return (
    <div className="hidden md:flex w-72 border-r border-border flex-col h-screen bg-background">
      <div className="h-14 flex items-center justify-center px-4 border-b border-border">
        <h2 className="text-base font-semibold flex items-center gap-2">
          <LayoutList className="h-5 w-5" />
          Rooms
        </h2>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {categories.map((category) => (
            <div key={category.id}>
              <CategoryHeader
                name={category.name}
                isExpanded={expandedCategories[category.id]}
                onToggle={() => toggleCategory(category.id)}
              />
              {expandedCategories[category.id] && (
                <div className="space-y-1 mt-1">
                  {category.rooms.map((room) => (
                    <Button
                      key={room.id}
                      variant={
                        currentRoomId === room.id ? "secondary" : "ghost"
                      }
                      className="w-full justify-start text-sm pl-8"
                      onClick={() => onRoomChange(room.id)}
                    >
                      <Hash className="mr-3 h-4 w-4" />
                      {room.name}
                    </Button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
