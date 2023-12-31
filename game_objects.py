from __future__ import annotations
from typing import TYPE_CHECKING, Dict

from utils import audio, constants
from utils.drawing import Drawable, TextTooltip
from utils.input import Inputs
from utils.logging import log_warning, log_info

if TYPE_CHECKING:
    from typing import List, Optional

import random
import pygame
import numpy as np

from utils.constants import LAYER_ENEMY, LAYER_PLAYER_HAND, LAYER_EFFECTS, LAYER_DEFAULT, ANIM_PRIORITY_CARD_DRAW, ANIM_PRIORITY_CARD_DISCARD, ANIM_PRIORITY_DEFAULT, FONT_ENEMY_HEALTH, \
    FONT_ENEMY_ICON_HINT, FONT_ENEMY_DAMAGE_EFFECT, FONT_CARD_NAME, FONT_CARD_DESCRIPTION, FONT_CARD_MANA_COST, ANIM_PRIORITY_CARD_REPOSITION, ENEMY_SPRITE_SCALING_FACTOR, SYMBOLS_FONT, \
    SYMBOLS_FONT_BG
from data.cards import CardData
from data.enemies import EnemySpawnData, EnemyIntentionData
from utils.animations import Animation, Tween, GetterTween, GetterTupleTween
from utils.io import ImageLibrary, load_image
from utils.math import get_random_inside_rect


class GameObjectCollection:
    """
    A collection of game object references.
    """

    def __init__(self):
        self.game_objects: List[GameObject] = []

    def add(self, game_object: GameObject):
        if game_object is None:
            raise Exception("Trying to add a None GameObject.")
        if game_object in self.game_objects:
            raise Exception("Trying to add a GameObject reference that is already in the collection.")
        self.game_objects.append(game_object)

    def remove(self, game_object: GameObject):
        if game_object is None:
            raise Exception("Trying to remove a None GameObject.")
        if not game_object.is_awaiting_destruction:
            game_object.destroy()
            return
        self.game_objects.remove(game_object)


class GameObject(Drawable):
    """
    A base class for all game objects. Game objects are objects that are updated and drawn every frame.
    """

    def __init__(self, game_object_collection: GameObjectCollection, drawn_surface: pygame.Surface, position, draw_order=LAYER_DEFAULT, name="unnamed game object"):
        super().__init__(drawn_surface, position, draw_order, None)
        self.game_object_collection: Optional[GameObjectCollection] = game_object_collection
        """The collection that this object belongs to."""
        self.draw_order: int = draw_order
        """The order in which the object will be drawn. Lower numbers are drawn first."""
        self.animations: Dict[int, Animation] = {}
        """
        A dict of animations that are currently playing.
        Use queue_animation() to add an animation to the dict.
        The key is used to determine the order in which animations are updated.
        Higher priority animations override lower priority animations.
        """
        self.is_awaiting_destruction: bool = False
        """If True, the object will be destroyed either at the end of the frame, or the next frame."""
        self.is_active: bool = True
        """If False, the object will not receive updates or be drawn."""
        self.is_queued_for_update = False
        """If True, the object has been initialized and is ready to be updated."""
        self.time_destroyed_at = -1
        """The time in milliseconds when the object was destroyed."""
        self.is_debugged = False
        """If this object is currently shown in the debug inspector."""
        self.name = name
        """The name of the object. Used for debugging."""

    def on_initialized(self):
        """
        This method is called after the object has been initialized.
        :return: None
        """
        pass

    def cancel_all_animations(self):
        """
        Cancels all animations.
        :return: None
        """
        self.animations.clear()

    def queue_animation(self, animation: Animation, priority: int):
        """
        Adds an animation to the object's animation dict.
        :param animation: The animation to add.
        :param priority: The priority of the animation.
        Higher priority animations override lower priority animations.
        :return: None
        """
        self.animations[priority] = animation

    def update(self, delta_time):
        # Check destruction
        if self.is_awaiting_destruction and self.time_destroyed_at > 0:
            current_time = pygame.time.get_ticks()
            seconds_waited_for_destruction = (current_time - self.time_destroyed_at) / 1000
            if seconds_waited_for_destruction > 3:
                log_warning(f"{self} has been waiting for destruction for {seconds_waited_for_destruction}s! This is a memory leak!")
                return
        # Ensure that the object is queued for updates
        if not self.is_queued_for_update:
            raise Exception(f"GameObject {self.name} is not queued for updates. Did you forget to call GameObject.queue() after creating it, or did you not call super in your subclass?")

        # Update the highest priority animation
        if self.animations:
            sorted_keys = sorted(self.animations.keys())
            animation = self.animations[sorted_keys[-1]]
            animation.update(delta_time)
            if self.is_debugged:
                log_info(f"{self.name} update anim {animation.name} (priority {sorted_keys[-1]})")
            if animation.is_finished:
                del self.animations[sorted_keys[-1]]

    def draw(self, screen: pygame.Surface):
        if not self.is_active:
            return

        # Check destruction
        if self.is_awaiting_destruction and self.time_destroyed_at > 0:
            current_time = pygame.time.get_ticks()
            seconds_waited_for_destruction = (current_time - self.time_destroyed_at) / 1000
            if seconds_waited_for_destruction > 3:
                log_warning(f"{self} has been waiting for destruction for {seconds_waited_for_destruction}s! This is a memory leak!")
                return

        super().draw(screen)

    def set_tooltip_text(self, tooltip_text_lines: Optional[List[str]]):
        self.tooltip = TextTooltip(tooltip_text_lines)

    def set_active(self, should_be_active):
        self.is_active = should_be_active

    def set_position(self, new_position):
        self.rect.topleft = new_position

    def get_position(self):
        return self.rect.topleft

    def destroy(self):
        # print(f"Destroying {self}")
        self.is_awaiting_destruction = True
        self.time_destroyed_at = pygame.time.get_ticks()
        if self.game_object_collection:
            self.game_object_collection.remove(self)
        else:
            raise Exception("GameObject was never queued. Did you forget to call GameObject.queue() after creating it, or did you not call super in your subclass?")


