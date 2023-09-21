import random
from typing import List

import pygame

import Cards
import Effects
import Enemies
import Saving
import Utils


class GameState:
    def __init__(self):
        self.game_data = GameData()
        self.current_game_save: Saving.GameSave = None
        self.current_round_index: int = 0
        self.current_player_mana: int = 0
        self.current_player_block: int = 0
        self.current_targeted_enemy: Enemies.EnemyCharacter = None
        self.current_hand: List[Cards.GameCard] = []
        self.current_draw_pile: List[Cards.CardData] = []
        self.current_discard_pile: List[Cards.CardData] = []
        self.current_reward_cards: List[Cards.GameCard] = []
        self.current_alive_enemies: List[Enemies.EnemyCharacter] = []
        self.active_visual_effects: List[Effects.VisualEffect] = []
        self.is_player_choosing_rewards: bool = False
        self.is_battle_in_progress: bool = False
        self.is_players_turn: bool = False

    def display_blocking_save_selection_screen(self):
        """
        Displays a screen where the player can choose to load an existing save or create a new one.
        Warning: This function is blocking and will not return until the player has chosen a save.
        """
        pygame.display.set_caption("Slay the Python - Initializing...")
        available_save_games = Saving.list_available_save_games()
        self.current_game_save = Saving.load_save_game(Utils.get_save_game_name(pygame.display.get_surface(), available_save_games))
        self.is_players_turn = True
        self.current_hand.clear()
        self.current_draw_pile.clear()
        self.current_discard_pile.clear()
        self.current_alive_enemies.clear()
        # Move cards from save to draw pile
        for card in self.current_game_save.player_cards:
            self.current_draw_pile.append(card)
        self.initialize_new_room(self.current_game_save.dungeon_room_index)
        Saving.save_game(self.current_game_save)

    def save(self):
        self.update_save_cards()
        Saving.save_game(self.current_game_save)

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
        Saving.delete_save_game(self.current_game_save.save_game_name)

    def load_next_room(self):
        # Player wins, let the player choose cards and increment the room index
        self.current_game_save.dungeon_room_index += 1
        self.initialize_new_room(self.current_game_save.dungeon_room_index)

    def initialize_new_room(self, room_index: int):
        # Move the discard pile to draw pile
        self.prepare_draw_pile()

        self.randomize_reward_cards()
        self.initialize_player_turn()

        # If the room is the boss room, spawn the boss
        if room_index == self.game_data.BOSS_ROOM_INDEX:
            boss = random.choice(self.game_data.available_bosses)
            x = pygame.display.get_surface().get_width() / 2
            y = pygame.display.get_surface().get_height() / 2 - pygame.display.get_surface().get_height() * 0.1
            self.current_alive_enemies.append(Enemies.EnemyCharacter(boss, x, y))
        else:  # Otherwise spawn normal enemies
            enemy_count = room_index + 1
            padding = 0
            enemy_width = 256

            screen_width = pygame.display.get_surface().get_width()
            screen_height = pygame.display.get_surface().get_height()

            # Calculate the total width of the images and padding
            total_width = enemy_count * enemy_width + (enemy_count - 1) * padding

            # Calculate the starting position from the center of the screen
            start_position = (screen_width - total_width) / 2

            positions = []

            for i in range(enemy_count):
                # Calculate the x position biased to the center of the screen
                x = start_position + (enemy_width + padding) * i + (enemy_width / 2)

                y = screen_height / 2 - screen_height * 0.1

                positions.append((x, y))

            for i, (x, y) in enumerate(positions):
                self.current_alive_enemies.append(Enemies.EnemyCharacter(random.choice(self.game_data.available_enemies), x, y))
        if len(self.current_alive_enemies) > 0:
            self.current_targeted_enemy = self.current_alive_enemies[0]

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
        self.current_hand.clear()
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
            self.current_hand.append(Cards.GameCard(selection, x, y))
            self.current_draw_pile.remove(selection)
            self.current_discard_pile.append(selection)

    def randomize_reward_cards(self):
        self.current_reward_cards.clear()
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
            self.current_reward_cards.append(Cards.GameCard(selection, x, y))

    def damage_player(self, amount):
        # Reduce current block by the damage amount
        remaining_damage = amount - self.current_player_block
        self.remove_block(amount)

        # Reduce current health by the damage amount
        if remaining_damage > 0:
            self.current_game_save.player_health = max(self.current_game_save.player_health - remaining_damage, 0)
            effect_pos = (pygame.display.get_surface().get_width() // 2, pygame.display.get_surface().get_height() // 2)
            new_effect = Effects.VisualEffect(self.game_data.effect_damaged_self, effect_pos, 1000)
            self.active_visual_effects.append(new_effect)

    def remove_block(self, amount):
        self.current_player_block = max(self.current_player_block - amount, 0)

    def get_fight_state(self) -> str:
        if len(self.current_alive_enemies) == 0:
            return "PLAYER_WIN"
        if self.current_game_save.player_health <= 0:
            return "PLAYER_LOSE"
        return "IN_PROGRESS"


class GameData:
    def __init__(self):
        # Consts
        self.BOSS_ROOM_INDEX: int = 4

        # Enemies
        self.available_enemies: List[Enemies.EnemySpawnData] = []
        self.available_bosses: List[Enemies.EnemySpawnData] = []

        # Cards
        self.available_cards: List[Cards.CardData] = []

        # UI
        self.icon_target: pygame.Surface = None
        self.icon_mana: pygame.Surface = None
        self.icon_block: pygame.Surface = None
        self.icon_health: pygame.Surface = None
        self.icon_attack: pygame.Surface = None
        # Intention icons
        self.icon_intention_block: pygame.Surface = None
        self.icon_intention_buff: pygame.Surface = None
        self.icon_intention_unknown: pygame.Surface = None
        self.icon_intention_damage_low: pygame.Surface = None
        self.icon_intention_damage_medium: pygame.Surface = None
        self.icon_intention_damage_high: pygame.Surface = None
        self.icon_intention_damage_veryhigh: pygame.Surface = None

        # Effects
        self.effect_damaged_self: pygame.Surface = None
        self.slash_effects_list: List[pygame.Surface] = []

        # Initializing
        self.load_enemies()
        self.load_cards()
        self.load_icons()
        self.load_effects()

    def load_enemies(self):
        self.available_enemies = Enemies.load_available_enemies()
        self.available_bosses = Enemies.load_available_bosses()

    def load_cards(self):
        self.available_cards = Cards.load_available_cards()

    def load_icons(self):
        try:
            icon_raw = pygame.image.load("Data/Sprites/UI/icon_mana.png")
            self.icon_mana = pygame.transform.scale(icon_raw, (icon_raw.get_width() * 1, icon_raw.get_height() * 1))

            icon_raw = pygame.image.load("Data/Sprites/UI/icon_block.png")
            self.icon_block = pygame.transform.scale(icon_raw, (icon_raw.get_width() * 0.8, icon_raw.get_height() * 0.8))

            icon_raw = pygame.image.load("Data/Sprites/UI/icon_health.png")
            self.icon_health = pygame.transform.scale(icon_raw, (icon_raw.get_width() * 0.8, icon_raw.get_height() * 0.8))

            icon_raw = pygame.image.load("Data/Sprites/UI/icon_attack.png")
            self.icon_attack = pygame.transform.scale(icon_raw, (icon_raw.get_width() * 0.8, icon_raw.get_height() * 0.8))

            self.icon_target = pygame.image.load("Data/Sprites/UI/icon_target.png")
            self.icon_intention_block = pygame.image.load("Data/Sprites/UI/icon_intention_block.png")
            self.icon_intention_buff = pygame.image.load("Data/Sprites/UI/icon_intention_buff.png")
            self.icon_intention_unknown = pygame.image.load("Data/Sprites/UI/icon_intention_unknown.png")
            self.icon_intention_damage_low = pygame.image.load("Data/Sprites/UI/icon_intention_damage_low.png")
            self.icon_intention_damage_medium = pygame.image.load("Data/Sprites/UI/icon_intention_damage_medium.png")
            self.icon_intention_damage_high = pygame.image.load("Data/Sprites/UI/icon_intention_damage_high.png")
            self.icon_intention_damage_veryhigh = pygame.image.load("Data/Sprites/UI/icon_intention_damage_veryhigh.png")
        except pygame.error as e:
            print("Error loading icons:", str(e))

    def load_effects(self):
        try:
            self.effect_damaged_self = pygame.image.load("Data/Sprites/Effects/effect_damaged_self.png")
            self.slash_effects_list.append(pygame.image.load("Data/Sprites/Effects/effect_slash_1.png"))
            self.slash_effects_list.append(pygame.image.load("Data/Sprites/Effects/effect_slash_2.png"))
            self.slash_effects_list.append(pygame.image.load("Data/Sprites/Effects/effect_slash_3.png"))
            self.slash_effects_list.append(pygame.image.load("Data/Sprites/Effects/effect_slash_4.png"))
        except pygame.error as e:
            print("Error loading effects:", str(e))

    def get_damage_icon_from_damage_amount(self, damage: int) -> pygame.Surface:
        if damage <= 5:
            return self.icon_intention_damage_low
        elif damage <= 10:
            return self.icon_intention_damage_medium
        elif damage <= 20:
            return self.icon_intention_damage_high
        else:
            return self.icon_intention_damage_veryhigh
