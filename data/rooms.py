from __future__ import annotations

import os
from typing import TYPE_CHECKING
from data.enemies import EnemySpawnData
import json

from utils.logging import log_info

if TYPE_CHECKING:
    from typing import List
    from state_management import GameState

last_combat_room_index: int = -1


class SpecialRoomAction:
    def __init__(self, action_name, action_description, change_health_amount, reward_cards_count, remove_cards_amount, change_mana_permanent):
        self.action_name: str = action_name
        self.action_description: str = action_description
        self.change_health_amount: int = change_health_amount
        self.reward_cards_count: int = reward_cards_count
        self.remove_cards_amount: int = remove_cards_amount
        self.change_mana_permanent: int = change_mana_permanent

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["action_name"],
            data["action_description"],
            data["change_health_amount"],
            data["reward_cards_count"],
            data["remove_cards_amount"],
            data["change_mana_permanent"],
        )

    def get_effects_text(self) -> List[str]:
        description = []
        if self.change_health_amount != 0:
            if self.change_health_amount > 0:
                description.append(f"Gain {self.change_health_amount} health.")
            else:
                description.append(f"Lose {-self.change_health_amount} health.")
            description.append("")
        if self.reward_cards_count > 0:
            description.append(f"Choose a card from {self.reward_cards_count} random cards to add to your deck.")
            description.append("")
        if self.remove_cards_amount > 0:
            description.append(f"Remove {self.remove_cards_amount} cards from your deck.")
            description.append("")
        if self.change_mana_permanent != 0:
            if self.change_mana_permanent > 0:
                description.append(f"Gain {self.change_mana_permanent} additional mana at the start of every turn.")
            else:
                description.append(f"Lose {-self.change_mana_permanent} mana at the start of every turn.")
            description.append("")
        if len(description) > 0:
            description.pop()
        return description

    def execute(self, game_state: GameState):
        if self.change_health_amount != 0:
            if self.change_health_amount < 0:
                game_state.current_game_save.player_health = max(game_state.current_game_save.player_health + self.change_health_amount, 0)
            else:
                game_state.current_game_save.player_health = min(game_state.current_game_save.player_health + self.change_health_amount, 100)
            print(f"Player health changed from {game_state.current_game_save.player_health - self.change_health_amount} to {game_state.current_game_save.player_health}.")
        if self.reward_cards_count > 0:
            game_state.generate_reward_cards(self.reward_cards_count)
            game_state.is_player_choosing_reward_cards = True
            print(f"Player is choosing {self.reward_cards_count} reward cards.")
        if self.remove_cards_amount > 0:
            game_state.player_can_remove_cards_count = self.remove_cards_amount
            game_state.generate_removal_cards()
            game_state.is_player_removing_cards = True
            print(f"Player is choosing {self.remove_cards_amount} cards to remove.")
        if self.change_mana_permanent > 0:
            game_state.current_game_save.player_base_mana = max(game_state.current_game_save.player_base_mana + self.change_mana_permanent, 0)
            print(f"Player base mana changed from {game_state.current_game_save.player_base_mana - self.change_mana_permanent} to {game_state.current_game_save.player_base_mana}.")


class RoomData:
    def __init__(self, room_background_sprite_path):
        self.room_background_sprite_path: str = room_background_sprite_path

    @staticmethod
    def get_rooms_in_directory(folder_path, from_dict_func):
        """
        :param folder_path: Path to the folder containing the rooms.
        :param from_dict_func: A function that takes a dictionary and returns an object of the type that the dictionary represents.
        :return: A list of CombatRoomData objects, one for each room in the folder.
        """
        rooms = []
        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, "r") as file:
                    json_data = json.load(file)
                    room_data = from_dict_func(json_data)
                    rooms.append(room_data)
        return rooms


class SpecialRoomData(RoomData):
    def __init__(self, room_name, room_description, room_background_sprite_path, room_actions):
        super().__init__(room_background_sprite_path)
        self.room_name: str = room_name
        self.room_description: str = room_description
        self.room_available_actions: List[SpecialRoomAction] = room_actions

    def to_dict(self):
        return {
            "room_name": self.room_name,
            "room_description": self.room_description,
            "room_background_sprite_path": self.room_background_sprite_path,
            "room_available_actions": self.room_available_actions,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["room_name"],
            data["room_description"],
            data["room_background_sprite_path"],
            [SpecialRoomAction.from_dict(action_data) for action_data in data["room_available_actions"]],
        )

    @staticmethod
    def load_available_special_rooms():
        folder_path = "Content/Rooms/Special"
        return RoomData.get_rooms_in_directory(folder_path, SpecialRoomData.from_dict)


class CombatRoomData(RoomData):
    def __init__(self, room_background_sprite_path, room_enemies):
        super().__init__(room_background_sprite_path)
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
        :return: A list of lists of CombatRoomData objects, one list for each level of difficulty.
        """
        max_index = CombatRoomData.get_last_combat_room_index()
        levels: List[List[CombatRoomData]] = []
        for difficulty in range(max_index + 1):
            folder_path = f"Content/Rooms/Combat/Room_{difficulty}"

            rooms = RoomData.get_rooms_in_directory(folder_path, CombatRoomData.from_dict)
            log_info(f"Loaded {len(rooms)} rooms from {folder_path}")
            if len(rooms) == 0:
                raise Exception(f"No combat rooms found in {folder_path}, even though max available room index is {max_index}.")
            levels.append(rooms)

        return levels

    @staticmethod
    def load_available_boss_rooms():
        folder_path = "Content/Rooms/Boss"
        return RoomData.get_rooms_in_directory(folder_path, CombatRoomData.from_dict)

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
