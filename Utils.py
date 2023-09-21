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


def get_random_inside_unit_rect() -> tuple[float, float]:
    """Returns a random point inside a unit rectangle.
    The unit rect is a square with both sides' width as 1, centered at (0, 0).
    """
    # Get a random point inside a unit square
    x = random.random() * 2 - 1
    y = random.random() * 2 - 1
    return x, y


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
