from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

from data import rooms
from data.cards import CardData
from data.rooms import RoomData
from data.saves import GameSave, display_blocking_save_selection_screen
from game_objects import EnemyCharacter, GameCard, GameObjectCollection, EnemyCharacterFactory, GameCardFactory, DamageNumberVisualEffectFactory
from utils import drawing
from utils.animations import Tween
from utils.io import ImageLibrary, load_image
from utils.logging import log_info
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
        self.current_room_background: Optional[pygame.Surface] = None
        self.current_round_index: int = 0
        self.current_player_mana: int = 0
        self.current_player_mana_limit: int = 0
        self.current_player_block: int = 0
        self.current_targeted_enemy_character: Optional[EnemyCharacter] = None
        self.current_hand_game_cards: List[GameCard] = []
        self.current_draw_pile: List[CardData] = []
        self.current_discard_pile: List[CardData] = []
        self.current_exhaust_pile: List[CardData] = []
        self.current_reward_game_cards: List[GameCard] = []
        self.current_alive_enemy_characters: List[EnemyCharacter] = []
        self.current_draw_limit: int = 5
        self.mana_addition_next_turn: int = 0
        self.draw_limit_addition_next_turn: int = 0
        self.target_icon_alpha: int = 255
        self.target_icon_alpha_direction: int = 1
        self.game_object_collection: GameObjectCollection = GameObjectCollection()
        self.is_player_choosing_rewards: bool = False
        self.is_players_turn: bool = False
        self.gameplay_pause_timer: float = 0
        self.draw_pile_position = self.screen.get_rect().bottomleft
        self.discard_pile_position = self.screen.get_rect().bottomright
        self.player_damaged_animation: Optional[Tween] = None
        self.player_damaged_overlay = self.game_data.image_library.effect_damaged_self
        self.damage_effect_font = pygame.font.Font(None, 55)
        self.text_color = (255, 255, 255)
        self.damage_number_visual_effect_factory = DamageNumberVisualEffectFactory(self.game_object_collection, self.damage_effect_font, "0", self.text_color, 3000)
        # noinspection PyTypeChecker
        self.enemy_character_factory = EnemyCharacterFactory(self.game_object_collection, None, self.game_data.image_library)
        # noinspection PyTypeChecker
        self.game_card_factory = GameCardFactory(self.game_object_collection, self.draw_pile_position, self.discard_pile_position, None)

    def play_player_damaged_animation(self):
        self.player_damaged_animation = Tween(255, 0, 0.5, self.__update_damage_overlay_alpha)

    def __update_damage_overlay_alpha(self, new_alpha: int):
        self.player_damaged_overlay.set_alpha(new_alpha)

    def instantiate_damage_number(self, damage_amount: int, was_blocked: bool, position: tuple[int, int], layer=None):
        self.damage_number_visual_effect_factory.set_layer(layer)
        if was_blocked:
            self.damage_number_visual_effect_factory.set_target_text(f"-{damage_amount}")
            self.damage_number_visual_effect_factory.set_target_color((0, 0, 255))
        else:
            self.damage_number_visual_effect_factory.set_target_text(f"-{damage_amount}")
            self.damage_number_visual_effect_factory.set_target_color((255, 0, 0))
        return self.damage_number_visual_effect_factory.instantiate(position)

    def enter_main_menu(self):
        """
        Displays a debug_screen where the player can choose to load an existing save or create a new one.
        Warning: This function is blocking and will not return until the player has chosen a save.
        """
        pygame.display.set_caption("Slay the Python - Initializing...")
        available_save_games = GameSave.list_available_save_games()
        self.current_game_save = GameSave.load_save_game(display_blocking_save_selection_screen(pygame.display.get_surface(), available_save_games))
        self.is_players_turn = True
        self.current_player_mana_limit = self.current_game_save.player_base_mana
        self.current_draw_limit = 5
        self.draw_limit_addition_next_turn = 0
        # Move cards from save to draw pile
        for card in self.current_game_save.player_cards:
            self.current_draw_pile.append(card)
        self.initialize_new_room(self.current_game_save)
        GameSave.save(self.current_game_save)

    def save(self):
        self.update_save_cards()
        GameSave.save(self.current_game_save)

    def exit_current_save(self):
        self.current_game_save = None

    def update_save_cards(self):
        self.current_game_save.player_cards.clear()
        for card in self.current_discard_pile:
            self.current_game_save.player_cards.append(card)
        for card in self.current_draw_pile:
            self.current_game_save.player_cards.append(card)

    def delete_current_save(self):
        GameSave.delete_save_game(self.current_game_save.save_game_name)
        self.current_game_save = None

    def load_next_room(self):
        # TODO: Clean up the game state
        # for old_game_object in self.game_object_collection.game_objects:
        #     old_game_object.destroy()
        # self.current_alive_enemy_characters.clear()
        # self.current_reward_game_cards.clear()
        # self.current_draw_pile.clear()
        # self.current_discard_pile.clear()
        # self.current_hand_game_cards.clear()
        # self.current_targeted_enemy_character = None
        # self.current_round_index = 0
        # self.is_player_choosing_rewards = False
        for reward_card in self.current_reward_game_cards:
            reward_card.destroy()
        self.current_reward_game_cards.clear()
        # Player wins, let the player choose cards and increment the room index
        self.current_game_save.dungeon_room_index += 1
        self.initialize_new_room(self.current_game_save)

    def initialize_new_room(self, current_game_save: GameSave):
        room_index: int = current_game_save.dungeon_room_index
        initialize_dungeon_random(self.current_game_save.dungeon_seed, room_index)

        self.current_player_mana_limit = 3
        self.current_draw_limit = 5
        self.draw_limit_addition_next_turn = 0
        self.add_discard_to_draw_pile()

        self.initialize_player_turn()

        # Select a random room with the correct difficulty
        # Selecting a boss room
        if room_index == self.game_data.boss_room_index:
            selected_room_data: RoomData = random.choice(self.game_data.available_boss_rooms)
        # Selecting the starting room
        elif room_index == 0:
            selected_room_data: RoomData = random.choice(self.game_data.available_room_difficulties[0])
        # Selecting a special room. After 2 rooms 20% chance
        elif room_index > 1 and len(self.game_data.available_special_rooms) > 0 and random.random() < 0.2:
            selected_room_data: RoomData = random.choice(self.game_data.available_special_rooms)
        # Selecting a normal room
        else:
            # Select a difficulty level within range of 1 of the current room index
            base_difficulty_level = room_index + 1
            selected_room_difficulty_level_min = max(base_difficulty_level - 1, 1)  # Never select a room with difficulty 0 in this phase
            selected_room_difficulty_level_max = min(base_difficulty_level + 1, len(self.game_data.available_room_difficulties) - 1)
            selected_room_difficulty_level = random.randint(selected_room_difficulty_level_min, selected_room_difficulty_level_max)
            selected_room_data: RoomData = random.choice(self.game_data.available_room_difficulties[selected_room_difficulty_level])

        self.spawn_enemies_from_room_data(self.screen.get_width(), self.screen.get_height(), selected_room_data, self.enemy_character_factory, self.current_alive_enemy_characters)

        self.current_room_background = load_image(selected_room_data.room_background_sprite_path)

        # Ensure that the player has a target
        if len(self.current_alive_enemy_characters) > 0:
            self.current_targeted_enemy_character = self.current_alive_enemy_characters[0]

        # # If the room is the boss room, spawn the boss
        # if room_index == self.game_data.boss_room_index:
        #     boss = random.choice(self.game_data.available_boss_spawn_data)
        #     x = pygame.display.get_surface().get_width() / 2
        #     y = pygame.display.get_surface().get_height() / 2 - pygame.display.get_surface().get_height() * 0.1
        #     self.enemy_character_factory.set_target_spawn_data(boss)
        #     enemy_reference = self.enemy_character_factory.instantiate((x, y))
        #     self.current_alive_enemy_characters.append(enemy_reference)
        # else:  # Otherwise spawn normal enemies
        #     enemy_count = room_index + 1
        #     padding = 0
        #     enemy_width = 256

        #     screen_width = self.screen.get_width()
        #     screen_height = self.screen.get_height()

        #     # Calculate the total width of the images and padding
        #     total_width = enemy_count * enemy_width + (enemy_count - 1) * padding

        #     # Calculate the starting position_or_rect from the center of the debug_screen
        #     start_position = (screen_width - total_width) / 2

        #     positions = []

        #     for i in range(enemy_count):
        #         # Calculate the x position_or_rect biased to the center of the debug_screen
        #         x = start_position + (enemy_width + padding) * i + (enemy_width / 2)

        #         y = screen_height / 2 - screen_height * 0.1

        #         positions.append((x, y))

        #     for i, (x, y) in enumerate(positions):
        #         self.enemy_character_factory.set_target_spawn_data(random.choice(self.game_data.available_enemy_spawn_data))
        #         enemy_reference = self.enemy_character_factory.instantiate((x, y))
        #         self.current_alive_enemy_characters.append(enemy_reference)
        # if len(self.current_alive_enemy_characters) > 0:
        #     self.current_targeted_enemy_character = self.current_alive_enemy_characters[0]

    @staticmethod
    def spawn_enemies_from_room_data(screen_width, screen_height, room_data: RoomData, enemy_character_factory: EnemyCharacterFactory, current_alive_enemy_characters: List[EnemyCharacter]):
        padding = 0
        enemy_width = 256
        enemy_count = len(room_data.room_enemies)

        available_width = enemy_count * enemy_width + (enemy_count - 1) * padding

        start_x = (screen_width - available_width) / 2
        positions = []
        for i in range(enemy_count):
            # Calculate the x position_or_rect biased to the center of the debug_screen
            x = start_x + (enemy_width + padding) * i + (enemy_width / 2)
            y = screen_height / 2 - screen_height * 0.1
            positions.append((x, y))
        for i, (x, y) in enumerate(positions):
            i: int
            enemy_character_factory.set_target_spawn_data(room_data.room_enemies[i])
            enemy_reference = enemy_character_factory.instantiate((x, y))
            current_alive_enemy_characters.append(enemy_reference)

    def initialize_player_turn(self):
        self.player_draw_new_hand_cards()
        self.current_player_mana = max(0, self.current_player_mana_limit + self.mana_addition_next_turn)
        self.mana_addition_next_turn = 0
        self.current_player_block = 0
        self.is_players_turn = True

    def add_discard_to_draw_pile(self):
        for card in self.current_discard_pile:
            self.current_draw_pile.append(card)
        self.current_discard_pile.clear()

    def change_mana_limit(self, amount):
        self.current_player_mana_limit += amount
        if self.current_player_mana_limit < 0:
            self.current_player_mana_limit = 0

    def change_mana_next_turn(self, amount):
        self.mana_addition_next_turn += amount

    def change_draw_limit(self, amount):
        self.current_draw_limit += amount
        if self.current_draw_limit < 3:
            self.current_draw_limit = 3
        if self.current_draw_limit > 8:
            self.current_draw_limit = 8

    def change_draw_limit_next_turn(self, amount):
        self.draw_limit_addition_next_turn += amount

    def player_draw_new_hand_cards(self):
        for old_card in self.current_hand_game_cards:
            old_card.on_played()
            self.current_discard_pile.append(old_card.card_data)
        self.current_hand_game_cards.clear()
        card_count = self.current_draw_limit + self.draw_limit_addition_next_turn
        if card_count > 8:
            card_count = 8
        if card_count < 3:
            card_count = 3
        self.draw_limit_addition_next_turn = 0
        # Check if draw pile has enough cards
        if len(self.current_draw_pile) < card_count:
            self.add_discard_to_draw_pile()

        # If there's still not enough cards, then limit the card count
        if len(self.current_draw_pile) < card_count:
            card_count = len(self.current_draw_pile)

        # Select x random cards from player's deck
        random.shuffle(self.current_draw_pile)
        selections = self.current_draw_pile[:card_count]
        for index, selection in enumerate(selections):
            # Evenly distribute the cards at the bottom of the debug_screen
            width_total = pygame.display.get_surface().get_width()
            card_visuals_width = width_total / 1.8
            start = (width_total - card_visuals_width) / 2
            spacing = card_visuals_width / (max(1, card_count - 1))
            x = start + (index * spacing)
            y = pygame.display.get_surface().get_height() - 0.08 * pygame.display.get_surface().get_height()
            self.game_card_factory.set_target_card_data(selection)
            card_reference = self.game_card_factory.instantiate((x, y))
            self.current_hand_game_cards.append(card_reference)
            self.current_draw_pile.remove(selection)

    def generate_reward_cards(self):
        self.current_reward_game_cards.clear()
        card_count = 3
        # Select X random cards from all available cards
        selections = random.sample(self.game_data.available_cards, k=card_count)
        for index, selection in enumerate(selections):
            # Evenly distribute the cards at the center of the debug_screen
            width_total = pygame.display.get_surface().get_width()
            card_visuals_width = width_total / 1.8
            start = (width_total - card_visuals_width) / 2
            spacing = card_visuals_width / (card_count - 1)
            x = start + (index * spacing)
            y = pygame.display.get_surface().get_height() / 2
            self.game_card_factory.set_target_card_data(selection)
            card_reference = self.game_card_factory.instantiate((x, y))
            self.current_reward_game_cards.append(card_reference)

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
            if (not game_object.is_awaiting_destruction) and game_object.is_active:
                game_object.update(self.delta_time)
                self.frame_buffer.add_drawable(game_object)


