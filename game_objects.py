from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional

import random
import pygame
import weakref

from constants import LAYER_DEFAULT, LAYER_ENEMY, LAYER_PLAYER_HAND, LAYER_EFFECTS
from data.cards import CardData
from data.enemies import EnemySpawnData
from utils.animations import Animation, DualTween, Tween
from utils.drawing import Drawable
from utils.io import ImageLibrary, load_image
from utils.math import get_random_inside_rect     # TODO: Create ButtonObject class, which is a GameObject that can be clicked and has a callback function


class GameObjectCollection:  # TODO: Move to StateManagement class. StateManagement does not need to depend on everything in this file.
    """
    A collection of game objects.
    """

    def __init__(self):
        self.game_objects: list[GameObject] = []

    def add(self, game_object):
        self.game_objects.append(game_object)

    def remove(self, game_object):
        self.game_objects.remove(game_object)


class GameObject(Drawable):  # TODO: Move to StateManagement class. StateManagement does not need to depend on everything in this file.
    """
    A base class for all game objects. Game objects are objects that are updated and drawn every frame.
    """

    def __init__(self, drawn_surface: pygame.Surface, position, draw_order=LAYER_DEFAULT):
        super().__init__(drawn_surface, position, draw_order)
        self.game_object_collection: Optional[GameObjectCollection] = None
        """The collection that this object belongs to."""
        self.rect: pygame.Rect = drawn_surface.get_rect()
        """The rect of the object."""
        self.draw_order: int = draw_order
        """The order in which the object will be drawn. Lower numbers are drawn first."""
        self.is_awaiting_destruction: bool = False
        """If True, the object will be destroyed either at the end of the frame, or the next frame."""
        self.is_active: bool = True
        """If False, the object will not receive updates or be drawn."""
        self.is_queued_for_update = False
        """If True, the object has been initialized and is ready to be updated."""

        self.rect.center = position

    def queue(self, game_object_collection: GameObjectCollection):
        """
        Queues the object to receive updates.
        Should only be called once.
        This method should be manually called after the object has been created, if not instantiated by some other object.
        :return: None
        """
        if self.is_queued_for_update:
            raise Exception("GameObject was already queued for updates, do not queue it again.")
        self.game_object_collection: GameObjectCollection = game_object_collection
        self.game_object_collection.add(self)
        self.is_queued_for_update = True
        self.on_initialized()

    def _queue_other(self, other_game_object):  # NOTE: The correct way would be to create a "template" class that instantiates the object, and returns a weak reference to it.
        """
        Queues some other object to the same update queue as this object.
        :param other_game_object: The GameObject to queue.
        :return: None
        """
        other_game_object.queue(self.game_object_collection)
        return weakref.proxy(other_game_object)

    def on_initialized(self):
        """
        This method is called after the object has been initialized.
        :return: None
        """
        pass

    def update(self, delta_time):
        if not self.is_queued_for_update:
            raise Exception("GameObject is not queued for updates. Did you forget to call GameObject.queue() after creating it, or did you not call super in your subclass?")
        self.draw_position = self.rect.topleft

    def set_active(self, should_be_active):
        self.is_active = should_be_active

    def destroy(self):
        self.is_awaiting_destruction = True