class GameObjectFactory:
    """
    A template for a game object.
    Call instantiate() to create an instance of the game object.
    """

    def __init__(self, game_object_collection: GameObjectCollection, game_object_create_func):
        self.game_object_collection = game_object_collection
        self.game_object_create_func = game_object_create_func

    def instantiate(self, position):
        """
        Instantiates a new game object.
        :return: A reference to the game object.
        """
        # Create a new game object
        game_object = self.game_object_create_func(position)

        # Queue the game object with a strong reference
        if game_object.is_queued_for_update:
            raise Exception("GameObject was already queued for updates, do not queue it again.")
        if self.game_object_collection is None:
            raise Exception(f"{type(self)} was not initialized with a GameObjectCollection? What?")
        game_object.game_object_collection.add(game_object)
        game_object.is_queued_for_update = True
        game_object.on_initialized()

        # Return a reference to the game object
        return game_object


class EnemyCharacterFactory(GameObjectFactory):
    def __init__(self, game_object_collection: GameObjectCollection, enemy_spawn_data: EnemySpawnData, image_library: ImageLibrary):
        self.image_library = image_library
        self.enemy_spawn_data = enemy_spawn_data
        self.current_health_font = FONT_ENEMY_HEALTH
        self.icon_subscript_font = FONT_ENEMY_ICON_HINT
        self.damage_effect_font = FONT_ENEMY_DAMAGE_EFFECT
        super().__init__(game_object_collection, self.create)

    def create(self, position) -> EnemyCharacter:
        return EnemyCharacter(self.game_object_collection, position, self.enemy_spawn_data, self.image_library, self.current_health_font, self.icon_subscript_font, self.damage_effect_font)

    def set_target_spawn_data(self, enemy_spawn_data: EnemySpawnData):
        self.enemy_spawn_data = enemy_spawn_data


