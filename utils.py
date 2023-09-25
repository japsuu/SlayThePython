import hashlib
import json
import os
import random
from typing import List

import pygame
from pygame.math import lerp

import constants
from drawing import Drawable

SAVE_FOLDER = "save-game-folder"


# def lerp(a: float, b: float, t: float) -> float:
#     """Linear interpolate on the scale given by a to b, using t as the point on that scale.
#     Examples
#     --------
#         50 == lerp(0, 100, 0.5)
#         4.2 == lerp(1, 5, 0.8)
#     """
#     return (1 - t) * a + t * b


class Tween:
    def __init__(self, start_value, end_value, duration: float, value_updated_callback=None, finished_callback=None):
        self.is_finished = False
        self.start_value = start_value
        self.current_value = start_value
        self.end_value = end_value
        self.duration: float = duration
        self.elapsed_time: float = 0
        self.on_value_updated_callback = value_updated_callback
        self.on_finished_callback = finished_callback

    def update(self, dt):
        self.elapsed_time += dt
        if self.elapsed_time >= self.duration:
            if not self.is_finished:
                self.is_finished = True
                if self.on_finished_callback:
                    self.on_finished_callback()
            self.current_value = self.end_value
            if self.on_value_updated_callback:
                self.on_value_updated_callback(self.current_value)
            return self.current_value

        progress = self.elapsed_time / self.duration
        self.current_value = self._calculate_current(progress)

        if self.on_value_updated_callback:
            self.on_value_updated_callback(self.current_value)

        return self.current_value

    def _calculate_current(self, progress):
        return lerp(self.start_value, self.end_value, progress)


class DualTween(Tween):
    def __init__(self, start_pos: tuple, end_pos: tuple, duration: float, value_updated_callback=None, finished_callback=None):
        super().__init__(start_pos, end_pos, duration, value_updated_callback, finished_callback)

    def _calculate_current(self, progress):
        return pygame.math.Vector2(self.start_value).lerp(self.end_value, progress)


class Animation:    # TODO: Animation.copy method to create animation templates?
    """
    An animation that consists of multiple tweens.
    is_finished is True when all tweens are finished.
    """

    def __init__(self, tweens: list[Tween], finished_callback=None):
        self.tweens = tweens
        self.is_finished = False
        self.on_finished_callback = finished_callback

    def update(self, dt):
        for tween in self.tweens:
            tween.update(dt)

        if all(tween.is_finished for tween in self.tweens):
            if not self.is_finished:
                self.is_finished = True
                if self.on_finished_callback:
                    self.on_finished_callback()


