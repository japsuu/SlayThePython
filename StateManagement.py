import random
from typing import List

import pygame

from Cards import CardData, GameCard, load_available_cards
from Effects import VisualEffect
from Enemies import EnemySpawnData, EnemyCharacter, load_available_enemies, load_available_bosses
from Saving import GameSave, list_available_save_games, load_save_game, delete_save_game, save_game
from Utils import get_save_game_name


class GameState:
    def __init__(self):
        self.game_data = GameData()
        self.current_game_save: GameSave = None
        self.current_round_index: int = 0
        self.current_player_mana: int = 0
        self.current_player_block: int = 0
        self.current_targeted_enemy: EnemyCharacter = None
        self.current_draw_pile: List[CardData] = []
        self.current_hand_cards: List[GameCard] = []
        self.current_discard_pile: List[CardData] = []
        self.current_reward_cards: List[GameCard] = []
        self.current_alive_enemies: List[EnemyCharacter] = []
        self.active_visual_effects: List[VisualEffect] = []
        self.is_player_choosing_rewards: bool = False
        self.is_battle_in_progress: bool = False
        self.is_players_turn: bool = False

    def display_blocking_save_selection_screen(self):
        """
        Displays a screen where the player can choose to load an existing save or create a new one.
        Warning: This function is blocking and will not return until the player has chosen a save.
        """
        pygame.display.set_caption("Slay the Python - Initializing...")
        available_save_games = list_available_save_games()
        self.current_game_save = load_save_game(get_save_game_name(pygame.display.get_surface(), available_save_games))
        self.is_players_turn = True
        self.current_hand_cards.clear()
        self.current_alive_enemies.clear()
        self.randomize_reward_cards()
        self.initialize_new_room(self.current_game_save.dungeon_room_index)
        save_game(self.current_game_save)

    def save(self):
        save_game(self.current_game_save)

    def save_and_exit_current_save(self):
        self.save()
        self.current_game_save = None

    def delete_current_save(self):
        delete_save_game(self.current_game_save.save_game_name)

    def load_next_room(self):
        # Player wins, let the player choose cards and increment the room index
        self.current_game_save.dungeon_room_index += 1
        self.randomize_reward_cards()
        self.initialize_new_room(self.current_game_save.dungeon_room_index)

    def initialize_new_room(self, room_index: int):
        self.initialize_player_turn()

        # If the room is the boss room, spawn the boss
        if room_index == self.game_data.BOSS_ROOM_INDEX:
            boss = random.choice(self.game_data.available_bosses)
            x = pygame.display.get_surface().get_width() / 2
            y = pygame.display.get_surface().get_height() / 2 - pygame.display.get_surface().get_height() * 0.1
            self.current_alive_enemies.append(EnemyCharacter(boss, x, y))
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
                self.current_alive_enemies.append(EnemyCharacter(random.choice(self.game_data.available_enemies), x, y))
        if len(self.current_alive_enemies) > 0:
            self.current_targeted_enemy = self.current_alive_enemies[0]

    def initialize_player_turn(self):
        self.current_player_mana = 3
        self.current_player_block = 0
        self.is_players_turn = True
        self.player_draw_cards()

    def player_draw_cards(self):
        self.current_hand_cards.clear()
        card_count = 5
        # Select x random cards from player's deck
        selections = random.choices(self.current_game_save.player_cards, k=card_count)
        for index, selection in enumerate(selections):
            # Evenly distribute the cards at the bottom of the screen
            width_total = pygame.display.get_surface().get_width()
            card_visuals_width = width_total / 1.8
            start = (width_total - card_visuals_width) / 2
            spacing = card_visuals_width / (card_count - 1)
            x = start + (index * spacing)
            y = pygame.display.get_surface().get_height() - 0.08 * pygame.display.get_surface().get_height()
            self.current_hand_cards.append(GameCard(selection, x, y))

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
            self.current_reward_cards.append(GameCard(selection, x, y))

    def damage_player(self, amount):
        # Reduce current block by the damage amount
        remaining_damage = amount - self.current_player_block
        self.remove_block(amount)

        # Reduce current health by the damage amount
        if remaining_damage > 0:
            self.current_game_save.player_health = max(self.current_game_save.player_health - remaining_damage, 0)

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
        self.available_enemies: List[EnemySpawnData] = []
        self.available_bosses: List[EnemySpawnData] = []

        # Cards
        self.available_cards: List[CardData] = []

        # UI
        self.icon_in_combat: pygame.Surface = None
        self.icon_mana: pygame.Surface = None
        self.icon_block: pygame.Surface = None
        self.icon_block_small: pygame.Surface = None
        self.icon_health: pygame.Surface = None
        self.icon_health_small: pygame.Surface = None
        self.icon_attack: pygame.Surface = None
        self.icon_attack_small: pygame.Surface = None
        self.icon_unknown: pygame.Surface = None

        # Effects
        self.effect_damaged: pygame.Surface = None
        self.slash_effects_list: List[pygame.Surface] = []

        # Initializing
        self.load_enemies()
        self.load_cards()
        self.load_icons()
        self.load_effects()

    def load_enemies(self):
        self.available_enemies = load_available_enemies()
        self.available_bosses = load_available_bosses()

    def load_cards(self):
        self.available_cards = load_available_cards()

    def load_icons(self):
        try:
            in_combat_icon = pygame.image.load("Data/Sprites/UI/icon_incombat.png")
            in_combat_icon = pygame.transform.scale(in_combat_icon, (in_combat_icon.get_width() * 0.1, in_combat_icon.get_height() * 0.1))
            self.icon_in_combat = in_combat_icon

            mana_icon = pygame.image.load("Data/Sprites/UI/icon_mana.png")
            mana_icon = pygame.transform.scale(mana_icon, (mana_icon.get_width() * 1, mana_icon.get_height() * 1))
            self.icon_mana = mana_icon

            block_icon = pygame.image.load("Data/Sprites/UI/icon_block.png")
            block_icon = pygame.transform.scale(block_icon, (block_icon.get_width() * 0.8, block_icon.get_height() * 0.8))
            self.icon_block = block_icon

            block_icon_small = pygame.transform.scale(block_icon, (block_icon.get_width() * 0.3, block_icon.get_height() * 0.3))
            self.icon_block_small = block_icon_small

            health_icon = pygame.image.load("Data/Sprites/UI/icon_health.png")
            health_icon = pygame.transform.scale(health_icon, (health_icon.get_width() * 0.8, health_icon.get_height() * 0.8))
            self.icon_health = health_icon

            health_icon_small = pygame.transform.scale(health_icon, (health_icon.get_width() * 0.3, health_icon.get_height() * 0.3))
            self.icon_health_small = health_icon_small

            attack_icon = pygame.image.load("Data/Sprites/UI/icon_attack.png")
            attack_icon = pygame.transform.scale(attack_icon, (attack_icon.get_width() * 0.8, attack_icon.get_height() * 0.8))
            self.icon_attack = attack_icon

            attack_icon_small = pygame.transform.scale(attack_icon, (attack_icon.get_width() * 0.3, attack_icon.get_height() * 0.3))
            self.icon_attack_small = attack_icon_small

            unknown_icon = pygame.image.load("Data/Sprites/UI/icon_unknown.png")
            unknown_icon = pygame.transform.scale(unknown_icon, (unknown_icon.get_width() * 0.8, unknown_icon.get_height() * 0.8))
            self.icon_unknown = unknown_icon
        except pygame.error as e:
            print("Error loading icons:", str(e))

    def load_effects(self):
        try:
            self.effect_damaged = pygame.image.load("Data/Sprites/Effects/effect_damaged.png")
            self.slash_effects_list.append(pygame.image.load("Data/Sprites/Effects/effect_slash_1.png"))
            self.slash_effects_list.append(pygame.image.load("Data/Sprites/Effects/effect_slash_2.png"))
            self.slash_effects_list.append(pygame.image.load("Data/Sprites/Effects/effect_slash_3.png"))
            self.slash_effects_list.append(pygame.image.load("Data/Sprites/Effects/effect_slash_4.png"))
        except pygame.error as e:
            print("Error loading effects:", str(e))
