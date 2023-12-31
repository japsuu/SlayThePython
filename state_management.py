from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

from data.cards import CardData
from data.rooms import CombatRoomData, SpecialRoomData, RoomData
from data.saves import GameSave, display_blocking_save_selection_screen
from game_objects import EnemyCharacter, GameCard, GameObjectCollection, EnemyCharacterFactory, GameCardFactory, DamageNumberVisualEffectFactory
from utils import drawing, layout, audio, constants
from utils.animations import Tween
from utils.constants import FONT_DAMAGE_EFFECT_GENERIC
from utils.io import ImageLibrary, load_image
from utils.logging import log_info, log_warning
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
        self.player_base_mana_limit_addition_this_combat: int = 0
        self.current_player_block: int = 0
        self.current_targeted_enemy_character: Optional[EnemyCharacter] = None
        self.current_hand: List[GameCard] = []
        self.current_draw_pile: List[CardData] = []
        self.current_discard_pile: List[CardData] = []
        self.current_exhaust_pile: List[CardData] = []
        self.current_reward_game_cards: List[GameCard] = []
        self.current_removal_game_cards: List[GameCard] = []
        self.current_alive_enemy_characters: List[EnemyCharacter] = []
        self.current_draw_limit: int = 5
        self.current_special_room_data: Optional[SpecialRoomData] = None
        self.mana_addition_next_turn: int = 0
        self.draw_limit_addition_next_turn: int = 0
        self.target_icon_alpha: int = 255
        self.target_icon_alpha_direction: int = 1
        self.game_object_collection: GameObjectCollection = GameObjectCollection()
        self.is_player_choosing_reward_cards: bool = False
        self.is_player_removing_cards: bool = False
        self.is_pause_menu_shown = False
        self.is_help_shown = False
        self.player_can_remove_cards_count: int = 0
        self.is_players_turn: bool = False
        self.gameplay_pause_timer: float = 0
        self.draw_pile_position = self.screen.get_rect().bottomleft
        self.discard_pile_position = self.screen.get_rect().bottomright
        self.player_damaged_animation: Optional[Tween] = None
        self.player_damaged_overlay = self.game_data.image_library.effect_damaged_self
        self.text_color = (255, 255, 255)
        self.tooltip_font_color = (255, 255, 255)
        self.card_grid_layout = layout.GridLayout((312, 410), 4)
        self.damage_number_visual_effect_factory = DamageNumberVisualEffectFactory(self.game_object_collection, FONT_DAMAGE_EFFECT_GENERIC, "0", self.text_color, 3000)
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
        Displays a screen where the player can choose to load an existing save or create a new one.
        Warning: This function is blocking and will not return until the player has chosen a save.
        """
        pygame.display.set_caption("Slay the Python - Initializing...")
        audio.play_one_shot(constants.scene_change_sound)
        available_save_games = GameSave.list_available_save_games()
        self.current_game_save = GameSave.load_save_game(display_blocking_save_selection_screen(pygame.display.get_surface(), self.clock, available_save_games))
        self.is_players_turn = True
        self.player_base_mana_limit_addition_this_combat = 0
        self.current_draw_limit = 5
        self.draw_limit_addition_next_turn = 0
        # Move cards from save to draw pile
        for card in self.current_game_save.player_cards:
            self.current_draw_pile.append(card)
        self.initialize_new_room(self.current_game_save)
        GameSave.save(self.current_game_save)
        audio.play_one_shot(constants.scene_change_sound)

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
        for reward_card in self.current_reward_game_cards:
            reward_card.destroy()
        self.current_reward_game_cards.clear()
        self.current_game_save.dungeon_room_index += 1
        self.initialize_new_room(self.current_game_save)

    def initialize_new_room(self, current_game_save: GameSave):
        room_index: int = current_game_save.dungeon_room_index
        initialize_dungeon_random(self.current_game_save.dungeon_seed, room_index)

        self.current_draw_limit = 5
        self.draw_limit_addition_next_turn = 0
        self.player_base_mana_limit_addition_this_combat = 0
        self.current_special_room_data = None
        self.add_discard_to_draw_pile()
        self.initialize_player_turn()
        audio.play_one_shot_delayed(constants.enter_room_sound, 0.5)

        # Select a random room with the correct difficulty
        # Selecting a boss room
        if room_index == self.game_data.boss_room_index:
            selected_room_data: RoomData = random.choice(self.game_data.available_boss_rooms)
        # Selecting the starting room
        elif room_index == 0:
            selected_room_data: RoomData = random.choice(self.game_data.available_room_difficulties[0])
        # Selecting a special room. After 2 rooms 20% chance
        elif room_index > 1 and len(self.game_data.available_special_rooms) > 0 and random.random() < 0.2:
            # Select a pool of special rooms based on rarity
            selected_rarity = random.choices(list(SpecialRoomData.rarity_weights.keys()), list(SpecialRoomData.rarity_weights.values()))[0]

            # Create a pool of rooms by filtering the available rooms based on selected rarity
            available_rooms_with_rarity = [room for room in self.game_data.available_special_rooms if room.rarity == selected_rarity]

            if available_rooms_with_rarity:
                self.current_special_room_data = random.choice(available_rooms_with_rarity)
                selected_room_data: RoomData = self.current_special_room_data
            else:
                selected_room_data: RoomData = self.get_normal_room_from_room_index(room_index)
                log_warning(f"Could not find any special rooms with rarity {selected_rarity}. Falling back to normal room.")
        else:
            selected_room_data: RoomData = self.get_normal_room_from_room_index(room_index)

        self.current_room_background = load_image(selected_room_data.room_background_sprite_path, False).convert()

        if self.current_special_room_data is not None:
            return

        if isinstance(selected_room_data, CombatRoomData):
            self.player_draw_new_hand_cards()
            self.spawn_enemies_from_room_data(self.screen.get_width(), self.screen.get_height(), selected_room_data, self.enemy_character_factory, self.current_alive_enemy_characters)
            # Ensure that the player has a target
            if len(self.current_alive_enemy_characters) > 0:
                self.current_targeted_enemy_character = self.current_alive_enemy_characters[0]

    def get_normal_room_from_room_index(self, index: int) -> CombatRoomData:
        base_difficulty_level = index + 1
        # Select a difficulty level within range of 1 of the current room index
        selected_room_difficulty_level_min = max(base_difficulty_level - 1, 1)  # Never select a room with difficulty 0 in this phase
        selected_room_difficulty_level_max = min(base_difficulty_level + 1, len(self.game_data.available_room_difficulties) - 1)
        selected_room_difficulty_level = random.randint(selected_room_difficulty_level_min, selected_room_difficulty_level_max)
        return random.choice(self.game_data.available_room_difficulties[selected_room_difficulty_level])

    @staticmethod
    def spawn_enemies_from_room_data(screen_width, screen_height,
                                     room_data: CombatRoomData, enemy_character_factory: EnemyCharacterFactory, current_alive_enemy_characters: List[EnemyCharacter]):
        padding = 0
        enemy_width = 256
        enemy_count = len(room_data.room_enemies)

        available_width = enemy_count * enemy_width + (enemy_count - 1) * padding

        start_x = (screen_width - available_width) / 2
        positions = []
        for i in range(enemy_count):
            # Calculate the x position_or_rect biased to the center of the screen
            x = start_x + (enemy_width + padding) * i + (enemy_width / 2)
            y = screen_height / 2 - screen_height * 0.1
            positions.append((x, y))
        for i, (x, y) in enumerate(positions):
            i: int
            enemy_character_factory.set_target_spawn_data(room_data.room_enemies[i])
            enemy_reference = enemy_character_factory.instantiate((x, y))
            current_alive_enemy_characters.append(enemy_reference)

    def initialize_player_turn(self):
        self.current_player_mana = max(0, self.current_game_save.player_base_mana + self.player_base_mana_limit_addition_this_combat + self.mana_addition_next_turn)
        self.mana_addition_next_turn = 0
        self.current_player_block = 0
        self.is_players_turn = True

    def add_discard_to_draw_pile(self):
        for card in self.current_discard_pile:
            self.current_draw_pile.append(card)
        self.current_discard_pile.clear()
        audio.play_one_shot(constants.shuffle_sound)

    def change_mana_limit_this_combat(self, amount):
        self.player_base_mana_limit_addition_this_combat += amount

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
        for old_card in self.current_hand:
            old_card.on_played()
            self.current_discard_pile.append(old_card.card_data)
        self.current_hand.clear()
        card_count = self.current_draw_limit + self.draw_limit_addition_next_turn
        if card_count > 8:
            card_count = 8
        if card_count < 1:
            card_count = 1
        self.draw_limit_addition_next_turn = 0
        self.create_new_hand_cards(card_count)

    def create_new_hand_cards(self, card_count: int):
        # Check if the draw pile has enough cards
        if len(self.current_draw_pile) < card_count:
            self.add_discard_to_draw_pile()

        # If there are still not enough cards, then limit the card count
        if len(self.current_draw_pile) < card_count:
            card_count = len(self.current_draw_pile)

        # Select x random cards from player's draw pile
        random.shuffle(self.current_draw_pile)
        selections = self.current_draw_pile[:card_count]
        new_hand_cards = []
        delay = 0
        for selection in selections:
            new_hand_cards.append(self.instantiate_new_hand_card(selection))
            audio.play_one_shot_delayed(random.choice(constants.deal_one_soundbank), delay)
            delay += 0.15
        for index, card in enumerate(self.current_hand):
            if card in new_hand_cards:
                card.play_draw_animation(self.get_position_of_hand_card_at_index(index))

    def instantiate_new_hand_card(self, card_data: CardData) -> GameCard:
        self.game_card_factory.set_target_card_data(card_data)
        card = self.game_card_factory.instantiate(self.draw_pile_position)
        self.current_hand.append(card)
        self.current_draw_pile.remove(card_data)
        return card

    def draw_hand_cards(self, count: int):
        log_info(f"Drawing {count} cards")
        old_hand_cards = self.current_hand.copy()
        self.create_new_hand_cards(count)
        self.reposition_cards(old_hand_cards)

    def reposition_cards(self, cards):
        for index, card in enumerate(cards):
            self.reposition_card(card, index)

    def reposition_card(self, card, card_index: int):
        x, y = self.get_position_of_hand_card_at_index(card_index)
        # log_info(f"Repositioning card {card.card_data.card_info_name} to position {(x, y)}")
        card.play_reposition_animation((x, y))

    def get_position_of_hand_card_at_index(self, index: int) -> tuple[float, float]:
        width_total = pygame.display.get_surface().get_width()
        y = pygame.display.get_surface().get_height() - 0.08 * pygame.display.get_surface().get_height()
        hand_cards_count = len(self.current_hand)
        if hand_cards_count < 2:
            return width_total / 2, y
        if hand_cards_count == 2:
            start = width_total / 2 - 200
            spacing = 400
            x = start + (index * spacing)
            return x, y
        cards_available_width = width_total / 1.8
        start = (width_total - cards_available_width) / 2
        spacing = cards_available_width / (max(1, hand_cards_count - 1))
        x = start + (index * spacing)
        return x, y

    def generate_reward_cards(self, card_count: int = 3):
        self.current_reward_game_cards.clear()
        selections = []
        for i in range(card_count):
            # Select a pool of cards based on rarity using CardData.rarity_weights
            selected_rarity = random.choices(list(CardData.rarity_weights.keys()), list(CardData.rarity_weights.values()))[0]
            available_cards_with_rarity = []
            for card in self.game_data.available_cards:
                if selected_rarity == card.card_rarity:
                    available_cards_with_rarity.append(card)
            if available_cards_with_rarity:
                infinite_loop_breaker = 0
                while True:
                    infinite_loop_breaker += 1
                    if infinite_loop_breaker > 1000:
                        raise Exception("Infinite loop detected while selecting reward cards.")
                    selected_card = random.choice(available_cards_with_rarity)
                    if selected_card not in selections:
                        selections.append(selected_card)
                        break
            else:
                log_warning(f"Could not find any cards with rarity {selected_rarity}. Selecting a random card.")
                selections.append(random.choice(self.game_data.available_cards))

        for index, selection in enumerate(selections):
            # Evenly distribute the cards at the center of the screen
            width_total = pygame.display.get_surface().get_width()
            card_visuals_width = width_total / 1.8
            start = (width_total - card_visuals_width) / 2
            y = pygame.display.get_surface().get_height() / 2
            if len(selections) < 2:
                x = width_total / 2
            elif len(selections) == 2:
                start = width_total / 2 - 200
                spacing = 400
                x = start + (index * spacing)
            else:
                spacing = card_visuals_width / (card_count - 1)
                x = start + (index * spacing)
            self.game_card_factory.set_target_card_data(selection)
            card_reference = self.game_card_factory.instantiate((x, y))
            self.current_reward_game_cards.append(card_reference)

    def generate_removal_cards(self):
        self.card_grid_layout.clear()
        self.current_removal_game_cards.clear()
        # Instantiate all cards in the player's deck as GameCards
        for index, card in enumerate(self.current_draw_pile + self.current_discard_pile + self.current_exhaust_pile):
            self.game_card_factory.set_target_card_data(card)
            card_reference: GameCard = self.game_card_factory.instantiate((0, 0))
            self.card_grid_layout.add_item(card_reference, (card_reference.set_position, card_reference.get_position))
            self.current_removal_game_cards.append(card_reference)

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
        # Enemies
        # self.available_enemy_spawn_data = EnemySpawnData.load_available_enemies()
        # self.available_boss_spawn_data = EnemySpawnData.load_available_bosses()
        # log_info(f"Successfully loaded {len(self.available_enemy_spawn_data)} enemies and {len(self.available_boss_spawn_data)} bosses.")

        # Cards
        self.available_cards: List[CardData] = CardData.load_available_cards()
        log_info(f"Successfully loaded {len(self.available_cards)} cards.")

        # Rooms
        self.available_room_difficulties: List[List[CombatRoomData]] = CombatRoomData.load_available_combat_rooms()
        room_count_in_total = sum([len(rooms_for_difficulty) for rooms_for_difficulty in self.available_room_difficulties])
        count_of_possible_runs = room_count_in_total ** 3
        log_info(f"Successfully loaded {len(self.available_room_difficulties)} room difficulties. {count_of_possible_runs} distinct room configurations available.")
        self.available_special_rooms: List[SpecialRoomData] = SpecialRoomData.load_available_special_rooms()
        log_info(f"Successfully loaded {len(self.available_special_rooms)} special rooms.")
        self.available_boss_rooms: List[CombatRoomData] = CombatRoomData.load_available_boss_rooms()
        log_info(f"Successfully loaded {len(self.available_boss_rooms)} boss rooms.")

        self.boss_room_index: int = len(self.available_room_difficulties)

        # Images
        self.image_library = ImageLibrary()