class EnemyCharacter(GameObject):
    def __init__(self, game_object_collection: GameObjectCollection, position, enemy_spawn_data: EnemySpawnData, image_library: ImageLibrary, health_font, icon_subscript_font,
                 damage_effect_font):
        self.enemy_spawn_data: EnemySpawnData = enemy_spawn_data
        self.image_library: ImageLibrary = image_library
        loaded_image = load_image(self.enemy_spawn_data.sprite_path)
        self.normal_image = pygame.transform.scale(loaded_image, (loaded_image.get_rect().width * ENEMY_SPRITE_SCALING_FACTOR, loaded_image.get_rect().height * ENEMY_SPRITE_SCALING_FACTOR))
        # Insert "_damaged" before the file extension
        damage_sprite_path = self.get_sprite_variant_path("_damaged")
        loaded_image = load_image(damage_sprite_path)
        self.damaged_image = pygame.transform.scale(loaded_image, (loaded_image.get_rect().width * ENEMY_SPRITE_SCALING_FACTOR, loaded_image.get_rect().height * ENEMY_SPRITE_SCALING_FACTOR))
        super().__init__(game_object_collection, self.normal_image, position, LAYER_ENEMY)
        self.damaged_image.set_alpha(0)
        self.damage_animation: Optional[Animation] = None
        self.max_health = random.randint(self.enemy_spawn_data.max_health_min, self.enemy_spawn_data.max_health_max)
        self.current_health = self.max_health
        self.current_block = 0
        self.current_round_index = -1
        self.turn_sprite: Optional[pygame.Surface] = None
        self.turn_animation: Optional[Animation] = None
        self.has_completed_turn = False
        self.health_font = health_font
        self.icon_subscript_font = icon_subscript_font
        self.damage_effect_font = damage_effect_font
        self.text_color = (255, 255, 255)
        health_bar_background_width = int(self.rect.width / 2)
        self.health_bar_background_rect = pygame.Rect(self.rect.left, self.rect.top - 10, health_bar_background_width, 5)
        self.visual_effect_factory = RandomVisualEffectFactory(self.game_object_collection, self.image_library.slash_effects_list, 1000)
        self.damage_number_visual_effect_factory = DamageNumberVisualEffectFactory(self.game_object_collection, self.damage_effect_font, "0", self.text_color, 3000)
        self.set_tooltip_text([enemy_spawn_data.name])
        self.dies_after_turns = 999
        if self.enemy_spawn_data.extras:
            for extra in self.enemy_spawn_data.extras:
                if "dies_after_turns" in extra:
                    self.dies_after_turns = int(extra.split(",")[1])

    def update(self, delta_time):
        super().update(delta_time)
        if self.damage_animation:
            self.damage_animation.update(delta_time)
            if self.damage_animation.is_finished:
                self.damage_animation = None
        if self.turn_animation:
            self.turn_animation.update(delta_time)
            if self.turn_animation.is_finished:
                self.turn_animation = None
                self.turn_sprite = None

    def draw(self, screen):
        super().draw(screen)
        if self.damage_animation:
            screen.blit(self.damaged_image, self.rect)
        if self.turn_animation:
            screen.blit(self.turn_sprite, self.rect)
        self.draw_health_bar(screen)
        if self.current_round_index >= 0:
            self.__draw_intentions(screen, self.current_round_index)

    def draw_health_bar(self, screen):
        has_block = self.current_block > 0

        # Calculate the width of the health bar based on current health
        health_ratio = self.current_health / self.max_health
        health_bar_width = int(self.rect.width / 2 * health_ratio)

        # Define the health bar's dimensions and position_or_rect
        health_bar_rect = pygame.Rect(self.rect.left, self.rect.top - 10, health_bar_width, 5)

        # Draw the actual health next to the health bar
        health_text_surface = self.health_font.render(f"{self.current_health} / {self.max_health}", True, self.text_color)
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
            block_text_surface = self.icon_subscript_font.render(f"{self.current_block}", True, block_text_color)
            block_text_rect = block_text_surface.get_rect()
            block_text_rect.center = block_icon_rect.center
            screen.blit(block_text_surface, block_text_rect)

    def take_damage(self, amount):
        # Reduce current block by the damage amount
        remaining_damage = amount - self.current_block
        self.remove_block(amount)

        # Reduce current health by the damage amount
        if remaining_damage > 0:
            self.current_health = max(self.current_health - remaining_damage, 0)
            # Draw a damage number effect
            text_color = (255, 0, 0)
            offset = get_random_inside_rect(100)
            position = (self.rect.center[0] + offset[0], (self.rect.top + self.rect.height / 4) + offset[1])
            self.__instantiate_damage_number_effect(position, remaining_damage, text_color)
            audio.play_one_shot_delayed(constants.damaged_sound, 0.1)

        # Play the damage animation
        self.damage_animation = Animation([
            Tween(0, 255, 0.5, self.__update_normal_sprite_alpha),
            Tween(255, 0, 0.5, self.__update_damage_sprite_alpha),
        ], name="Damage animation")

        # Draw a damage effect
        effect_pos = self.rect.center
        self.visual_effect_factory.instantiate(effect_pos)

        if self.current_health <= 0:
            self.destroy()
            audio.play_one_shot_delayed(constants.killed_sound, 0.15)

    def __instantiate_damage_number_effect(self, position, damage_amount, color):
        self.damage_number_visual_effect_factory.set_target_text(f"-{damage_amount}")
        self.damage_number_visual_effect_factory.set_target_color(color)
        self.damage_number_visual_effect_factory.instantiate(position)

    def get_sprite_variant_path(self, variant_name):
        return self.enemy_spawn_data.sprite_path[:-4] + variant_name + self.enemy_spawn_data.sprite_path[-4:]

    def gain_health(self, amount):
        self.current_health = min(self.current_health + amount, self.max_health)
        audio.play_one_shot_delayed(constants.healed_sound, 0.05)

    def gain_block(self, amount):
        self.current_block += amount

    def remove_block(self, amount, draw_effect=True):
        old_block = self.current_block
        self.current_block = max(self.current_block - amount, 0)
        removed_block = old_block - self.current_block

        # Draw a "block lost" number effect.
        if (removed_block > 0) and draw_effect:
            text_color = (0, 0, 255)
            offset = get_random_inside_rect(100)
            position = (self.rect.center[0] + offset[0], (self.rect.top + self.rect.height / 4) + offset[1])
            self.__instantiate_damage_number_effect(position, removed_block, text_color)
            audio.play_one_shot_delayed(constants.blocked_sound, 0.05)

    def get_intention(self, turn_index):
        # Get the intention for the current turn index. Use modulo to loop the pattern.
        intention = self.enemy_spawn_data.intention_pattern[turn_index % len(self.enemy_spawn_data.intention_pattern)]

        return intention

    def play_turn_animation(self, intention: EnemyIntentionData):
        sprite_path = self.get_sprite_variant_path(intention.get_turn_sprite_path_prefix())
        loaded_image = load_image(sprite_path)
        self.turn_sprite = pygame.transform.scale(loaded_image, (loaded_image.get_rect().width * ENEMY_SPRITE_SCALING_FACTOR, loaded_image.get_rect().height * ENEMY_SPRITE_SCALING_FACTOR))
        self.turn_animation = Animation([
            Tween(255, 0, 1, self.__update_turn_sprite_alpha),
            Tween(0, 255, 1.5, self.__update_normal_sprite_alpha, self.__hide_intentions)
        ], name="Turn animation")

    def __update_turn_sprite_alpha(self, new_alpha):
        self.turn_sprite.set_alpha(new_alpha)

    def __update_normal_sprite_alpha(self, new_alpha):
        self.normal_image.set_alpha(new_alpha)

    def __update_damage_sprite_alpha(self, new_alpha):
        self.damaged_image.set_alpha(new_alpha)

    def __hide_intentions(self):
        self.current_round_index = -1

    def __draw_intentions(self, screen, current_round_index):
        next_intention = self.get_intention(current_round_index)
        has_shown_intentions = False
        next_rect_pos: tuple[int, int] = self.health_bar_background_rect.topleft
        negative_icon = self.image_library.icon_intention_negative
        if next_intention.gain_health_amount != 0:
            if next_intention.gain_health_amount < 0:
                icon_rect = self.__draw_intention_icon(screen, self.image_library.icon_intention_buff, next_rect_pos, negative_icon)
            else:
                icon_rect = self.__draw_intention_icon(screen, self.image_library.icon_intention_buff, next_rect_pos)
            next_rect_pos = icon_rect.bottomright
            has_shown_intentions = True
        if next_intention.gain_block_amount != 0:
            if next_intention.gain_block_amount < 0:
                icon_rect = self.__draw_intention_icon(screen, self.image_library.icon_intention_block, next_rect_pos, negative_icon)
            else:
                icon_rect = self.__draw_intention_icon(screen, self.image_library.icon_intention_block, next_rect_pos)
            next_rect_pos = icon_rect.bottomright
            has_shown_intentions = True
        if next_intention.deal_damage_amount > 0:
            attack_icon = self.image_library.get_damage_icon_from_damage_amount(next_intention.deal_damage_amount)
            icon_rect = self.__draw_intention_icon(screen, attack_icon, next_rect_pos)
            next_rect_pos = icon_rect.bottomright

            text_color = (255, 255, 255)
            text_surface = self.icon_subscript_font.render(f"{next_intention.deal_damage_amount}", True, text_color)
            text_rect = text_surface.get_rect()
            text_rect.center = (icon_rect.left + 20, icon_rect.bottom - 20)
            screen.blit(text_surface, text_rect)

            has_shown_intentions = True
        if not has_shown_intentions:  # If no intentions are shown, display the "unknown intentions" icon
            rect = self.__draw_intention_icon(screen, self.image_library.icon_intention_unknown, next_rect_pos)
            next_rect_pos = rect.bottomright

        tooltip_lines = [self.enemy_spawn_data.name]
        intentions = next_intention.get_description()
        if intentions:
            tooltip_lines.append("")
            tooltip_lines.extend(intentions)
        if self.dies_after_turns < 10:
            tooltip_lines.append("")
            if self.dies_after_turns == 1:
                tooltip_lines.append(f"Dies next turn.")
            else:
                tooltip_lines.append(f"Dies after {self.dies_after_turns} turns.")
            self.__draw_intention_icon(screen, self.image_library.icon_intention_die, next_rect_pos)
        self.set_tooltip_text(tooltip_lines)

    @staticmethod
    def __draw_intention_icon(screen, icon, position, overlay_icon=None):
        icon_rect = pygame.Rect(0, 0, icon.get_width(), icon.get_height())
        icon_rect.bottomleft = position
        screen.blit(icon, icon_rect)
        if overlay_icon:
            icon_rect_o = pygame.Rect(0, 0, overlay_icon.get_width(), overlay_icon.get_height())
            icon_rect_o.center = icon_rect.center
            screen.blit(icon, icon_rect_o)
        return icon_rect