class EnemyCharacter(GameObject):
    def __init__(self, position, enemy_spawn_data: EnemySpawnData, image_library: ImageLibrary):
        self.enemy_spawn_data: EnemySpawnData = enemy_spawn_data
        self.image_library: ImageLibrary = image_library
        loaded_image = pygame.image.load(self.enemy_spawn_data.sprite_path)
        loaded_damaged_image = pygame.image.load(self.enemy_spawn_data.damaged_sprite_path)
        self.normal_image = pygame.transform.scale(loaded_image, (int(loaded_image.get_width() * 0.5), int(loaded_image.get_height() * 0.5)))  # TODO: remove scaling
        super().__init__(self.normal_image, position, LAYER_ENEMY)
        self.damaged_image = pygame.transform.scale(loaded_damaged_image, (int(loaded_damaged_image.get_width() * 0.5), int(loaded_damaged_image.get_height() * 0.5)))  # TODO: remove scaling
        self.damaged_image.set_alpha(0)
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

    def update(self, delta_time):
        super().update(delta_time)
        self.update_damage_visuals()
        if self.damaged:
            self.drawn_surface = self.damaged_image
        else:
            self.drawn_surface = self.normal_image

    def draw(self, screen):
        super().draw(screen)
        self.draw_health_bar(screen)

    def draw_health_bar(self, screen):
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
            block_icon_rect = pygame.Rect(0, 0, self.image_library.icon_intention_block.get_width(), self.image_library.icon_intention_block.get_height())
            block_icon_rect.midright = health_bar_rect.midleft
            screen.blit(self.image_library.icon_intention_block, block_icon_rect)

            block_text_color = (0, 0, 0)
            block_text_surface = self.block_font.render(f"{self.current_block}", True, block_text_color)
            block_text_rect = block_text_surface.get_rect()
            block_text_rect.center = block_icon_rect.center
            screen.blit(block_text_surface, block_text_rect)

    def take_damage(self, amount):
        # Reduce current block by the damage amount
        remaining_damage = amount - self.current_block
        self.remove_block(amount)
        removed_block = min(self.current_block, amount)

        # Draw a "block lost" number effect
        if removed_block > 0:
            text_color = (0, 0, 255)
            offset = get_random_inside_rect(100)
            position = (self.rect.center[0] + offset[0], (self.rect.top + self.rect.height / 4) + offset[1])
            effect = DamageNumberVisualEffect(self.damage_effect_font, f"-{removed_block}", text_color, position, 3000)
            self._queue_other(effect)

        # Reduce current health by the damage amount
        if remaining_damage > 0:
            self.current_health -= remaining_damage
            # Draw a damage number effect
            text_color = (255, 0, 0)
            offset = get_random_inside_rect(100)
            position = (self.rect.center[0] + offset[0], (self.rect.top + self.rect.height / 4) + offset[1])
            effect = DamageNumberVisualEffect(self.damage_effect_font, f"-{removed_block}", text_color, position, 3000)
            self._queue_other(effect)

        # Trigger the damaged state and start the color lerp
        self.damaged = True
        self.lerp_start_time = pygame.time.get_ticks()

        # Draw a damage effect
        random_slash_effect = random.choice(self.image_library.slash_effects_list)
        effect_pos = self.rect.center
        effect = VisualEffect(random_slash_effect, effect_pos, 1000)
        self._queue_other(effect)

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
                self.normal_image.set_alpha(255)
                self.damaged = False
            else:
                self.normal_image.set_alpha(255 * lerp_progress)
                self.damaged_image.set_alpha(255 * (1 - lerp_progress))

    def get_intention(self, turn_index):
        # Get the intention for the current turn index. Use modulo to loop the pattern.
        intention = self.enemy_spawn_data.intention_pattern[turn_index % len(self.enemy_spawn_data.intention_pattern)]

        return intention

    def draw_intentions(self, screen, current_round_index):
        next_intention = self.get_intention(current_round_index)
        has_shown_intentions = False
        next_rect_pos: tuple[int, int] = self.health_bar_background_rect.topleft
        if next_intention.gain_health_amount > 0:
            health_icon_rect = pygame.Rect(0, 0, self.image_library.icon_intention_buff.get_width(), self.image_library.icon_intention_buff.get_height())
            health_icon_rect.bottomleft = next_rect_pos
            next_rect_pos = health_icon_rect.bottomright
            screen.blit(self.image_library.icon_intention_buff, health_icon_rect)
            has_shown_intentions = True
        if next_intention.gain_block_amount > 0:
            block_icon_rect = pygame.Rect(0, 0, self.image_library.icon_intention_block.get_width(), self.image_library.icon_intention_block.get_height())
            block_icon_rect.bottomleft = next_rect_pos
            next_rect_pos = block_icon_rect.bottomright
            screen.blit(self.image_library.icon_intention_block, block_icon_rect)
            has_shown_intentions = True
        if next_intention.deal_damage_amount > 0:
            attack_icon = self.image_library.get_damage_icon_from_damage_amount(next_intention.deal_damage_amount)
            attack_icon_rect = pygame.Rect(0, 0, attack_icon.get_width(), attack_icon.get_height())
            attack_icon_rect.bottomleft = next_rect_pos
            next_rect_pos = attack_icon_rect.bottomright
            screen.blit(attack_icon, attack_icon_rect)

            text_color = (255, 255, 255)
            text_surface = self.block_font.render(f"{next_intention.deal_damage_amount}", True, text_color)
            text_rect = text_surface.get_rect()
            text_rect.center = (attack_icon_rect.left + 20, attack_icon_rect.bottom - 20)
            screen.blit(text_surface, text_rect)

            has_shown_intentions = True
        if not has_shown_intentions:  # If no intentions are shown, display the "unknown intentions" icon
            unknown_icon_rect = pygame.Rect(0, 0, self.image_library.icon_intention_unknown.get_width(), self.image_library.icon_intention_unknown.get_height())
            unknown_icon_rect.bottomleft = next_rect_pos
            screen.blit(self.image_library.icon_intention_unknown, unknown_icon_rect)


