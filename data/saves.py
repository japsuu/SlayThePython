from __future__ import annotations
from typing import TYPE_CHECKING

import json
import os

import pygame

from constants import SAVE_GAME_FOLDER
from data.cards import CardData
from utils.input import Inputs

if TYPE_CHECKING:
    from typing import List


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

    def save(self):
        if not os.path.exists(SAVE_GAME_FOLDER):
            os.makedirs(SAVE_GAME_FOLDER)

        filename = os.path.join(SAVE_GAME_FOLDER, f"{self.save_game_name}.json")
        with open(filename, "w") as file:
            json.dump(self.to_dict(), file)

    @staticmethod
    def load_save_game(save_game_name):
        filename = os.path.join(SAVE_GAME_FOLDER, f"{save_game_name}.json")
        if os.path.exists(filename):
            with open(filename, "r") as file:
                data = json.load(file)
                return GameSave.from_dict(data)
        else:
            # If no GameSave with the name is found, return a new GameSave with default values.
            # Create the default cards
            # Copy PLAYER_STARTING_CARDS to a new list
            player_cards = []
            from constants import PLAYER_STARTING_CARDS, PLAYER_STARTING_HEALTH
            for card in PLAYER_STARTING_CARDS:
                # Create a new CardData object with the same values as the original
                new_card = CardData(card.card_name, card.card_description, card.card_damage, card.card_block, card.card_cost, card.sprite_path)
                player_cards.append(new_card)

            from utils.math import hash_string
            return GameSave(save_game_name, hash_string(save_game_name), 0, PLAYER_STARTING_HEALTH, player_cards)

    @staticmethod
    def delete_save_game(save_game_name):
        filename = os.path.join(SAVE_GAME_FOLDER, f"{save_game_name}.json")
        if os.path.exists(filename):
            os.remove(filename)

    @staticmethod
    def list_available_save_games():
        save_games = []
        from constants import SAVE_GAME_FOLDER
        if os.path.exists(SAVE_GAME_FOLDER):
            for filename in os.listdir(SAVE_GAME_FOLDER):
                if filename.endswith(".json"):
                    save_game_name = os.path.splitext(filename)[0]
                    save_games.append(save_game_name)
        return save_games


def display_blocking_save_selection_screen(screen, available_save_games):
    save_game_name = ""
    input_active = True

    while input_active:
        Inputs.handle_input_events()
        if Inputs.should_quit():
            pygame.quit()
            quit()
        if Inputs.is_key_pressed(pygame.K_RETURN):
            if save_game_name and (save_game_name not in available_save_games):
                input_active = False
        elif Inputs.is_key_pressed(pygame.K_BACKSPACE):
            save_game_name = save_game_name[:-1]
        elif len(save_game_name) < 20:
            save_game_name += Inputs.get_unicode()

        screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 36)

        note_text = font.render("Note: Your save name is used as the world generation seed.", True, (180, 180, 180))
        screen.blit(note_text, (10, 40))

        input_text = font.render("New save name: " + save_game_name, True, (255, 255, 255))
        screen.blit(input_text, (10, 110))
        button = pygame.Rect(10, 110, 800, 30)
        pygame.draw.rect(screen, (100, 100, 100), button, 1)

        note_text_1 = font.render("Available saved games (click to load):", True, (180, 180, 180))
        screen.blit(note_text_1, (10, 180))

        # List all existing save games
        for index, existing_game_save in enumerate(available_save_games):
            save = GameSave.load_save_game(existing_game_save)

            # Split the text into two parts
            name_text = font.render(existing_game_save, True, (210, 210, 210))
            info_text = font.render(f"(room {save.dungeon_room_index + 1}, {save.player_health} health)", True, (210, 210, 210))

            # Get rectangles for both texts
            name_rect = name_text.get_rect()
            info_rect = info_text.get_rect()

            # Set the positions
            name_rect.topleft = (10, 210 + (index * 30))
            info_rect.topleft = (280, name_rect.top)  # Info starts at the same x-coordinate as the name

            # Blit both texts
            screen.blit(name_text, name_rect)
            screen.blit(info_text, info_rect)

            # draw a rect over the save game (use name_rect for positioning)
            button = pygame.Rect(name_rect.left, name_rect.top, 530, 30)
            pygame.draw.rect(screen, (100, 100, 100), button, 1)
            if Inputs.is_mouse_button_pressed(1):
                if button.collidepoint(Inputs.get_mouse_position()):
                    save_game_name = existing_game_save
                    input_active = False

        pygame.display.flip()

    return save_game_name
