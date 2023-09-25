import random
from typing import Optional, List

import pygame
import drawing
import utils


class GameState:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock):
        self.frame_buffer = drawing.FrameBuffer(screen)
        self.game_data = GameData()
        self.screen = screen
        self.clock: pygame.time.Clock = clock
        self.delta_time = 1 / 60
        self.current_game_save: Optional[utils.GameSave] = None
        self.current_round_index: int = 0
        self.current_player_mana: int = 0
        self.current_player_block: int = 0
        self.current_targeted_enemy_character = None
        self.current_hand_game_cards = []
        self.current_draw_pile: List[utils.CardData] = []
        self.current_discard_pile = []
        self.current_reward_game_cards = []
        self.current_alive_enemy_characters = []
        self.game_objects = []
        self.is_player_choosing_rewards: bool = False
        self.is_battle_in_progress: bool = False
        self.is_players_turn: bool = False

    def display_blocking_save_selection_screen(self):
        """
        Displays a screen where the player can choose to load an existing save or create a new one.
        Warning: This function is blocking and will not return until the player has chosen a save.
        """
        pygame.display.set_caption("Slay the Python - Initializing...")
        available_save_games = utils.list_available_save_games()
        self.current_game_save = utils.load_save_game(utils.get_save_game_name(pygame.display.get_surface(), available_save_games))
        self.is_players_turn = True
        self.current_hand_game_cards.clear()
        self.current_draw_pile.clear()
        self.current_discard_pile.clear()
        self.current_alive_enemy_characters.clear()
        # Move cards from save to draw pile
        for card in self.current_game_save.player_cards:
            self.current_draw_pile.append(card)
        self.initialize_new_room(self.current_game_save.dungeon_room_index)
        utils.save_game(self.current_game_save)

    def save(self):
        self.update_save_cards()
        utils.save_game(self.current_game_save)

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
        utils.delete_save_game(self.current_game_save.save_game_name)

    def load_next_room(self):
        # Player wins, let the player choose cards and increment the room index
        self.current_game_save.dungeon_room_index += 1
        self.initialize_new_room(self.current_game_save.dungeon_room_index)

    def initialize_new_room(self, room_index: int):
        # Move the discard pile to draw pile
        self.prepare_draw_pile()

        self.initialize_player_turn()

        # If the room is the boss room, spawn the boss
        if room_index == self.game_data.BOSS_ROOM_INDEX:
            boss = random.choice(self.game_data.available_boss_spawn_data)
            x = pygame.display.get_surface().get_width() / 2
            y = pygame.display.get_surface().get_height() / 2 - pygame.display.get_surface().get_height() * 0.1
            self.current_alive_enemy_characters.append(utils.EnemyCharacter(self, boss, (x, y)))
        else:  # Otherwise spawn normal enemies
            enemy_count = room_index + 1
            padding = 0
            enemy_width = 256

            screen_width = self.screen.get_width()
            screen_height = self.screen.get_height()

            # Calculate the total width of the images and padding
            total_width = enemy_count * enemy_width + (enemy_count - 1) * padding

            # Calculate the starting position_or_rect from the center of the screen
            start_position = (screen_width - total_width) / 2

            positions = []

            for i in range(enemy_count):
                # Calculate the x position_or_rect biased to the center of the screen
                x = start_position + (enemy_width + padding) * i + (enemy_width / 2)

                y = screen_height / 2 - screen_height * 0.1

                positions.append((x, y))

            for i, (x, y) in enumerate(positions):
                self.current_alive_enemy_characters.append(utils.EnemyCharacter(self, random.choice(self.game_data.available_enemy_spawn_data), (x, y)))
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
            # Evenly distribute the cards at the bottom of the screen
            width_total = pygame.display.get_surface().get_width()
            card_visuals_width = width_total / 1.8
            start = (width_total - card_visuals_width) / 2
            spacing = card_visuals_width / (card_count - 1)
            x = start + (index * spacing)
            y = pygame.display.get_surface().get_height() - 0.08 * pygame.display.get_surface().get_height()
            self.current_hand_game_cards.append(utils.GameCard(self, selection, (x, y)))
            self.current_draw_pile.remove(selection)
            self.current_discard_pile.append(selection)

    def generate_reward_cards(self):
        self.current_reward_game_cards.clear()
        card_count = 3
        # Select X random cards from all available cards
        selections = random.choices(self.game_data.available_cards, k=card_count)
        for index, selection in enumerate(selections):
            # Evenly distribute the cards at the center of the screen
            width_total = pygame.display.get_surface().get_width()
            card_visuals_width = width_total / 1.8
            start = (width_total - card_visuals_width) / 2
            spacing = card_visuals_width / (card_count - 1)
            x = start + (index * spacing)
            y = pygame.display.get_surface().get_height() / 2
            self.current_reward_game_cards.append(utils.GameCard(self, selection, (x, y)))

    def remove_block(self, amount):
        self.current_player_block = max(self.current_player_block - amount, 0)

    def get_fight_state(self) -> str:
        if len(self.current_alive_enemy_characters) == 0:
            return "PLAYER_WIN"
        if self.current_game_save.player_health <= 0:
            return "PLAYER_LOSE"
        return "IN_PROGRESS"

    def update_game_objects(self):
        for game_object in self.game_objects:
            if game_object.is_active:
                game_object.update()
                self.frame_buffer.add_drawable(game_object)
            if game_object.is_awaiting_destruction:
                self.game_objects.remove(game_object)