class GameData:
    def __init__(self):
        # Consts
        self.boss_room_index: int = rooms.last_combat_room_index + 1

        # Enemies
        # self.available_enemy_spawn_data = EnemySpawnData.load_available_enemies()
        # self.available_boss_spawn_data = EnemySpawnData.load_available_bosses()
        # log_info(f"Successfully loaded {len(self.available_enemy_spawn_data)} enemies and {len(self.available_boss_spawn_data)} bosses.")

        # Cards
        self.available_cards: List[CardData] = CardData.load_available_cards()
        log_info(f"Successfully loaded {len(self.available_cards)} cards.")

        # Rooms
        self.available_room_difficulties: List[List[RoomData]] = RoomData.load_available_combat_rooms()
        room_count_in_total = sum([len(rooms_for_difficulty) for rooms_for_difficulty in self.available_room_difficulties])
        log_info(f"Successfully loaded {len(self.available_room_difficulties)} room difficulties with {room_count_in_total} rooms in total.")
        self.available_special_rooms: List[RoomData] = RoomData.load_available_special_rooms()
        log_info(f"Successfully loaded {len(self.available_special_rooms)} special rooms.")
        self.available_boss_rooms: List[RoomData] = RoomData.load_available_boss_rooms()
        log_info(f"Successfully loaded {len(self.available_boss_rooms)} boss rooms.")

        # UI
        self.image_library = ImageLibrary()
