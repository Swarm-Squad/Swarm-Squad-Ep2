import asyncio
import json
import os
import sys
from datetime import datetime

import matplotlib

matplotlib.use("TkAgg")
import aiohttp
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

# Add the project root to Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from backend.scripts.utils.client import SwarmClient


class VehicleVisualizer:
    def __init__(self, num_vehicles=3):
        """Initialize the visualizer."""
        self.num_vehicles = num_vehicles
        self.client = SwarmClient()
        self.connected = False
        self.last_update = {}
        self.ws_tasks = []
        self.anim = None

        # Store vehicle positions and data
        self.vehicles = {}
        for i in range(1, num_vehicles + 1):
            self.vehicles[f"v{i}"] = {
                "lat": [],
                "lon": [],
                "speed": [],
                "battery": [],
                "status": "unknown",
            }
            self.last_update[f"v{i}"] = None

        # Setup the plot
        plt.style.use("dark_background")
        self.fig = plt.figure(figsize=(15, 8))
        self.gs = self.fig.add_gridspec(2, 2, height_ratios=[4, 1])

        # Create subplots
        self.map_ax = self.fig.add_subplot(self.gs[0, 0])
        self.stats_ax = self.fig.add_subplot(self.gs[0, 1])
        self.status_ax = self.fig.add_subplot(self.gs[1, :])
        self.status_ax.axis("off")

        self.fig.suptitle("Vehicle Swarm Visualization", fontsize=16)

        # Setup map subplot
        self.map_ax.set_title("Vehicle Positions")
        self.map_ax.set_xlabel("Longitude")
        self.map_ax.set_ylabel("Latitude")
        self.map_ax.grid(True, linestyle="--", alpha=0.6)

        # Set initial map limits
        self.map_ax.set_xlim(-180, 180)
        self.map_ax.set_ylim(-90, 90)

        # Setup stats subplot
        self.stats_ax.set_title("Vehicle Statistics")
        self.stats_ax.set_xlabel("Time")
        self.stats_ax.set_ylabel("Speed (km/h)")
        self.stats_ax.grid(True, linestyle="--", alpha=0.6)
        self.stats_ax.set_ylim(0, 120)  # Set speed limit to 120 km/h

        # Initialize scatter plots with different colors for each vehicle
        self.colors = plt.cm.rainbow(np.linspace(0, 1, num_vehicles))
        self.scatter_plots = {}
        self.speed_lines = {}

        for i, vehicle_id in enumerate(self.vehicles.keys()):
            scatter = self.map_ax.scatter(
                [], [], c=[self.colors[i]], label=vehicle_id, s=100
            )
            (line,) = self.stats_ax.plot(
                [], [], c=self.colors[i], label=f"{vehicle_id} speed"
            )
            self.scatter_plots[vehicle_id] = scatter
            self.speed_lines[vehicle_id] = line

        # Add legends
        self.map_ax.legend()
        self.stats_ax.legend()

        # Initialize status text
        self.status_text = self.status_ax.text(
            0.02,
            0.5,
            "",
            fontsize=10,
            verticalalignment="center",
            transform=self.status_ax.transAxes,
        )

        plt.tight_layout()

    async def check_server_connection(self):
        """Check if the FastAPI server is running."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8000") as response:
                    return response.status == 200
        except aiohttp.ClientError:
            return False

    async def subscribe_to_vehicle(self, vehicle_id: str):
        """Subscribe to a vehicle's room with automatic reconnection."""
        while True:
            try:
                print(f"Connecting to vehicle {vehicle_id}...")
                await self.client.connect()  # Ensure client is connected
                async with self.client.session.ws_connect(
                    f"{self.client.ws_url}/ws?rooms={vehicle_id}",
                    heartbeat=30,  # Add heartbeat to keep connection alive
                ) as ws:
                    print(f"✅ Connected to vehicle {vehicle_id}")
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                                await self.update_vehicle_data(data)
                            except Exception as e:
                                print(f"Error processing message for {vehicle_id}: {e}")
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"WebSocket error for {vehicle_id}: {ws.exception()}")
                            break
            except Exception as e:
                print(f"Connection error for {vehicle_id}: {e}")
                await asyncio.sleep(1)  # Wait before reconnecting

    async def update_vehicle_data(self, message):
        """Update vehicle data when receiving WebSocket messages."""
        try:
            data = message if isinstance(message, dict) else json.loads(message)
            entity_id = data.get("entity_id")
            state = data.get("state", {})

            if entity_id in self.vehicles:
                self.connected = True  # Set connected when we actually receive data
                self.last_update[entity_id] = datetime.now()

                # Extract and validate data
                lat = state.get("latitude")
                lon = state.get("longitude")
                speed = state.get("speed")
                battery = state.get("battery")

                if all(v is not None for v in [lat, lon, speed, battery]):
                    self.vehicles[entity_id]["lat"].append(lat)
                    self.vehicles[entity_id]["lon"].append(lon)
                    self.vehicles[entity_id]["speed"].append(speed)
                    self.vehicles[entity_id]["battery"].append(battery)
                    self.vehicles[entity_id]["status"] = state.get("status", "unknown")

                    # Keep only last 50 points for the trail
                    max_trail = 50
                    self.vehicles[entity_id]["lat"] = self.vehicles[entity_id]["lat"][
                        -max_trail:
                    ]
                    self.vehicles[entity_id]["lon"] = self.vehicles[entity_id]["lon"][
                        -max_trail:
                    ]
                    self.vehicles[entity_id]["speed"] = self.vehicles[entity_id][
                        "speed"
                    ][-max_trail:]
                    self.vehicles[entity_id]["battery"] = self.vehicles[entity_id][
                        "battery"
                    ][-max_trail:]

                    print(
                        f"Updated {entity_id}: pos=({lat:.2f}, {lon:.2f}), speed={speed:.1f}, battery={battery:.1f}%"
                    )
                else:
                    print(f"Warning: Incomplete state data for {entity_id}")

        except Exception as e:
            print(f"Error processing message: {e}")
            import traceback

            traceback.print_exc()

    def update_plot(self, frame):
        """Update the visualization (called by animation)."""
        status_msg = []
        artists = []

        if not self.connected:
            status_msg.append("WARNING: Waiting for data... Is the simulation running?")

        # Track min/max coordinates for auto-scaling
        all_lats = []
        all_lons = []
        all_speeds = []

        for vehicle_id, data in self.vehicles.items():
            if data["lat"] and data["lon"]:
                # Update position scatter plot
                self.scatter_plots[vehicle_id].set_offsets(
                    np.c_[data["lon"], data["lat"]]
                )
                artists.append(self.scatter_plots[vehicle_id])

                # Update speed plot
                x = range(len(data["speed"]))
                self.speed_lines[vehicle_id].set_data(x, data["speed"])
                artists.append(self.speed_lines[vehicle_id])

                # Collect coordinates for auto-scaling
                all_lats.extend(data["lat"])
                all_lons.extend(data["lon"])
                all_speeds.extend(data["speed"])

                # Add status for this vehicle
                last_update = self.last_update[vehicle_id]
                if last_update:
                    time_since_update = (datetime.now() - last_update).total_seconds()
                    status = (
                        "[ONLINE]"
                        if time_since_update < 5
                        else "[WARN]"
                        if time_since_update < 10
                        else "[OFFLINE]"
                    )
                    status_msg.append(f"{vehicle_id}: {status} ({data['status']})")

        # Update status text
        self.status_text.set_text("\n".join(status_msg))
        artists.append(self.status_text)

        # Auto-scale the map view if we have data
        if all_lats and all_lons:
            lat_min, lat_max = min(all_lats), max(all_lats)
            lon_min, lon_max = min(all_lons), max(all_lons)

            # Add padding (20% of the range)
            lat_pad = max(0.1, (lat_max - lat_min) * 0.2)
            lon_pad = max(0.1, (lon_max - lon_min) * 0.2)

            self.map_ax.set_xlim(lon_min - lon_pad, lon_max + lon_pad)
            self.map_ax.set_ylim(lat_min - lat_pad, lat_max + lat_pad)

        # Update speed plot limits
        if all_speeds:
            self.stats_ax.set_xlim(0, len(all_speeds))
            max_speed = max(max(all_speeds), 1)  # Ensure non-zero
            self.stats_ax.set_ylim(0, max_speed * 1.1)  # Add 10% padding

        return artists

    async def run(self):
        """Run the visualization."""
        print("Starting vehicle visualization...")
        print("Checking server connection...")

        if not await self.check_server_connection():
            print(
                "❌ Error: Cannot connect to the FastAPI server at http://localhost:8000"
            )
            print("Please make sure to:")
            print("1. Start the FastAPI server first:")
            print("   cd backend")
            print("   uvicorn fastapi.main:app --reload")
            print("\n2. Then start the simulation:")
            print("   python -m backend.scripts.run_simulation")
            print("\n3. Finally, run this visualization")
            return

        print("✅ Server connection successful")
        print(f"Visualizing {self.num_vehicles} vehicles")
        print("Close the plot window to stop")

        # Create WebSocket connections first
        async with self.client:
            # Start WebSocket tasks for each vehicle
            for i in range(1, self.num_vehicles + 1):
                vehicle_id = f"v{i}"
                task = asyncio.create_task(self.subscribe_to_vehicle(vehicle_id))
                self.ws_tasks.append(task)

            # Wait a moment for initial connections
            await asyncio.sleep(1)

            if not self.connected:
                print("⚠️ No data received yet. Waiting for simulation updates...")

            # Create animation after connections are established
            self.anim = FuncAnimation(
                self.fig,
                self.update_plot,
                interval=500,
                blit=True,
                cache_frame_data=False,
            )

            try:
                # Show the plot (this will block until window is closed)
                plt.show()
            finally:
                # Cancel all WebSocket tasks when plot is closed
                for task in self.ws_tasks:
                    task.cancel()
                await asyncio.gather(*self.ws_tasks, return_exceptions=True)


async def main():
    """Run the vehicle visualization."""
    visualizer = VehicleVisualizer(num_vehicles=3)
    await visualizer.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping visualization...")
