export const categories = [
  {
    id: "1",
    name: "TEXT CHANNELS",
    rooms: [
      { id: "1", name: "general" },
      { id: "2", name: "homework-help" },
      { id: "3", name: "session-planning" },
      { id: "4", name: "off-topic" },
    ],
  },
  {
    id: "2",
    name: "VOICE CHANNELS",
    rooms: [
      { id: "5", name: "Study Room 1" },
      { id: "6", name: "Study Room 2" },
    ],
  },
]

// Utility function to get all rooms
export const getAllRooms = () => categories.flatMap((category) => category.rooms)

export const users = [
  { id: "1", name: "Alice", roomId: "1", status: "online" },
  { id: "2", name: "Bob", roomId: "2", status: "online" },
  { id: "3", name: "Charlie", roomId: "1", status: "offline" },
  { id: "4", name: "David", roomId: "3", status: "online" },
  { id: "5", name: "Eve", roomId: "1", status: "online" },
  { id: "6", name: "Frank", roomId: "2", status: "offline" },
  { id: "7", name: "Grace", roomId: "4", status: "offline" },
  { id: "8", name: "Henry", roomId: "1", status: "online" },
  { id: "9", name: "Ivy", roomId: "3", status: "offline" },
  { id: "10", name: "Jack", roomId: "2", status: "online" },
  { id: "11", name: "Kyle", roomId: "4", status: "offline" },
  { id: "12", name: "Liam", roomId: "1", status: "online" },
  { id: "13", name: "Mia", roomId: "3", status: "offline" },
  { id: "14", name: "Noah", roomId: "2", status: "online" },
  { id: "15", name: "Olivia", roomId: "4", status: "offline" },
]

export const messages = [
  { id: "1", roomId: "1", userId: "1", content: "Hello everyone!", timestamp: "2023-04-01T12:00:00Z" },
  { id: "2", roomId: "1", userId: "2", content: "Hi Alice!", timestamp: "2023-04-01T12:01:00Z" },
  { id: "3", roomId: "2", userId: "3", content: "Anyone need help with homework? ", timestamp: "2023-04-01T12:02:00Z" },
  { id: "1", roomId: "1", userId: "1", content: "Hello everyone!", timestamp: "2023-04-01T12:00:00Z" },
  { id: "2", roomId: "1", userId: "2", content: "Hi Alice!", timestamp: "2023-04-01T12:01:00Z" },
  { id: "3", roomId: "2", userId: "3", content: "Anyone need help with homework?", timestamp: "2023-04-01T12:02:00Z" },
  { id: "1", roomId: "1", userId: "1", content: "Hello everyone!", timestamp: "2023-04-01T12:00:00Z" },
  { id: "2", roomId: "1", userId: "2", content: "Hi Alice!", timestamp: "2023-04-01T12:01:00Z" },
  { id: "3", roomId: "2", userId: "3", content: "Anyone need help with homework?", timestamp: "2023-04-01T12:02:00Z" },
  { id: "1", roomId: "1", userId: "1", content: "Hello everyone!", timestamp: "2023-04-01T12:00:00Z" },
  { id: "2", roomId: "1", userId: "2", content: "Hi Alice!", timestamp: "2023-04-01T12:01:00Z" },
  { id: "3", roomId: "2", userId: "3", content: "Anyone need help with homework?", timestamp: "2023-04-01T12:02:00Z" },
  { id: "1", roomId: "1", userId: "1", content: "Hello everyone!", timestamp: "2023-04-01T12:00:00Z" },
  { id: "2", roomId: "1", userId: "2", content: "Hi Alice!", timestamp: "2023-04-01T12:01:00Z" },
  { id: "3", roomId: "2", userId: "3", content: "Anyone need help with homework?", timestamp: "2023-04-01T12:02:00Z" },
  { id: "1", roomId: "1", userId: "1", content: "Hello everyone!", timestamp: "2023-04-01T12:00:00Z" },
  { id: "2", roomId: "1", userId: "2", content: "Hi Alice!", timestamp: "2023-04-01T12:01:00Z" },
  { id: "3", roomId: "2", userId: "3", content: "Anyone need help with homework?", timestamp: "2023-04-01T12:02:00Z" },
  { id: "1", roomId: "1", userId: "1", content: "Hello everyone!", timestamp: "2023-04-01T12:00:00Z" },
  { id: "2", roomId: "1", userId: "2", content: "Hi Alice!", timestamp: "2023-04-01T12:01:00Z" },
  { id: "3", roomId: "2", userId: "3", content: "Anyone need help with homework?", timestamp: "2023-04-01T12:02:00Z" },
  { id: "1", roomId: "1", userId: "1", content: "Hello everyone!", timestamp: "2023-04-01T12:00:00Z" },
  { id: "2", roomId: "1", userId: "2", content: "Hi Alice!", timestamp: "2023-04-01T12:01:00Z" },
  { id: "3", roomId: "2", userId: "3", content: "Anyone need help with homework?", timestamp: "2023-04-01T12:02:00Z" },
  { id: "1", roomId: "1", userId: "1", content: "Hello everyone!", timestamp: "2023-04-01T12:00:00Z" },
  { id: "2", roomId: "1", userId: "2", content: "Hi Alice!", timestamp: "2023-04-01T12:01:00Z" },
  { id: "3", roomId: "2", userId: "3", content: "Anyone need help with homework?", timestamp: "2023-04-01T12:02:00Z" },
]

