from __future__ import annotations
from typing import TYPE_CHECKING

import random
import pygame

from data.cards import CardData
from data.enemies import EnemySpawnData
from data.saves import GameSave, display_blocking_save_selection_screen
from game_objects import EnemyCharacter, GameCard, GameObjectCollection
from utils import drawing
from utils.io import ImageLibrary
from utils.math import initialize_dungeon_random

if TYPE_CHECKING:
    from typing import Optional, List


class GameState:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock):
        self.frame_buffer: drawing.FrameBuffer = drawing.FrameBuffer(screen)
        self.game_data: GameData = GameData()
        self.screen: pygame.Surface = screen
        self.clock: pygame.time.Clock = clock
        self.delta_time: float = 1 / 60
        self.current_game_save: Optional[GameSave] = None
        self.current_round_index: int = 0
        self.current_player_mana: int = 0
        self.current_player_block: int = 0
        self.current_targeted_enemy_character: Optional[EnemyCharacter] = None
        self.current_hand_game_cards: List[GameCard] = []
        self.current_draw_pile: List[CardData] = []
        self.current_discard_pile: List[CardData] = []
        self.current_reward_game_cards: List[GameCard] = []
        self.current_alive_enemy_characters: List[EnemyCharacter] = []
        self.game_object_collection: GameObjectCollection = GameObjectCollection()
        self.is_player_choosing_rewards: bool = False
        self.is_players_turn: bool = False

    def enter_main_menu(self):
        """
        Displays a debug_screen where the player can choose to load an existing save or create a new one.
        Warning: This function is blocking and will not return until the player has chosen a save.
        """
        pygame.display.set_caption("Slay the Python - Initializing...")
        available_save_games = GameSave.list_available_save_games()
        self.current_game_save = GameSave.load_save_game(display_blocking_save_selection_screen(pygame.display.get_surface(), available_save_games))
        self.is_players_turn = True
        self.current_hand_game_cards.clear()
        self.current_draw_pile.clear()
        self.current_discard_pile.clear()
        self.current_alive_enemy_characters.clear()
        # Move cards from save to draw pile
        for card in self.current_game_save.player_cards:
            self.current_draw_pile.append(card)
        self.initialize_new_room(self.current_game_save.dungeon_room_index)
        GameSave.save(self.current_game_save)

    def save(self):
        self.update_save_cards()
        GameSave.save(self.current_game_save)

    def save_and_exit_current_save(self):
        self.save()
        self.current_game_save = None

    def update_save_cards(self):
        self.current_game_save.player_cards.clear()
        for card in self.current_discard_pile:
            self.current_game_save.player_cards.append(card)
        for card in self.current_draw_pile:
            self.current_game_save.player_cards.append(card)

    def delete_current_save(self):
        GameSave.delete_save_game(self.current_game_save.save_game_name)

    def load_next_room(self):
        # Player wins, let the player choose cards and increment the room index
        self.current_game_save.dungeon_room_index += 1
        self.initialize_new_room(self.current_game_save.dungeon_room_index)

    def initialize_new_room(self, room_index: int):
        initialize_dungeon_random(self.current_game_save.dungeon_seed, room_index)
        # Move the discard pile to draw pile
        self.prepare_draw_pile()

        self.initialize_player_turn()

        # If the room is the boss room, spawn the boss
        if room_index == self.game_data.BOSS_ROOM_INDEX:
            boss = random.choice(self.game_data.available_boss_spawn_data)
            x = pygame.display.get_surface().get_width() / 2
            y = pygame.display.get_surface().get_height() / 2 - pygame.display.get_surface().get_height() * 0.1
            new_enemy = EnemyCharacter((x, y), boss, self.game_data.image_library)
            new_enemy.queue(self.game_object_collection)
            self.current_alive_enemy_characters.append(new_enemy)
        else:  # Otherwise spawn normal enemies
            enemy_count = room_index + 1
            padding = 0
            enemy_width = 256

            screen_width = self.screen.get_width()
            screen_height = self.screen.get_height()

            # Calculate the total width of the images and padding
            total_width = enemy_count * enemy_width + (enemy_count - 1) * padding

            # Calculate the starting position_or_rect from the center of the debug_screen
            start_position = (screen_width - total_width) / 2

            positions = []

            for i in range(enemy_count):
                # Calculate the x position_or_rect biased to the center of the debug_screen
                x = start_position + (enemy_width + padding) * i + (enemy_width / 2)

                y = screen_height / 2 - screen_height * 0.1

                positions.append((x, y))

            for i, (x, y) in enumerate(positions):
                new_enemy = EnemyCharacter((x, y), random.choice(self.game_data.available_enemy_spawn_data), self.game_data.image_library)
                new_enemy.queue(self.game_object_collection)
                self.current_alive_enemy_characters.append(new_enemy)
        if len(self.current_alive_enemy_characters) > 0:
            self.current_targeted_enemy_character = self.current_alive_enemy_characters[0]

    def initialize_player_turn(self):
        self.player_draw_new_hand_cards()
        self.current_player_mana = 3
        self.current_player_block = 0
        self.is_players_turn = True

    def prepare_draw_pile(self):
        for card in self.current_discard_pile:
            self.current_draw_pile.append(card)
        self.current_discard_pile.clear()

    def player_draw_new_hand_cards(self):
        self.current_hand_game_cards.clear()
        card_count = 5
        # Check if draw pile has enough cards
        if len(self.current_draw_pile) < card_count:
            self.prepare_draw_pile()

        # If there's still not enough cards, then limit the card count
        if len(self.current_draw_pile) < card_count:
            card_count = len(self.current_draw_pile)

        # Select x random cards from player's deck
        selections = random.sample(self.current_draw_pile, k=card_count)  # Use random.sample instead of random.choices to prevent duplicates
        for index, selection in enumerate(selections):
            # Evenly distribute the cards at the bottom of the debug_screen
            width_total = pygame.display.get_surface().get_width()
            card_visuals_width = width_total / 1.8
            start = (width_total - card_visuals_width) / 2
            spacing = card_visuals_width / (card_count - 1)
            x = start + (index * spacing)
            y = pygame.display.get_surface().get_height() - 0.08 * pygame.display.get_surface().get_height()
            new_card = GameCard(self.screen.get_rect().bottomleft, self.screen.get_rect().bottomright, (x, y), selection)
            new_card.queue(self.game_object_collection)
            self.current_hand_game_cards.append(new_card)
            self.current_draw_pile.remove(selection)
            self.current_discard_pile.append(selection)

    def generate_reward_cards(self):
        self.current_reward_game_cards.clear()
        card_count = 3
        # Select X random cards from all available cards
        selections = random.choices(self.game_data.available_cards, k=card_count)
        for index, selection in enumerate(selections):
            # Evenly distribute the cards at the center of the debug_screen
            width_total = pygame.display.get_surface().get_width()
            card_visuals_width = width_total / 1.8
            start = (width_total - card_visuals_width) / 2
            spacing = card_visuals_width / (card_count - 1)
            x = start + (index * spacing)
            y = pygame.display.get_surface().get_height() / 2
            new_card = GameCard(self.screen.get_rect().bottomleft, self.screen.get_rect().bottomright, (x, y), selection)
            new_card.queue(self.game_object_collection)
            self.current_reward_game_cards.append(new_card)

    def remove_block(self, amount):
        self.current_player_block = max(self.current_player_block - amount, 0)

    def get_fight_state(self) -> str:
        if len(self.current_alive_enemy_characters) == 0:
            return "PLAYER_WIN"
        if self.current_game_save.player_health <= 0:
            return "PLAYER_LOSE"
        return "IN_PROGRESS"

    def update_game_objects(self):
        for game_object in self.game_object_collection.game_objects:
            if game_object.is_active:
                game_object.update(self.delta_time)
                self.frame_buffer.add_drawable(game_object)
            if game_object.is_awaiting_destruction:
                self.game_object_collection.remove(game_object)


class GameData:
    def __init__(self):
        # Consts
        self.BOSS_ROOM_INDEX: int = 4

        # Enemies
        self.available_enemy_spawn_data = EnemySpawnData.load_available_enemies()
        self.available_boss_spawn_data = EnemySpawnData.load_available_bosses()

        # Cards
        self.available_cards: List[CardData] = CardData.load_available_cards()

        # UI
        self.image_library = ImageLibrary()
