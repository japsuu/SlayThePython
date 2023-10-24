from __future__ import annotations

from typing import TYPE_CHECKING

from utils.math import ceil_div

if TYPE_CHECKING:
    from typing import Optional

import pygame

from utils import animations, math
from utils.input import Inputs


class GridLayout:
    PADDING = 10

    def __init__(self, item_size, max_horizontal_items):
        self.item_size = item_size
        self.max_horizontal_items = max_horizontal_items
        self.item_reposition_funcs = {}
        self.scroll_offset = 0
        self.scroll_tween: Optional[animations.Tween] = None

    def add_item(self, game_object, reposition_func):
        self.item_reposition_funcs[game_object] = reposition_func

    def remove_item(self, game_object):
        self.item_reposition_funcs.pop(game_object)

    def clear(self):
        self.item_reposition_funcs.clear()

    def update(self, delta_time):
        if self.scroll_tween is not None:
            self.scroll_tween.update(delta_time)
            if self.scroll_tween.is_finished:
                self.scroll_tween = None
        self.__handle_scroll()
        x, y = self.PADDING, self.PADDING

        for index, reposition_func in enumerate(self.item_reposition_funcs.values()):
            setter, getter = reposition_func
            item_x = x + (index % self.max_horizontal_items) * (self.item_size[0] + self.PADDING)
            item_y = 80 + y + (index // self.max_horizontal_items) * (self.item_size[1] + self.PADDING)

            # Adjust position for scrolling
            item_y += self.scroll_offset
            target = math.lerp_tuple(getter(), (item_x, item_y), 0.1)
            setter(target)

    def __get_max_scroll_offset(self):
        return max(0, ceil_div(len(self.item_reposition_funcs), self.max_horizontal_items) * (self.item_size[1] + self.PADDING) - 600)

    def __handle_scroll(self):
        if Inputs.is_mouse_button_pressed(pygame.BUTTON_WHEELUP):
            self.scroll_tween = animations.Tween(
                self.scroll_offset,
                self.scroll_offset + 100,
                0.1,
                self.__update_scroll_offset
            )
        elif Inputs.is_mouse_button_pressed(pygame.BUTTON_WHEELDOWN):
            self.scroll_tween = animations.Tween(
                self.scroll_offset,
                self.scroll_offset - 100,
                0.1,
                self.__update_scroll_offset
            )

    def __update_scroll_offset(self, new_offset):
        self.scroll_offset = new_offset
        if self.scroll_offset > 0:
            self.scroll_offset = 0
        elif self.scroll_offset < -self.__get_max_scroll_offset():
            self.scroll_offset = -self.__get_max_scroll_offset()
