"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button
        variant="ghost"
        size="sm"
        className="flex items-center justify-center gap-2 w-full"
      >
        <div className="h-4 w-4" />
        <span className="invisible">Placeholder</span>
      </Button>
    );
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      className="flex items-center justify-center gap-2 w-full"
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
    >
      {theme === "light" ? (
        <>
          <Moon className="h-4 w-4" />
          <span>Dark mode</span>
        </>
      ) : (
        <>
          <Sun className="h-4 w-4" />
          <span>Light mode</span>
        </>
      )}
    </Button>
  );
}