class GameCardFactory(GameObjectFactory):
    def __init__(self, game_object_collection: GameObjectCollection, draw_pile_position: tuple, discard_pile_position: tuple, card_data: CardData):
        self.card_data: CardData = card_data
        self.draw_pile_position = draw_pile_position
        self.discard_pile_position = discard_pile_position
        self.card_name_font = FONT_CARD_NAME
        self.card_description_font = FONT_CARD_DESCRIPTION
        self.card_mana_cost_font = FONT_CARD_MANA_COST
        super().__init__(game_object_collection, self.create)

    def create(self, position) -> GameCard:
        return GameCard(self.game_object_collection, self.draw_pile_position, self.discard_pile_position, position, self.card_data,
                        self.card_name_font, self.card_description_font, self.card_mana_cost_font)

    def set_target_card_data(self, card_data: CardData):
        self.card_data = card_data


class GameCard(GameObject):
    def __init__(self, game_object_collection: GameObjectCollection, draw_pile_position: tuple, discard_pile_position: tuple, card_position: tuple, card_data: CardData,
                 card_name_font, card_description_font, card_mana_cost_font):
        self.card_data: CardData = card_data
        self.current_scale_factor = 1
        self.draw_pile_position = draw_pile_position
        self.discard_pile_position = discard_pile_position
        self.home_position = card_position
        self.has_been_played = False
        self.is_self_hovered = False
        self.is_other_card_hovered = False
        self.can_be_clicked = False     # NOTE: This may cause unexpected behaviour.
        self.alpha = 255

        self.original_card_image = load_image(self.card_data.sprite_path)
        self.original_scale = (int(self.original_card_image.get_width()), int(self.original_card_image.get_height()))
        image_copy = self.original_card_image.copy()

        self.card_name_font = card_name_font
        self.card_description_font = card_description_font
        self.card_mana_cost_font = card_mana_cost_font
        self.card_info_text_color = (0, 0, 0)
        self.card_description_text_color = (255, 255, 255)
        self.card_info_mana_text_color = (0, 0, 0)

        super().__init__(game_object_collection, image_copy, card_position, LAYER_PLAYER_HAND, name=f"Card {self.card_data.card_info_name}")
        self.blocks_tooltips = True
        self.__update_tooltip()

    def __update_tooltip(self):
        generated_tooltip_lines = self.__generate_tooltip_lines()
        if len(generated_tooltip_lines) > 0:
            self.set_tooltip_text(generated_tooltip_lines)
        elif self.tooltip:
            self.tooltip = None

    def __generate_tooltip_lines(self):
        tooltip_lines = []
        if self.card_data.exhaust:
            tooltip_lines.append("Exhaust:")
            tooltip_lines.append("When played, this card is removed")
            tooltip_lines.append("from your deck for the rest of the combat.")
            tooltip_lines.append("")
        if self.card_data.delete:
            tooltip_lines.append("Delete:")
            tooltip_lines.append("When played, this card is permanently")
            tooltip_lines.append("removed from your deck.")
        return tooltip_lines

    def __enable_clicking(self):
        self.can_be_clicked = True

    def __update_position(self, new_position):
        self.rect.center = new_position

    def __update_alpha(self, new_alpha):
        self.alpha = new_alpha

    def __update_scale(self, new_scale):
        image_copy = self.original_card_image.copy()
        self.drawn_surface = pygame.transform.scale(image_copy, (int(self.original_scale[0] * new_scale), int(self.original_scale[1] * new_scale)))
        self.current_scale_factor = new_scale

    def play_draw_animation(self, target_position):
        self.home_position = target_position
        self.can_be_clicked = False
        draw_animation = Animation([
            GetterTupleTween(self.__get_position, self.home_position, 0.5, self.__update_position),
            GetterTween(self.__get_scale_factor, 1, 0.3, self.__update_scale),
            GetterTween(self.__get_alpha, 255, 1, self.__update_alpha)
        ], finished_callback=self.__enable_clicking, name="Card draw animation")
        self.cancel_all_animations()
        self.queue_animation(draw_animation, priority=ANIM_PRIORITY_CARD_DRAW)

    def play_reposition_animation(self, target_position):
        self.home_position = target_position
        # self.can_be_clicked = False
        draw_animation = Animation([
            GetterTupleTween(self.__get_position, self.home_position, 0.2, self.__update_position)
        ], name="Card reposition animation")  # , finished_callback=self.__enable_clicking
        self.queue_animation(draw_animation, priority=ANIM_PRIORITY_CARD_REPOSITION)

    def on_played(self, exhausted: bool = False, deleted: bool = False):
        if self.has_been_played:
            return
        if deleted:
            animation = Animation([
                GetterTupleTween(self.__get_position, (self.rect.centerx, pygame.display.get_surface().get_rect().bottom + 200), 0.4, self.__update_position)
            ], finished_callback=self.destroy, name="Card deletion animation")
        elif exhausted:
            animation = Animation([
                GetterTupleTween(self.__get_position, (self.rect.centerx, self.rect.top - 100), 1, self.__update_position),
                GetterTween(self.__get_alpha, 0, 0.8, self.__update_alpha)
            ], finished_callback=self.destroy, name="Card exhaustion animation")
        else:
            animation = Animation([
                GetterTupleTween(self.__get_position, self.discard_pile_position, 0.5, self.__update_position),
                GetterTween(self.__get_scale_factor, 0.5, 0.8, self.__update_scale),
                GetterTween(self.__get_alpha, 0, 1, self.__update_alpha)
            ], finished_callback=self.destroy, name="Card discard animation")
        self.cancel_all_animations()
        self.queue_animation(animation, priority=ANIM_PRIORITY_CARD_DISCARD)
        self.has_been_played = True

    def create_and_queue_animation(self, new_position, position_duration, new_alpha, alpha_duration, priority=ANIM_PRIORITY_DEFAULT, name="unnamed"):
        if self.has_been_played:
            return
        animation = Animation([
            GetterTupleTween(self.__get_position, new_position, position_duration, self.__update_position),
            GetterTween(self.__get_alpha, new_alpha, alpha_duration, self.__update_alpha)
        ], name=name)
        self.queue_animation(animation, priority)

    def __get_position(self):
        return self.rect.center

    def __get_alpha(self):
        return self.alpha

    def __get_scale_factor(self):
        return self.current_scale_factor

    def draw(self, screen):
        self.drawn_surface.set_alpha(self.alpha)
        super().draw(screen)

        # Draw card name
        name_surface = self.card_name_font.render(self.card_data.card_info_name, True, self.card_info_text_color)
        name_rect = name_surface.get_rect()
        name_rect.midtop = (self.rect.centerx + 20, self.rect.top + 30)
        size = (name_surface.get_width() * self.current_scale_factor, name_surface.get_height() * self.current_scale_factor)
        name_surface.set_alpha(self.alpha)
        screen.blit(pygame.transform.scale(name_surface, size), name_rect)

        # Draw rarity
        rarity_stars = 1
        previous_x = self.rect.centerx - 110
        color = (255, 255, 255)
        if self.card_data.card_rarity == "uncommon":
            rarity_stars = 2
            color = (0, 255, 0)
        elif self.card_data.card_rarity == "rare":
            rarity_stars = 3
            color = (255, 0, 255)
        last_rarity_rect = None
        for i in range(rarity_stars):
            rarity_bg_surface = SYMBOLS_FONT_BG.render("I", True, (0, 0, 0))
            rarity_bg_rect = rarity_bg_surface.get_rect()
            rarity_bg_rect.topleft = (previous_x, self.rect.bottom - 55)
            previous_x = rarity_bg_rect.right + 5
            size = (rarity_bg_surface.get_width() * self.current_scale_factor, rarity_bg_surface.get_height() * self.current_scale_factor)
            rarity_bg_surface.set_alpha(self.alpha)
            last_rarity_rect = rarity_bg_rect
            screen.blit(pygame.transform.scale(rarity_bg_surface, size), rarity_bg_rect)
            rarity_surface = SYMBOLS_FONT.render("I", True, color)
            rarity_rect = rarity_surface.get_rect()
            rarity_rect.center = rarity_bg_rect.center
            size = (rarity_surface.get_width() * self.current_scale_factor, rarity_surface.get_height() * self.current_scale_factor)
            rarity_surface.set_alpha(self.alpha)
            screen.blit(pygame.transform.scale(rarity_surface, size), rarity_rect)
        if last_rarity_rect:
            rarity_tooltip_rect = pygame.Rect(self.rect.centerx - 115, self.rect.bottom - 60, (last_rarity_rect.width + 5) * rarity_stars, last_rarity_rect.height + 5)
            if rarity_tooltip_rect.collidepoint(Inputs.get_mouse_position()):
                self.set_tooltip_text(["Rarity:", self.card_data.card_rarity.capitalize()])
            elif self.tooltip and (self.tooltip.text_lines == ["Rarity:", self.card_data.card_rarity.capitalize()]):
                self.__update_tooltip()

        # Draw card description
        previous_description_midbottom = (self.rect.centerx + 5, self.rect.bottom - 150)
        for description in self.card_data.card_info_description.split("\n"):
            description_surface = self.card_description_font.render(description, True, self.card_description_text_color)
            description_rect = description_surface.get_rect()
            description_rect.midtop = previous_description_midbottom
            size = (description_surface.get_width() * self.current_scale_factor, description_surface.get_height() * self.current_scale_factor)
            description_surface.set_alpha(self.alpha)
            previous_description_midbottom = (description_rect.midbottom[0], description_rect.midbottom[1] - 10)
            screen.blit(pygame.transform.scale(description_surface, size), description_rect)

        # Draw card cost
        cost_surface = self.card_mana_cost_font.render(f"{self.card_data.card_cost}", True, self.card_info_mana_text_color)
        cost_rect = cost_surface.get_rect()
        cost_rect.center = (self.rect.topleft[0] + 50, self.rect.topleft[1] + 44)
        size = (cost_surface.get_width() * self.current_scale_factor, cost_surface.get_height() * self.current_scale_factor)
        cost_surface.set_alpha(self.alpha)
        screen.blit(pygame.transform.scale(cost_surface, size), cost_rect)


