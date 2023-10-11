from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from typing import List


# def transform_resource_path(relative_path):     # PyInstaller support
#     # noinspection PyBroadException
#     try:
#         # noinspection PyUnresolvedReferences,PyProtectedMember
#         base_path = sys._MEIPASS
#     except Exception:
#         base_path = os.path.abspath(".")
#
#     return os.path.join(base_path, relative_path)


def load_image(path, convert_alpha=True):
    # asset_url = transform_resource_path(path)
    try:
        img = pygame.image.load(path)
        if convert_alpha:
            return img.convert_alpha()
        return img
    except pygame.error as e:
        raise SystemExit(f"Error loading image @ {path}: {str(e)}")


class ImageLibrary:
    def __init__(self):
        # UI
        self.icon_level: pygame.Surface = load_image("Content/Sprites/UI/icon_level.png")
        self.icon_draw_pile: pygame.Surface = load_image("Content/Sprites/UI/icon_draw_pile.png")
        self.icon_discard_pile: pygame.Surface = load_image("Content/Sprites/UI/icon_discard_pile.png")
        self.icon_target: pygame.Surface = load_image("Content/Sprites/UI/icon_target.png")
        self.icon_mana: pygame.Surface = load_image("Content/Sprites/UI/icon_mana.png")
        self.icon_block: pygame.Surface = load_image("Content/Sprites/UI/icon_block.png")
        self.icon_health: pygame.Surface = load_image("Content/Sprites/UI/icon_health.png")
        # Intention icons
        self.icon_intention_block: pygame.Surface = load_image("Content/Sprites/UI/icon_intention_block.png")
        self.icon_intention_buff: pygame.Surface = load_image("Content/Sprites/UI/icon_intention_buff.png")
        self.icon_intention_unknown: pygame.Surface = load_image("Content/Sprites/UI/icon_intention_unknown.png")
        self.icon_intention_damage_low: pygame.Surface = load_image("Content/Sprites/UI/icon_intention_damage_low.png")
        self.icon_intention_damage_medium: pygame.Surface = load_image("Content/Sprites/UI/icon_intention_damage_medium.png")
        self.icon_intention_damage_high: pygame.Surface = load_image("Content/Sprites/UI/icon_intention_damage_high.png")
        self.icon_intention_damage_veryhigh: pygame.Surface = load_image("Content/Sprites/UI/icon_intention_damage_veryhigh.png")

        # Effects
        self.effect_damaged_self: pygame.Surface = load_image("Content/Sprites/Effects/effect_damaged_self.png")
        self.slash_effects_list: List[pygame.Surface] = [
            load_image("Content/Sprites/Effects/effect_slash_1.png"),
            load_image("Content/Sprites/Effects/effect_slash_2.png"),
            load_image("Content/Sprites/Effects/effect_slash_3.png"),
            load_image("Content/Sprites/Effects/effect_slash_4.png")
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
