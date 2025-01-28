import asyncio
import os
import sys

# Add the project root to Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from backend.scripts.simulator import VehicleSimulator


async def main():
    """Run the vehicle simulation."""
    simulator = VehicleSimulator(num_vehicles=3)
    await simulator.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping simulation...")
