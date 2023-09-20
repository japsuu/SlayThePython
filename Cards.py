import json

import pygame

from Utils import lerp


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


class GameCard(pygame.sprite.Sprite):
    def __init__(self, card_data, x, y):
        super().__init__()
        self.card_data: CardData = card_data
        self.image = pygame.image.load(self.card_data.sprite_path)
        self.rect = self.image.get_rect()
        self.original_position = (x, y)
        self.target_position = (x, y)
        self.original_scale = (int(self.image.get_width()), int(self.image.get_height()))
        self.current_scale_factor = 1.0
        self.target_scale_factor = self.current_scale_factor
        self.rect.center = (x, y)
        self.position_lerp_duration = 0.5
        self.scale_lerp_duration = 3
        self.lerp_start_time = None

        # Define font and text color for card stats
        self.font = pygame.font.Font(None, 36)
        self.mana_font = pygame.font.Font(None, 65)
        self.text_color = (255, 255, 255)  # White color for text
        self.mana_cost_text_color = (0, 0, 0)  # Blue color for cost text

        # Flag to track if the card is selected (clicked)
        self.marked_for_cleanup = False

    def draw(self, screen):

        # Lerp position to target position
        if self.lerp_start_time is not None:
            current_time = pygame.time.get_ticks()
            elapsed_time = (current_time - self.lerp_start_time) / 1000  # Convert to seconds

            # Calculate position lerping progress (0 to 1)
            pos_lerp_progress = elapsed_time / self.position_lerp_duration
            if pos_lerp_progress >= 1:
                self.rect.center = self.target_position
            else:
                # Lerp the card's position
                self.rect.center = pygame.math.Vector2(self.rect.center).lerp(self.target_position, pos_lerp_progress)

            # Calculate scale lerping progress (0 to 1)
            scale_lerp_progress = elapsed_time / self.scale_lerp_duration
            if scale_lerp_progress >= 1:
                self.current_scale_factor = self.target_scale_factor
            else:
                # Lerp the scale
                self.current_scale_factor = lerp(self.current_scale_factor, self.target_scale_factor, scale_lerp_progress)

        self.image = pygame.transform.scale(self.image, (self.original_scale[0] * self.current_scale_factor, self.original_scale[1] * self.current_scale_factor))

        # Draw the card image onto the screen
        screen.blit(self.image, self.rect.topleft)

        # Create text surfaces for card stats
        card_name_surface = self.font.render(self.card_data.card_name, True, self.text_color)
        card_description_surface = self.font.render(self.card_data.card_description, True, self.text_color)
        card_cost_surface = self.mana_font.render(f"{self.card_data.card_cost}", True, self.mana_cost_text_color)

        # Set positions for text surfaces
        card_name_rect = card_name_surface.get_rect()
        card_description_rect = card_description_surface.get_rect()
        card_cost_rect = card_cost_surface.get_rect()

        card_name_rect.midtop = (self.rect.centerx + 20, self.rect.top + 55)
        card_description_rect.midtop = (self.rect.centerx, self.rect.bottom - 250)
        card_cost_rect.center = (self.rect.topleft[0] + 55, self.rect.topleft[1] + 55)

        # Blit the text surfaces onto the card image
        screen.blit(pygame.transform.scale(card_name_surface, (card_name_surface.get_width() * self.current_scale_factor, card_name_surface.get_height() * self.current_scale_factor)),
                    card_name_rect)
        screen.blit(pygame.transform.scale(card_description_surface,
                                           (card_description_surface.get_width() * self.current_scale_factor, card_description_surface.get_height() * self.current_scale_factor)),
                    card_description_rect)
        screen.blit(pygame.transform.scale(card_cost_surface, (card_cost_surface.get_width() * self.current_scale_factor, card_cost_surface.get_height() * self.current_scale_factor)),
                    card_cost_rect)

    def set_target_position_and_scale(self, pos, scale: float, pos_lerp_duration: float = 0.5, scale_lerp_duration: float = 3):
        if self.marked_for_cleanup:
            return
        self.target_position = pos
        self.target_scale_factor = scale
        self.position_lerp_duration = pos_lerp_duration
        self.scale_lerp_duration = scale_lerp_duration
        self.lerp_start_time = pygame.time.get_ticks()

    def has_completed_lerps(self):
        return self.rect.center == self.target_position and self.current_scale_factor == self.target_scale_factor

    def should_delete(self):
        return self.marked_for_cleanup and self.has_completed_lerps()
