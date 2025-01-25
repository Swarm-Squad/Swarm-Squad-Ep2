import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// Predefined distinct colors for better visibility
const DISTINCT_COLORS = {
  V1: {
    bg: "#3b82f6", // bright blue
    text: "#eff6ff",
  },
  V2: {
    bg: "#22c55e", // bright green
    text: "#f0fdf4",
  },
  V3: {
    bg: "#f97316", // bright orange
    text: "#fff7ed",
  },
  V4: {
    bg: "#8b5cf6", // bright purple
    text: "#f5f3ff",
  },
  V5: {
    bg: "#ec4899", // bright pink
    text: "#fdf2f8",
  },
};

export function generateColor(vehicleId: string) {
  return (
    DISTINCT_COLORS[vehicleId as keyof typeof DISTINCT_COLORS] || {
      bg: "#6b7280", // fallback gray
      text: "#f9fafb",
    }
  );
}

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
