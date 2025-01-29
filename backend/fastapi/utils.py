from typing import List, Optional

from sqlalchemy.orm import Session

from backend.fastapi.models import Entity, EntityType, Room, RoomType


def create_simulation_resources(
    db: Session,
    num_vehicles: int,
    room_types: Optional[List[RoomType]] = None,
    entity_types: Optional[List[EntityType]] = None,
    force_recreate: bool = False,
) -> None:
    """Create rooms and entities for simulation."""
    try:
        # Check if resources already exist
        existing_rooms = db.query(Room).count()
        existing_entities = db.query(Entity).count()

        if existing_rooms > 0 or existing_entities > 0:
            if force_recreate:
                # Delete existing resources
                db.query(Entity).delete()
                db.query(Room).delete()
                db.commit()
                print("Deleted existing resources")
            else:
                print("Resources already exist, skipping creation")
                return

        # Use all room types if none specified
        if room_types is None:
            room_types = [RoomType.VEHICLE, RoomType.VL, RoomType.LLM]

        # Use all entity types if none specified
        if entity_types is None:
            entity_types = [EntityType.VEHICLE, EntityType.LLM]

        rooms = []
        entities = []

        # Create rooms based on specified types
        for i in range(1, num_vehicles + 1):
            if RoomType.VEHICLE in room_types:
                rooms.append(
                    Room(id=f"v{i}", name=f"Vehicle {i} Room", type=RoomType.VEHICLE)
                )
            if RoomType.VL in room_types:
                rooms.append(
                    Room(
                        id=f"vl{i}",
                        name=f"Vehicle {i} to LLM Room",
                        type=RoomType.VL,
                    )
                )
            if RoomType.LLM in room_types:
                rooms.append(
                    Room(
                        id=f"l{i}",
                        name=f"LLM {i} Room",
                        type=RoomType.LLM,
                    )
                )

        # Create entities based on specified types
        for i in range(1, num_vehicles + 1):
            if EntityType.VEHICLE in entity_types:
                entities.append(
                    Entity(
                        id=f"v{i}",
                        name=f"Vehicle {i}",
                        type=EntityType.VEHICLE,
                        room_id=f"v{i}",
                        status="online",
                    )
                )
            if EntityType.LLM in entity_types:
                entities.append(
                    Entity(
                        id=f"l{i}",
                        name=f"LLM {i}",
                        type=EntityType.LLM,
                        room_id=f"l{i}",
                        status="online",
                    )
                )

        if rooms:
            db.add_all(rooms)
        if entities:
            db.add_all(entities)

        db.commit()
        print(f"Created {len(rooms)} rooms and {len(entities)} entities")

    except Exception as e:
        print(f"Error creating simulation resources: {e}")
        db.rollback()
        raise
