import hashlib
import random

import pygame

from Input import Inputs
import Saving


def hash_seed(seed):
    sha256 = hashlib.sha256(seed.encode()).hexdigest()
    seed_integer = int(sha256, 16)
    return seed_integer


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolate on the scale given by a to b, using t as the point on that scale.
    Examples
    --------
        50 == lerp(0, 100, 0.5)
        4.2 == lerp(1, 5, 0.8)
    """
    return (1 - t) * a + t * b


class ValueTween:
    def __init__(self, start_value, end_value, duration):
        self.start_value = start_value
        self.current_value = start_value
        self.end_value = end_value
        self.duration: float = duration
        self.elapsed_time: float = 0
        self.is_finished = False

    def update(self, dt):
        self.elapsed_time += dt
        if self.elapsed_time >= self.duration:
            self.is_finished = True
            self.current_value = self.end_value
            return self.current_value

        # Calculate the new draw_position and scale based on interpolation
        progress = self.elapsed_time / self.duration
        new_value = lerp(self.start_value, self.end_value, progress)

        # Update the draw_position and scale
        self.current_value = new_value
        return self.current_value


def get_random_inside_rect(rect_size) -> tuple[float, float]:
    """Returns a random point inside a unit rectangle.
    The unit rect is a square with both sides' width as 1, centered at (0, 0).
    """
    # Get a random point inside a unit square
    x = (random.random() * 2 - 1) * rect_size
    y = (random.random() * 2 - 1) * rect_size
    return x, y


def load_image(path):
    try:
        return pygame.image.load(path)
    except pygame.error as e:
        print(f"Error loading image @ {path}: {str(e)}")


def get_save_game_name(screen, available_save_games):
    save_game_name = ""
    input_active = True

    while input_active:
        Inputs.handle_input_events()
        if Inputs.should_quit():
            pygame.quit()
            quit()
        if Inputs.is_key_pressed(pygame.K_RETURN):
            if save_game_name and (save_game_name not in available_save_games):
                input_active = False
        elif Inputs.is_key_pressed(pygame.K_BACKSPACE):
            save_game_name = save_game_name[:-1]
        elif len(save_game_name) < 20:
            save_game_name += Inputs.get_unicode()

        screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 36)

        note_text = font.render("Note: Your save name is used as the world generation seed.", True, (180, 180, 180))
        screen.blit(note_text, (10, 40))

        input_text = font.render("New save name: " + save_game_name, True, (255, 255, 255))
        screen.blit(input_text, (10, 110))
        button = pygame.Rect(10, 110, 800, 30)
        pygame.draw.rect(screen, (100, 100, 100), button, 1)

        note_text_1 = font.render("Available saved games (click to load):", True, (180, 180, 180))
        screen.blit(note_text_1, (10, 180))

        # List all existing save games
        for index, existing_game_save in enumerate(available_save_games):
            save = Saving.load_save_game(existing_game_save)

            # Split the text into two parts
            name_text = font.render(existing_game_save, True, (210, 210, 210))
            info_text = font.render(f"(room {save.dungeon_room_index + 1}, {save.player_health} health)", True, (210, 210, 210))

            # Get rectangles for both texts
            name_rect = name_text.get_rect()
            info_rect = info_text.get_rect()

            # Set the positions
            name_rect.topleft = (10, 210 + (index * 30))
            info_rect.topleft = (280, name_rect.top)  # Info starts at the same x-coordinate as the name

            # Blit both texts
            screen.blit(name_text, name_rect)
            screen.blit(info_text, info_rect)

            # draw a rect over the save game (use name_rect for positioning)
            button = pygame.Rect(name_rect.left, name_rect.top, 530, 30)
            pygame.draw.rect(screen, (100, 100, 100), button, 1)
            if Inputs.is_mouse_button_pressed(1):
                if button.collidepoint(Inputs.get_mouse_position()):
                    save_game_name = existing_game_save
                    input_active = False

        pygame.display.flip()

    return save_game_name
