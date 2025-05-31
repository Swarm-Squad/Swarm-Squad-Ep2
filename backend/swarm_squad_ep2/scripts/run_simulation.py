import asyncio

from swarm_squad_ep2.scripts.simulator import VehicleSimulator


async def main():
    """Run the vehicle simulation."""
    simulator = VehicleSimulator(num_vehicles=3)
    await simulator.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping simulation...")
