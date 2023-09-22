import pygame

import StateManagement
from Constants import DEFAULT_DRAW_ORDER
from Drawing import Drawable


class GameObject(Drawable):
    """
    A base class for all game objects. Game objects are objects that are updated and drawn every frame.
    Automatically adds itself to the game state's list of game objects.
    Automatically destroys itself when it is removed from the game state's list of game objects.
    """
    def __init__(self, game_state, drawn_surface: pygame.Surface, position, scale_multiplier=1.0, draw_order=DEFAULT_DRAW_ORDER):
        super().__init__(drawn_surface, position, draw_order)
        self.game_state: StateManagement.GameState = game_state
        """A reference to the current GameState object. Useful for accessing game data."""
        self.rect: pygame.Rect = drawn_surface.get_rect()
        self.rect.center = position
        """The rect of the object."""
        self.scale_multiplier: float = scale_multiplier
        """A multiplier to scale the object by. Useful for scaling up sprites that are too small/large."""
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
