"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { categories, users } from "@/lib/mock-data";
import { Hash, Users, LayoutList, User } from "lucide-react";
import { ThemeToggle } from "./theme-toggle";
import { CategoryHeader } from "./category-header";

interface SidebarProps {
  currentRoomId: string;
  onRoomChange: (roomId: string) => void;
}

export function Sidebar({ currentRoomId, onRoomChange }: SidebarProps) {
  const [expandedCategories, setExpandedCategories] = useState<
    Record<string, boolean>
  >(Object.fromEntries(categories.map((category) => [category.id, true])));

  const toggleCategory = (categoryId: string) => {
    setExpandedCategories((prev) => ({
      ...prev,
      [categoryId]: !prev[categoryId],
    }));
  };

  return (
    <div className="w-64 border-r border-border flex flex-col h-screen">
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
                      className="w-full justify-start text-sm pl-4"
                      onClick={() => onRoomChange(room.id)}
                    >
                      <Hash className="mr-2 h-4 w-4" />
                      {room.name}
                    </Button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </ScrollArea>
      <div className="h-14 flex items-center justify-center px-4 border-t border-b border-border">
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
              <div key={user.id} className="flex items-center space-x-3 p-2">
                <div className="relative">
                  <User className="h-5 w-5 text-gray-500" />
                  <div
                    className={`absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full ${user.status === "online" ? "bg-green-500" : "bg-gray-400"}`}
                  />
                </div>
                <span className="text-sm">{user.name}</span>
              </div>
            ))}
        </div>
      </ScrollArea>
      <div className="border-t border-border">
        <div className="h-14 px-4 flex items-center justify-center border-b border-border">
          <ThemeToggle />
        </div>
        <div className="px-4 py-3 flex flex-col items-center">
          <h3 className="text-lg font-bold">Swarm Squad</h3>
          <p className="text-sm text-muted-foreground">The Digital Dialogue</p>
        </div>
      </div>
    </div>
  );
}
