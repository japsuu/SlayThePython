from __future__ import annotations

import os
from typing import TYPE_CHECKING
from data.enemies import EnemySpawnData
import json

from utils.logging import log_info

if TYPE_CHECKING:
    from typing import List

last_combat_room_index: int = -1


class RoomData:
    def __init__(self, room_background_sprite_path, room_enemies):
        self.room_background_sprite_path: str = room_background_sprite_path
        self.room_enemies: List[EnemySpawnData] = room_enemies

    def to_dict(self):
        return {
            "room_background_sprite_path": self.room_background_sprite_path,
            "room_enemies": self.room_enemies,
        }

    @classmethod
    def from_dict(cls, data):
        room_enemies = [EnemySpawnData.from_dict(enemy_data) for enemy_data in data["room_enemies"]]
        return cls(
            data["room_background_sprite_path"],
            room_enemies,
        )

    @staticmethod
    def load_available_combat_rooms():
        """
        :return: A list of lists of RoomData objects, one list for each level of difficulty.
        """
        max_index = RoomData.get_last_combat_room_index()
        levels: List[List[RoomData]] = []
        for difficulty in range(max_index + 1):
            folder_path = f"Content/Rooms/Combat/Room_{difficulty}"

            rooms = RoomData.get_rooms_in_directory(folder_path)
            log_info(f"Loaded {len(rooms)} rooms from {folder_path}")
            if len(rooms) == 0:
                raise Exception(f"No combat rooms found in {folder_path}, even though max available room index is {max_index}.")
            levels.append(rooms)

        return levels

    @staticmethod
    def load_available_special_rooms():
        folder_path = "Content/Rooms/Special"
        return RoomData.get_rooms_in_directory(folder_path)

    @staticmethod
    def load_available_boss_rooms():
        folder_path = "Content/Rooms/Boss"
        return RoomData.get_rooms_in_directory(folder_path)

    @staticmethod
    def get_rooms_in_directory(folder_path):
        """
        :param folder_path: Path to the folder containing the rooms.
        :return: A list of RoomData objects, one for each room in the folder.
        """
        rooms = []
        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, "r") as file:
                    json_data = json.load(file)
                    room_data = RoomData.from_dict(json_data)
                    rooms.append(room_data)
        return rooms

    @staticmethod
    def get_last_combat_room_index():
        """
        :return: The largest level index available in the "Content/Rooms/Combat" folder.
        """
        global last_combat_room_index
        if last_combat_room_index != -1:
            return last_combat_room_index

        folder_path = "Content/Rooms/Combat"
        for folder_name in os.listdir(folder_path):
            if folder_name.startswith("Room_"):
                for filename in os.listdir(folder_path + "/" + folder_name):
                    if filename.endswith(".json"):
                        level = int(folder_name.split("_")[1])
                        last_combat_room_index = max(last_combat_room_index, level)
                        break

        if last_combat_room_index == -1:
            raise Exception("No combat rooms found in Content/Rooms/Combat.")

        return last_combat_room_index
