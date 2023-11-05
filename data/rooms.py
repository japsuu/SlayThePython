from __future__ import annotations

import os
from typing import TYPE_CHECKING
from data.enemies import EnemySpawnData
import json

from utils import audio, constants
from utils.logging import log_info

if TYPE_CHECKING:
    from typing import List
    from state_management import GameState


class SpecialRoomAction:
    def __init__(self, action_name, action_description, change_health_amount, choose_from_cards_count, remove_cards_amount, change_mana_permanent):
        self.action_name: str = action_name
        self.action_description: str = action_description
        self.change_health_amount: int = change_health_amount
        self.choose_from_cards_count: int = choose_from_cards_count
        self.remove_cards_amount: int = remove_cards_amount
        self.change_mana_permanent: int = change_mana_permanent

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["action_name"],
            data["action_description"],
            data["change_health_amount"],
            data["choose_from_cards_count"],
            data["remove_cards_amount"],
            data["change_mana_permanent"],
        )

    def get_effects_text(self, current_player_health) -> List[str]:
        description = []
        if self.change_health_amount != 0:
            if self.change_health_amount > 0:
                description.append(f"Gain {abs(self.change_health_amount)} health.")
            else:
                # Ensure player is left with at least 1 health
                self.change_health_amount = -min(abs(self.change_health_amount), current_player_health - 1)
                description.append(f"Lose {abs(self.change_health_amount)} health.")
            description.append("")
        if self.choose_from_cards_count > 0:
            description.append(f"Choose a card from {self.choose_from_cards_count} random cards to add to your deck.")
            description.append("")
        if self.remove_cards_amount > 0:
            description.append(f"Remove {self.remove_cards_amount} cards from your deck.")
            description.append("")
        if self.change_mana_permanent != 0:
            if self.change_mana_permanent > 0:
                description.append(f"Gain {abs(self.change_mana_permanent)} additional mana at the start of every turn.")
            else:
                description.append(f"Lose {abs(self.change_mana_permanent)} mana at the start of every turn.")
            description.append("")
        if len(description) > 0:
            description.pop()
        else:
            description.append("No effects.")
        return description

    def execute(self, game_state: GameState):
        if self.change_health_amount != 0:
            previous_health = game_state.current_game_save.player_health
            if self.change_health_amount < 0:
                # Ensure player is left with at least 1 health
                self.change_health_amount = -min(abs(self.change_health_amount), game_state.current_game_save.player_health - 1)
                game_state.current_game_save.player_health = max(game_state.current_game_save.player_health + self.change_health_amount, 0)
                audio.play_one_shot_delayed(constants.damaged_sound, 0.1)
            else:
                game_state.current_game_save.player_health = min(game_state.current_game_save.player_health + self.change_health_amount, 100)
                audio.play_one_shot_delayed(constants.healed_sound, 0.1)
            log_info(f"Player health changed from {previous_health} to {game_state.current_game_save.player_health}.")
        if self.choose_from_cards_count > 0:
            game_state.generate_reward_cards(self.choose_from_cards_count)
            game_state.is_player_choosing_reward_cards = True
            audio.play_one_shot(constants.show_rewards_sound)
            log_info(f"Player is choosing from {self.choose_from_cards_count} reward cards.")
        if self.remove_cards_amount > 0:
            game_state.player_can_remove_cards_count = self.remove_cards_amount
            game_state.generate_removal_cards()
            game_state.is_player_removing_cards = True
            audio.play_one_shot(constants.show_rewards_sound)
            log_info(f"Player is choosing {self.remove_cards_amount} cards to remove.")
        if self.change_mana_permanent > 0:
            previous_mana = game_state.current_game_save.player_base_mana
            game_state.current_game_save.player_base_mana = max(game_state.current_game_save.player_base_mana + self.change_mana_permanent, 0)
            audio.play_one_shot_delayed(constants.gain_mana_sound, 0.2)
            log_info(f"Player base mana changed from {previous_mana - self.change_mana_permanent} to {game_state.current_game_save.player_base_mana}.")


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

    @staticmethod
    def get_rooms_in_directory_recursive(folder_path, from_dict_func):
        """
        :param folder_path: Path to loop recursively through all subfolders to find rooms.
        :param from_dict_func: A function that takes a dictionary and returns an object of the type that the dictionary represents.
        :return: A list of CombatRoomData objects, one for each room found in the folder.
        """
        rooms = []
        # Loop recursively through all subfolders no matters their name or depth
        folders = RoomData.get_folders_directory_recursive(folder_path)
        for folder_name in folders:
            rooms += RoomData.get_rooms_in_directory(folder_name, from_dict_func)
        return rooms

    @staticmethod
    def get_folders_directory_recursive(folder_path):
        """
        :param folder_path: Path to loop recursively through all subfolders.
        :return: A list of all folders inside folder_path.
        """
        folders = []
        # Loop recursively through all subfolders no matters their name or depth
        for folder_name in os.listdir(folder_path):
            if os.path.isdir(folder_path + "/" + folder_name):
                folders.append(folder_path + "/" + folder_name)
                folders += RoomData.get_folders_directory_recursive(folder_path + "/" + folder_name)
        return folders


