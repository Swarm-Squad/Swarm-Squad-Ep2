import asyncio
import json
import os
import sys
from datetime import datetime

import aiohttp
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# Add the project root to Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from backend.scripts.utils.client import SwarmClient

# Try different backends in order of preference
backends = ["Qt5Agg", "TkAgg", "Agg"]
backend_set = False

for backend in backends:
    try:
        matplotlib.use(backend)
        print(f"Using {backend} backend")
        backend_set = True
        break
    except Exception as e:
        print(f"Failed to use {backend} backend: {e}")

if not backend_set:
    print("Warning: Could not set any preferred backend, using default")


class VehicleVisualizer:
    def __init__(self, num_vehicles=3):
        """Initialize the visualizer."""
        # Initialize core attributes
        self.num_vehicles = num_vehicles
        self.client = SwarmClient()
        self.connected = False
        self.last_update = {}
        self.ws_tasks = []

        # Initialize vehicle data storage
        self.vehicles = {}
        for i in range(1, num_vehicles + 1):
            vehicle_id = f"v{i}"
            self.vehicles[vehicle_id] = {
                "lat": [],
                "lon": [],
                "speed": [],
                "battery": [],
                "status": "unknown",
            }
            self.last_update[vehicle_id] = None

        # Setup plot styling
        plt.style.use("dark_background")
        self.setup_plot_layout()
        self.setup_vehicle_plots()  # Initialize vehicle plots after layout setup

    def setup_plot_layout(self):
        """Setup the plot layout and styling."""
        # Create figure with a 2x2 grid
        self.fig = plt.figure(figsize=(16, 12))
        self.gs = self.fig.add_gridspec(2, 2, height_ratios=[1, 1])

        # Create subplots in a 2x2 layout
        self.map_ax = self.fig.add_subplot(self.gs[0, 0])  # Top left
        self.status_ax = self.fig.add_subplot(self.gs[0, 1])  # Top right
        self.speed_ax = self.fig.add_subplot(self.gs[1, 0])  # Bottom left
        self.battery_ax = self.fig.add_subplot(self.gs[1, 1])  # Bottom right

        # Setup titles and labels
        self.fig.suptitle("Vehicle Swarm Visualization", fontsize=16)

        # Map plot setup
        self.map_ax.set_title("Vehicle Positions")
        self.map_ax.set_xlabel("Longitude")
        self.map_ax.set_ylabel("Latitude")
        self.map_ax.grid(True, linestyle="--", alpha=0.6)
        self.map_ax.set_xlim(-180, 180)
        self.map_ax.set_ylim(-90, 90)

        # Speed plot setup
        self.speed_ax.set_title("Vehicle Speeds")
        self.speed_ax.set_xlabel("Time")
        self.speed_ax.set_ylabel("Speed (km/h)")
        self.speed_ax.grid(True, linestyle="--", alpha=0.6)
        self.speed_ax.set_ylim(0, 120)

        # Battery plot setup
        self.battery_ax.set_title("Battery Levels")
        self.battery_ax.set_xlabel("Time")
        self.battery_ax.set_ylabel("Battery (%)")
        self.battery_ax.grid(True, linestyle="--", alpha=0.6)
        self.battery_ax.set_ylim(0, 100)

        # Status indicators setup
        self.status_ax.set_title("Vehicle Status")
        self.status_ax.axis("off")

        plt.tight_layout()

    def setup_vehicle_plots(self):
        """Initialize scatter plots and speed lines for each vehicle."""
        self.colors = plt.cm.rainbow(np.linspace(0, 1, self.num_vehicles))
        self.scatter_plots = {}
        self.speed_lines = {}
        self.battery_lines = {}
        self.status_indicators = {}

        for i, vehicle_id in enumerate(self.vehicles.keys()):
            color = self.colors[i]

            # Create scatter plot for position
            scatter = self.map_ax.scatter([], [], c=[color], label=vehicle_id, s=100)
            self.scatter_plots[vehicle_id] = scatter

            # Create line plot for speed
            (speed_line,) = self.speed_ax.plot(
                [], [], c=color, label=f"{vehicle_id} speed"
            )
            self.speed_lines[vehicle_id] = speed_line

            # Create line plot for battery
            (battery_line,) = self.battery_ax.plot(
                [], [], c=color, label=f"{vehicle_id} battery"
            )
            self.battery_lines[vehicle_id] = battery_line

            # Create status indicators with text format
            status_y = 0.9 - (i * 0.1)  # Vertical spacing between vehicles

            # Create vehicle ID label with its color
            self.status_ax.text(
                0.1,
                status_y,
                f"{vehicle_id}:",
                color=color,
                fontsize=10,
                fontweight="bold",
                verticalalignment="center",
            )

            # Create status text indicators
            self.status_indicators[vehicle_id] = {
                "moving": self.create_status_button(0.25, status_y, "Moving", color),
                "idle": self.create_status_button(0.45, status_y, "Idle", color),
                "charging": self.create_status_button(
                    0.65, status_y, "Charging", color
                ),
                "current": None,
            }

        # Add legends
        self.map_ax.legend()
        self.speed_ax.legend()
        self.battery_ax.legend()

        # Set status axis limits to ensure indicators are visible
        self.status_ax.set_xlim(0, 1)
        self.status_ax.set_ylim(0, 1)

    def create_status_button(self, x, y, label, color):
        """Create a status text indicator."""
        # Add label with position and styling
        text = self.status_ax.text(
            x,
            y,
            label,
            verticalalignment="center",
            horizontalalignment="left",
            fontsize=10,
            color="darkgray",
        )
        return text

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
                await self.client.connect()
                async with self.client.session.ws_connect(
                    f"{self.client.ws_url}/ws?rooms={vehicle_id}",
                    heartbeat=30,
                ) as ws:
                    print(f"✅ Connected to vehicle {vehicle_id}")
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                                # Process the message immediately
                                await self.update_vehicle_data(data)
                                # Force a redraw of the plot
                                self.fig.canvas.draw_idle()
                                self.fig.canvas.flush_events()
                            except Exception as e:
                                print(f"Error processing message for {vehicle_id}: {e}")
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"WebSocket error for {vehicle_id}: {ws.exception()}")
                            break
            except Exception as e:
                print(f"Connection error for {vehicle_id}: {e}")
                await asyncio.sleep(1)

    async def update_vehicle_data(self, message):
        """Update vehicle data when receiving WebSocket messages."""
        try:
            data = message if isinstance(message, dict) else json.loads(message)
            entity_id = data.get("entity_id")
            state = data.get("state", {})

            if entity_id in self.vehicles:
                self.connected = True
                self.last_update[entity_id] = datetime.now()

                # Extract and validate data
                lat = state.get("latitude")
                lon = state.get("longitude")
                speed = state.get("speed")
                battery = state.get("battery")

                if all(v is not None for v in [lat, lon, speed, battery]):
                    # Update vehicle data
                    vehicle = self.vehicles[entity_id]
                    vehicle["lat"].append(lat)
                    vehicle["lon"].append(lon)
                    vehicle["speed"].append(speed)
                    vehicle["battery"].append(battery)
                    vehicle["status"] = state.get("status", "unknown")

                    # Keep only last 50 points
                    max_trail = 50
                    for key in ["lat", "lon", "speed", "battery"]:
                        vehicle[key] = vehicle[key][-max_trail:]

                    print(
                        f"Updated {entity_id}: pos=({lat:.2f}, {lon:.2f}), "
                        f"speed={speed:.1f}, battery={battery:.1f}%"
                    )

                    # Update the plot immediately
                    self.update_plot(None)
                else:
                    print(f"Warning: Incomplete state data for {entity_id}")

        except Exception as e:
            print(f"Error processing message: {e}")
            import traceback

            traceback.print_exc()

    def update_plot(self, frame):
        """Update the visualization."""
        status_msg = []
        artists = []

        if not self.connected:
            status_msg.append("WARNING: Waiting for data... Is the simulation running?")

        # Track min/max coordinates for auto-scaling
        all_lats = []
        all_lons = []
        all_speeds = []
        all_batteries = []

        for vehicle_id, data in self.vehicles.items():
            if data["lat"] and data["lon"]:
                # Update position scatter plot
                latest_pos = np.c_[data["lon"][-1:], data["lat"][-1:]]
                self.scatter_plots[vehicle_id].set_offsets(latest_pos)
                artists.append(self.scatter_plots[vehicle_id])

                # Update speed plot
                x = range(len(data["speed"]))
                self.speed_lines[vehicle_id].set_data(x, data["speed"])
                artists.append(self.speed_lines[vehicle_id])

                # Update battery plot
                self.battery_lines[vehicle_id].set_data(x, data["battery"])
                artists.append(self.battery_lines[vehicle_id])

                # Update status indicators
                indicators = self.status_indicators[vehicle_id]
                current_status = data["status"]

                # Reset all status text to dark gray
                for status, text in indicators.items():
                    if status != "current":
                        text.set_color("darkgray")

                # Highlight current status with vehicle's color
                if current_status in indicators:
                    indicators[current_status].set_color(
                        self.colors[int(vehicle_id[1]) - 1]
                    )
                    indicators["current"] = current_status

                # Collect coordinates for auto-scaling
                all_lats.extend(data["lat"])
                all_lons.extend(data["lon"])
                all_speeds.extend(data["speed"])
                all_batteries.extend(data["battery"])

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
                    status_msg.append(
                        f"{vehicle_id}: {status} - {current_status.upper()}"
                        f" (Speed: {data['speed'][-1]:.1f} km/h,"
                        f" Battery: {data['battery'][-1]:.1f}%)"
                    )

        # Auto-scale the map view if we have data
        if all_lats and all_lons:
            lat_min, lat_max = min(all_lats), max(all_lats)
            lon_min, lon_max = min(all_lons), max(all_lons)

            # Add padding (20% of the range)
            lat_pad = max(0.1, (lat_max - lat_min) * 0.2)
            lon_pad = max(0.1, (lon_max - lon_min) * 0.2)

            self.map_ax.set_xlim(lon_min - lon_pad, lon_max + lon_pad)
            self.map_ax.set_ylim(lat_min - lat_pad, lat_max + lat_pad)

        # Update axis limits for speed and battery plots if we have data
        if all_speeds:
            self.speed_ax.set_xlim(0, len(all_speeds))
        if all_batteries:
            self.battery_ax.set_xlim(0, len(all_batteries))

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

        # Enable interactive mode
        plt.ion()

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

            try:
                # Show the plot and keep it updating
                plt.show(block=False)

                while plt.fignum_exists(self.fig.number):
                    # Update the plot
                    self.update_plot(None)
                    # Process GUI events
                    self.fig.canvas.start_event_loop(0.1)
                    await asyncio.sleep(0.1)

            except KeyboardInterrupt:
                print("\nStopping visualization...")
            finally:
                # Cancel all WebSocket tasks when plot is closed
                for task in self.ws_tasks:
                    task.cancel()
                await asyncio.gather(*self.ws_tasks, return_exceptions=True)
                plt.close("all")


async def main():
    """Run the vehicle visualization."""
    visualizer = VehicleVisualizer(num_vehicles=3)
    await visualizer.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping visualization...")
