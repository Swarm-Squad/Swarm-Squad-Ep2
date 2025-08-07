// Create a new file for API functions

export interface Room {
  id: string;
  name: string;
  type: string;
  messages: Message[];
}

export interface Message {
  id: number | string;
  room_id: string;
  entity_id: string;
  content: string;
  timestamp: string;
  message_type: string;
  state: {
    latitude?: number;
    longitude?: number;
    speed?: number;
    battery?: number;
    status?: string;
  };
}

export interface Entity {
  id: string;
  name: string;
  type: string;
  room_id: string;
  status: string;
  last_seen: string;
}

const API_BASE = "http://localhost:8000";

export async function fetchRooms(): Promise<Room[]> {
  try {
    console.log("Making request to:", `${API_BASE}/rooms`);
    const response = await fetch(`${API_BASE}/rooms`);
    console.log("Response status:", response.status);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const text = await response.text();
    console.log("Response text length:", text.length);
    console.log("Response text preview:", text.substring(0, 200));

    if (!text.trim()) {
      console.warn("Received empty response from /rooms");
      return [];
    }

    try {
      const parsed = JSON.parse(text);
      console.log("Successfully parsed JSON:", parsed);
      return parsed;
    } catch (parseError) {
      console.error("JSON parse error in fetchRooms:", parseError);
      console.error("Raw response that failed to parse:", text);
      return [];
    }
  } catch (error) {
    console.error("Error fetching rooms:", error);
    return [];
  }
}

export async function fetchMessages(roomId: string): Promise<Message[]> {
  try {
    const response = await fetch(`${API_BASE}/messages?room_id=${roomId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const text = await response.text();
    if (!text.trim()) {
      console.warn("Received empty response from /messages");
      return [];
    }

    return JSON.parse(text);
  } catch (error) {
    console.error("Error fetching messages:", error);
    return [];
  }
}

export async function fetchEntities(roomId: string): Promise<Entity[]> {
  try {
    const response = await fetch(`${API_BASE}/entities?room_id=${roomId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const text = await response.text();
    if (!text.trim()) {
      console.warn("Received empty response from /entities");
      return [];
    }

    return JSON.parse(text);
  } catch (error) {
    console.error("Error fetching entities:", error);
    return [];
  }
}
