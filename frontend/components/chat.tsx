import { ScrollArea } from "@/components/ui/scroll-area";
import { messages, users } from "@/lib/mock-data";
import { User } from "lucide-react";

export function Chat({ roomId }: { roomId: string }) {
  const roomMessages = messages.filter((message) => message.roomId === roomId);

  return (
    <ScrollArea className="flex-1">
      <div className="flex justify-center w-full mt-4">
        <div className="w-full max-w-[1500px] px-2">
          <div className="space-y-4 py-4">
            {roomMessages.map((message) => {
              const user = users.find((u) => u.id === message.userId);
              return (
                <div key={message.id} className="flex space-x-2">
                  <div className="flex-shrink-0 w-8 h-8 sm:w-12 sm:h-12 rounded-full bg-gray-300 dark:bg-gray-700 flex items-center justify-center mr-2">
                    <User className="h-4 w-4 sm:h-6 sm:w-6 text-gray-500" />
                  </div>
                  <div className="flex-grow">
                    <div className="flex items-baseline gap-2 flex-wrap">
                      <span className="font-semibold text-sm sm:text-base">
                        {user?.name}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="mt-1 text-sm sm:text-base break-words">
                      {message.content}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </ScrollArea>
  );
}
