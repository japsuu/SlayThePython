import json
import random
from typing import List

import pygame

import StateManagement
import Effects


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


# Describes all the actions an enemy will take during their turn
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


# Example usage:
# Create an EnemySpawnData instance
# spawn_data = EnemySpawnData(max_health_min=10, max_health_max=30, sprite_path="enemy_sprite.png")
# Spawn an enemy using the spawn_enemy method
# enemy = spawn_data.spawn_enemy(100, 100)
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


class EnemyCharacter(pygame.sprite.Sprite):
    def __init__(self, enemy_spawn_data, x, y):
        super().__init__()
        self.enemy_spawn_data: EnemySpawnData = enemy_spawn_data
        loaded_image = pygame.image.load(self.enemy_spawn_data.sprite_path)
        self.image = pygame.transform.scale(loaded_image, (int(loaded_image.get_width() * 0.5), int(loaded_image.get_height() * 0.5)))
        loaded_damaged_image = pygame.image.load(self.enemy_spawn_data.damaged_sprite_path)
        self.damaged_image = pygame.transform.scale(loaded_damaged_image, (int(loaded_damaged_image.get_width() * 0.5), int(loaded_damaged_image.get_height() * 0.5)))
        self.damaged_image.set_alpha(0)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.max_health = random.randint(self.enemy_spawn_data.max_health_min, self.enemy_spawn_data.max_health_max)
        self.current_health = self.max_health
        self.current_block = 0
        self.lerp_duration = 0.6
        self.lerp_start_time = None
        self.lerp_progress = 0
        self.damaged = False
        self.font = pygame.font.Font(None, 36)
        self.block_font = pygame.font.Font(None, 25)
        self.text_color = (255, 255, 255)
        health_bar_background_width = int(self.rect.width / 2)
        self.health_bar_background_rect = pygame.Rect(self.rect.left, self.rect.top - 10, health_bar_background_width, 5)

    def draw(self, screen, game_state):
        # Draw the enemy sprite and health bar onto the screen
        self.update_damage_visuals()
        screen.blit(self.image, self.rect.topleft)
        screen.blit(self.damaged_image, self.rect.topleft)
        self.draw_health_bar(screen, game_state)

    def draw_health_bar(self, screen, game_state):
        has_block = self.current_block > 0

        # Calculate the width of the health bar based on current health
        health_ratio = self.current_health / self.max_health
        health_bar_width = int(self.rect.width / 2 * health_ratio)

        # Define the health bar's dimensions and position
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

            block_text_color = (100, 255, 255)  # Light blue
            block_text_surface = self.block_font.render(f"{self.current_block}", True, block_text_color)
            block_text_rect = block_text_surface.get_rect()
            block_text_rect.center = block_icon_rect.center
            screen.blit(block_text_surface, block_text_rect)

    def take_damage(self, game_state, amount):
        # Reduce current block by the damage amount
        remaining_damage = amount - self.current_block
        self.remove_block(amount)

        # Reduce current health by the damage amount
        if remaining_damage > 0:
            self.current_health -= remaining_damage

        # Trigger the damaged state and start the color lerp
        self.damaged = True
        self.lerp_start_time = pygame.time.get_ticks()

        # Draw a damage effect
        random_slash_effect = random.choice(game_state.game_data.slash_effects_list)
        effect_rect = self.rect.center
        new_effect = Effects.VisualEffect(random_slash_effect, effect_rect, 1000)
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
            has_shown_intentions = True
        if not has_shown_intentions:  # If no intentions are shown, display the "unknown intentions" icon
            unknown_icon_rect = pygame.Rect(0, 0, game_state.game_data.icon_intention_unknown.get_width(), game_state.game_data.icon_intention_unknown.get_height())
            unknown_icon_rect.bottomleft = next_rect_pos
            screen.blit(game_state.game_data.icon_intention_unknown, unknown_icon_rect)
