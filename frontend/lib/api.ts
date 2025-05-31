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
    const response = await fetch(`${API_BASE}/rooms`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
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
    return response.json();
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
    return response.json();
  } catch (error) {
    console.error("Error fetching entities:", error);
    return [];
  }
}