class GameData:
    def __init__(self):
        # Consts
        self.BOSS_ROOM_INDEX: int = 4

        # Enemies
        self.available_enemy_spawn_data = utils.load_available_enemies()
        self.available_boss_spawn_data = utils.load_available_bosses()

        # Cards
        self.available_cards: List[utils.CardData] = utils.load_available_cards()

        # UI
        self.icon_target: pygame.Surface = utils.load_image("Data/Sprites/UI/icon_target.png")
        self.icon_mana: pygame.Surface = utils.load_image("Data/Sprites/UI/icon_mana.png")
        icon_raw: pygame.Surface = utils.load_image("Data/Sprites/UI/icon_block.png")
        self.icon_block: pygame.Surface = pygame.transform.scale(icon_raw, (icon_raw.get_width() * 0.8, icon_raw.get_height() * 0.8))   # TODO: Remove scaling
        icon_raw: pygame.Surface = utils.load_image("Data/Sprites/UI/icon_health.png")
        self.icon_health: pygame.Surface = pygame.transform.scale(icon_raw, (icon_raw.get_width() * 0.8, icon_raw.get_height() * 0.8))
        icon_raw: pygame.Surface = utils.load_image("Data/Sprites/UI/icon_attack.png")
        self.icon_attack: pygame.Surface = pygame.transform.scale(icon_raw, (icon_raw.get_width() * 0.8, icon_raw.get_height() * 0.8))
        # Intention icons
        self.icon_intention_block: pygame.Surface = utils.load_image("Data/Sprites/UI/icon_intention_block.png")
        self.icon_intention_buff: pygame.Surface = utils.load_image("Data/Sprites/UI/icon_intention_buff.png")
        self.icon_intention_unknown: pygame.Surface = utils.load_image("Data/Sprites/UI/icon_intention_unknown.png")
        self.icon_intention_damage_low: pygame.Surface = utils.load_image("Data/Sprites/UI/icon_intention_damage_low.png")
        self.icon_intention_damage_medium: pygame.Surface = utils.load_image("Data/Sprites/UI/icon_intention_damage_medium.png")
        self.icon_intention_damage_high: pygame.Surface = utils.load_image("Data/Sprites/UI/icon_intention_damage_high.png")
        self.icon_intention_damage_veryhigh: pygame.Surface = utils.load_image("Data/Sprites/UI/icon_intention_damage_veryhigh.png")

        # Effects
        self.effect_damaged_self: pygame.Surface = utils.load_image("Data/Sprites/Effects/effect_damaged_self.png")
        self.slash_effects_list: List[pygame.Surface] = [
            utils.load_image("Data/Sprites/Effects/effect_slash_1.png"),
            utils.load_image("Data/Sprites/Effects/effect_slash_2.png"),
            utils.load_image("Data/Sprites/Effects/effect_slash_3.png"),
            utils.load_image("Data/Sprites/Effects/effect_slash_4.png")
        ]

    def get_damage_icon_from_damage_amount(self, damage: int) -> pygame.Surface:
        if damage <= 5:
            return self.icon_intention_damage_low
        elif damage <= 10:
            return self.icon_intention_damage_medium
        elif damage <= 20:
            return self.icon_intention_damage_high
        else:
            return self.icon_intention_damage_veryhigh