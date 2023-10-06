#
# Project: Slay the Python
# Author: Jasper Honkasalo
# Description: Contains classes for drawing to the debug_screen.
#

import pygame


class Drawable:
    """
    An object that can be drawn to the debug_screen.
    Not automatically added to the frame buffer.
    """
    def __init__(self, drawn_surface: pygame.Surface, draw_position, draw_order: int, alpha=255):
        self.drawn_surface: pygame.Surface = drawn_surface
        """The surface that will be drawn to the debug_screen."""
        self.draw_position: tuple = draw_position
        """The card_position on the debug_screen where the drawn surface will be drawn."""
        self.draw_order: int = draw_order
        """The order in which this object will be drawn. Objects with a lower draw order will be drawn first."""

    def draw(self, screen: pygame.Surface):
        screen.blit(self.drawn_surface, self.draw_position)


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

    def clear(self):
        self.drawables.clear()


class DrawCall(Drawable):
    """
    A draw call for a single frame.
    Useful for drawing sprites that are not GameObjects.
    Call queue() to automatically add the draw call to the frame buffer.
    """
    def __init__(self, image: pygame.Surface, position_or_rect, draw_order: int):
        self.image = image
        self.draw_order = draw_order
        if isinstance(position_or_rect, pygame.Rect):
            self.position = position_or_rect.topleft
        else:
            self.position = position_or_rect
        super().__init__(image, self.position, draw_order)

    def queue(self, game_state):
        game_state.frame_buffer.add_drawable(self)