# No idea how to make singletons in Python, so this will have to do
class Inputs:
    def __init__(self):
        self.quit = False
        self.mouse_pos = (0, 0)
        self.mouse_buttons_pressed_this_frame = set()
        self.mouse_buttons_up = set()
        self.mouse_buttons_down = set()
        self.keys_pressed_this_frame = set()
        self.keys_up = set()
        self.keys_down = set()
        self.unicode: str = ""

    @staticmethod
    def is_key_down(key):
        return key in global_inputs.keys_down

    @staticmethod
    def is_key_up(key):
        return key in global_inputs.keys_up

    @staticmethod
    def is_key_pressed(key):
        return key in global_inputs.keys_pressed_this_frame

    @staticmethod
    def is_mouse_button_down(button):
        return button in global_inputs.mouse_buttons_down

    @staticmethod
    def is_mouse_button_up(button):
        return button in global_inputs.mouse_buttons_up

    @staticmethod
    def is_mouse_button_pressed(button):
        return button in global_inputs.mouse_buttons_pressed_this_frame

    @staticmethod
    def get_mouse_position():
        return global_inputs.mouse_pos

    @staticmethod
    def should_quit():
        return global_inputs.quit

    @staticmethod
    def get_unicode():
        return global_inputs.unicode

    @staticmethod
    def handle_input_events():
        global_inputs.keys_up.clear()
        global_inputs.mouse_buttons_up.clear()
        global_inputs.keys_pressed_this_frame.clear()
        global_inputs.mouse_buttons_pressed_this_frame.clear()
        global_inputs.unicode = ""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                global_inputs.quit = True
            elif event.type == pygame.KEYDOWN:
                global_inputs.keys_down.add(event.key)
                global_inputs.keys_pressed_this_frame.add(event.key)
                global_inputs.unicode = event.unicode
            elif event.type == pygame.KEYUP:
                global_inputs.keys_down.discard(event.key)
                global_inputs.keys_up.add(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                global_inputs.mouse_buttons_down.add(event.button)
                global_inputs.mouse_buttons_pressed_this_frame.add(event.button)
            elif event.type == pygame.MOUSEBUTTONUP:
                global_inputs.mouse_buttons_down.discard(event.button)
                global_inputs.mouse_buttons_up.add(event.button)
            elif event.type == pygame.MOUSEMOTION:
                global_inputs.mouse_pos = event.pos


global_inputs = Inputs()


def get_random_inside_rect(rect_size) -> tuple[float, float]:
    """Returns a random point inside a unit rectangle.
    The unit rect is a square with both sides' width as 1, centered at (0, 0).
    """
    # Get a random point inside a unit square
    x = (random.random() * 2 - 1) * rect_size
    y = (random.random() * 2 - 1) * rect_size
    return x, y


def load_image(path):
    try:
        return pygame.image.load(path)
    except pygame.error as e:
        print(f"Error loading image @ {path}: {str(e)}")


def get_save_game_name(screen, available_save_games):
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
            save = load_save_game(existing_game_save)

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


def load_available_cards():
    card_data_list = []
    file_path = "Data/cards.json"
    try:
        with open(file_path, "r") as file:
            data = json.load(file)

            for enemy_data in data:
                card_data = CardData.from_dict(enemy_data)
                card_data_list.append(card_data)

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON file: {file_path}")

    return card_data_list


def load_available_enemies():
    enemy_spawn_data_list = []
    file_path = "Data/enemies.json"
    try:
        with open(file_path, "r") as file:
            data = json.load(file)

            for enemy_data in data:
                enemy_spawn_data = EnemySpawnData.from_dict(enemy_data)
                enemy_spawn_data_list.append(enemy_spawn_data)

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON file: {file_path}")

    return enemy_spawn_data_list


def load_available_bosses():
    boss_spawn_data_list = []
    file_path = "Data/bosses.json"
    try:
        with open(file_path, "r") as file:
            data = json.load(file)

            for enemy_data in data:
                enemy_spawn_data = EnemySpawnData.from_dict(enemy_data)
                boss_spawn_data_list.append(enemy_spawn_data)

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON file: {file_path}")

    return boss_spawn_data_list


class EnemyIntentionData:
    def __init__(self, gain_health_amount, gain_block_amount, deal_damage_amount, turn_sprite_path):
        self.gain_health_amount = gain_health_amount
        self.gain_block_amount = gain_block_amount
        self.deal_damage_amount = deal_damage_amount
        self.turn_sprite_path = turn_sprite_path

    def to_dict(self):
        return {
            "gain_health_amount": self.gain_health_amount,
            "gain_block_amount": self.gain_block_amount,
            "deal_damage_amount": self.deal_damage_amount,
            "turn_sprite_path": self.turn_sprite_path
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["gain_health_amount"],
            data["gain_block_amount"],
            data["deal_damage_amount"],
            data["turn_sprite_path"]
        )


class EnemySpawnData:
    def __init__(self, name, max_health_min, max_health_max, sprite_path, damaged_sprite_path, intention_pattern):
        self.name = name
        self.max_health_min = max_health_min
        self.max_health_max = max_health_max
        self.sprite_path = sprite_path
        self.damaged_sprite_path = damaged_sprite_path
        self.intention_pattern: List[EnemyIntentionData] = [EnemyIntentionData.from_dict(data) for data in intention_pattern]

    def to_dict(self):
        return {
            "name": self.name,
            "max_health_min": self.max_health_min,
            "max_health_max": self.max_health_max,
            "sprite_path": self.sprite_path,
            "damaged_sprite_path": self.damaged_sprite_path,
            "intention_pattern": self.intention_pattern
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["name"],
            data["max_health_min"],
            data["max_health_max"],
            data["sprite_path"],
            data["damaged_sprite_path"],
            data["intention_pattern"]
        )


class CardData:
    def __init__(self, card_name, card_description, card_damage, card_block, card_cost, sprite_path):
        self.card_name = card_name
        self.card_description = card_description
        self.card_damage = card_damage
        self.card_block = card_block
        self.card_cost = card_cost
        self.sprite_path = sprite_path

    def to_dict(self):
        return {
            "card_name": self.card_name,
            "card_description": self.card_description,
            "card_damage": self.card_damage,
            "card_block": self.card_block,
            "card_cost": self.card_cost,
            "sprite_path": self.sprite_path
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["card_name"],
            data["card_description"],
            data["card_damage"],
            data["card_block"],
            data["card_cost"],
            data["sprite_path"]
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
        for i in range(2):
            player_cards.append(CardData("Strike", "Deal 6 damage", 6, 0, 1, "Data/Sprites/Cards/strike.png"))
            player_cards.append(CardData("Defend", "Gain 5 block", 0, 5, 1, "Data/Sprites/Cards/defend.png"))

        return GameSave(save_game_name, hash_seed(save_game_name), 0, 100, player_cards)


def delete_save_game(save_game_name):
    filename = os.path.join(SAVE_FOLDER, f"{save_game_name}.json")
    if os.path.exists(filename):
        os.remove(filename)


def hash_seed(seed):
    sha256 = hashlib.sha256(seed.encode()).hexdigest()
    seed_integer = int(sha256, 16)
    return seed_integer


class GameObject(Drawable):
    """
    A base class for all game objects. Game objects are objects that are updated and drawn every frame.
    Automatically adds itself to the game state's list of game objects.
    Automatically destroys itself when it is removed from the game state's list of game objects.
    """
    def __init__(self, game_state, drawn_surface: pygame.Surface, position, draw_order=constants.DEFAULT_DRAW_ORDER):
        super().__init__(drawn_surface, position, draw_order)
        self.game_state = game_state
        """A reference to the current GameState object. Useful for accessing game data."""
        self.rect: pygame.Rect = drawn_surface.get_rect()
        self.rect.center = position
        """The rect of the object."""
        self.draw_order: int = draw_order
        """The order in which the object will be drawn. Lower numbers are drawn first."""
        self.is_awaiting_destruction: bool = False
        """If True, the object will be destroyed either at the end of the frame, or the next frame."""
        self.is_active: bool = True
        """If False, the object will not receive updates or be drawn."""

        self.game_state.game_objects.append(self)

    def update(self):
        self.draw_position = self.rect.topleft

    def set_active(self, should_be_active):
        self.is_active = should_be_active

    def destroy(self):
        self.is_awaiting_destruction = True


class EnemyCharacter(GameObject):
    def __init__(self, game_state, enemy_spawn_data, position):
        self.enemy_spawn_data: EnemySpawnData = enemy_spawn_data
        loaded_image = pygame.image.load(self.enemy_spawn_data.sprite_path)
        self.image = pygame.transform.scale(loaded_image, (int(loaded_image.get_width() * 0.5), int(loaded_image.get_height() * 0.5)))  # TODO: remove scaling
        loaded_damaged_image = pygame.image.load(self.enemy_spawn_data.damaged_sprite_path)
        self.damaged_image = pygame.transform.scale(loaded_damaged_image, (int(loaded_damaged_image.get_width() * 0.5), int(loaded_damaged_image.get_height() * 0.5)))  # TODO: remove scaling
        self.damaged_image.set_alpha(0)
        super().__init__(game_state, self.image, position, constants.ENEMY_DRAW_ORDER)
        self.max_health = random.randint(self.enemy_spawn_data.max_health_min, self.enemy_spawn_data.max_health_max)
        self.current_health = self.max_health
        self.current_block = 0
        self.lerp_duration = 0.6
        self.lerp_start_time = None
        self.lerp_progress = 0
        self.damaged = False
        self.font = pygame.font.Font(None, 36)
        self.damage_effect_font = pygame.font.Font(None, 55)
        self.block_font = pygame.font.Font(None, 25)
        self.text_color = (255, 255, 255)
        health_bar_background_width = int(self.rect.width / 2)
        self.health_bar_background_rect = pygame.Rect(self.rect.left, self.rect.top - 10, health_bar_background_width, 5)

    def draw(self, screen):
        self.update_damage_visuals()    # TODO: Move to update
        super().draw(screen)
        # Draw the damage overlay and health bar onto the screen
        screen.blit(self.damaged_image, self.rect.topleft)
        self.draw_health_bar(screen, self.game_state)

    def draw_health_bar(self, screen, game_state):
        has_block = self.current_block > 0

        # Calculate the width of the health bar based on current health
        health_ratio = self.current_health / self.max_health
        health_bar_width = int(self.rect.width / 2 * health_ratio)

        # Define the health bar's dimensions and position_or_rect
        health_bar_rect = pygame.Rect(self.rect.left, self.rect.top - 10, health_bar_width, 5)

        # Draw the actual health next to the health bar
        health_text_surface = self.font.render(f"{self.current_health} / {self.max_health}", True, self.text_color)
        health_text_rect = health_text_surface.get_rect()
        health_text_rect.midleft = (self.health_bar_background_rect.right + 5, self.health_bar_background_rect.centery)

        # Draw the health bar with a green color if there is no shield, otherwise draw it with a blue color
        pygame.draw.rect(screen, (255, 0, 0), self.health_bar_background_rect)
        if has_block:
            pygame.draw.rect(screen, (0, 0, 255), health_bar_rect)
        else:
            pygame.draw.rect(screen, (0, 200, 0), health_bar_rect)
        # Draw the outline of the health bar
        pygame.draw.rect(screen, (255, 255, 255), health_bar_rect, 1)

        screen.blit(pygame.transform.scale(health_text_surface, (health_text_surface.get_width(), health_text_surface.get_height())), health_text_rect)

        # Draw the current block
        if has_block:
            block_icon_rect = pygame.Rect(0, 0, game_state.game_data.icon_intention_block.get_width(), game_state.game_data.icon_intention_block.get_height())
            block_icon_rect.midright = health_bar_rect.midleft
            screen.blit(game_state.game_data.icon_intention_block, block_icon_rect)

            block_text_color = (0, 0, 0)
            block_text_surface = self.block_font.render(f"{self.current_block}", True, block_text_color)
            block_text_rect = block_text_surface.get_rect()
            block_text_rect.center = block_icon_rect.center
            screen.blit(block_text_surface, block_text_rect)

    def take_damage(self, game_state, amount):
        # Reduce current block by the damage amount
        remaining_damage = amount - self.current_block
        self.remove_block(amount)
        removed_block = min(self.current_block, amount)

        # Draw a "block lost" number effect
        if removed_block > 0:
            text_color = (0, 0, 255)
            offset = get_random_inside_rect(100)
            position = (self.rect.center[0] + offset[0], (self.rect.top + self.rect.height / 4) + offset[1])
            new_effect = DamageVisualEffect(game_state, self.damage_effect_font, f"-{removed_block}", text_color, position, 3000)
            game_state.active_visual_effects.append(new_effect)

        # Reduce current health by the damage amount
        if remaining_damage > 0:
            self.current_health -= remaining_damage
            # Draw a damage number effect
            text_color = (255, 0, 0)
            offset = get_random_inside_rect(100)
            position = (self.rect.center[0] + offset[0], (self.rect.top + self.rect.height / 4) + offset[1])
            new_effect = DamageVisualEffect(game_state, self.damage_effect_font, f"-{removed_block}", text_color, position, 3000)
            game_state.active_visual_effects.append(new_effect)

        # Trigger the damaged state and start the color lerp
        self.damaged = True
        self.lerp_start_time = pygame.time.get_ticks()

        # Draw a damage effect
        random_slash_effect = random.choice(game_state.game_data.slash_effects_list)
        effect_pos = self.rect.center
        new_effect = VisualEffect(game_state, random_slash_effect, effect_pos, 1000)
        game_state.active_visual_effects.append(new_effect)

    def gain_health(self, amount):
        self.current_health = min(self.current_health + amount, self.max_health)

    def gain_block(self, amount):
        self.current_block += amount

    def remove_block(self, amount):
        self.current_block = max(self.current_block - amount, 0)

    def update_damage_visuals(self):
        # Check if the enemy is in a damaged state and lerping color
        if self.damaged:
            current_time = pygame.time.get_ticks()
            elapsed_time = (current_time - self.lerp_start_time) / 1000  # Convert to seconds

            # Calculate lerping progress (0 to 1)
            lerp_progress = elapsed_time / self.lerp_duration
            if lerp_progress >= 1:
                self.image.set_alpha(255)
                self.damaged = False
            else:
                self.image.set_alpha(255 * lerp_progress)
                self.damaged_image.set_alpha(255 * (1 - lerp_progress))

    def get_intentions(self, turn_index) -> EnemyIntentionData:
        # Get the intention for the current turn index. Use modulo to loop the pattern.
        intention = self.enemy_spawn_data.intention_pattern[turn_index % len(self.enemy_spawn_data.intention_pattern)]

        return intention

    def draw_intentions(self, screen, game_state, current_round_index):
        intentions = self.get_intentions(current_round_index)
        has_shown_intentions = False
        next_rect_pos: tuple[int, int] = self.health_bar_background_rect.topleft
        if intentions.gain_health_amount > 0:
            health_icon_rect = pygame.Rect(0, 0, game_state.game_data.icon_intention_buff.get_width(), game_state.game_data.icon_intention_buff.get_height())
            health_icon_rect.bottomleft = next_rect_pos
            next_rect_pos = health_icon_rect.bottomright
            screen.blit(game_state.game_data.icon_intention_buff, health_icon_rect)
            has_shown_intentions = True
        if intentions.gain_block_amount > 0:
            block_icon_rect = pygame.Rect(0, 0, game_state.game_data.icon_intention_block.get_width(), game_state.game_data.icon_intention_block.get_height())
            block_icon_rect.bottomleft = next_rect_pos
            next_rect_pos = block_icon_rect.bottomright
            screen.blit(game_state.game_data.icon_intention_block, block_icon_rect)
            has_shown_intentions = True
        if intentions.deal_damage_amount > 0:
            attack_icon = game_state.game_data.get_damage_icon_from_damage_amount(intentions.deal_damage_amount)
            attack_icon_rect = pygame.Rect(0, 0, attack_icon.get_width(), attack_icon.get_height())
            attack_icon_rect.bottomleft = next_rect_pos
            next_rect_pos = attack_icon_rect.bottomright
            screen.blit(attack_icon, attack_icon_rect)

            text_color = (255, 255, 255)
            text_surface = self.block_font.render(f"{intentions.deal_damage_amount}", True, text_color)
            text_rect = text_surface.get_rect()
            text_rect.center = (attack_icon_rect.left + 20, attack_icon_rect.bottom - 20)
            screen.blit(text_surface, text_rect)

            has_shown_intentions = True
        if not has_shown_intentions:  # If no intentions are shown, display the "unknown intentions" icon
            unknown_icon_rect = pygame.Rect(0, 0, game_state.game_data.icon_intention_unknown.get_width(), game_state.game_data.icon_intention_unknown.get_height())
            unknown_icon_rect.bottomleft = next_rect_pos
            screen.blit(game_state.game_data.icon_intention_unknown, unknown_icon_rect)


class GameCard(GameObject):
    def __init__(self, game_state, card_data, position):
        self.card_data: CardData = card_data
        self.current_scale_factor = 1
        self.has_been_played = False
        self.is_self_hovered = False
        self.is_other_card_hovered = False
        self.original_position = position

        self.draw_animation = Animation([
            DualTween(game_state.screen.get_rect().bottomleft, position, 3, self.__update_position),
            Tween(0, 1, 2, self.__update_scale)
        ])

        # Play a draw animation when the card is created
        self.current_animation: Animation = self.draw_animation     # TODO: Ensure that this animation is not skipped, by adding a is_overrideable flag to animations

        self.original_card_image = load_image(self.card_data.sprite_path)
        self.original_scale = (int(self.original_card_image.get_width()), int(self.original_card_image.get_height()))
        image_copy = self.original_card_image.copy()
        super().__init__(game_state, image_copy, position, draw_order=constants.PLAYER_HAND_DRAW_ORDER)

        self.card_info_font = pygame.font.Font(None, 36)
        self.card_info_mana_font = pygame.font.Font(None, 65)
        self.card_info_text_color = (255, 255, 255)
        self.card_info_mana_text_color = (0, 0, 0)

    def __update_position(self, new_position):
        self.rect.center = new_position

    def __update_scale(self, new_scale):
        image_copy = self.original_card_image.copy()
        self.drawn_surface = pygame.transform.scale(image_copy, (int(self.original_scale[0] * new_scale), int(self.original_scale[1] * new_scale)))
        self.current_scale_factor = new_scale

    def on_played(self):
        discard_animation = Animation([
            DualTween(self.rect.center, self.game_state.screen.get_rect().bottomright, 3, self.__update_position),
            Tween(self.current_scale_factor, 0, 4, self.__update_scale)
        ], finished_callback=self.destroy)
        self.current_animation = discard_animation
        self.has_been_played = True

    def move_to(self, new_position, duration):
        if self.has_been_played:
            return
        animation = Animation([
            DualTween(self.rect.center, new_position, duration, self.__update_position)
        ])
        self.current_animation = animation
        self.has_been_played = True

    def update(self):
        # Update animations
        if self.current_animation:
            self.current_animation.update(self.game_state.delta_time)
            if self.current_animation.is_finished:
                self.current_animation = None

    def draw(self, screen):
        super().draw(screen)

        # Draw card name
        name_surface = self.card_info_font.render(self.card_data.card_name, True, self.card_info_text_color)
        name_rect = name_surface.get_rect()
        name_rect.midtop = (self.rect.centerx + 20, self.rect.top + 55)
        size = (name_surface.get_width() * self.current_scale_factor, name_surface.get_height() * self.current_scale_factor)
        screen.blit(pygame.transform.scale(name_surface, size), name_rect)

        # Draw card description
        description_surface = self.card_info_font.render(self.card_data.card_description, True, self.card_info_text_color)
        description_rect = description_surface.get_rect()
        description_rect.midtop = (self.rect.centerx, self.rect.bottom - 250)
        size = (description_surface.get_width() * self.current_scale_factor, description_surface.get_height() * self.current_scale_factor)
        screen.blit(pygame.transform.scale(description_surface, size), description_rect)

        # Draw card cost
        cost_surface = self.card_info_mana_font.render(f"{self.card_data.card_cost}", True, self.card_info_mana_text_color)
        cost_rect = cost_surface.get_rect()
        cost_rect.center = (self.rect.topleft[0] + 55, self.rect.topleft[1] + 55)
        size = (cost_surface.get_width() * self.current_scale_factor, cost_surface.get_height() * self.current_scale_factor)
        screen.blit(pygame.transform.scale(cost_surface, size), cost_rect)


class VisualEffect(GameObject):
    """
    A visual effect that is drawn on the screen for a certain amount of time.
    Fades out over time.
    Destroyed when the lifetime is over.
    """
    def __init__(self, game_state, drawn_surface: pygame.Surface, position: tuple[int, int], lifetime):
        super().__init__(game_state, drawn_surface, position)
        self.lifetime = lifetime
        self.start_time = pygame.time.get_ticks()
        self.alpha = 255

    def update(self):
        elapsed_time = pygame.time.get_ticks() - self.start_time
        if elapsed_time >= self.lifetime:
            self.destroy()
        else:
            # Calculate alpha value based on elapsed time and lifetime
            progress_factor = elapsed_time / self.lifetime
            self.alpha = 255 - int(progress_factor * 255)
        super().update()


class DamageVisualEffect(VisualEffect):
    """
    A visual effect that is drawn on the screen for a certain amount of time.
    Moves up and fades out over time.
    """
    def __init__(self, game_state, font, text, color, position: tuple[int, int], lifetime):
        text_surface = font.render(f"{text}", True, color)
        super().__init__(game_state, text_surface, position, lifetime)
        self.start_x = position[0]
        tween_start_y = position[1]
        tween_end_y = tween_start_y - 200
        self.tween = Tween(tween_start_y, tween_end_y, lifetime)

    def update(self):
        new_y = self.tween.update(self.game_state.delta_time)
        self.rect.center = (self.start_x, new_y)
        super().update()
