export const categories = [
  {
    id: "1",
    name: "VEHICLE CHANNELS",
    rooms: [
      { id: "v1", name: "vehicle-1", type: "vehicle" },
      { id: "v2", name: "vehicle-2", type: "vehicle" },
      { id: "v3", name: "vehicle-3", type: "vehicle" },
    ],
  },
  {
    id: "2",
    name: "LLM CHANNELS",
    rooms: [
      { id: "a1", name: "agent-1", type: "agent" },
      { id: "a2", name: "agent-2", type: "agent" },
      { id: "a3", name: "agent-3", type: "agent" },
    ],
  },
  {
    id: "3",
    name: "VEH2LLM CHANNELS",
    rooms: [
      { id: "va1", name: "veh1-agent1", type: "veh2llm" },
      { id: "va2", name: "veh2-agent2", type: "veh2llm" },
      { id: "va3", name: "veh3-agent3", type: "veh2llm" },
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
  { id: "a1", name: "Agent 1", roomId: "a1", status: "online", type: "agent" },
  { id: "a2", name: "Agent 2", roomId: "a2", status: "online", type: "agent" },
  { id: "a3", name: "Agent 3", roomId: "a3", status: "online", type: "agent" },
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
