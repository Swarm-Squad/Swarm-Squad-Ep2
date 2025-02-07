// Create a new file for API functions

export interface Room {
  id: string;
  name: string;
  type: string;
  messages: Message[];
}

export interface Message {
  id: number;
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

const API_BASE = 'http://localhost:8000';

export async function fetchRooms(): Promise<Room[]> {
  try {
    const response = await fetch(`${API_BASE}/rooms`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  } catch (error) {
    console.error('Error fetching rooms:', error);
    return [];
  }
}

export async function fetchMessages(roomId: string): Promise<Message[]> {
  try {
    // Get the base vehicle ID from the room ID (e.g., 'v1' from 'vl1')
    const vehicleId = roomId.replace('vl', 'v');
    const vlRoomId = `vl${vehicleId.replace('v', '')}`;

    // Fetch messages from both rooms if it's a vehicle room
    const responses = await Promise.all([
      fetch(`${API_BASE}/messages?room_id=${roomId}`),
      roomId.startsWith('v') ? fetch(`${API_BASE}/messages?room_id=${vlRoomId}`) : Promise.resolve(null)
    ]);

    if (!responses[0].ok) {
      throw new Error(`HTTP error! status: ${responses[0].status}`);
    }

    const messages = await responses[0].json();
    if (responses[1] && responses[1].ok) {
      const vlMessages = await responses[1].json();
      return [...messages, ...vlMessages].sort((a, b) => 
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      );
    }

    return messages;
  } catch (error) {
    console.error('Error fetching messages:', error);
    return [];
  }
}

export async function fetchEntities(roomId: string): Promise<Entity[]> {
  const response = await fetch(`${API_BASE}/entities?room_id=${roomId}`);
  return response.json();
} 