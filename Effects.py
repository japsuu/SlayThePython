import pygame


class VisualEffect:
    def __init__(self, sprite: pygame.Surface, position: tuple[int, int], lifetime):
        self.sprite = sprite
        self.position = position
        self.lifetime = lifetime
        self.start_time = pygame.time.get_ticks()
        self.alpha = 255

    def update(self):
        elapsed_time = pygame.time.get_ticks() - self.start_time
        if elapsed_time >= self.lifetime:
            return True  # VisualEffect has exceeded its lifetime and should be removed
        else:
            # Calculate alpha value based on elapsed time and lifetime
            self.alpha = 255 - int((elapsed_time / self.lifetime) * 255)
            return False

    def draw(self, surface):
        self.sprite.set_alpha(self.alpha)
        surface.blit(self.sprite, (self.position[0] - self.sprite.get_width() // 2, self.position[1] - self.sprite.get_height() // 2))
