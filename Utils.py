import hashlib

import pygame

from Input import Inputs


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
        else:
            save_game_name += Inputs.get_unicode()

        screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 36)

        note_text = font.render("Note: Your save name is used as the world generation seed.", True, (180, 180, 180))
        screen.blit(note_text, (10, 40))

        input_text = font.render("New save name: " + save_game_name, True, (255, 255, 255))
        screen.blit(input_text, (10, 110))
        button = pygame.Rect(10, 110, 800, 30)
        pygame.draw.rect(screen, (100, 100, 100), button, 1)

        note_text_1 = font.render("Available saved games (click to load):", True, (255, 0, 0))
        screen.blit(note_text_1, (10, 180))

        # List all existing save games
        for index, existing_game_save in enumerate(available_save_games):
            save_game_text = font.render(existing_game_save, True, (0, 255, 0))
            screen.blit(save_game_text, (10, 210 + (index * 30)))
            # draw a rect over the save game
            button = pygame.Rect(10, 210 + (index * 30), 400, 30)
            pygame.draw.rect(screen, (100, 100, 100), button, 1)
            if Inputs.is_mouse_button_pressed(1):
                if button.collidepoint(Inputs.get_mouse_position()):
                    save_game_name = existing_game_save
                    input_active = False

        pygame.display.flip()

    return save_game_name