class SpecialRoomData(RoomData):
    rarity_weights = {
        "common": 60,       # 60% chance
        "uncommon": 30,     # 30% chance
        "rare": 10          # 10% chance
    }

    def __init__(self, rarity, room_name, room_description, room_background_sprite_path, room_actions):
        super().__init__(room_background_sprite_path)
        self.rarity: str = rarity
        self.room_name: str = room_name
        self.room_description: str = room_description
        self.room_available_actions: List[SpecialRoomAction] = room_actions

    def to_dict(self):
        return {
            "rarity": self.rarity,
            "room_name": self.room_name,
            "room_description": self.room_description,
            "room_background_sprite_path": self.room_background_sprite_path,
            "room_available_actions": self.room_available_actions,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["rarity"],
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
    def __init__(self, room_background_sprite_path, encountered_at_levels, room_enemies):
        super().__init__(room_background_sprite_path)
        self.encountered_at_levels: str = encountered_at_levels
        self.room_enemies: List[EnemySpawnData] = room_enemies

    def to_dict(self):
        return {
            "room_background_sprite_path": self.room_background_sprite_path,
            "encountered_at_levels": self.encountered_at_levels,
            "room_enemies": self.room_enemies,
        }

    @classmethod
    def from_dict(cls, data):
        room_enemies = [EnemySpawnData.from_dict(enemy_data) for enemy_data in data["room_enemies"]]
        return cls(
            data["room_background_sprite_path"],
            data["encountered_at_levels"],
            room_enemies,
        )

    @staticmethod
    def load_available_combat_rooms():
        """
        :return: A list of lists of CombatRoomData objects, one list for each level of difficulty.
        Encountered_at_levels can be specified by defining a range:
        - "1-5" to appear on levels 1, 2, 3, 4 and 5
        """
        levels: List[List[CombatRoomData]] = []
        base_folder_path = f"Content/Rooms/Combat"
        # Loop recursively through all subfolders
        rooms: List[CombatRoomData] = RoomData.get_rooms_in_directory_recursive(base_folder_path, CombatRoomData.from_dict)
        if len(rooms) < 1:
            raise Exception(f"No combat rooms found in {base_folder_path}!")

        for room in rooms:
            for encountered_at_level in room.encountered_at_levels.split(","):
                if "-" in encountered_at_level:
                    start, end = encountered_at_level.split("-")
                    start = int(start)
                    end = int(end)
                    for level in range(start, end + 1):
                        while level > len(levels):
                            levels.append([])
                        levels[level - 1].append(room)
                else:
                    level = int(encountered_at_level)
                    while level > len(levels):
                        levels.append([])
                    levels[level - 1].append(room)
        # Check if there are empty levels
        for level in range(len(levels)):
            if len(levels[level]) == 0:
                raise Exception(f"No combat rooms found for level {level + 1} (index {level})!")
        log_info(f"Loaded {len(rooms)} combat rooms of {len(levels)} levels from {base_folder_path}")

        return levels

    @staticmethod
    def load_available_boss_rooms():
        folder_path = "Content/Rooms/Boss"
        return RoomData.get_rooms_in_directory(folder_path, CombatRoomData.from_dict)

    # @staticmethod
    # def get_last_combat_room_index():
    #     """
    #     :return: The largest level index available in the "Content/Rooms/Combat" folder.
    #     """
    #     global last_combat_room_index
    #     if last_combat_room_index != -1:
    #         return last_combat_room_index

    #     folder_path = "Content/Rooms/Combat"
    #     for folder_name in os.listdir(folder_path):
    #         if folder_name.startswith("Room_"):
    #             for filename in os.listdir(folder_path + "/" + folder_name):
    #                 if filename.endswith(".json"):
    #                     level = int(folder_name.split("_")[1])
    #                     last_combat_room_index = max(last_combat_room_index, level)
    #                     break

    #     if last_combat_room_index == -1:
    #         raise Exception("No combat rooms found in Content/Rooms/Combat.")

    #     return last_combat_room_index
