export const categories = [
  {
    id: "1",
    name: "VEHICLE CHANNELS",
    rooms: [
      { id: "v1", name: "Vehicle 1 Room", type: "vehicle" },
      { id: "v2", name: "Vehicle 2 Room", type: "vehicle" },
      { id: "v3", name: "Vehicle 3 Room", type: "vehicle" },
    ],
  },
  {
    id: "2",
    name: "LLM CHANNELS",
    rooms: [
      { id: "l1", name: "LLM 1 Room", type: "llm" },
      { id: "l2", name: "LLM 2 Room", type: "llm" },
      { id: "l3", name: "LLM 3 Room", type: "llm" },
    ],
  },
  {
    id: "3",
    name: "VEH2LLM CHANNELS",
    rooms: [
      { id: "vl1", name: "Veh1 - LLM1", type: "vl" },
      { id: "vl2", name: "Veh2 - LLM2", type: "vl" },
      { id: "vl3", name: "Veh3 - LLM3", type: "vl" },
    ],
  },
];

// Utility function to get all rooms
export const getAllRooms = () =>
  categories.flatMap((category) => category.rooms);

// Updated users to represent vehicles and agents
export const users = [
  {
    id: "v1",
    name: "Vehicle 1",
    roomId: "v1",
    status: "online",
    type: "vehicle",
  },
  {
    id: "v2",
    name: "Vehicle 2",
    roomId: "v2",
    status: "online",
    type: "vehicle",
  },
  {
    id: "v3",
    name: "Vehicle 3",
    roomId: "v3",
    status: "online",
    type: "vehicle",
  },
  { id: "l1", name: "LLM 1", roomId: "l1", status: "online", type: "llm" },
  { id: "l2", name: "LLM 2", roomId: "l2", status: "online", type: "llm" },
  { id: "l3", name: "LLM 3", roomId: "l3", status: "online", type: "llm" },
];

// Sample messages showing different types of communication
export const messages = [
  {
    id: "1",
    roomId: "v1",
    userId: "v1",
    content: "Vehicle 1 status update",
    timestamp: new Date().toISOString(),
    type: "vehicle_update",
  },
  {
    id: "2",
    roomId: "a1",
    userId: "a1",
    content: "Agent 1 processing vehicle data",
    timestamp: new Date().toISOString(),
    type: "agent_response",
  },
  {
    id: "3",
    roomId: "ac1",
    userId: "a1",
    content: "Coordinating with nearby agents",
    timestamp: new Date().toISOString(),
    type: "agent_coordination",
  },
];
