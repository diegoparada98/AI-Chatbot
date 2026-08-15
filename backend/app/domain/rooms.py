"""Static room catalogue for the Cubo Itau office.

Single source of truth for the five rooms and their capacities. The challenge
spec fixes the room letters (A-E) but not the capacities, so we assign sensible
corporate-meeting-room sizes here.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Room:
    name: str
    capacity: int


ROOMS: dict[str, Room] = {
    "A": Room("A", 4),
    "B": Room("B", 6),
    "C": Room("C", 8),
    "D": Room("D", 10),
    "E": Room("E", 20),
}

ROOM_NAMES: list[str] = list(ROOMS.keys())


def get_room(name: str) -> Room | None:
    """Look up a room by name, case-insensitively (accepts 'a' or 'A')."""
    if not name:
        return None
    return ROOMS.get(name.strip().upper())
