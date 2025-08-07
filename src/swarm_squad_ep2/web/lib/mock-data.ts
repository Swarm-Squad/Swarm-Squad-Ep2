// Generate dynamic room structure based on vehicle count
function generateRoomStructure(numVehicles: number = 3) {
  const vehicleRooms = [];
  const llmRooms = [];
  const veh2llmRooms = [];

  // Add master rooms first
  vehicleRooms.push({
    id: "master-vehicles",
    name: "🚗 All Vehicles",
    type: "master-vehicle",
  });
  llmRooms.push({ id: "master-llms", name: "🤖 All LLMs", type: "master-llm" });

  // Generate individual rooms based on vehicle count
  for (let i = 1; i <= numVehicles; i++) {
    vehicleRooms.push({
      id: `v${i}`,
      name: `Vehicle ${i} Room`,
      type: "vehicle",
    });
    llmRooms.push({ id: `l${i}`, name: `LLM ${i} Room`, type: "llm" });
    veh2llmRooms.push({ id: `vl${i}`, name: `Veh${i} - LLM${i}`, type: "vl" });
  }

  return [
    {
      id: "1",
      name: "VEHICLE CHANNELS",
      rooms: vehicleRooms,
    },
    {
      id: "2",
      name: "LLM CHANNELS",
      rooms: llmRooms,
    },
    {
      id: "3",
      name: "VEH2LLM CHANNELS",
      rooms: veh2llmRooms,
    },
  ];
}

// Default to 3 vehicles, but this will be dynamic
export const categories = generateRoomStructure(3);

// Export the generator function for dynamic use
export const getRoomStructure = generateRoomStructure;

// Utility function to get all rooms
export const getAllRooms = (numVehicles?: number) => {
  const roomStructure = numVehicles
    ? generateRoomStructure(numVehicles)
    : categories;
  return roomStructure.flatMap((category) => category.rooms);
};

// Generate dynamic users based on vehicle count
export const getUsers = (numVehicles: number = 3) => {
  const users = [];

  // Add master room "users" (these represent the aggregated channels)
  users.push({
    id: "master-vehicles",
    name: "🚗 All Vehicles",
    roomId: "master-vehicles",
    status: "online",
    type: "master-vehicle",
  });

  users.push({
    id: "master-llms",
    name: "🤖 All LLMs",
    roomId: "master-llms",
    status: "online",
    type: "master-llm",
  });

  // Generate individual vehicle and LLM users
  for (let i = 1; i <= numVehicles; i++) {
    users.push({
      id: `v${i}`,
      name: `Vehicle ${i}`,
      roomId: `v${i}`,
      status: "online",
      type: "vehicle",
    });

    users.push({
      id: `l${i}`,
      name: `LLM ${i}`,
      roomId: `l${i}`,
      status: "online",
      type: "llm",
    });
  }

  return users;
};

// Default users for 3 vehicles
export const users = getUsers(3);

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
