from __future__ import annotations
from typing import TYPE_CHECKING

from utils.constants import FONT_TOOLTIP_GENERIC, LAYER_OVERRIDE_FG, FONT_BUTTON_GENERIC, LAYER_OVERRIDE_BG
from utils.input import Inputs

import pygame

if TYPE_CHECKING:
    from typing import List, Optional


class Drawable:
    """
    An object that can be drawn to the screen.
    Not automatically added to the frame buffer.
    Optionally has a tooltip.
    """
    def __init__(self, drawn_surface: pygame.Surface, position, draw_order: int, tooltip: Optional[Drawable], mask_tooltip_surface: bool = True, blocks_tooltips: bool = False):
        self.drawn_surface: pygame.Surface = drawn_surface
        """The surface that will be drawn to the screen."""
        self.rect: pygame.Rect = drawn_surface.get_rect()
        """The rect of the object. Sets where the drawn surface will be drawn"""
        self.rect.center = position
        self.draw_order: int = draw_order
        """The order in which this object will be drawn. Objects with a lower draw order will be drawn first."""
        self.tooltip: Drawable = tooltip
        """The tooltip that will be shown when the mouse hovers over this object."""
        self.mask_tooltip_surface = mask_tooltip_surface
        self.blocks_tooltips = blocks_tooltips

    def draw(self, screen: pygame.Surface):
        screen.blit(self.drawn_surface, self.rect)

    def should_show_tooltip(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            if not self.mask_tooltip_surface:
                return True
            mask = pygame.mask.from_surface(self.drawn_surface)
            pos_x = mouse_pos[0] - self.rect.x
            pos_y = mouse_pos[1] - self.rect.y
            if pos_x < self.drawn_surface.get_width() and pos_y < self.drawn_surface.get_height():
                return mask.get_at((pos_x, pos_y))
        return False

    def update_tooltip_position(self, screen: pygame.Surface, mouse_position):
        if self.tooltip is None:
            return
        self.tooltip.rect.topleft = (mouse_position[0] + 10, mouse_position[1] + 10)
        self.tooltip.rect.clamp_ip(screen.get_rect())


class FrameBuffer:
    """
    A buffer that stores drawables and draws them in order based on their draw order attribute.
    The buffer is cleared at the end of each frame.
    """
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.drawables: list[Drawable] = []

    def add_drawable(self, drawable: Drawable):
        self.drawables.append(drawable)

    def draw(self):
        # Sort the drawables based on their draw order attribute
        sorted_drawables = sorted(self.drawables, key=lambda d: d.draw_order)

        for drawable in sorted_drawables:
            drawable.draw(self.screen)

        mouse_pos = Inputs.get_mouse_position()
        # Reverse the list so that the drawables with the highest draw order are checked first.
        for drawable in reversed(sorted_drawables):
            if self.__draw_object_tooltip(drawable, mouse_pos):
                break

    def __draw_object_tooltip(self, drawable: Drawable, mouse_pos) -> bool:
        """
        Call the draw method of the tooltip.
        Recursively repeat until the tooltip has no tooltip.
        :param drawable: The drawable to draw the tooltip for.
        :param mouse_pos: The mouse position.
        :return: True if the mouse collided with the drawable's rect.
        """
        drawable.update_tooltip_position(self.screen, mouse_pos)
        if drawable.should_show_tooltip(mouse_pos):
            if drawable.tooltip is None:
                if drawable.blocks_tooltips:
                    return True
                return False
            drawable.tooltip.draw(self.screen)
            self.__draw_object_tooltip(drawable.tooltip, mouse_pos)
            return True
        return False

    def clear(self):
        self.drawables.clear()


class TextTooltip(Drawable):
    """
    A tooltip that displays multiple lines of text.
    """
    def __init__(self, text_lines: List[str]):
        self.TEXT_PADDING = 5
        self.TEXT_SPACING = 5
        self.text_lines = text_lines
        self.text_surfaces = [FONT_TOOLTIP_GENERIC.render(line, True, (255, 255, 255)) for line in self.text_lines]
        self.width = max([surface.get_width() for surface in self.text_surfaces]) + self.TEXT_PADDING * 2
        self.height = sum([surface.get_height() for surface in self.text_surfaces]) + self.TEXT_SPACING * (len(self.text_surfaces) - 1) + self.TEXT_PADDING * 2
        self.__surface: Optional[pygame.Surface] = pygame.Surface((self.width, self.height))
        self.__surface.set_alpha(200)
        super().__init__(self.__surface, (0, 0), LAYER_OVERRIDE_FG, None)
        # Draw tooltip background
        self.__surface.fill((80, 80, 80))
        # Draw tooltip bounds
        rect = pygame.Rect(0, 0, self.width, self.height)
        pygame.draw.rect(self.__surface, (255, 255, 255), rect, 1)
        # Draw tooltip text
        for i, surface in enumerate(self.text_surfaces):
            self.__surface.blit(surface, (self.TEXT_PADDING, self.TEXT_PADDING + i * (surface.get_height() + self.TEXT_SPACING)))


class DrawCall(Drawable):
    """
    A draw call for a single frame.
    Useful for drawing sprites that are not GameObjects.
    Call queue() to automatically add the draw call to the frame buffer.
    """
    def __init__(self, image: pygame.Surface, position_or_rect, draw_order: int, tooltip_text_lines: List[str] = None, mask_tooltip_surface: bool = True, blocks_tooltips: bool = False):
        self.image = image
        self.draw_order = draw_order
        self.frame_buffer: Optional[FrameBuffer] = None
        if isinstance(position_or_rect, pygame.Rect):
            self.position = position_or_rect.center
        else:
            self.position = position_or_rect
        if (tooltip_text_lines is not None) and len(tooltip_text_lines) > 0:
            super().__init__(image, self.position, draw_order, TextTooltip(tooltip_text_lines), mask_tooltip_surface, blocks_tooltips)
        else:
            super().__init__(image, self.position, draw_order, None, mask_tooltip_surface=mask_tooltip_surface, blocks_tooltips=blocks_tooltips)

    def queue(self, frame_buffer: FrameBuffer):
        self.frame_buffer = frame_buffer
        self.frame_buffer.add_drawable(self)

    def should_show_tooltip(self, mouse_pos):
        should = super().should_show_tooltip(mouse_pos)
        return should


def draw_button(frame_buffer, text: str, button_rect: pygame.Rect, button_color: tuple, text_color: tuple, tooltip_text_lines=None):
    # Create the button sprite
    button_surface = pygame.Surface((button_rect.width, button_rect.height))
    button_surface.fill(button_color)

    # Create the button text
    text_surface = FONT_BUTTON_GENERIC.render(text, True, text_color)

    # Calculate button and text positions
    text_rect = text_surface.get_rect()
    text_rect.center = button_rect.center

    if tooltip_text_lines:
        DrawCall(button_surface, button_rect, LAYER_OVERRIDE_BG, tooltip_text_lines).queue(frame_buffer)
        DrawCall(text_surface, text_rect, LAYER_OVERRIDE_BG).queue(frame_buffer)
    else:
        DrawCall(button_surface, button_rect, LAYER_OVERRIDE_BG).queue(frame_buffer)
        DrawCall(text_surface, text_rect, LAYER_OVERRIDE_BG).queue(frame_buffer)
    return button_rect


def is_rect_clicked(rect: pygame.Rect):
    if Inputs.is_mouse_button_up(1):
        if rect.collidepoint(Inputs.get_mouse_position()):
            return True
    return False