class GameCard(GameObject):
    def __init__(self, draw_pile_position, discard_pile_position, card_position, card_data):
        self.card_data: CardData = card_data
        self.current_scale_factor = 1
        self.draw_pile_position = draw_pile_position
        self.discard_pile_position = discard_pile_position
        self.original_position = card_position
        self.has_been_played = False
        self.is_self_hovered = False
        self.is_other_card_hovered = False

        self.original_card_image = load_image(self.card_data.sprite_path)
        self.original_scale = (int(self.original_card_image.get_width()), int(self.original_card_image.get_height()))
        image_copy = self.original_card_image.copy()

        self.card_info_font = pygame.font.Font(None, 36)
        self.card_info_mana_font = pygame.font.Font(None, 65)
        self.card_info_text_color = (255, 255, 255)
        self.card_info_mana_text_color = (0, 0, 0)

        # Play a draw animation when the card is created
        draw_animation = Animation([
            DualTween(self.draw_pile_position, self.original_position, 0.5, self.__update_position),
            Tween(0, 1, 0.3, self.__update_scale)
        ])
        self.current_animation: Animation = draw_animation  # TODO: Ensure that this animation is not instantly skipped by adding an is_overrideable flag to animations

        super().__init__(image_copy, card_position, LAYER_PLAYER_HAND)
        import debugging
        debugging.debug_target_object = self

    def __update_position(self, new_position):
        self.rect.center = new_position

    def __update_scale(self, new_scale):
        image_copy = self.original_card_image.copy()
        self.drawn_surface = pygame.transform.scale(image_copy, (int(self.original_scale[0] * new_scale), int(self.original_scale[1] * new_scale)))
        self.current_scale_factor = new_scale

    def on_played(self):
        discard_animation = Animation([
            DualTween(self.rect.center, self.discard_pile_position, 3, self.__update_position),
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

    def update(self, delta_time):
        super().update(delta_time)
        # Update animations
        if self.current_animation:
            self.current_animation.update(delta_time)
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
    A visual effect that is drawn on the debug_screen for a certain amount of time.
    Fades out over time.
    Destroyed when the lifetime is over.
    """

    def __init__(self, drawn_surface: pygame.Surface, position: tuple[int, int], lifetime):
        self.lifetime = lifetime
        self.start_time = pygame.time.get_ticks()
        self.alpha = 255
        super().__init__(drawn_surface, position, LAYER_EFFECTS)

    def update(self, delta_time):
        super().update(delta_time)
        elapsed_time = pygame.time.get_ticks() - self.start_time
        if elapsed_time >= self.lifetime:
            self.destroy()
        else:
            # Calculate alpha value based on elapsed time and lifetime
            progress_factor = elapsed_time / self.lifetime
            self.alpha = 255 - int(progress_factor * 255)


class DamageNumberVisualEffect(VisualEffect):
    """
    A visual effect that is drawn on the debug_screen for a certain amount of time.
    Moves up and fades out over time.
    """

    def __init__(self, font, text, color, position: tuple[int, int], lifetime):
        text_surface = font.render(f"{text}", True, color)
        self.start_x = position[0]
        tween_start_y = position[1]
        tween_end_y = tween_start_y - 200
        self.tween = Tween(tween_start_y, tween_end_y, lifetime)
        super().__init__(text_surface, position, lifetime)

    def update(self, delta_time):
        new_y = self.tween.update(delta_time)
        self.rect.center = (self.start_x, new_y)    # TODO: Animate x with sine.
        super().update(delta_time)
