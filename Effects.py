import pygame

import GameObjects
from Utils import ValueTween


class VisualEffect(GameObjects.GameObject):
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
        self.tween = ValueTween(tween_start_y, tween_end_y, lifetime)

    def update(self):
        new_y = self.tween.update(self.game_state.delta_time)
        self.rect.center = (self.start_x, new_y)
        super().update()