class VisualEffectFactory(GameObjectFactory):
    def __init__(self, game_object_collection: GameObjectCollection, effect_surface: pygame.Surface, lifetime: int):
        self.effect_surface = effect_surface
        self.lifetime = lifetime
        super().__init__(game_object_collection, self.create)

    def create(self, position) -> VisualEffect:
        return VisualEffect(self.game_object_collection, self.effect_surface, position, self.lifetime)


class RandomVisualEffectFactory(GameObjectFactory):
    def __init__(self, game_object_collection: GameObjectCollection, effect_surfaces: List[pygame.Surface], lifetime: int):
        self.effect_surfaces = effect_surfaces
        self.lifetime = lifetime
        super().__init__(game_object_collection, self.create)

    def create(self, position) -> VisualEffect:
        random_effect = random.choice(self.effect_surfaces)
        return VisualEffect(self.game_object_collection, random_effect, position, self.lifetime)


class VisualEffect(GameObject):
    """
    A visual effect that is drawn on the screen for a certain amount of time.
    Fades out over time.
    Destroyed when the lifetime is over.
    """

    def __init__(self, game_object_collection: GameObjectCollection, drawn_surface: pygame.Surface, position: tuple[int, int], lifetime, layer=None):
        self.lifetime = lifetime
        self.start_time = pygame.time.get_ticks()
        self.alpha = 255
        if layer is None:
            layer = LAYER_EFFECTS
        super().__init__(game_object_collection, drawn_surface, position, layer)

    def update(self, delta_time):
        super().update(delta_time)
        elapsed_time = pygame.time.get_ticks() - self.start_time
        if elapsed_time >= self.lifetime:
            self.destroy()
        else:
            # Calculate alpha value based on elapsed time and lifetime
            progress_factor = elapsed_time / self.lifetime
            self.alpha = 255 - int(progress_factor * 255)
            self.drawn_surface.set_alpha(self.alpha)


