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

// Global request throttling and deduplication
let roomsPromise: Promise<Room[]> | null = null;
let messagesPromises: Map<string, Promise<Message[]>> = new Map();
let entitiesPromises: Map<string, Promise<Entity[]>> = new Map();
let lastRequestTime = 0;
const MIN_REQUEST_INTERVAL = 100; // Minimum 100ms between requests
let requestCount = 0;
const MAX_REQUESTS_PER_SECOND = 10; // Rate limiting
let requestCountResetTime = Date.now();

// Clear caches on page unload to prevent stale promises
if (typeof window !== "undefined") {
  window.addEventListener("beforeunload", () => {
    roomsPromise = null;
    messagesPromises.clear();
    entitiesPromises.clear();
  });
}

export async function fetchRooms(): Promise<Room[]> {
  // If there's already a request in flight, return that promise
  if (roomsPromise) {
    console.log("Reusing existing fetchRooms request");
    return roomsPromise;
  }

  // Rate limiting - ensure minimum interval between requests and max requests per second
  const now = Date.now();

  // Reset request count every second
  if (now - requestCountResetTime >= 1000) {
    requestCount = 0;
    requestCountResetTime = now;
  }

  // Check if we've exceeded max requests per second
  if (requestCount >= MAX_REQUESTS_PER_SECOND) {
    console.log("Rate limit exceeded, delaying request...");
    await new Promise((resolve) =>
      setTimeout(resolve, 1000 - (now - requestCountResetTime)),
    );
    requestCount = 0;
    requestCountResetTime = Date.now();
  }

  const timeSinceLastRequest = now - lastRequestTime;
  if (timeSinceLastRequest < MIN_REQUEST_INTERVAL) {
    await new Promise((resolve) =>
      setTimeout(resolve, MIN_REQUEST_INTERVAL - timeSinceLastRequest),
    );
  }

  requestCount++;
  lastRequestTime = Date.now();

  // Create the request promise
  roomsPromise = (async () => {
    try {
      console.log("Making request to:", `${API_BASE}/rooms`);
      const response = await fetch(`${API_BASE}/rooms`, {
        signal: AbortSignal.timeout(5000), // 5 second timeout
      });
      console.log("Response status:", response.status);
      console.log(
        "Response headers:",
        Object.fromEntries(response.headers.entries()),
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const text = await response.text();
      console.log("Response text length:", text.length);
      console.log("Response text preview:", text.substring(0, 200));

      // Check if response looks like HTML (error page)
      if (text.trim().startsWith("<")) {
        console.error(
          "🚨 RECEIVED HTML INSTEAD OF JSON:",
          text.substring(0, 500),
        );
        throw new Error("Server returned HTML instead of JSON");
      }

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
  })();

  try {
    const result = await roomsPromise;
    return result;
  } finally {
    // Clear the promise so subsequent calls can make new requests
    roomsPromise = null;
  }
}

export async function fetchMessages(roomId: string): Promise<Message[]> {
  // Check for existing request for this room
  const existingPromise = messagesPromises.get(roomId);
  if (existingPromise) {
    console.log(`Reusing existing fetchMessages request for room: ${roomId}`);
    return existingPromise;
  }

  const promise = (async () => {
    try {
      const response = await fetch(`${API_BASE}/messages?room_id=${roomId}`, {
        signal: AbortSignal.timeout(5000),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const text = await response.text();

      // Check for HTML response
      if (text.trim().startsWith("<")) {
        console.error(
          "🚨 RECEIVED HTML INSTEAD OF JSON in fetchMessages:",
          text.substring(0, 500),
        );
        throw new Error("Server returned HTML instead of JSON");
      }

      if (!text.trim()) {
        console.warn("Received empty response from /messages");
        return [];
      }

      try {
        return JSON.parse(text);
      } catch (parseError) {
        console.error("🚨 JSON PARSE ERROR in fetchMessages:", parseError);
        console.error("Raw response that failed to parse:", text);
        return [];
      }
    } catch (error) {
      console.error("Error fetching messages:", error);
      return [];
    }
  })();

  messagesPromises.set(roomId, promise);

  try {
    const result = await promise;
    return result;
  } finally {
    // Clear the promise after completion
    messagesPromises.delete(roomId);
  }
}

export async function fetchEntities(roomId: string): Promise<Entity[]> {
  // Check for existing request for this room
  const existingPromise = entitiesPromises.get(roomId);
  if (existingPromise) {
    console.log(`Reusing existing fetchEntities request for room: ${roomId}`);
    return existingPromise;
  }

  const promise = (async () => {
    try {
      const response = await fetch(`${API_BASE}/entities?room_id=${roomId}`, {
        signal: AbortSignal.timeout(5000),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const text = await response.text();

      // Check for HTML response
      if (text.trim().startsWith("<")) {
        console.error(
          "🚨 RECEIVED HTML INSTEAD OF JSON in fetchEntities:",
          text.substring(0, 500),
        );
        throw new Error("Server returned HTML instead of JSON");
      }

      if (!text.trim()) {
        console.warn("Received empty response from /entities");
        return [];
      }

      try {
        return JSON.parse(text);
      } catch (parseError) {
        console.error("🚨 JSON PARSE ERROR in fetchEntities:", parseError);
        console.error("Raw response that failed to parse:", text);
        return [];
      }
    } catch (error) {
      console.error("Error fetching entities:", error);
      return [];
    }
  })();

  entitiesPromises.set(roomId, promise);

  try {
    const result = await promise;
    return result;
  } finally {
    // Clear the promise after completion
    entitiesPromises.delete(roomId);
  }
}
