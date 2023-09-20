import json
import os
from typing import List

from Cards import CardData
from Utils import hash_seed

SAVE_FOLDER = "save-game-folder"


class GameSave:
    def __init__(self, save_game_name, dungeon_seed, dungeon_room_index, player_health, player_cards):
        self.save_game_name: str = save_game_name
        self.dungeon_seed: int = dungeon_seed
        self.dungeon_room_index: int = dungeon_room_index
        self.player_health: int = player_health
        self.player_cards: List[CardData] = player_cards

    def to_dict(self):
        return {
            "save_game_name": self.save_game_name,
            "dungeon_seed": self.dungeon_seed,
            "dungeon_room_index": self.dungeon_room_index,
            "player_health": self.player_health,
            "player_cards": [card.to_dict() for card in self.player_cards]
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["save_game_name"],
            data["dungeon_seed"],
            data["dungeon_room_index"],
            data["player_health"],
            [CardData.from_dict(card_data) for card_data in data["player_cards"]]
        )


def list_available_save_games():
    save_games = []
    if os.path.exists(SAVE_FOLDER):
        for filename in os.listdir(SAVE_FOLDER):
            if filename.endswith(".json"):
                save_game_name = os.path.splitext(filename)[0]
                save_games.append(save_game_name)
    return save_games


def save_game(game_save):
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)

    filename = os.path.join(SAVE_FOLDER, f"{game_save.save_game_name}.json")
    with open(filename, "w") as file:
        json.dump(game_save.to_dict(), file)


def load_save_game(save_game_name):
    filename = os.path.join(SAVE_FOLDER, f"{save_game_name}.json")
    if os.path.exists(filename):
        with open(filename, "r") as file:
            data = json.load(file)
            return GameSave.from_dict(data)
    else:
        # If no GameSave with the name is found, return a new GameSave with default values.
        # Create the default cards
        player_cards = []
        for i in range(5):
            player_cards.append(CardData("Strike", "Deal 6 damage", 6, 0, 1, "Data/Sprites/Cards/strike.png"))
            player_cards.append(CardData("Defend", "Gain 5 block", 0, 5, 1, "Data/Sprites/Cards/defend.png"))

        return GameSave(save_game_name, hash_seed(save_game_name), 0, 100, player_cards)


def delete_save_game(save_game_name):
    filename = os.path.join(SAVE_FOLDER, f"{save_game_name}.json")
    if os.path.exists(filename):
        os.remove(filename)