class DamageNumberVisualEffectFactory(GameObjectFactory):
    def __init__(self, game_object_collection: GameObjectCollection, font, text, color, lifetime: int):
        self.font = font
        self.text = text
        self.color = color
        self.lifetime = lifetime
        self.layer = None
        super().__init__(game_object_collection, self.create)

    def create(self, position) -> DamageNumberVisualEffect:
        return DamageNumberVisualEffect(self.game_object_collection, self.font, self.text, self.color, position, self.lifetime, self.layer)

    def set_target_text(self, text):
        self.text = text

    def set_target_color(self, color):
        self.color = color

    def set_layer(self, layer):
        self.layer = layer


class DamageNumberVisualEffect(VisualEffect):
    """
    A visual effect that is drawn on the screen for a certain amount of time.
    Moves up and fades out over time.
    """

    def __init__(self, game_object_collection: GameObjectCollection, font, text, color, position: tuple[int, int], lifetime, layer=None):
        text_surface = font.render(f"{text}", True, color)
        self.start_x = position[0]
        tween_start_y = position[1]
        tween_end_y = tween_start_y - 200
        self.tween = Tween(tween_start_y, tween_end_y, lifetime / 1000)
        super().__init__(game_object_collection, text_surface, position, lifetime, layer)

    def update(self, delta_time):
        new_y = self.tween.update(delta_time)
        # Get sine value in range 0 to 1
        new_x = self.start_x + (np.sin(new_y / 20) * 20)
        self.rect.center = (new_x, new_y)
        super().update(delta_time)
