from __future__ import annotations
from typing import TYPE_CHECKING

import json
import os

import pygame

from utils import constants, audio
from utils.constants import SAVE_GAME_FOLDER, FONT_SAVE_SELECTION, FONT_SAVE_SELECTION_S
from data.cards import CardData
from utils.input import Inputs

if TYPE_CHECKING:
    from typing import List


class GameSave:
    def __init__(self, save_game_name, dungeon_seed, dungeon_room_index, player_health, player_base_mana, player_cards):
        self.save_game_name: str = save_game_name
        self.dungeon_seed: int = dungeon_seed
        self.dungeon_room_index: int = dungeon_room_index
        self.player_health: int = player_health
        self.player_base_mana: int = player_base_mana
        self.player_cards: List[CardData] = player_cards

    def to_dict(self):
        return {
            "save_game_name": self.save_game_name,
            "dungeon_seed": self.dungeon_seed,
            "dungeon_room_index": self.dungeon_room_index,
            "player_health": self.player_health,
            "player_base_mana": self.player_base_mana,
            "player_cards": [card.to_dict() for card in self.player_cards]
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["save_game_name"],
            data["dungeon_seed"],
            data["dungeon_room_index"],
            data["player_health"],
            data["player_base_mana"],
            [CardData.from_dict(card_data) for card_data in data["player_cards"]]
        )

    def save(self):
        if not os.path.exists(SAVE_GAME_FOLDER):
            os.makedirs(SAVE_GAME_FOLDER)

        filename = os.path.join(SAVE_GAME_FOLDER, f"{self.save_game_name}.json")
        with open(filename, "w") as file:
            json.dump(self.to_dict(), file, indent=2)

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
            from utils.constants import PLAYER_STARTING_CARDS, PLAYER_STARTING_HEALTH
            for card in PLAYER_STARTING_CARDS:
                # Create a new CardData object with the same values as the original
                player_cards.append(card.copy())

            from utils.math import hash_string
            return GameSave(save_game_name, hash_string(save_game_name), 0, PLAYER_STARTING_HEALTH, 3, player_cards)

    @staticmethod
    def delete_save_game(save_game_name):
        filename = os.path.join(SAVE_GAME_FOLDER, f"{save_game_name}.json")
        if os.path.exists(filename):
            os.remove(filename)
        else:
            raise Exception(f"Could not delete save game {save_game_name}, because it does not exist.")

    @staticmethod
    def list_available_save_games():
        save_games = []
        from utils.constants import SAVE_GAME_FOLDER
        if os.path.exists(SAVE_GAME_FOLDER):
            for filename in os.listdir(SAVE_GAME_FOLDER):
                if filename.endswith(".json"):
                    save_game_name = os.path.splitext(filename)[0]
                    save_games.append(save_game_name)
        return save_games
    
    
def is_valid_file_name_character(char: str) -> bool:
    return char.isalnum() or char == "_" or char == " "


def display_blocking_save_selection_screen(screen, clock, available_save_games):
    save_game_name = ""
    input_active = True
    delta_time = 1 / 60
    input_ticker: float = 1
    input_ticker_flip: bool = False
    input_ticker_text = FONT_SAVE_SELECTION.render("|", True, (255, 255, 255))
    input_ticker_text_rect = input_ticker_text.get_rect()

    while input_active:     # Quick and dirty
        Inputs.handle_input_events()
        if Inputs.should_quit():
            pygame.quit()
            quit()
        if Inputs.is_key_pressed(pygame.K_RETURN):
            if save_game_name and (save_game_name not in available_save_games):
                input_active = False
        elif Inputs.is_key_pressed(pygame.K_BACKSPACE):
            if len(save_game_name) > 0:
                save_game_name = save_game_name[:-1]
        elif len(save_game_name) < 20:
            unicode = Inputs.get_unicode()
            if unicode and is_valid_file_name_character(unicode):
                save_game_name += unicode

        # Animate the input ticker
        if input_ticker_flip:
            input_ticker += delta_time
        else:
            input_ticker -= delta_time
        if input_ticker <= 0:
            input_ticker = 0
            input_ticker_flip = True
            input_ticker_text.set_alpha(0)
        elif input_ticker >= 1:
            input_ticker = 1
            input_ticker_flip = False
            input_ticker_text.set_alpha(255)

        screen.fill((0, 0, 0))

        # Draw the title
        note_text = FONT_SAVE_SELECTION.render("Start typing to name your new save.", True, (180, 180, 180))
        screen.blit(note_text, (10, 15))
        note_text = FONT_SAVE_SELECTION_S.render("Note: Your save name is used as the world generation seed.", True, (180, 180, 180))
        screen.blit(note_text, (10, 50))

        # Draw a rect around the input
        input_rect = pygame.Rect(10, 110, 800, 50)
        pygame.draw.rect(screen, (100, 100, 100), input_rect, 1)

        # Draw the input text
        input_text = FONT_SAVE_SELECTION.render("New save name: " + save_game_name, True, (255, 255, 255))
        input_text_rect = input_text.get_rect()
        input_text_rect.midleft = (input_rect.left + 10, input_rect.centery)
        screen.blit(input_text, input_text_rect)

        # Draw the input ticker
        input_ticker_text_rect.topleft = input_text_rect.topright
        screen.blit(input_ticker_text, input_ticker_text_rect)

        # Draw available saved games title
        saved_games_title_text = FONT_SAVE_SELECTION.render("Available saved games (click to load):", True, (180, 180, 180))
        saved_games_title_text_rect = saved_games_title_text.get_rect()
        saved_games_title_text_rect.topleft = (10, 220)
        screen.blit(saved_games_title_text, saved_games_title_text_rect)

        # List all existing save games
        previous_rect_bottom = saved_games_title_text_rect.bottom + 20
        for existing_game_save in available_save_games:
            save = GameSave.load_save_game(existing_game_save)

            button = pygame.Surface((680, 40))
            button_rect = button.get_rect()
            button_rect.topleft = (10, previous_rect_bottom)
            color = (255, 255, 255)
            if button_rect.collidepoint(Inputs.get_mouse_position()):
                if Inputs.is_mouse_button_up(1):
                    save_game_name = existing_game_save
                    input_active = False
                    audio.play_one_shot(constants.button_sound)
                color = (80, 80, 80)
            button.fill(color)
            screen.blit(button, button_rect)

            # Split the text into two parts
            name_text = FONT_SAVE_SELECTION.render(existing_game_save, True, (0, 0, 0))
            info_text = FONT_SAVE_SELECTION.render(f"(room {save.dungeon_room_index + 1}, {save.player_health} health, {len(save.player_cards)} cards)", True, (0, 0, 0))

            # Get rectangles for both texts
            name_rect = name_text.get_rect()
            info_rect = info_text.get_rect()

            # Set the positions
            name_rect.midleft = (20, button_rect.centery)
            info_rect.midleft = (320, name_rect.centery)

            # Blit both texts
            screen.blit(name_text, name_rect)
            screen.blit(info_text, info_rect)

            previous_rect_bottom = button_rect.bottom + 10

        pygame.display.flip()
        clock.tick(60)
        delta_time = clock.get_time() / 1000

    return save_game_name
